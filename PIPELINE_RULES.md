# Pipeline Rules

Operational guidelines for the autonovel pipeline. Every agent session
(human or AI) must follow these rules. Violations break reproducibility.

---

## Session Flow

Every session follows this sequence:

1. **Read state** -- `state.json` is the single source of truth
2. **Determine task** -- `determine_next_task(state)` picks the next action
3. **Check active session** -- reuse if the agent has one alive
4. **Execute** -- run the agent's scripts in order
5. **Evaluate** -- score the output with `agents/evaluator/evaluate.py`
6. **Commit** -- atomic commit per chapter/artifact, message format below
7. **Update state** -- write scores, advance phase if thresholds met

Do not skip steps. Do not reorder.

---

## File Ownership (The Golden Rule)

Each agent declares what it reads and writes in its `config.json`:

```json
{
  "reads": ["seed.txt", "voice.md", "CRAFT.md"],
  "writes": ["world.md", "characters.md"]
}
```

**An agent may ONLY create or modify files listed in its `writes` array.**
Reading is unrestricted -- any agent can read any file.
The `ownership-check` workflow enforces this on every PR.

### Ownership Map

| Agent        | Writes                                                     |
|-------------|-------------------------------------------------------------|
| foundation  | `world.md`, `characters.md`, `outline.md`, `canon.md`      |
| drafter     | `chapters/ch_*.md`                                          |
| evaluator   | `eval_logs/*`, `edit_logs/*`                                |
| reviewer    | `edit_logs/reader_panel.json`, `reviews.md`                 |
| reviser     | `chapters/ch_*.md`, `briefs/*`                              |
| exporter    | `outline.md`, `arc_summary.md`, `manuscript.md`             |

`state.json` is shared -- any agent advancing the pipeline may update it.
`voice.md` is written by foundation and read by everyone.

---

## Never Delete, Only Archive

Files are never deleted. If something is superseded:
- Chapters move to `chapters/archive/`
- Briefs move to `briefs/archive/`
- Eval logs accumulate (timestamped)

The `.trash/` convention from rosencrantz-coin applies: if you must remove
a file, `git mv` it to `.trash/`. The `no-delete-check` workflow blocks
bare deletions.

---

## Commit Messages

Format: `{agent}: {imperative description}`

Examples:
```
foundation: generate world bible iteration 3
drafter: draft ch07 (4200w, score 7.2)
evaluator: adversarial edit pass on ch01-ch10
reviser: apply OVER-EXPLAIN cuts (312w removed)
exporter: rebuild outline from final chapters
```

Include word count and score when available. One commit per logical unit
(one chapter, one evaluation pass, one revision cycle).

---

## Session Reuse

Sessions are expensive. Reuse them:

1. Before creating a new Jules session, check `agents/{name}/active-sessions/current.json`
2. If a session exists and is active (not expired, not terminal): send a continuation message
3. If terminal: archive to `active-sessions/history/`, create fresh
4. Session TTL: 12 hours (configurable via `JULES_SESSION_TTL`)

The `jules_client.py` handles this automatically. The `heartbeat.py`
orchestrator respects per-agent sessions.

---

## Evaluation Thresholds

Nothing advances without meeting score thresholds:

| Gate                    | Threshold | Evaluator script                  |
|------------------------|-----------|-----------------------------------|
| Foundation complete     | >= 7.5    | `evaluate.py --phase=foundation`  |
| Chapter accepted        | >= 6.0    | `evaluate.py --chapter=N`         |
| Revision keeps change   | post > pre | `evaluate.py --chapter=N`        |
| Revision cycle stops    | plateau < 0.3 delta for 2 cycles | `evaluate.py --full` |
| Opus review stops       | >= 4 stars, no major items | `review.py`           |

If a chapter scores below threshold: discard and retry (max 5 attempts).
If a revision makes the score worse: `git reset --hard HEAD` and skip.

---

## Anti-Slop Discipline

Every generated text is checked for AI tells:

- **Tier 1** (hard block): delve, tapestry, myriad, resonate, embark, unfold
- **Fiction tells**: "a beat of silence", "let out a breath", "without missing a beat"
- **Telling violations**: "He felt angry" instead of showing anger through action

The `slop_score()` function in `evaluate.py` computes a penalty.
Any tier-1 hit on a final chapter is a pipeline failure.

---

## State Machine

```
foundation ──(score >= 7.5)──> drafting ──(all chapters)──> revision ──(plateau)──> export ──> complete
     ^                              |                            |
     |                              v                            v
     └── (max 20 iterations)    (max 5 retries/ch)        (max 6 cycles)
```

`state.json` tracks: `phase`, `iteration`, `chapters_drafted`, `chapters_total`,
`foundation_score`, `lore_score`, `novel_score`, `revision_cycle`, `debts[]`.

Only `determine_next_task()` decides what happens next. No agent freelances.

---

## Heartbeat Protocol

The GitHub Actions heartbeat runs every 15 minutes:

1. Load `state.json`
2. Determine next task
3. Check the target agent's active session
4. If active: send continuation ("keep going, commit when done")
5. If terminal: archive, create new session for next task
6. If expired (>12h): archive as EXPIRED, create fresh
7. Log heartbeat to `sessions/heartbeats/`

The heartbeat never runs scripts directly. It manages Jules sessions
that run the scripts autonomously.

---

## Directory Structure

```
autonovel/
  agents/
    foundation/       # worldbuilding, characters, outline, canon
      config.json
      active-sessions/
      gen_world.py, gen_characters.py, ...
    drafter/          # chapter drafting
    evaluator/        # scoring, adversarial editing
    reviewer/         # reader panel, Opus review
    reviser/          # briefs, revisions, mechanical cuts
    exporter/         # outline rebuild, arc summary, manuscript
  chapters/           # generated chapters (ch_01.md ... ch_24.md)
  scripts/            # orchestration (heartbeat.py, build-novel-prompt.py)
  .github/workflows/  # CI/CD (heartbeat, session, status, ownership-check)
  engine.py           # cognitive motor abstraction
  jules_client.py     # Jules API client with session reuse
  _paths.py           # repo root resolution
  state.json          # pipeline state (single source of truth)
```
