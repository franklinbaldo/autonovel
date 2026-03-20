#!/usr/bin/env python3
"""
jules_client.py -- Jules Sequence cognitive motor for autonovel.

Replaces direct Anthropic API calls with Google Jules sessions.
The "Jules Sequence" is: create session -> send prompt -> poll activities -> extract result.

Each generation task becomes a Jules session, leveraging Jules as an autonomous
coding agent that can reason about, plan, and execute complex creative tasks.

Usage:
    from jules_client import create_caller

    call_writer = create_caller(role="writer")
    result = call_writer(prompt, system="You are a ...", max_tokens=16000)

    call_judge = create_caller(role="judge")
    result = call_judge(prompt, system="You are a ...", max_tokens=2000)
"""
import os
import sys
import time
import json
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

# --- Configuration ---
JULES_API_BASE = os.environ.get(
    "JULES_API_BASE_URL",
    "https://jules.googleapis.com/v1alpha",
)
JULES_API_KEY = os.environ.get("JULES_API_KEY", "")
JULES_SOURCE_REPO = os.environ.get("JULES_SOURCE_REPO", "")

# Polling configuration
JULES_POLL_INTERVAL = float(os.environ.get("JULES_POLL_INTERVAL", "3"))
JULES_MAX_WAIT = float(os.environ.get("JULES_MAX_WAIT", "900"))  # 15 min default

# Session TTL: reuse sessions younger than this (seconds)
JULES_SESSION_TTL = float(os.environ.get("JULES_SESSION_TTL", str(12 * 3600)))

# Session title prefixes per role
ROLE_PREFIXES = {
    "writer": "autonovel:draft",
    "judge": "autonovel:eval",
    "review": "autonovel:review",
}

# Terminal session states
TERMINAL_STATES = {"COMPLETED", "FAILED", "CANCELLED"}
ACTIVE_STATES = {"IN_PROGRESS", "WAITING_FOR_USER_RESPONSE", "AWAITING_PLAN_APPROVAL"}

# --- Per-agent session persistence (Verne protocol) ---
AGENTS_DIR = BASE_DIR / "agents"

# Map roles to agent names for session tracking
ROLE_TO_AGENT = {
    "writer": None,       # resolved dynamically from title_suffix
    "judge": "evaluator",
    "review": "reviewer",
}

# Map title_suffix hints to agent names
SUFFIX_TO_AGENT = {
    "world": "foundation",
    "characters": "foundation",
    "outline": "foundation",
    "outline2": "foundation",
    "canon": "foundation",
    "seed": "foundation",
    "voice": "foundation",
    "fingerprint": "foundation",
    "draft": "drafter",
    "chapter": "drafter",
    "eval": "evaluator",
    "adversarial": "evaluator",
    "compare": "evaluator",
    "panel": "reviewer",
    "review": "reviewer",
    "brief": "reviser",
    "revision": "reviser",
    "cuts": "reviser",
    "export": "exporter",
    "outline_export": "exporter",
    "arc": "exporter",
}


def _resolve_agent(role, title_suffix=""):
    """Resolve the agent name from role + title_suffix."""
    # Direct mapping from role
    agent = ROLE_TO_AGENT.get(role)
    if agent:
        return agent
    # Try title_suffix lookup
    if title_suffix:
        suffix_lower = title_suffix.lower()
        for key, agent_name in SUFFIX_TO_AGENT.items():
            if key in suffix_lower:
                return agent_name
    # Fallback by role
    return {"writer": "foundation", "judge": "evaluator", "review": "reviewer"}.get(role, "foundation")


