#!/usr/bin/env python3
"""
engine.py -- Cognitive motor abstraction for autonovel.

Provides a unified interface for LLM calls that routes to either:
  - Jules Sequence (Google Jules API) -- session-based cognitive motor
  - Anthropic API (Claude) -- direct API calls

The engine is selected via AUTONOVEL_ENGINE env var ("jules" or "anthropic").

Usage in scripts:
    from engine import call_writer, call_judge, call_review

    # Same interface regardless of engine:
    result = call_writer(prompt, system="You are a ...", max_tokens=16000)
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

ENGINE = os.environ.get("AUTONOVEL_ENGINE", "jules").lower()


def _build_anthropic_caller(model_env, default_model, default_temp=0.7,
                            default_timeout=300, use_beta=False):
    """Build an Anthropic API caller function."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    api_base = os.environ.get("AUTONOVEL_API_BASE_URL", "https://api.anthropic.com")
    model = os.environ.get(model_env, default_model)

    def call(prompt, system=None, max_tokens=16000, title_suffix="",
             temperature=None, timeout=None):
        import httpx
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        if use_beta:
            headers["anthropic-beta"] = "context-1m-2025-08-07"

        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature if temperature is not None else default_temp,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            payload["system"] = system

        resp = httpx.post(
            f"{api_base}/v1/messages",
            headers=headers,
            json=payload,
            timeout=timeout or default_timeout,
        )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"]

    return call


def _build_jules_caller(role):
    """Build a Jules Sequence caller function."""
    from jules_client import jules_sequence

    def call(prompt, system=None, max_tokens=16000, title_suffix="",
             temperature=None, timeout=None):
        return jules_sequence(
            prompt=prompt,
            system=system,
            role=role,
            title_suffix=title_suffix,
        )

    return call


def _make_caller(role, model_env, default_model, default_temp=0.7,
                 default_timeout=300, use_beta=False):
    """Create a caller for the configured engine."""
    if ENGINE == "jules":
        return _build_jules_caller(role)
    else:
        return _build_anthropic_caller(
            model_env, default_model, default_temp,
            default_timeout, use_beta,
        )


# --- Pre-built callers (used by generation scripts) ---

call_writer = _make_caller(
    role="writer",
    model_env="AUTONOVEL_WRITER_MODEL",
    default_model="claude-sonnet-4-6",
    default_temp=0.7,
    default_timeout=300,
    use_beta=True,
)

call_judge = _make_caller(
    role="judge",
    model_env="AUTONOVEL_JUDGE_MODEL",
    default_model="claude-sonnet-4-6",
    default_temp=0.3,
    default_timeout=300,
    use_beta=True,
)

call_review = _make_caller(
    role="review",
    model_env="AUTONOVEL_REVIEW_MODEL",
    default_model="claude-opus-4-6",
    default_temp=0.3,
    default_timeout=600,
    use_beta=True,
)


if __name__ == "__main__":
    print(f"Active engine: {ENGINE}")
    if ENGINE == "jules":
        key = os.environ.get("JULES_API_KEY", "")
        print(f"Jules API key: {'set' if key else 'NOT SET'}")
    else:
        key = os.environ.get("ANTHROPIC_API_KEY", "")
        print(f"Anthropic API key: {'set' if key else 'NOT SET'}")
