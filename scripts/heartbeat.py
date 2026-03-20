#!/usr/bin/env python3
"""
heartbeat.py -- Novel pipeline session orchestrator.

Manages the Jules Sequence lifecycle for autonovel:
  - Creates sessions for the next pipeline task
  - Sends continuation messages to active sessions
  - Tracks session state in sessions/
  - Advances the pipeline when sessions complete

Inspired by the rosencrantz-coin and Verne heartbeat patterns.

Commands:
  python scripts/heartbeat.py status        # Show current state
  python scripts/heartbeat.py heartbeat     # Main loop: check/create/continue
  python scripts/heartbeat.py force-new     # Force new session regardless of TTL
  python scripts/heartbeat.py create        # Create session for next task

Environment:
  JULES_API_KEY     -- Google Jules API key (required)
  GH_TOKEN          -- GitHub token for PR operations (optional)
"""
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
AGENTS_DIR = BASE_DIR / "agents"
SESSIONS_DIR = BASE_DIR / "sessions"
HISTORY_DIR = SESSIONS_DIR / "history"
HEARTBEAT_DIR = BASE_DIR / "sessions" / "heartbeats"
STATE_FILE = BASE_DIR / "state.json"

JULES_API_KEY = os.environ.get("JULES_API_KEY", "")
JULES_API_BASE = "https://jules.googleapis.com/v1alpha"

# Session TTL: 12 hours (after this, create a new one)
SESSION_TTL_HOURS = 12

# Terminal states
TERMINAL_STATES = {"COMPLETED", "FAILED", "CANCELLED"}
ACTIVE_STATES = {"IN_PROGRESS", "WAITING_FOR_USER_RESPONSE", "AWAITING_PLAN_APPROVAL"}

# Phase → agent mapping
PHASE_TO_AGENT = {
    "foundation": "foundation",
    "drafting": "drafter",
    "revision": "reviser",
    "export": "exporter",
}


def now_utc():
    return datetime.now(timezone.utc)


