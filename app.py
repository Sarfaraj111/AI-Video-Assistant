import html
import random
import time

import streamlit as st
from dotenv import load_dotenv
load_dotenv()

from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarize import summarize, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.rag_engine import build_rag_chain, ask_question


# ─── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Video Assistant",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Animated background (pure CSS, so it works inside Streamlit) ──────────────
# Concept: the app turns sound into text, so the page "listens" — a live
# equalizer skyline rises from the bottom while soft aurora light drifts above.
_rng = random.Random(7)


def _bars(n: int, lo: int = 22, hi: int = 100) -> str:
    return "".join(
        f'<i style="--d:{_rng.uniform(0.9, 2.6):.2f}s;'
        f'--dl:-{_rng.uniform(0, 2.6):.2f}s;'
        f'--h:{_rng.uniform(lo, hi):.0f}%"></i>'
        for _ in range(n)
    )


BG_HTML = f"""
<div class="bg-layer" aria-hidden="true">
    <div class="aurora a1"></div>
    <div class="aurora a2"></div>
    <div class="aurora a3"></div>
    <div class="grid"></div>
    <div class="eq">{_bars(72)}</div>
</div>
"""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@500;700;800&family=DM+Sans:wght@400;500;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg: #07070d;
    --surface: rgba(17, 17, 28, 0.72);
    --surface-2: rgba(28, 28, 44, 0.8);
    --border: rgba(120, 110, 180, 0.22);
    --accent: #7c3aed;
    --accent-glow: #a78bfa;
    --accent-2: #22d3ee;
    --text: #ececf6;
    --text-muted: #8b8bb0;
    --success: #34d399;
    --danger: #f87171;
}

/* ── Base ── */
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: var(--bg) !important; color: var(--text); }
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stHeader"] { background: transparent !important; }
#MainMenu, footer { visibility: hidden; }
[data-testid="stMain"] { position: relative; z-index: 1; }
.block-container { padding-top: 2.5rem; padding-bottom: 7rem; max-width: 1250px; }
h1, h2, h3, h4 { font-family: 'Syne', sans-serif !important; color: var(--text) !important; }
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li { color: var(--text); line-height: 1.7; }
label { color: var(--text-muted) !important; font-size: 0.82rem !important; }

/* ── Background layers ── */
div[data-testid="stElementContainer"]:has(.bg-layer),
div.element-container:has(.bg-layer) {
    position: fixed !important;
    inset: 0;
    z-index: 0;
    margin: 0 !important;
    pointer-events: none;
}
.bg-layer { position: absolute; inset: 0; overflow: hidden; }