def _agent_sessions_dir(agent_name):
    """Get the active-sessions directory for an agent."""
    d = AGENTS_DIR / agent_name / "active-sessions"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _list_active_sessions(agent_name):
    """List all active session files for an agent (newest first)."""
    d = _agent_sessions_dir(agent_name)
    files = sorted(d.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    return files


def _load_agent_session(agent_name):
    """Load the newest active session for an agent. Returns (data, path) or (None, None)."""
    for path in _list_active_sessions(agent_name):
        try:
            data = json.loads(path.read_text())
            return data, path
        except (json.JSONDecodeError, OSError):
            continue
    return None, None


def _save_agent_session(agent_name, session_data):
    """Save session metadata as individual file named by session_id."""
    session_id = session_data.get("session_id", "unknown")
    session_file = _agent_sessions_dir(agent_name) / f"{session_id}.json"
    session_file.write_text(json.dumps(session_data, indent=2) + "\n")


def _archive_agent_session(agent_name, session_data, final_state="COMPLETED"):
    """Move session file to history/ subdirectory."""
    session_id = session_data.get("session_id", "unknown")
    history_dir = _agent_sessions_dir(agent_name) / "history"
    history_dir.mkdir(parents=True, exist_ok=True)

    session_data["final_state"] = final_state
    session_data["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # Write to history
    (history_dir / f"{session_id}.json").write_text(
        json.dumps(session_data, indent=2) + "\n"
    )

    # Remove from active
    active_file = _agent_sessions_dir(agent_name) / f"{session_id}.json"
    if active_file.exists():
        active_file.unlink()


def _is_session_valid(session_data):
    """Check if a saved session is still potentially active (not expired)."""
    created = session_data.get("created_at", "")
    if not created:
        return False
    try:
        from datetime import datetime, timezone
        created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
        age_secs = (datetime.now(timezone.utc) - created_dt).total_seconds()
        return age_secs < JULES_SESSION_TTL
    except (ValueError, TypeError):
        return False


def _headers():
    """Build authorization headers for Jules API."""
    return {
        "Authorization": f"Bearer {JULES_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _post(path, body=None, timeout=30):
    """POST to Jules API with retry on transient errors."""
    import httpx
    url = f"{JULES_API_BASE}{path}"
    for attempt in range(4):
        try:
            resp = httpx.post(url, headers=_headers(), json=body or {}, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.WriteTimeout) as e:
            if attempt == 3:
                raise
            wait = 2 ** (attempt + 1)
            print(f"  [jules] retry {attempt+1}/3 after {wait}s: {e}", file=sys.stderr)
            time.sleep(wait)


def _get(path, timeout=30):
    """GET from Jules API with retry on transient errors."""
    import httpx
    url = f"{JULES_API_BASE}{path}"
    for attempt in range(4):
        try:
            resp = httpx.get(url, headers=_headers(), timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.WriteTimeout) as e:
            if attempt == 3:
                raise
            wait = 2 ** (attempt + 1)
            print(f"  [jules] retry {attempt+1}/3 after {wait}s: {e}", file=sys.stderr)
            time.sleep(wait)


def create_session(title, prompt, source_repo=None):
    """
    Create a new Jules session.

    Returns the session object with at least: name, state, title.
    """
    body = {
        "title": title,
        "prompt": prompt,
    }
    if source_repo or JULES_SOURCE_REPO:
        body["sourceContext"] = {
            "repository": source_repo or JULES_SOURCE_REPO,
        }
    return _post("/sessions", body)


def get_session(session_id):
    """Get current session state."""
    return _get(f"/sessions/{session_id}")


def approve_plan(session_id, plan_id="auto"):
    """Auto-approve a Jules plan to keep the sequence flowing."""
    return _post(f"/sessions/{session_id}:approvePlan", {"planId": plan_id})


def send_message(session_id, prompt):
    """Send a follow-up message to an active session."""
    return _post(f"/sessions/{session_id}:sendMessage", {"prompt": prompt})


def get_activities(session_id):
    """Get all activities for a session."""
    return _get(f"/sessions/{session_id}/activities")


def _extract_session_id(session):
    """Extract the session ID from the session name field."""
    name = session.get("name", "")
    # name format: "sessions/{id}" or just the id
    if "/" in name:
        return name.split("/")[-1]
    return name


def _extract_text_from_activities(activities):
    """
    Extract the final text output from a list of Jules activities.

    Walks activities in order, collecting agent messages.
    Returns the concatenated agent response text.
    """
    texts = []
    for activity in activities:
        # Agent messages contain the generated content
        if "agentMessaged" in activity:
            msg = activity["agentMessaged"]
            if isinstance(msg, dict):
                text = msg.get("message", msg.get("content", ""))
            elif isinstance(msg, str):
                text = msg
            else:
                text = str(msg)
            if text:
                texts.append(text)

        # Progress updates may contain artifacts with content
        if "progressUpdated" in activity:
            progress = activity["progressUpdated"]
            if isinstance(progress, dict):
                artifacts = progress.get("artifacts", [])
                for artifact in artifacts:
                    if isinstance(artifact, dict):
                        # Check for text content in various artifact formats
                        for key in ("content", "text", "body"):
                            if key in artifact:
                                texts.append(str(artifact[key]))

    return "\n".join(texts) if texts else ""


def jules_sequence(prompt, system=None, role="writer", title_suffix="",
                   max_wait=None, poll_interval=None):
    """
    Execute the full Jules Sequence with per-agent session reuse:
      1. Check for existing active session for this agent
      2. If active: send continuation message (reuse session)
      3. If none: create new session with prompt
      4. Auto-approve plan if needed
      5. Poll until completion
      6. Extract and return the generated text
      7. Archive session when terminal

    Args:
        prompt: The full task prompt (system + user context combined)
        system: Optional system-level instruction (prepended to prompt)
        role: "writer", "judge", or "review" -- affects session naming
        title_suffix: Added to session title for identification
        max_wait: Max seconds to wait for completion (default: JULES_MAX_WAIT)
        poll_interval: Seconds between polls (default: JULES_POLL_INTERVAL)

    Returns:
        The generated text content from Jules.

    Raises:
        TimeoutError: If session doesn't complete within max_wait
        RuntimeError: If session fails or produces no output
    """
    if max_wait is None:
        max_wait = JULES_MAX_WAIT
    if poll_interval is None:
        poll_interval = JULES_POLL_INTERVAL

    # Resolve which agent this call belongs to
    agent_name = _resolve_agent(role, title_suffix)

    # Build the full prompt (Jules doesn't have a separate system field,
    # so we prepend it as context)
    full_prompt = prompt
    if system:
        full_prompt = f"""ROLE & INSTRUCTIONS:
{system}

---

TASK:
{prompt}"""

    prefix = ROLE_PREFIXES.get(role, "autonovel")
    title = f"{prefix}:{title_suffix}" if title_suffix else prefix

    # --- Session reuse: check for active session for this agent ---
    existing, _existing_path = _load_agent_session(agent_name)
    session_id = None
    reused = False

    if existing and _is_session_valid(existing):
        old_id = existing.get("session_id", "")
        if old_id:
            try:
                api_state = get_session(old_id).get("state", "UNKNOWN")
            except Exception:
                api_state = "UNKNOWN"

            if api_state in ACTIVE_STATES:
                # Reuse: send continuation message with new task
                print(f"  [jules] reusing session {old_id} for {agent_name} "
                      f"(state: {api_state})", file=sys.stderr)
                send_message(old_id, full_prompt)
                session_id = old_id
                reused = True
            elif api_state in TERMINAL_STATES:
                # Session finished — archive it
                print(f"  [jules] archiving finished session {old_id} "
                      f"({api_state})", file=sys.stderr)
                _archive_agent_session(agent_name, existing, api_state)
            else:
                # Unknown state — archive and start fresh
                _archive_agent_session(agent_name, existing, api_state)

    # --- Create new session if no reuse ---
    if session_id is None:
        print(f"  [jules] creating session for {agent_name}: {title}",
              file=sys.stderr)
        session = create_session(title, full_prompt)
        session_id = _extract_session_id(session)
        state = session.get("state", "UNKNOWN")
        print(f"  [jules] session {session_id} state: {state}", file=sys.stderr)

        # Persist session for future reuse
        _save_agent_session(agent_name, {
            "session_id": session_id,
            "agent": agent_name,
            "role": role,
            "title": title,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
    else:
        session = get_session(session_id)
        state = session.get("state", "UNKNOWN")

    # --- Poll loop: auto-approve plans & wait for completion ---
    start = time.time()
    plan_approved = reused  # skip plan approval if reusing

    while time.time() - start < max_wait:
        if state in TERMINAL_STATES:
            break

        if state == "AWAITING_PLAN_APPROVAL" and not plan_approved:
            acts = get_activities(session_id)
            plan_id = "auto"
            for act in acts.get("activities", []):
                if "planGenerated" in act:
                    pg = act["planGenerated"]
                    if isinstance(pg, dict) and "planId" in pg:
                        plan_id = pg["planId"]
                    break

            print(f"  [jules] auto-approving plan: {plan_id}", file=sys.stderr)
            approve_plan(session_id, plan_id)
            plan_approved = True
            time.sleep(1)

        time.sleep(poll_interval)
        session = get_session(session_id)
        state = session.get("state", "UNKNOWN")

    elapsed = time.time() - start

    if state == "FAILED":
        saved, _ = _load_agent_session(agent_name)
        _archive_agent_session(agent_name,
                               saved or {"session_id": session_id},
                               "FAILED")
        raise RuntimeError(f"Jules session {session_id} failed after {elapsed:.0f}s")

    if state not in TERMINAL_STATES:
        raise TimeoutError(
            f"Jules session {session_id} still {state} after {elapsed:.0f}s "
            f"(max_wait={max_wait}s)"
        )

    # --- Extract result from activities ---
    acts = get_activities(session_id)
    activities = acts.get("activities", [])
    result = _extract_text_from_activities(activities)

    if not result.strip():
        saved_empty, _ = _load_agent_session(agent_name)
        _archive_agent_session(agent_name,
                               saved_empty or {"session_id": session_id},
                               "EMPTY")
        raise RuntimeError(
            f"Jules session {session_id} completed but produced no text output. "
            f"Activities: {json.dumps(activities[:3], indent=2)}"
        )

    # Archive completed session
    saved_done, _ = _load_agent_session(agent_name)
    if saved_done:
        _archive_agent_session(agent_name, saved_done, "COMPLETED")

    print(f"  [jules] session {session_id} complete ({elapsed:.0f}s, "
          f"{len(result)} chars, agent={agent_name}, "
          f"{'reused' if reused else 'new'})", file=sys.stderr)

    return result


def create_caller(role="writer"):
    """
    Factory that returns a call function compatible with the existing
    autonovel script interface.

    Usage:
        call_writer = create_caller(role="writer")
        text = call_writer(prompt, system="...", max_tokens=16000)

    The returned function signature:
        call(prompt, system=None, max_tokens=16000, title_suffix="") -> str

    Note: max_tokens is accepted for API compatibility but Jules manages
    its own output length. The prompt should specify length requirements.
    """
    def call(prompt, system=None, max_tokens=16000, title_suffix=""):
        return jules_sequence(
            prompt=prompt,
            system=system,
            role=role,
            title_suffix=title_suffix,
        )
    call.__name__ = f"call_{role}"
    call.__doc__ = f"Call Jules as {role} role via the Jules Sequence."
    return call


# --- Convenience pre-built callers ---

def call_writer(prompt, system=None, max_tokens=16000, title_suffix=""):
    """Drop-in replacement for the per-script call_writer functions."""
    return jules_sequence(prompt=prompt, system=system, role="writer",
                          title_suffix=title_suffix)


def call_judge(prompt, system=None, max_tokens=2000, title_suffix=""):
    """Drop-in replacement for the per-script call_judge functions."""
    return jules_sequence(prompt=prompt, system=system, role="judge",
                          title_suffix=title_suffix)


def call_review(prompt, system=None, max_tokens=8000, title_suffix=""):
    """Drop-in replacement for review.py's call_opus function."""
    return jules_sequence(prompt=prompt, system=system, role="review",
                          title_suffix=title_suffix)


if __name__ == "__main__":
    # Quick self-test
    if not JULES_API_KEY:
        print("Set JULES_API_KEY in .env to test", file=sys.stderr)
        sys.exit(1)

    result = call_writer(
        prompt="Write a single paragraph describing a fantasy city at dawn.",
        system="You are a literary fiction writer. Write clean, sensory prose.",
        title_suffix="self-test",
    )
    print(result)
