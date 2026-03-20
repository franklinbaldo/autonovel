#!/usr/bin/env python3
"""
Central orchestrator for autonovel, applying sequential orchestration logic.
It uses git-chaining and session_state.json persistence.
"""
import os
import sys
import json
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).parent
STATE_FILE = BASE_DIR / "session_state.json"
AGENTS_DIR = BASE_DIR / "agents"

def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"phase": "drafting", "current_chapter": 1, "chapters_drafted": 0}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def run_agent(agent_name, script_name, *args):
    """Run an agent script from the specific agents directory."""
    script_path = AGENTS_DIR / agent_name / script_name
    cmd = [sys.executable, str(script_path)] + list(args)
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running {agent_name}/{script_name}:")
        print(result.stderr)
        return False, result.stdout
    return True, result.stdout

def git_commit(message):
    subprocess.run(["git", "add", "-A"], cwd=BASE_DIR, check=True)
    subprocess.run(["git", "commit", "-m", message, "--allow-empty"], cwd=BASE_DIR, check=True)

def git_reset():
    subprocess.run(["git", "reset", "--hard", "HEAD~1"], cwd=BASE_DIR, check=True)

def parse_score(eval_out):
    """Parse a score from evaluate.py output."""
    for line in eval_out.splitlines():
        if "overall_score:" in line:
            try:
                return float(line.split(":")[1].strip())
            except ValueError:
                pass
    return 0.0

def get_total_chapters(state):
    if state.get("chapters_total", 0) > 0:
        return state["chapters_total"]

    # Try to read outline.md
    outline = BASE_DIR / "outline.md"
    if outline.exists():
        import re
        text = outline.read_text()
        match = re.search(r'\*\*(\d+)\s+chapters', text)
        if match:
            state["chapters_total"] = int(match.group(1))
            save_state(state)
            return int(match.group(1))
    return 20 # default if cannot determine

def main():
    state = load_state()
    print("Starting pipeline orchestrator...")

    if state["phase"] == "drafting":
        ch = state.get("current_chapter", 1)
        total_chapters = get_total_chapters(state)

        while ch <= total_chapters:
            print(f"\n--- Drafting Chapter {ch} ---")
            success, out = run_agent("drafter", "draft_chapter.py", str(ch))
            if not success:
                print("Drafting failed, retrying...")
                continue

            success, eval_out = run_agent("evaluator", "evaluate.py", f"--chapter={ch}")
            if not success:
                print("Evaluation failed. Retrying...")
                subprocess.run(["git", "restore", "."], cwd=BASE_DIR)
                subprocess.run(["git", "clean", "-f"], cwd=BASE_DIR)
                continue

            score = parse_score(eval_out)
            print(f"Chapter {ch} score: {score}")

            if score > 6.0:
                git_commit(f"Draft chapter {ch} (score: {score})")
                state["chapters_drafted"] = ch
                ch += 1
                state["current_chapter"] = ch
                save_state(state)
            else:
                print(f"Score too low ({score}), reverting and retrying...")
                subprocess.run(["git", "restore", "."], cwd=BASE_DIR)
                subprocess.run(["git", "clean", "-f"], cwd=BASE_DIR)

        print("\nDrafting complete. Building outline...")
        success, out = run_agent("outliner", "build_outline.py")
        if success:
            git_commit("Rebuild outline")
            state["phase"] = "completed"
            save_state(state)

if __name__ == "__main__":
    main()
