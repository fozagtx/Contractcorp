"""Nemotron over the Meterless Nightshift Runtime (OpenAI-compatible).

Settings come from the workspace .env, all from the same route:
  MODEL_BASE_URL  - the Nightshift Runtime URL (e.g. http://127.0.0.1:8088/v1)
  MODEL_API_KEY   - the Nightshift Runtime token
  NEMOTRON_MODEL  - the Nemotron model pinned in the Nightshift lane

The Nemotron 3.5 models are reasoning models by default; for the claim
check we run them with thinking disabled (fast, ~2s verdicts, strict
JSON) and retry transient provider-side empty responses.
"""
import os
import time

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

BASE_URL = os.environ["MODEL_BASE_URL"].rstrip("/")
API_KEY = os.environ["MODEL_API_KEY"]
MODEL = os.environ["NEMOTRON_MODEL"]

RETRIES = 3


def client() -> OpenAI:
    return OpenAI(
        base_url=BASE_URL,
        api_key=API_KEY,
        default_headers={
            "meterless-app": "contractcop-demo",
            "meterless-scope": "user",
        },
    )


def chat(messages, temperature=0.0, max_tokens=1200):
    """One chat completion through Nightshift. Returns (content, raw_response).

    Retries transient provider errors and empty replies (the NVIDIA
    endpoint occasionally returns an empty response through Nightshift),
    with a short backoff between attempts.
    """
    last_error = None
    for attempt in range(RETRIES):
        try:
            response = client().chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                extra_body={"chat_template_kwargs": {"thinking": False}},
            )
            content = response.choices[0].message.content
            if content and content.strip():
                return content, response
            last_error = RuntimeError("empty model reply (attempt "
                                      f"{attempt + 1}/{RETRIES})")
        except Exception as error:
            last_error = error
        time.sleep(1.5 * (attempt + 1))
    raise last_error
