#!/usr/bin/env python3
"""
Build the Jules session prompt for a specific pipeline phase.

Reads project files (seed, voice, world, characters, outline, canon, state)
and constructs a comprehensive prompt that tells Jules what to do.

Usage:
  python scripts/build-novel-prompt.py --phase foundation
  python scripts/build-novel-prompt.py --phase drafting --chapter 5
  python scripts/build-novel-prompt.py --phase revision --hint "focus on pacing"
"""
import argparse
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent


def load(name):
    """Load a file from the project root, return empty string if missing."""
    path = BASE_DIR / name
    if path.exists():
        return path.read_text().strip()
    return ""


def load_state():
    """Load pipeline state."""
    state_path = BASE_DIR / "state.json"
    if state_path.exists():
        return json.loads(state_path.read_text())
    return {"phase": "foundation", "iteration": 0}


def build_foundation_prompt(state, hint=""):
    """Build prompt for foundation phase (world, characters, outline, canon)."""
    seed = load("seed.txt")
    voice = load("voice.md")
    craft = load("CRAFT.md")
    anti_slop = load("ANTI-SLOP.md")
    anti_patterns = load("ANTI-PATTERNS.md")
    program = load("program.md")

    iteration = state.get("iteration", 0)
    prev_score = state.get("foundation_score", 0)
    prev_lore = state.get("lore_score", 0)

    return f"""# AUTONOVEL: Foundation Phase (Iteration {iteration + 1})

You are building the planning documents for a fantasy novel. Your job is to
generate or improve these files in the repository:

- `world.md` -- Complete world bible (magic system, geography, factions, culture)
- `characters.md` -- Character registry (wound/want/need/lie, speech patterns)
- `outline.md` -- Chapter-by-chapter outline with beats and foreshadowing ledger
- `canon.md` -- Hard facts database for consistency checking
- `voice.md` Part 2 -- Discovered voice identity from trial passages

## SEED CONCEPT
{seed}

## CURRENT SCORES
- Foundation score: {prev_score}/10 (target: >= 7.5)
- Lore score: {prev_lore}/10 (target: >= 7.0)
- Iteration: {iteration}/20

## VOICE DEFINITION
{voice}

## CRAFT REQUIREMENTS
{craft}

## ANTI-SLOP RULES
{anti_slop[:3000]}

## PIPELINE INSTRUCTIONS
{program[:2000]}

## TASK
{"Generate all foundation documents from scratch." if iteration == 0 else
 f"Improve the foundation documents. Previous scores: foundation={prev_score}, lore={prev_lore}. Focus on the weakest dimensions."}

After generating/updating the files, run `python evaluate.py --phase=foundation`
to score the results. Keep iterating until foundation_score >= 7.5 AND lore_score >= 7.0.

Update `state.json` with the new scores after evaluation.

{f"ADDITIONAL GUIDANCE: {hint}" if hint else ""}
"""


def build_drafting_prompt(state, chapter=None, hint=""):
    """Build prompt for drafting a specific chapter."""
    seed = load("seed.txt")
    voice = load("voice.md")
    world = load("world.md")
    characters = load("characters.md")
    outline = load("outline.md")
    canon = load("canon.md")
    anti_patterns = load("ANTI-PATTERNS.md")

    chapters_drafted = state.get("chapters_drafted", 0)
    chapters_total = state.get("chapters_total", 0)

    if chapter is None:
        chapter = chapters_drafted + 1

    return f"""# AUTONOVEL: Draft Chapter {chapter}

You are writing Chapter {chapter} of the novel. Use `draft_chapter.py {chapter}`
to generate the chapter, then `evaluate.py --chapter={chapter}` to score it.

The chapter must score >= 6.0 to keep. If it scores lower, retry (max 5 attempts).

## PROGRESS
- Chapters drafted: {chapters_drafted}/{chapters_total}
- Current chapter: {chapter}

## VOICE DEFINITION
{voice[:2000]}

## WORLD BIBLE (reference)
{world[:3000]}

## CHARACTER REGISTRY
{characters[:2000]}

## OUTLINE
{outline[:4000]}

## CANON (do not contradict)
{canon[:2000]}

## ANTI-PATTERNS TO AVOID
{anti_patterns}

## TASK
1. Run: `python draft_chapter.py {chapter}`
2. Run: `python evaluate.py --chapter={chapter}`
3. If score >= 6.0: update state.json (chapters_drafted += 1), commit
4. If score < 6.0: discard and retry
5. After all chapters drafted, move state.json phase to "revision"

{f"ADDITIONAL GUIDANCE: {hint}" if hint else ""}
"""


def build_revision_prompt(state, chapter=None, hint=""):
    """Build prompt for revision phase."""
    voice = load("voice.md")
    anti_patterns = load("ANTI-PATTERNS.md")

    revision_cycle = state.get("revision_cycle", 0)
    novel_score = state.get("novel_score", 0)

    return f"""# AUTONOVEL: Revision Phase (Cycle {revision_cycle + 1})

You are improving the novel through systematic revision. Follow this sequence:

1. Run `python adversarial_edit.py all` -- identify weak passages
2. Run `python apply_cuts.py all --types OVER-EXPLAIN REDUNDANT` -- mechanical cuts
3. Run `python reader_panel.py` -- 4-persona evaluation
4. For each consensus item from the panel:
   a. `python gen_brief.py --panel <chapter>` -- generate revision brief
   b. `python gen_revision.py <chapter> <brief>` -- rewrite chapter
   c. `python evaluate.py --chapter=<chapter>` -- verify improvement
5. Run `python evaluate.py --full` -- novel-level evaluation
6. Update state.json with new novel_score and revision_cycle

## CURRENT STATE
- Revision cycle: {revision_cycle}/6
- Novel score: {novel_score}/10
- Stop when: score plateau (delta < 0.3 for 2 cycles after cycle 3)

## VOICE (preserve this)
{voice[:1500]}

## ANTI-PATTERNS
{anti_patterns}

{f"FOCUS ON CHAPTER {chapter}" if chapter else ""}
{f"ADDITIONAL GUIDANCE: {hint}" if hint else ""}
"""


def build_export_prompt(state, hint=""):
    """Build prompt for export phase."""
    return f"""# AUTONOVEL: Export Phase

Final assembly of the novel. Run these in order:

1. `python build_outline.py` -- rebuild outline from final chapters
2. `python build_arc_summary.py` -- build chapter summaries
3. Concatenate all chapters into a manuscript
4. `python typeset/build_tex.py` -- generate LaTeX
5. Run `tectonic typeset/novel.tex` if available (or skip PDF)
6. Update state.json: set phase to "complete"
7. Commit all final files

{f"ADDITIONAL GUIDANCE: {hint}" if hint else ""}
"""


def main():
    parser = argparse.ArgumentParser(description="Build Jules session prompt")
    parser.add_argument("--phase", required=True,
                        choices=["foundation", "drafting", "revision", "export"])
    parser.add_argument("--chapter", type=int, default=None)
    parser.add_argument("--hint", default="")
    args = parser.parse_args()

    state = load_state()

    builders = {
        "foundation": lambda: build_foundation_prompt(state, args.hint),
        "drafting": lambda: build_drafting_prompt(state, args.chapter, args.hint),
        "revision": lambda: build_revision_prompt(state, args.chapter, args.hint),
        "export": lambda: build_export_prompt(state, args.hint),
    }

    prompt = builders[args.phase]()
    print(prompt)


if __name__ == "__main__":
    main()
