#!/home/feoh/.openclaw/workspace/.venv/bin/python3
"""
Open Brain embedding adapter.

Supports:
- OpenAI-compatible embeddings over HTTPS
- Ollama embeddings
- disabled/keyword-only mode
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from dotenv import load_dotenv

load_dotenv(".env")


def _env(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name)
    if value is None or value == "":
        return default
    return value


def _ollama_available() -> bool:
    try:
        import ollama  # noqa: F401
    except ImportError:
        return False
    return True


def get_provider() -> str:
    provider = (_env("OPENBRAIN_EMBEDDING_PROVIDER", "auto") or "auto").lower()
    if provider != "auto":
        return provider

    if _env("OPENBRAIN_OPENAI_API_KEY") or _env("OPENAI_API_KEY"):
        return "openai"
    if _ollama_available():
        return "ollama"
    return "none"


def get_model() -> str | None:
    provider = get_provider()
    if provider == "openai":
        return _env("OPENBRAIN_EMBEDDING_MODEL", "text-embedding-3-small")
    if provider == "ollama":
        return _env("OPENBRAIN_EMBEDDING_MODEL", "nomic-embed-text")
    return None


def get_vector_dimensions() -> int:
    explicit = _env("OPENBRAIN_EMBEDDING_DIMENSIONS")
    if explicit:
        return int(explicit)

    provider = get_provider()
    model = get_model()

    if provider == "openai":
        if model == "text-embedding-3-large":
            return 3072
        return 1536
    if provider == "ollama" and model == "nomic-embed-text":
        return 768
    return 1536


def describe_backend() -> str:
    provider = get_provider()
    model = get_model()
    if provider == "none":
        return "disabled"
    return f"{provider}:{model}"


def _openai_headers() -> dict[str, str]:
    api_key = _env("OPENBRAIN_OPENAI_API_KEY") or _env("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("missing OPENBRAIN_OPENAI_API_KEY or OPENAI_API_KEY")
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def _openai_base_url() -> str:
    return (_env("OPENBRAIN_OPENAI_BASE_URL", "https://api.openai.com/v1") or "https://api.openai.com/v1").rstrip("/")


def _generate_openai_embedding(text: str) -> list[float]:
    payload = {
        "model": get_model(),
        "input": text[:10000],
        "encoding_format": "float",
    }
    request = urllib.request.Request(
        url=f"{_openai_base_url()}/embeddings",
        data=json.dumps(payload).encode("utf-8"),
        headers=_openai_headers(),
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI embedding request failed: HTTP {exc.code}: {detail[:300]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"OpenAI embedding request failed: {exc.reason}") from exc

    data = body.get("data") or []
    if not data or "embedding" not in data[0]:
        raise RuntimeError("OpenAI embedding response missing data[0].embedding")
    return data[0]["embedding"]


def _generate_ollama_embedding(text: str) -> list[float]:
    import ollama

    response = ollama.embeddings(model=get_model(), prompt=text[:10000])
    embedding = response.get("embedding")
    if not embedding:
        raise RuntimeError("Ollama embedding response missing embedding")
    return embedding


def generate_embedding(text: str, input_type: str = "document") -> list[float] | None:
    del input_type

    if not text:
        return None

    provider = get_provider()
    if provider == "none":
        return None
    if provider == "openai":
        return _generate_openai_embedding(text)
    if provider == "ollama":
        return _generate_ollama_embedding(text)
    raise RuntimeError(f"unsupported embedding provider: {provider}")


def probe_embedding_backend() -> tuple[bool, str | None]:
    provider = get_provider()
    if provider == "none":
        return False, "embeddings disabled (provider=none)"
    try:
        embedding = generate_embedding("health probe", input_type="query")
        if not embedding:
            return False, "embedding backend returned no vector"
        return True, None
    except Exception as exc:
        return False, str(exc)