def api_get(path):
    """GET from Jules API."""
    import requests
    resp = requests.get(
        f"{JULES_API_BASE}{path}",
        headers={"x-goog-api-key": JULES_API_KEY},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def api_post(path, body=None):
    """POST to Jules API."""
    import requests
    resp = requests.post(
        f"{JULES_API_BASE}{path}",
        headers={
            "x-goog-api-key": JULES_API_KEY,
            "Content-Type": "application/json",
        },
        json=body or {},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def load_state():
    """Load pipeline state."""
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {
        "phase": "foundation",
        "iteration": 0,
        "foundation_score": 0.0,
        "lore_score": 0.0,
        "chapters_drafted": 0,
        "chapters_total": 0,
        "novel_score": 0.0,
        "revision_cycle": 0,
        "debts": [],
    }


def save_state(state):
    """Save pipeline state."""
    STATE_FILE.write_text(json.dumps(state, indent=2) + "\n")


def _agent_sessions_dir(agent_name):
    """Get the active-sessions directory for an agent."""
    d = AGENTS_DIR / agent_name / "active-sessions"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _list_active_sessions(agent_name):
    """List active session files for an agent (newest first)."""
    d = _agent_sessions_dir(agent_name)
    return sorted(d.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)


def load_current_session(agent_name=None):
    """Load newest active session for an agent, or global fallback."""
    if agent_name:
        for path in _list_active_sessions(agent_name):
            try:
                return json.loads(path.read_text())
            except (json.JSONDecodeError, OSError):
                continue
        return None
    # Legacy global fallback
    path = SESSIONS_DIR / "current.json"
    if path.exists():
        return json.loads(path.read_text())
    return None


def save_current_session(session_data, agent_name=None):
    """Save session as individual file named by session_id."""
    session_id = session_data.get("session_id", "unknown")
    if agent_name:
        path = _agent_sessions_dir(agent_name) / f"{session_id}.json"
    else:
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        path = SESSIONS_DIR / f"{session_id}.json"
    path.write_text(json.dumps(session_data, indent=2) + "\n")


def archive_session(session_data, final_state="COMPLETED", agent_name=None):
    """Move session file to history/ subdirectory."""
    session_id = session_data.get("session_id", "unknown")
    session_data["final_state"] = final_state
    session_data["finished_at"] = now_utc().isoformat()

    if agent_name:
        hist_dir = _agent_sessions_dir(agent_name) / "history"
        active_file = _agent_sessions_dir(agent_name) / f"{session_id}.json"
    else:
        hist_dir = HISTORY_DIR
        active_file = SESSIONS_DIR / f"{session_id}.json"

    hist_dir.mkdir(parents=True, exist_ok=True)
    (hist_dir / f"{session_id}.json").write_text(
        json.dumps(session_data, indent=2) + "\n"
    )
    if active_file.exists():
        active_file.unlink()
    # Clean up legacy current.json if it exists
    legacy = (SESSIONS_DIR / "current.json")
    if not agent_name and legacy.exists():
        legacy.unlink()


def get_session_state(session_id):
    """Query Jules API for session state."""
    try:
        resp = api_get(f"/sessions/{session_id}")
        return resp.get("state", "UNKNOWN")
    except Exception as e:
        print(f"  Warning: could not check session {session_id}: {e}")
        return "UNKNOWN"


def is_session_expired(session_data):
    """Check if session has exceeded TTL."""
    created = session_data.get("created_at", "")
    if not created:
        return True
    try:
        created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
        age_hours = (now_utc() - created_dt).total_seconds() / 3600
        return age_hours > SESSION_TTL_HOURS
    except (ValueError, TypeError):
        return True


def determine_next_task(state):
    """
    Determine the next pipeline task based on state.

    Returns dict with: phase, chapter (optional), hint (optional)
    Returns None if pipeline is complete.
    """
    phase = state.get("phase", "foundation")

    if phase == "complete":
        return None

    if phase == "foundation":
        score = state.get("foundation_score", 0)
        lore = state.get("lore_score", 0)
        iteration = state.get("iteration", 0)
        if score >= 7.5 and lore >= 7.0:
            return {"phase": "drafting", "hint": "Foundation complete, begin drafting"}
        if iteration >= 20:
            return {"phase": "drafting", "hint": "Max iterations reached, begin drafting"}
        return {"phase": "foundation"}

    if phase == "drafting":
        drafted = state.get("chapters_drafted", 0)
        total = state.get("chapters_total", 0)
        if total > 0 and drafted >= total:
            return {"phase": "revision", "hint": "All chapters drafted, begin revision"}
        return {"phase": "drafting", "chapter": str(drafted + 1)}

    if phase == "revision":
        cycle = state.get("revision_cycle", 0)
        if cycle >= 6:
            return {"phase": "export", "hint": "Max revision cycles reached"}
        return {"phase": "revision"}

    if phase == "export":
        return {"phase": "export"}

    return None


def build_prompt(phase, chapter=None, hint=""):
    """Build session prompt by calling build-novel-prompt.py."""
    cmd = [sys.executable, str(BASE_DIR / "scripts" / "build-novel-prompt.py"),
           "--phase", phase]
    if chapter:
        cmd.extend(["--chapter", str(chapter)])
    if hint:
        cmd.extend(["--hint", hint])
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        print(f"  Error building prompt: {result.stderr}", file=sys.stderr)
        return f"Run the {phase} phase of the autonovel pipeline. {hint}"
    return result.stdout


def get_repo_name():
    """Get the GitHub repository name (owner/repo)."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True, cwd=str(BASE_DIR),
        )
        url = result.stdout.strip()
        # Extract owner/repo from various URL formats
        for prefix in ["https://github.com/", "git@github.com:"]:
            if prefix in url:
                repo = url.split(prefix)[-1].rstrip(".git")
                return repo
    except Exception:
        pass
    return os.environ.get("GITHUB_REPOSITORY", "")


def get_current_branch():
    """Get current git branch."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, cwd=str(BASE_DIR),
        )
        return result.stdout.strip()
    except Exception:
        return "main"


def create_session(phase, chapter=None, hint=""):
    """Create a new Jules session for the given task."""
    prompt = build_prompt(phase, chapter, hint)
    repo = get_repo_name()
    branch = get_current_branch()
    agent_name = PHASE_TO_AGENT.get(phase, phase)

    title = f"autonovel:{phase}"
    if chapter:
        title += f":ch{chapter}"

    print(f"  Creating session: {title} (agent: {agent_name})")
    print(f"  Source: {repo} (branch: {branch})")
    print(f"  Prompt: {len(prompt)} chars")

    body = {
        "prompt": prompt,
        "title": title,
        "sourceContext": {
            "source": f"sources/github/{repo}",
            "githubRepoContext": {"startingBranch": branch},
        },
        "automationMode": "AUTO_CREATE_PR",
    }

    resp = api_post("/sessions", body)
    session_id = resp.get("name", "").split("/")[-1] or resp.get("name", "")
    state = resp.get("state", "UNKNOWN")

    print(f"  Session created: {session_id} (state: {state})")

    session_data = {
        "session_id": session_id,
        "agent": agent_name,
        "phase": phase,
        "chapter": chapter,
        "hint": hint,
        "branch": branch,
        "created_at": now_utc().isoformat(),
    }
    save_current_session(session_data, agent_name=agent_name)
    return session_data


def send_continuation(session_id, message=None):
    """Send a continuation message to an active session."""
    msg = message or "Continue your work. Check state.json for progress. Commit when done."
    print(f"  Sending continuation to {session_id}")
    api_post(f"/sessions/{session_id}:sendMessage", {"prompt": msg})


def log_heartbeat(action, details=""):
    """Log a heartbeat event."""
    HEARTBEAT_DIR.mkdir(parents=True, exist_ok=True)
    ts = now_utc().strftime("%Y%m%d_%H%M%S")
    log = {
        "timestamp": now_utc().isoformat(),
        "action": action,
        "details": details,
    }
    log_file = HEARTBEAT_DIR / f"{ts}.json"
    log_file.write_text(json.dumps(log, indent=2) + "\n")


# ── Commands ──────────────────────────────────────────────────────


def _discover_agents():
    """Find all agent directories that have active-sessions/."""
    agents = []
    if AGENTS_DIR.exists():
        for d in sorted(AGENTS_DIR.iterdir()):
            if d.is_dir() and (d / "active-sessions").is_dir():
                agents.append(d.name)
    return agents


def cmd_status():
    """Show current pipeline and session status."""
    state = load_state()

    print("=== Pipeline State ===")
    print(f"  Phase:            {state.get('phase')}")
    print(f"  Foundation score: {state.get('foundation_score')}/10")
    print(f"  Lore score:       {state.get('lore_score')}/10")
    print(f"  Chapters:         {state.get('chapters_drafted')}/{state.get('chapters_total')}")
    print(f"  Novel score:      {state.get('novel_score')}/10")
    print(f"  Revision cycle:   {state.get('revision_cycle')}")

    # Show per-agent sessions
    agents = _discover_agents()
    has_active = False
    for agent_name in agents:
        session = load_current_session(agent_name=agent_name)
        if session:
            has_active = True
            session_id = session.get("session_id")
            api_state = get_session_state(session_id)
            print(f"\n=== Agent: {agent_name} ===")
            print(f"  Session: {session_id}")
            print(f"  Phase:   {session.get('phase')}")
            print(f"  Chapter: {session.get('chapter', 'n/a')}")
            print(f"  Created: {session.get('created_at')}")
            print(f"  State:   {api_state}")
            print(f"  Expired: {is_session_expired(session)}")

    # Fallback: check global session
    global_session = load_current_session()
    if global_session:
        has_active = True
        session_id = global_session.get("session_id")
        api_state = get_session_state(session_id)
        print(f"\n=== Global Session (legacy) ===")
        print(f"  ID:      {session_id}")
        print(f"  Phase:   {global_session.get('phase')}")
        print(f"  State:   {api_state}")

    if not has_active:
        print("\n  No active sessions")

    # Next task
    task = determine_next_task(state)
    if task:
        print(f"\n=== Next Task ===")
        print(f"  Phase:   {task.get('phase')}")
        if task.get("chapter"):
            print(f"  Chapter: {task['chapter']}")
        if task.get("hint"):
            print(f"  Hint:    {task['hint']}")
    else:
        print("\n  Pipeline complete!")


def cmd_heartbeat(force_new=False):
    """Main heartbeat loop: check per-agent sessions, create/continue as needed."""
    state = load_state()

    # Check if pipeline is done
    task = determine_next_task(state)
    if task is None:
        print("Pipeline complete, nothing to do")
        log_heartbeat("noop", "pipeline complete")
        return

    phase = task["phase"]
    agent_name = PHASE_TO_AGENT.get(phase, phase)

    # Check existing session for this agent
    session = load_current_session(agent_name=agent_name)

    if session and not force_new:
        session_id = session.get("session_id")
        api_state = get_session_state(session_id)
        print(f"Agent {agent_name} session {session_id}: {api_state}")

        if api_state in ACTIVE_STATES:
            if is_session_expired(session):
                print("  Session expired (TTL), archiving and creating new")
                archive_session(session, "EXPIRED", agent_name=agent_name)
            else:
                send_continuation(session_id)
                log_heartbeat("continuation",
                              f"agent={agent_name} session={session_id}")
                return

        if api_state in TERMINAL_STATES:
            print(f"  Session {api_state}, archiving")
            archive_session(session, api_state, agent_name=agent_name)
            # Re-check state (session may have advanced the pipeline)
            state = load_state()
            task = determine_next_task(state)
            if task is None:
                print("Pipeline complete after session finished")
                log_heartbeat("complete",
                              f"agent={agent_name} session={session_id}")
                return
            # Task may have changed agent
            phase = task["phase"]
            agent_name = PHASE_TO_AGENT.get(phase, phase)

    # Create new session for next task
    chapter = task.get("chapter")
    hint = task.get("hint", "")

    print(f"\nCreating session for agent {agent_name}: {phase}" +
          (f" ch{chapter}" if chapter else ""))

    try:
        new_session = create_session(phase, chapter, hint)
        log_heartbeat("create",
                      f"agent={agent_name} phase={phase} "
                      f"session={new_session['session_id']}")
    except Exception as e:
        print(f"  Error creating session: {e}", file=sys.stderr)
        log_heartbeat("error", str(e))
        raise


def cmd_create():
    """Create a session for the next pipeline task (no continuation check)."""
    cmd_heartbeat(force_new=True)


# ── Main ──────────────────────────────────────────────────────────


def main():
    if not JULES_API_KEY:
        print("Error: JULES_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    if len(sys.argv) < 2:
        print("Usage: heartbeat.py {status|heartbeat|force-new|create}")
        sys.exit(1)

    command = sys.argv[1]
    commands = {
        "status": cmd_status,
        "heartbeat": cmd_heartbeat,
        "force-new": lambda: cmd_heartbeat(force_new=True),
        "create": cmd_create,
    }

    if command not in commands:
        print(f"Unknown command: {command}")
        print(f"Available: {', '.join(commands.keys())}")
        sys.exit(1)

    commands[command]()


if __name__ == "__main__":
    main()
