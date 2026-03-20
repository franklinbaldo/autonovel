#!/usr/bin/env python3
"""
Determine the next pipeline task from state.json.
Outputs GitHub Actions output variables: phase, chapter, hint.
"""
import json
import sys
from pathlib import Path

STATE_FILE = Path(__file__).parent.parent / "state.json"


def main():
    if not STATE_FILE.exists():
        print("phase=foundation")
        return

    state = json.loads(STATE_FILE.read_text())
    phase = state.get("phase", "foundation")

    if phase == "complete":
        print("phase=complete")
        return

    if phase == "foundation":
        score = state.get("foundation_score", 0)
        lore = state.get("lore_score", 0)
        iteration = state.get("iteration", 0)
        if (score >= 7.5 and lore >= 7.0) or iteration >= 20:
            print("phase=drafting")
            print("hint=Foundation complete, begin drafting chapter 1")
        else:
            print("phase=foundation")
        return

    if phase == "drafting":
        drafted = state.get("chapters_drafted", 0)
        total = state.get("chapters_total", 0)
        if total > 0 and drafted >= total:
            print("phase=revision")
            print("hint=All chapters drafted, begin revision cycle 1")
        else:
            ch = drafted + 1
            print("phase=drafting")
            print(f"chapter={ch}")
        return

    if phase == "revision":
        cycle = state.get("revision_cycle", 0)
        if cycle >= 6:
            print("phase=export")
            print("hint=Max revision cycles, proceed to export")
        else:
            print("phase=revision")
        return

    if phase == "export":
        print("phase=export")
        return

    # Fallback
    print(f"phase={phase}")


if __name__ == "__main__":
    main()