.aurora { position: absolute; border-radius: 50%; filter: blur(90px); opacity: 0.5; will-change: transform; }
.a1 { width: 46vw; height: 46vw; left: -12vw; top: -14vw;
      background: radial-gradient(circle, #7c3aed 0%, transparent 68%);
      animation: drift1 22s ease-in-out infinite alternate; }
.a2 { width: 40vw; height: 40vw; right: -10vw; top: 8vh;
      background: radial-gradient(circle, #0891b2 0%, transparent 68%);
      animation: drift2 26s ease-in-out infinite alternate; }
.a3 { width: 34vw; height: 34vw; left: 30vw; bottom: -18vw;
      background: radial-gradient(circle, #c026d3 0%, transparent 68%);
      opacity: 0.35;
      animation: drift3 30s ease-in-out infinite alternate; }

@keyframes drift1 { to { transform: translate(18vw, 14vh) scale(1.2); } }
@keyframes drift2 { to { transform: translate(-16vw, 20vh) scale(0.9); } }
@keyframes drift3 { to { transform: translate(-22vw, -10vh) scale(1.25); } }

.grid {
    position: absolute; inset: 0;
    background-image:
        linear-gradient(rgba(167, 139, 250, 0.06) 1px, transparent 1px),
        linear-gradient(90deg, rgba(167, 139, 250, 0.06) 1px, transparent 1px);
    background-size: 44px 44px;
    -webkit-mask-image: radial-gradient(ellipse at 50% 30%, #000 0%, transparent 75%);
            mask-image: radial-gradient(ellipse at 50% 30%, #000 0%, transparent 75%);
    animation: gridmove 14s linear infinite;
}
@keyframes gridmove { to { background-position: 0 44px, 44px 0; } }

.eq {
    position: absolute; left: 0; right: 0; bottom: 0;
    height: 34vh; display: flex; align-items: flex-end; gap: 5px; padding: 0 1.5vw;
    opacity: 0.32;
    -webkit-mask-image: linear-gradient(to top, #000 0%, transparent 100%);
            mask-image: linear-gradient(to top, #000 0%, transparent 100%);
}
.eq i {
    flex: 1; height: var(--h); border-radius: 3px 3px 0 0;
    background: linear-gradient(to top, var(--accent), var(--accent-2));
    transform-origin: bottom;
    animation: bounce var(--d) ease-in-out var(--dl) infinite alternate;
    will-change: transform;
}
@keyframes bounce { from { transform: scaleY(0.12); } to { transform: scaleY(1); } }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: rgba(10, 10, 18, 0.88) !important;
    backdrop-filter: blur(14px);
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text); }

/* ── Hero ── */
.hero-title {
    font-family: 'Syne', sans-serif;
    font-size: clamp(2.2rem, 5vw, 3.8rem);
    font-weight: 800; line-height: 1.05; margin: 0;
    background: linear-gradient(110deg, #fff 0%, var(--accent-glow) 35%, var(--accent-2) 65%, #fff 100%);
    background-size: 220% auto;
    -webkit-background-clip: text; background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: shine 7s linear infinite;
}
@keyframes shine { to { background-position: 220% center; } }
.hero-sub { font-size: 1rem; color: var(--text-muted); margin-top: 0.6rem; }

/* ── Cards (bordered containers) ── */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--surface);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid var(--border) !important;
    border-radius: 14px !important;
    transition: border-color .25s, transform .25s;
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover { border-color: var(--accent) !important; }

.card-title {
    font-family: 'Syne', sans-serif; font-size: 0.95rem; font-weight: 700;
    color: var(--accent-glow); margin-bottom: 0.6rem;
}
.title-card {
    font-family: 'Syne', sans-serif; font-size: 1.6rem; font-weight: 700;
    line-height: 1.25; color: var(--text);
}

/* ── Stats ── */
.stat {
    background: var(--surface); border: 1px solid var(--border); border-radius: 14px;
    padding: 0.9rem 1.1rem; backdrop-filter: blur(12px);
}
.stat b { display: block; font-family: 'Syne', sans-serif; font-size: 1.5rem; color: var(--text); }
.stat span { font-size: 0.78rem; color: var(--text-muted); }

/* ── Badges ── */
.badge { display: inline-block; padding: 0.2rem 0.65rem; border-radius: 999px; font-size: 0.72rem; font-weight: 700; }
.badge-purple { background: rgba(124,58,237,.2); color: var(--accent-glow); border: 1px solid rgba(124,58,237,.35); }
.badge-cyan   { background: rgba(34,211,238,.14); color: var(--accent-2);   border: 1px solid rgba(34,211,238,.3); }
.badge-green  { background: rgba(52,211,153,.14); color: var(--success);    border: 1px solid rgba(52,211,153,.3); }

/* ── Inputs & buttons ── */
.stTextInput input, .stSelectbox > div > div {
    background: var(--surface-2) !important; border: 1px solid var(--border) !important;
    border-radius: 10px !important; color: var(--text) !important;
}
.stTextInput input:focus { border-color: var(--accent) !important; box-shadow: 0 0 0 2px rgba(124,58,237,.25) !important; }

.stButton > button, .stDownloadButton > button {
    background: linear-gradient(135deg, var(--accent), #5b21b6) !important;
    color: #fff !important; border: none !important; border-radius: 10px !important;
    font-family: 'Syne', sans-serif !important; font-weight: 700 !important;
    padding: 0.55rem 1.3rem !important; transition: transform .2s, box-shadow .2s !important;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    transform: translateY(-1px); box-shadow: 0 8px 28px rgba(124,58,237,.45);
}
.stButton > button[kind="secondary"], .stDownloadButton > button {
    background: var(--surface-2) !important; border: 1px solid var(--border) !important;
}

/* ── Pipeline status ── */
.status-bar {
    display: flex; align-items: center; gap: .7rem; padding: .55rem .85rem; margin: .35rem 0;
    background: var(--surface-2); border: 1px solid var(--border); border-radius: 10px; font-size: .82rem;
}
.status-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.dot-active  { background: var(--accent-glow); box-shadow: 0 0 10px var(--accent-glow); animation: pulse 1.2s infinite; }
.dot-done    { background: var(--success); }
.dot-error   { background: var(--danger); }
.dot-pending { background: var(--border); }
@keyframes pulse { 50% { opacity: .35; transform: scale(1.4); } }

/* ── Chat ── */
[data-testid="stChatMessage"] {
    background: var(--surface); border: 1px solid var(--border); border-radius: 14px;
    backdrop-filter: blur(12px);
}
[data-testid="stChatInput"] { background: var(--surface-2) !important; border: 1px solid var(--border); border-radius: 14px; }
[data-testid="stChatInput"] textarea { color: var(--text) !important; }
[data-testid="stBottom"], [data-testid="stBottom"] > div { background: transparent !important; }

/* ── Empty state ── */
.empty { display: flex; flex-direction: column; align-items: center; text-align: center; padding: 4rem 1rem 2rem; }
.mini-eq { display: flex; align-items: flex-end; gap: 6px; height: 64px; margin-bottom: 1.4rem; }
.mini-eq i { width: 8px; height: var(--h); border-radius: 4px; transform-origin: bottom;
    background: linear-gradient(to top, var(--accent), var(--accent-2));
    animation: bounce var(--d) ease-in-out var(--dl) infinite alternate; }
.empty h2 { font-size: 1.7rem; margin: 0 0 .5rem; }
.empty p { color: var(--text-muted); max-width: 440px; line-height: 1.7; }
.steps { display: flex; gap: 1rem; flex-wrap: wrap; justify-content: center; margin-top: 2rem; }
.step { background: var(--surface); border: 1px solid var(--border); border-radius: 14px;
    padding: 1rem 1.2rem; width: 190px; text-align: left; backdrop-filter: blur(12px); }
.step b { font-family: 'Syne', sans-serif; color: var(--accent-glow); display: block; margin-bottom: .25rem; }
.step span { font-size: .82rem; color: var(--text-muted); }

::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent); }

/* ── Accessibility ── */
@media (prefers-reduced-motion: reduce) {
    .aurora, .grid, .eq i, .mini-eq i, .hero-title, .status-dot { animation: none !important; }
}
</style>
"""

st.markdown(CSS + BG_HTML, unsafe_allow_html=True)

# ─── Session state ──────────────────────────────────────────────────────────────
for key, default in {
    "result": None,
    "chat_history": [],
    "pipeline_done": False,
    "pipeline_steps": {},
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

STEPS = [
    ("audio",      "🔊", "Extracting audio"),
    ("transcript", "📝", "Transcribing"),
    ("title",      "🏷️", "Writing a title"),
    ("summary",    "📋", "Summarising"),
    ("extract",    "🔍", "Finding actions & decisions"),
    ("rag",        "🧠", "Building search index"),
]


# ─── Helpers ────────────────────────────────────────────────────────────────────
def to_md(value) -> str:
    """Accept str or list output from the LLM helpers and return markdown."""
    if isinstance(value, (list, tuple)):
        return "\n".join(f"- {v}" for v in value) or "_Nothing found._"
    return str(value).strip() or "_Nothing found._"


def card(icon: str, title: str, body_md: str):
    with st.container(border=True):
        st.markdown(f'<div class="card-title">{icon} {title}</div>', unsafe_allow_html=True)
        st.markdown(body_md)


def render_pipeline():
    rows = "".join(
        f'<div class="status-bar"><div class="status-dot dot-{st.session_state.pipeline_steps.get(k, "pending")}"></div>'
        f"<span>{icon} {label}</span></div>"
        for k, icon, label in STEPS
    )
    pipeline_ph.markdown(rows, unsafe_allow_html=True)


def update_step(key: str, state: str):
    st.session_state.pipeline_steps[key] = state
    render_pipeline()


def build_report(r: dict) -> str:
    return (
        f"# {r['title']}\n\n## Summary\n{to_md(r['summary'])}\n\n"
        f"## Action items\n{to_md(r['action_items'])}\n\n"
        f"## Key decisions\n{to_md(r['key_decisions'])}\n\n"
        f"## Open questions\n{to_md(r['open_questions'])}\n\n"
        f"## Transcript\n{r['transcript']}\n"
    )


# ─── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="hero-title" style="font-size:1.8rem">🎬 AI Video<br>Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub" style="font-size:.85rem">Turn any video into notes you can chat with.</div>', unsafe_allow_html=True)
    st.markdown("---")

    st.markdown('<span class="badge badge-purple">Input</span>', unsafe_allow_html=True)
    source = st.text_input(
        "YouTube URL or file path",
        placeholder="https://youtube.com/watch?v=… or /path/to/file.mp4",
    )
    language = st.selectbox("Language", ["english", "hinglish"], index=0)
    run_btn = st.button("⚡  Analyse video", use_container_width=True)

    st.markdown("---")
    st.markdown('<span class="badge badge-green">Progress</span>', unsafe_allow_html=True)
    pipeline_ph = st.empty()
    if st.session_state.pipeline_steps:
        render_pipeline()

# ─── Hero ───────────────────────────────────────────────────────────────────────
st.markdown('<div class="hero-title">AI Video Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Transcribe, summarise, and ask questions about any video.</div>', unsafe_allow_html=True)
st.markdown("---")

# ─── Run pipeline ───────────────────────────────────────────────────────────────
if run_btn:
    if not source.strip():
        st.error("Enter a YouTube URL or a file path in the sidebar.")
    else:
        st.session_state.pipeline_done = False
        st.session_state.result = None
        st.session_state.chat_history = []
        st.session_state.pipeline_steps = {}
        render_pipeline()

        banner = st.empty()
        banner.info("⚙️ Analysing… follow the progress in the sidebar.")

        try:
            update_step("audio", "active")
            chunks = process_input(source)
            update_step("audio", "done")

            update_step("transcript", "active")
            transcript = transcribe_all(chunks, language)
            update_step("transcript", "done")

            update_step("title", "active")
            title = generate_title(transcript)
            update_step("title", "done")

            update_step("summary", "active")
            summary = summarize(transcript)
            update_step("summary", "done")

            update_step("extract", "active")
            action_items = extract_action_items(transcript)
            decisions = extract_key_decisions(transcript)
            questions = extract_questions(transcript)
            update_step("extract", "done")

            update_step("rag", "active")
            rag_chain = build_rag_chain(transcript)
            update_step("rag", "done")

            st.session_state.result = {
                "title": title,
                "language": language,
                "transcript": transcript,
                "summary": summary,
                "action_items": action_items,
                "key_decisions": decisions,
                "open_questions": questions,
                "rag_chain": rag_chain,
            }
            st.session_state.pipeline_done = True
            banner.success("✅ Analysis complete.")
            time.sleep(0.6)
            st.rerun()

        except Exception as e:
            for k, state in list(st.session_state.pipeline_steps.items()):
                if state == "active":
                    st.session_state.pipeline_steps[k] = "error"
            render_pipeline()
            banner.error(f"❌ Something went wrong: {e}")

# ─── Results ────────────────────────────────────────────────────────────────────
if st.session_state.result:
    r = st.session_state.result
    words = len(r["transcript"].split())
    minutes = max(1, round(words / 150))

    with st.container(border=True):
        st.markdown('<div class="card-title">📌 Session title</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="title-card">{html.escape(str(r["title"]))}</div>', unsafe_allow_html=True)

    s1, s2, s3, s4 = st.columns([1, 1, 1, 1.2], gap="medium")
    s1.markdown(f'<div class="stat"><b>{words:,}</b><span>Words transcribed</span></div>', unsafe_allow_html=True)
    s2.markdown(f'<div class="stat"><b>~{minutes} min</b><span>Estimated speech length</span></div>', unsafe_allow_html=True)
    s3.markdown(f'<div class="stat"><b>{html.escape(r["language"].title())}</b><span>Language</span></div>', unsafe_allow_html=True)
    with s4:
        st.download_button(
            "⬇ Download report (.md)",
            build_report(r),
            file_name="video_report.md",
            mime="text/markdown",
            use_container_width=True,
        )

    col1, col2 = st.columns([3, 2], gap="medium")
    with col1:
        card("📋", "Summary", to_md(r["summary"]))
    with col2:
        with st.container(border=True):
            st.markdown('<div class="card-title">📝 Full transcript</div>', unsafe_allow_html=True)
            with st.container(height=260):
                st.text(r["transcript"])

    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        card("✅", "Action items", to_md(r["action_items"]))
    with c2:
        card("🔑", "Key decisions", to_md(r["key_decisions"]))
    with c3:
        card("❓", "Open questions", to_md(r["open_questions"]))

    st.markdown("---")

    # ── RAG chat ───────────────────────────────────────────────────────────────
    head_l, head_r = st.columns([5, 1])
    head_l.markdown("### 💬 Chat with this video")
    if st.session_state.chat_history and head_r.button("Clear chat", type="secondary", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else "🤖"):
            st.markdown(msg["content"])

    if not st.session_state.chat_history:
        st.caption("Try one of these, or type your own question below.")
        suggestions = [
            "Summarise this in three bullet points",
            "What are the next steps?",
            "What was the main disagreement?",
        ]
        cols = st.columns(len(suggestions))
        for col, q in zip(cols, suggestions):
            col.button(
                q,
                key=f"sugg_{q}",
                type="secondary",
                use_container_width=True,
                on_click=lambda q=q: st.session_state.__setitem__("pending_q", q),
            )

    pending = st.session_state.pop("pending_q", None)
    prompt = st.chat_input("Ask anything about this video…") or pending

    if prompt:
        prompt = prompt.strip()
        with st.chat_message("user", avatar="🧑"):
            st.markdown(prompt)
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Searching the transcript…"):
                answer = ask_question(r["rag_chain"], prompt)
            st.markdown(answer)
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        st.rerun()

else:
    mini = _bars(9, 30, 100)
    st.markdown(
        f"""
    <div class="empty">
        <div class="mini-eq">{mini}</div>
        <h2>Paste a video, get the whole story</h2>
        <p>Add a YouTube link or a local file in the sidebar. The assistant listens,
        writes it all down, and lets you ask follow-up questions.</p>
        <div class="steps">
            <div class="step"><b>1. Transcribe</b><span>Audio is extracted and converted to text with Whisper.</span></div>
            <div class="step"><b>2. Summarise</b><span>Get a title, summary, action items, and decisions.</span></div>
            <div class="step"><b>3. Ask</b><span>Chat with answers drawn from the transcript.</span></div>
        </div>
    </div>""",
        unsafe_allow_html=True,
    )