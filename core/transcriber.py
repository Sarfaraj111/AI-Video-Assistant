import os
import time

_groq_client = None
_local_model = None

GROQ_MODEL = "whisper-large-v3-turbo"
MAX_GROQ_BYTES = 24 * 1024 * 1024  # Groq free tier limit is 25 MB


def _lang_code(language: str) -> str:
    return "en" if language.lower() == "english" else "hi"


# ── Groq (free tier, hosted) ──────────────────────────────────────────────────
def _get_groq():
    global _groq_client
    if _groq_client is None:
        from groq import Groq
        _groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    return _groq_client


def _transcribe_groq(path: str, lang: str) -> str:
    from groq import RateLimitError

    if os.path.getsize(path) > MAX_GROQ_BYTES:
        raise ValueError("File too large for Groq free tier")

    client = _get_groq()
    for attempt in range(3):
        try:
            with open(path, "rb") as f:
                r = client.audio.transcriptions.create(
                    file=(os.path.basename(path), f.read()),
                    model=GROQ_MODEL,
                    language=lang,
                    response_format="text",
                )
            return r if isinstance(r, str) else r.text
        except RateLimitError:
            time.sleep(10 * (attempt + 1))
    raise RuntimeError("Groq rate limit")


# ── faster-whisper (free, local, no torch) ────────────────────────────────────
def _get_local():
    global _local_model
    if _local_model is None:
        from faster_whisper import WhisperModel
        size = os.getenv("WHISPER_MODEL", "base")
        if size not in ("tiny", "base", "small"):  # keep within free-tier RAM
            size = "base"
        _local_model = WhisperModel(size, device="cpu", compute_type="int8")
    return _local_model


def _transcribe_local(path: str, lang: str) -> str:
    segments, _ = _get_local().transcribe(path, language=lang, vad_filter=True)
    return " ".join(s.text.strip() for s in segments)


# ── Public API ────────────────────────────────────────────────────────────────
def _transcribe_chunk(path: str, lang: str) -> str:
    if os.getenv("GROQ_API_KEY"):
        try:
            return _transcribe_groq(path, lang)
        except Exception as e:
            print(f"Groq failed ({e}); falling back to local faster-whisper")
    return _transcribe_local(path, lang)


def transcribe_all(chunks, language: str = "english") -> str:
    lang = _lang_code(language)
    parts = [_transcribe_chunk(p, lang) for p in chunks]
    return "\n".join(p.strip() for p in parts if p)