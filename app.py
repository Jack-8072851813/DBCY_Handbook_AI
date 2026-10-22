import streamlit as st
import re
import requests
import base64
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from databricks.vector_search.client import VectorSearchClient
from databricks.sdk import WorkspaceClient

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Don Bosco College of Arts & Science – Handbook AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# LOGO LOADER
# ============================================================
LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo", "dbcy_logo.jpg")

def load_logo_b64(path: str) -> str:
    try:
        if os.path.exists(path):
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode()
    except Exception:
        pass
    return ""

logo_b64 = load_logo_b64(LOGO_PATH)
logo_img_html = (
    f'<img src="data:image/jpeg;base64,{logo_b64}" '
    f'style="height:76px;width:76px;border-radius:50%;object-fit:cover;'
    f'border:3px solid #D4AF37;box-shadow:0 4px 16px rgba(0,0,0,0.3);" alt="Don Bosco Logo"/>'
    if logo_b64 else
    '<div style="height:76px;width:76px;border-radius:50%;background:linear-gradient(135deg,#D4AF37,#f0d060);'
    'display:flex;align-items:center;justify-content:center;font-size:2.2rem;'
    'border:3px solid #ffffff;box-shadow:0 4px 16px rgba(0,0,0,0.25);">🎓</div>'
)
sidebar_logo_html = (
    f'<img src="data:image/jpeg;base64,{logo_b64}" '
    f'style="height:64px;width:64px;border-radius:50%;object-fit:cover;'
    f'border:2px solid #D4AF37;display:block;margin:0 auto;" alt="Logo"/>'
    if logo_b64 else
    '<div style="height:64px;width:64px;border-radius:50%;background:linear-gradient(135deg,#D4AF37,#f0d060);'
    'display:flex;align-items:center;justify-content:center;font-size:1.8rem;margin:0 auto;">🎓</div>'
)

# ============================================================
# CSS — Professional, clear, animated
# ============================================================
st.markdown("""
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Playfair+Display:wght@600;700;800&display=swap');

/* ── Base ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; }
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 15px;
    color: #1a1a2e;
    -webkit-font-smoothing: antialiased;
}

/* ── App background ── */
.stApp {
    background: linear-gradient(150deg, #eef2ff 0%, #f8faff 55%, #f0f4ff 100%);
    min-height: 100vh;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }
[data-testid="stToolbar"] { display: none; }

/* ─────────────────────────────────────────
   HEADER BANNER
───────────────────────────────────────── */
.db-header {
    background: linear-gradient(135deg, #0b1f4a 0%, #1B3A6D 50%, #1e4a8a 100%);
    border-radius: 18px;
    margin-bottom: 1.6rem;
    box-shadow: 0 10px 40px rgba(11,31,74,0.32), 0 2px 8px rgba(0,0,0,0.12);
    overflow: hidden;
    position: relative;
    animation: slideDown 0.65s cubic-bezier(0.22,1,0.36,1) both;
}
/* Subtle dot-grid texture */
.db-header::before {
    content: '';
    position: absolute; inset: 0;
    background-image: radial-gradient(circle, rgba(255,255,255,0.07) 1px, transparent 1px);
    background-size: 24px 24px;
    pointer-events: none;
}
/* Gold accent bar at bottom */
.db-header::after {
    content: '';
    position: absolute; bottom: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, transparent, #D4AF37 30%, #f5d060 70%, transparent);
}
.db-header-inner {
    display: flex;
    align-items: center;
    gap: 1.4rem;
    padding: 1.4rem 2rem 1.5rem;
    position: relative;
    z-index: 1;
}
.db-header-text { flex: 1; min-width: 0; }
.db-college-name {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 1.7rem;
    font-weight: 800;
    color: #D4AF37;
    line-height: 1.15;
    letter-spacing: 0.01em;
    text-shadow: 0 2px 12px rgba(0,0,0,0.25);
    margin-bottom: 0.22rem;
}
.db-college-location {
    font-size: 0.78rem;
    font-weight: 500;
    color: rgba(255,255,255,0.65);
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 0.18rem;
}
.db-header-tagline {
    font-size: 0.83rem;
    color: rgba(255,255,255,0.78);
    font-weight: 400;
    letter-spacing: 0.02em;
}
.db-live-badge {
    display: flex;
    align-items: center;
    gap: 6px;
    background: rgba(212,175,55,0.14);
    border: 1.5px solid rgba(212,175,55,0.5);
    border-radius: 24px;
    padding: 0.38rem 1rem;
    font-size: 0.71rem;
    font-weight: 700;
    color: #D4AF37;
    letter-spacing: 0.08em;
    white-space: nowrap;
    flex-shrink: 0;
}
.db-live-dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    background: #4ade80;
    animation: livePulse 1.8s ease-in-out infinite;
    flex-shrink: 0;
}

/* ─────────────────────────────────────────
   WELCOME / LANDING SCREEN
───────────────────────────────────────── */
.welcome-wrap {
    text-align: center;
    padding: 2.5rem 1rem 2rem;
    animation: fadeInUp 0.6s ease both;
}
.welcome-icon {
    font-size: 3.2rem;
    margin-bottom: 0.7rem;
    filter: drop-shadow(0 4px 8px rgba(27,58,109,0.2));
}
.welcome-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.45rem;
    font-weight: 700;
    color: #1B3A6D;
    margin-bottom: 0.45rem;
}
.welcome-sub {
    font-size: 0.9rem;
    color: #6b7280;
    max-width: 520px;
    margin: 0 auto 2rem;
    line-height: 1.6;
}
/* Suggestion cards grid */
.suggest-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
    gap: 0.7rem;
    max-width: 780px;
    margin: 0 auto;
}
.suggest-card {
    background: #ffffff;
    border: 1.5px solid #e0e7ff;
    border-radius: 12px;
    padding: 0.75rem 1rem;
    text-align: left;
    cursor: default;
    transition: border-color 0.2s, box-shadow 0.2s, transform 0.18s;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.suggest-card:hover {
    border-color: #4f6ef7;
    box-shadow: 0 4px 16px rgba(79,110,247,0.14);
    transform: translateY(-2px);
}
.suggest-card-icon { font-size: 1.3rem; margin-bottom: 0.3rem; }
.suggest-card-text {
    font-size: 0.83rem;
    font-weight: 500;
    color: #374151;
    line-height: 1.35;
}

/* ─────────────────────────────────────────
   CHAT MESSAGES
───────────────────────────────────────── */
.stChatMessage {
    animation: fadeInUp 0.32s ease both !important;
    border-radius: 16px !important;
    margin-bottom: 0.8rem !important;
    box-shadow: 0 2px 14px rgba(0,0,0,0.07) !important;
    border: 1px solid rgba(0,0,0,0.045) !important;
    overflow: hidden;
    background: #ffffff !important;
}

/* User message */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"])
  div[data-testid="stChatMessageContent"] {
    background: linear-gradient(135deg, #eef2ff 0%, #e6edff 100%) !important;
    border-left: 4px solid #4f6ef7 !important;
    border-radius: 0 14px 14px 0 !important;
    padding: 1rem 1.2rem !important;
    font-size: 0.96rem !important;
    font-weight: 500 !important;
    color: #1a1a2e !important;
    line-height: 1.55 !important;
}

/* Assistant message */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"])
  div[data-testid="stChatMessageContent"] {
    background: linear-gradient(135deg, #f0f7ff 0%, #e8f4ff 100%) !important;
    border-left: 4px solid #1B3A6D !important;
    border-radius: 0 14px 14px 0 !important;
    padding: 1rem 1.2rem !important;
    color: #111827 !important;
    font-size: 0.93rem !important;
    line-height: 1.75 !important;
}

/* Markdown inside assistant */
div[data-testid="stChatMessageContent"] p       { margin: 0.4rem 0; }
div[data-testid="stChatMessageContent"] ul,
div[data-testid="stChatMessageContent"] ol      { padding-left: 1.5rem; margin: 0.45rem 0; }
div[data-testid="stChatMessageContent"] li      { margin: 0.25rem 0; }
div[data-testid="stChatMessageContent"] strong  { color: #0f2a5e; font-weight: 700; }
div[data-testid="stChatMessageContent"] h1,
div[data-testid="stChatMessageContent"] h2,
div[data-testid="stChatMessageContent"] h3      { color: #1B3A6D; margin: 0.6rem 0 0.3rem; font-family: 'Playfair Display', serif; }
div[data-testid="stChatMessageContent"] code    {
    background: #eef2ff; border-radius: 5px;
    padding: 0.1rem 0.38rem; font-size: 0.85em; color: #3730a3;
}

/* ─────────────────────────────────────────
   CHAT INPUT BAR
───────────────────────────────────────── */
.stChatInputContainer {
    border-top: 2px solid #D4AF37 !important;
    padding-top: 0.9rem !important;
    background: transparent !important;
}
.stChatInputContainer textarea {
    border-radius: 14px !important;
    border: 1.5px solid #c7d2fe !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    font-size: 1rem !important;
    font-weight: 400 !important;
    letter-spacing: 0.01em !important;
    line-height: 1.55 !important;
    background: #ffffff !important;
    color: #111827 !important;
    padding: 0.9rem 1.15rem !important;
    box-shadow: 0 2px 10px rgba(79,110,247,0.09) !important;
    transition: border-color 0.22s, box-shadow 0.22s !important;
}
.stChatInputContainer textarea::placeholder {
    color: #9ca3af !important;
    font-size: 0.95rem !important;
    font-weight: 400 !important;
    font-style: italic !important;
}
.stChatInputContainer textarea:focus {
    border-color: #4f6ef7 !important;
    box-shadow: 0 0 0 4px rgba(79,110,247,0.14) !important;
    outline: none !important;
}
.stChatInputContainer button {
    border-radius: 12px !important;
    background: linear-gradient(135deg, #1B3A6D 0%, #2c5aa0 100%) !important;
    border: none !important;
    transition: transform 0.16s, box-shadow 0.16s !important;
    box-shadow: 0 3px 10px rgba(27,58,109,0.25) !important;
}
.stChatInputContainer button:hover {
    transform: scale(1.07) !important;
    box-shadow: 0 5px 18px rgba(27,58,109,0.38) !important;
}

/* ─────────────────────────────────────────
   THINKING / LOADING INDICATOR
───────────────────────────────────────── */
.thinking-wrap {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 0.5rem 0 0.8rem;
}
.thinking-label {
    font-size: 0.83rem;
    font-weight: 500;
    color: #6b7280;
    letter-spacing: 0.02em;
}
.thinking-dots {
    display: flex;
    gap: 5px;
}
.thinking-dots span {
    width: 7px; height: 7px;
    border-radius: 50%;
    background: #1B3A6D;
    animation: dotBounce 1.2s ease-in-out infinite both;
}
.thinking-dots span:nth-child(2) { animation-delay: 0.18s; background: #4f6ef7; }
.thinking-dots span:nth-child(3) { animation-delay: 0.36s; background: #D4AF37; }

/* ─────────────────────────────────────────
   SIDEBAR
───────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(170deg, #0b1f4a 0%, #1B3A6D 60%, #152f5c 100%) !important;
    border-right: none !important;
    box-shadow: 4px 0 24px rgba(0,0,0,0.18) !important;
}
[data-testid="stSidebar"] * { color: #d8e4f4 !important; }
[data-testid="stSidebar"] h3 {
    color: #D4AF37 !important;
    font-family: 'Playfair Display', serif !important;
    font-size: 0.92rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    border-bottom: 1px solid rgba(212,175,55,0.25) !important;
    padding-bottom: 0.45rem !important;
    margin-bottom: 0.65rem !important;
}
[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.1) !important;
    margin: 0.9rem 0 !important;
}
[data-testid="stSidebar"] .stButton button {
    background: rgba(255,255,255,0.07) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255,255,255,0.18) !important;
    border-radius: 10px !important;
    width: 100% !important;
    font-size: 0.84rem !important;
    font-weight: 500 !important;
    padding: 0.55rem 1rem !important;
    transition: background 0.2s, border-color 0.2s !important;
}
[data-testid="stSidebar"] .stButton button:hover {
    background: rgba(212,175,55,0.18) !important;
    border-color: rgba(212,175,55,0.5) !important;
}

/* Sidebar status pill */
.status-pill {
    display: inline-flex; align-items: center; gap: 7px;
    background: rgba(74,222,128,0.12);
    border: 1px solid rgba(74,222,128,0.35);
    border-radius: 20px;
    padding: 0.32rem 0.85rem;
    font-size: 0.74rem; font-weight: 600;
    color: #4ade80 !important;
    margin: 0.35rem 0 0.1rem;
}
.status-dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: #4ade80;
    animation: livePulse 2s ease-in-out infinite;
    flex-shrink: 0;
}

/* Sidebar quick-chips */
.qs-chip {
    display: inline-block;
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.14);
    border-radius: 18px;
    padding: 0.26rem 0.72rem;
    margin: 0.18rem 0.12rem;
    font-size: 0.75rem;
    color: #b8cce4 !important;
    cursor: default;
    transition: background 0.18s, border-color 0.18s;
    line-height: 1.4;
}
.qs-chip:hover {
    background: rgba(212,175,55,0.18);
    border-color: rgba(212,175,55,0.4);
    color: #D4AF37 !important;
}

/* ─────────────────────────────────────────
   SCROLLBAR
───────────────────────────────────────── */
::-webkit-scrollbar        { width: 5px; }
::-webkit-scrollbar-track  { background: transparent; }
::-webkit-scrollbar-thumb  { background: rgba(27,58,109,0.28); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(27,58,109,0.5); }

/* ─────────────────────────────────────────
   SPINNER override
───────────────────────────────────────── */
.stSpinner > div { border-top-color: #1B3A6D !important; }

/* ─────────────────────────────────────────
   KEYFRAME ANIMATIONS
───────────────────────────────────────── */
@keyframes slideDown {
    from { opacity: 0; transform: translateY(-20px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes livePulse {
    0%,100% { opacity: 1;   transform: scale(1); }
    50%      { opacity: 0.5; transform: scale(0.85); }
}
@keyframes dotBounce {
    0%,80%,100% { transform: translateY(0);    opacity: 0.6; }
    40%          { transform: translateY(-7px); opacity: 1; }
}
@keyframes shimmer {
    0%   { background-position: -300% 0; }
    100% { background-position:  300% 0; }
}

/* ─────────────────────────────────────────
   BOTTOM ANCHOR
───────────────────────────────────────── */
#chat-bottom { height: 1px; display: block; }
</style>
""", unsafe_allow_html=True)

# ── Auto-scroll JS — fires on every Streamlit re-render ──
st.markdown("""
<script>
(function autoScroll(){
    function go(){
        var el = document.getElementById('chat-bottom');
        if(el){ el.scrollIntoView({behavior:'smooth',block:'end'}); return; }
        var mc = document.querySelector('section.main .block-container');
        if(mc) mc.scrollTop = mc.scrollHeight;
    }
    go();
    setTimeout(go, 150);
    setTimeout(go, 500);
})();
</script>
""", unsafe_allow_html=True)

# ============================================================
# HEADER
# ============================================================
st.markdown(f"""
<div class="db-header">
  <div class="db-header-inner">
    {logo_img_html}
    <div class="db-header-text">
      <div class="db-college-name">Don Bosco College of Arts &amp; Science</div>
      <div class="db-college-location">Yelagiri Hills &nbsp;·&nbsp; Tirupattur Dist &nbsp;·&nbsp; Tamil Nadu</div>
      <div class="db-header-tagline">Handbook AI Assistant &nbsp;·&nbsp; Meta Llama 3.3 70B &nbsp;·&nbsp; 634 indexed sections</div>
    </div>
    <div class="db-live-badge">
      <span class="db-live-dot"></span> AI LIVE
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# CONFIGURATION  ← UNTOUCHED
# ============================================================
VECTOR_ENDPOINT_NAME = os.getenv("DATABRICKS_VECTOR_SEARCH_ENDPOINT", "aichatbot-vs-endpoint")
VECTOR_INDEX_NAME    = "aichatbot.gold.handbook_vector_index_v2"
SOURCE_TABLE         = "aichatbot.gold.vector_source_chunks"
LLM_MODEL            = os.getenv(
    "DATABRICKS_AI_GATEWAY_MODEL",
    "system.ai.meta-llama-3-3-70b-instruct"
)

# ============================================================
# SESSION STATE  ← UNTOUCHED
# ============================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Response cache: normalised_query → answer ─────────────
# Greetings and repeated questions are served instantly from
# cache — no backend API or model is called.
if "response_cache" not in st.session_state:
    st.session_state.response_cache = {}

if "db_ready" not in st.session_state:
    try:
        vsc = VectorSearchClient(disable_notice=True)
        st.session_state.index = vsc.get_index(
            endpoint_name=VECTOR_ENDPOINT_NAME,
            index_name=VECTOR_INDEX_NAME
        )
        st.session_state.w = WorkspaceClient()
        st.session_state.db_ready = True
    except Exception as e:
        st.session_state.db_ready = False
        if VECTOR_ENDPOINT_NAME == LLM_MODEL:
            st.session_state.db_error = (
                f"DATABRICKS_VECTOR_SEARCH_ENDPOINT is set to the model-serving endpoint "
                f"'{LLM_MODEL}', but this app needs a Vector Search endpoint for index "
                f"'{VECTOR_INDEX_NAME}'. Set it to the Vector Search endpoint name "
                f"(the configured default is 'aichatbot-vs-endpoint'), then restart the app. "
                f"Details: {e}"
            )
        else:
            st.session_state.db_error = (
                f"Could not open Vector Search index '{VECTOR_INDEX_NAME}' on endpoint "
                f"'{VECTOR_ENDPOINT_NAME}'. Verify that the endpoint exists and is ready in "
                f"this Databricks workspace, and that the index is attached to it. Set "
                f"DATABRICKS_VECTOR_SEARCH_ENDPOINT to the endpoint's exact name if it differs. "
                f"Details: {e}"
            )

if not st.session_state.get("db_ready"):
    st.error(f"❌ Failed to connect: {st.session_state.get('db_error')}")
    st.stop()

# ============================================================
# HELPERS  ← UNTOUCHED
# ============================================================
def run_sql(sql: str) -> list:
    try:
        w = st.session_state.w
        response = w.statement_execution.execute_statement(
            warehouse_id=_get_warehouse_id(),
            statement=sql,
            wait_timeout="30s"
        )
        rows = []
        if (response.result and response.result.data_array):
            for row in response.result.data_array:
                rows.append(list(row))
        return rows
    except Exception:
        return []

def _get_warehouse_id() -> str:
    if "warehouse_id" not in st.session_state:
        try:
            warehouses = list(st.session_state.w.warehouses.list())
            running = [wh for wh in warehouses if str(wh.state).upper() == "RUNNING"]
            chosen = running[0] if running else warehouses[0]
            st.session_state.warehouse_id = chosen.id
        except Exception:
            st.session_state.warehouse_id = ""
    return st.session_state.warehouse_id

def vsearch(query: str, n: int, seen: set) -> list:
    try:
        result = st.session_state.index.similarity_search(
            query_text=query,
            columns=["chunk_text", "element_type", "chunk_id"],
            num_results=n
        )
        rows = result.get("result", {}).get("data_array", [])
        fresh = []
        for row in rows:
            cid = row[2]
            if cid not in seen:
                seen.add(cid)
                fresh.append(list(row))
        return fresh
    except Exception:
        return []

# ============================================================
# GREETING RESPONSES  — instant, no API call
# ============================================================
_GREETINGS = {
    "hi"           : "Hello! 👋 Welcome to Don Bosco College Handbook AI.\nHow can I help you today? You can ask about faculty, policies, vision, anthem, hostel, departments and more.",
    "hello"        : "Hello! 👋 Welcome to Don Bosco College Handbook AI.\nHow can I help you today? You can ask about faculty, policies, vision, anthem, hostel, departments and more.",
    "hey"          : "Hey there! 👋 I'm the Don Bosco College Handbook Assistant.\nFeel free to ask me anything about the college!",
    "hi there"     : "Hi there! 👋 How can I assist you with the Don Bosco College Handbook today?",
    "good morning" : "Good morning! ☀️ Welcome to Don Bosco College Handbook AI. How can I help you?",
    "good afternoon": "Good afternoon! 🌤️ Welcome to Don Bosco College Handbook AI. How can I help you?",
    "good evening" : "Good evening! 🌙 Welcome to Don Bosco College Handbook AI. How can I help you?",
    "thanks"       : "You're welcome! 😊 Feel free to ask if you have more questions about the college.",
    "thank you"    : "You're welcome! 😊 Feel free to ask if you have more questions about the college.",
    "thank you so much": "Happy to help! 😊 Let me know if you need anything else.",
    "ok"           : "Sure! Let me know if you have any other questions about Don Bosco College.",
    "okay"         : "Sure! Let me know if you have any other questions about Don Bosco College.",
    "bye"          : "Goodbye! 👋 Feel free to come back anytime you need information about Don Bosco College.",
    "goodbye"      : "Goodbye! 👋 Have a great day! Come back whenever you need help.",
    "help"         : "I can help you with:\n- 👤 Faculty and staff details\n- 📋 College policies and rules\n- 🎵 College anthem and prayer\n- 🔭 Vision and mission\n- 🏠 Hostel facilities\n- 📝 Examination rules\n- 🏅 IQAC details\n- And much more from the college handbook!\n\nJust type your question.",
    "who are you"  : "I'm the **Don Bosco College Handbook AI Assistant** 🤖\n\nI help you find information from the official college handbook — faculty, policies, vision, anthem, hostel, departments and more.\n\nAsk me anything!",
    "what can you do": "I can answer questions from the **Don Bosco College Handbook**, including:\n- 👤 Faculty names, roles and qualifications\n- 📋 Attendance and examination policies\n- 🎵 College anthem and Lord's Prayer\n- 🔭 Vision, Mission and values\n- 🏠 Hostel rules and facilities\n- 🏅 IQAC and committee details\n- 📚 Department information\n\nJust ask away!",
}

def _normalise(text: str) -> str:
    """Lowercase, strip punctuation/extra spaces — used as cache key."""
    return re.sub(r'[^\w\s]', '', text.lower()).strip()

def get_response(query_text: str) -> tuple[str, bool]:
    """
    Returns (answer, from_cache).
    Order of resolution:
      1. Greeting dict  — instant, no API
      2. Session cache  — instant, no API
      3. ask_handbook() — hits backend
    Result from step 3 is stored in cache for future identical queries.
    """
    key = _normalise(query_text)

    # 1. Greeting check
    if key in _GREETINGS:
        return _GREETINGS[key], True

    # 2. Cache hit
    if key in st.session_state.response_cache:
        return st.session_state.response_cache[key], True

    # 3. Backend call
    answer = ask_handbook(query_text)

    # Store in cache (don't cache errors)
    if not answer.startswith("❌"):
        st.session_state.response_cache[key] = answer

    return answer, False

# ============================================================
# ASK_HANDBOOK  ← UNTOUCHED — exact notebook port
# ============================================================
def ask_handbook(query_text: str, num_results: int = 10) -> str:
    try:
        original_query = query_text

        is_person_query = bool(
            re.search(r'\b(who is|who are|tell me about|about)\b', query_text.lower())
        )

        transformed_query = query_text.lower()
        transformations = [
            (r'\bcs\b',             'Computer Science'),
            (r'\bca\b',             'Computer Applications'),
            (r'\bmca\b',            'Master of Computer Applications'),
            (r'\bbca\b',            'Bachelor of Computer Applications'),
            (r'\biqac\b',           'Internal Quality Assurance Cell'),
            (r'\bhod\b',            'Head of Department'),
            (r'\bhods\b',           'Heads of Department'),
            (r'\bfacult(y|ies)\b',  'faculty members'),
            (r'\bteachers\b',       'faculty members'),
            (r'\bprofs\b',          'professors'),
            (r'\bquardinator\b',    'coordinator'),
            (r'\bcoordinator\b',    'coordinator'),
            (r'\bco-ordinator\b',   'coordinator'),
            (r'(tell me|give me|show me)\s+', ''),
            (r'\bnames?\b',         'list'),
        ]
        for pat, rep in transformations:
            transformed_query = re.sub(pat, rep, transformed_query, flags=re.IGNORECASE)
        transformed_query = ' '.join(transformed_query.split())

        cleaned  = re.sub(r'[^\w\s]', '', query_text)
        keywords = [w.strip() for w in cleaned.split() if len(w.strip()) > 2]
        keywords = [w for w in keywords if w.lower() not in
                    ['who','what','when','where','why','how','are','the',
                     'tell','give','show','about']]

        keyword_chunks = []
        if keywords:
            try:
                fuzzy_conditions = []
                for kw in keywords[:3]:
                    kw_lower = kw.lower()
                    fuzzy_conditions.append(f"LOWER(chunk_text) LIKE '%{kw_lower}%'")
                    if len(kw_lower) >= 5:
                        prefix = kw_lower[:int(len(kw_lower)*0.8)]
                        fuzzy_conditions.append(f"LOWER(chunk_text) LIKE '%{prefix}%'")
                    if len(kw_lower) >= 4:
                        fuzzy_conditions.append(f"LOWER(chunk_text) LIKE '%{kw_lower[:3]}%'")
                    if len(kw_lower) >= 6:
                        s = int(len(kw_lower)*0.2); e = int(len(kw_lower)*0.8)
                        mid = kw_lower[s:e]
                        if len(mid) >= 3:
                            fuzzy_conditions.append(f"LOWER(chunk_text) LIKE '%{mid}%'")
                    if len(kw_lower) >= 6:
                        fuzzy_conditions.append(f"LOWER(chunk_text) LIKE '%{kw_lower[-4:]}%'")

                limit    = 25 if is_person_query else 20
                first_kw = keywords[0].lower()
                sql = f"""
                    SELECT chunk_text, element_type, chunk_id,
                           CASE WHEN LOWER(chunk_text) LIKE '%{first_kw}%' THEN 1 ELSE 2 END AS match_score
                    FROM {SOURCE_TABLE}
                    WHERE {' OR '.join(fuzzy_conditions)}
                    ORDER BY match_score, chunk_id
                    LIMIT {limit}
                """
                rows = run_sql(sql)
                for row in rows:
                    keyword_chunks.append(row[:3])
            except Exception:
                try:
                    conditions = [f"LOWER(chunk_text) LIKE '%{kw.lower()}%'" for kw in keywords[:3]]
                    limit = 20 if is_person_query else 10
                    sql = f"""
                        SELECT chunk_text, element_type, chunk_id
                        FROM {SOURCE_TABLE}
                        WHERE {' OR '.join(conditions)}
                        LIMIT {limit}
                    """
                    keyword_chunks = run_sql(sql)
                except Exception:
                    pass

        semantic_chunks = []
        seen_sem        = set()
        semantic_chunks += vsearch(query_text, num_results, seen_sem)
        if transformed_query != query_text.lower():
            semantic_chunks += vsearch(transformed_query, num_results, seen_sem)

        expanded_chunks     = []
        chunk_ids_to_expand = set()
        for chunk in (keyword_chunks + semantic_chunks):
            if len(chunk) > 2 and chunk[2]:
                if chunk[1] == "Section Header" or len(chunk[0]) < 150:
                    chunk_ids_to_expand.add(chunk[2])

        if chunk_ids_to_expand:
            try:
                conditions = []
                for cid in list(chunk_ids_to_expand)[:5]:
                    try:
                        num = int(cid.replace('chunk_', ''))
                        lo  = max(1, num - 2)
                        hi  = num + 15
                        conditions.append(
                            f"(CAST(SUBSTRING(chunk_id, 7) AS INT) BETWEEN {lo} AND {hi})")
                    except Exception:
                        pass
                if conditions:
                    sql = f"""
                        SELECT chunk_id, chunk_text, element_type
                        FROM {SOURCE_TABLE}
                        WHERE {' OR '.join(conditions)}
                        ORDER BY CAST(SUBSTRING(chunk_id, 7) AS INT)
                    """
                    for row in run_sql(sql):
                        expanded_chunks.append([row[1], row[2], row[0]])
            except Exception:
                pass

        final_chunks = []
        seen         = set()
        priority_order = (
            [keyword_chunks, expanded_chunks, semantic_chunks] if is_person_query
            else [keyword_chunks, semantic_chunks, expanded_chunks]
        )
        for chunk_list in priority_order:
            for chunk in chunk_list:
                cid = chunk[2] if len(chunk) > 2 else chunk[0][:50]
                if cid not in seen:
                    final_chunks.append(chunk)
                    seen.add(cid)
                    if len(final_chunks) >= 50:
                        break
            if len(final_chunks) >= 50:
                break

        if not final_chunks:
            return "I couldn't find relevant information. Try rephrasing your question."

        context = "\n".join(
            f"[Section {i+1}]\n{doc[0]}\n"
            for i, doc in enumerate(final_chunks[:50])
        )

        prompt = f"""You are a helpful assistant for Don Bosco College. Answer based on the handbook context.

IMPORTANT:
- Provide COMPLETE, comprehensive answers
- For person/name queries: list ALL relevant information about that person (name, role, department, qualifications)
- For faculty/people queries: list ALL relevant names with roles
- For Vision/Mission/Anthem: provide FULL content
- For policies: provide COMPLETE information
- Use bullet points or lists for clarity
- Don't cut off in the middle
- If you find the person in the context, provide ALL their information

User Question: {query_text}
(System understood as: {transformed_query})

Context:
{context}

Answer:"""

        w     = st.session_state.w
        host  = os.getenv("DATABRICKS_HOST", w.config.host).rstrip("/")
        token = os.getenv("DATABRICKS_TOKEN") or w.config.token
        gateway_url = os.getenv(
            "DATABRICKS_AI_GATEWAY_BASE_URL",
            f"{host}/ai-gateway/mlflow/v1"
        ).rstrip("/")
        if not token:
            raise ValueError(
                "Databricks authentication did not provide a token. Set DATABRICKS_TOKEN "
                "or configure Databricks authentication for the workspace."
            )

        response = requests.post(
            f"{gateway_url}/chat/completions",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"model": LLM_MODEL,
                  "messages": [{"role": "user", "content": prompt}],
                  "max_tokens": 2500, "temperature": 0.2},
            timeout=60
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    except Exception as e:
        return f"❌ Error: {str(e)}"

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown(
        f'<div style="padding:0.6rem 0 0.4rem;">{sidebar_logo_html}</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div style="text-align:center;">'
        '<div style="font-family:\'Playfair Display\',serif;font-size:0.95rem;'
        'font-weight:700;color:#D4AF37;margin-top:0.45rem;line-height:1.3;">'
        'Don Bosco College</div>'
        '<div style="font-size:0.72rem;color:#8aa0be;margin-top:0.2rem;'
        'letter-spacing:0.06em;">YELAGIRI HILLS, TAMIL NADU</div>'
        '</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div style="text-align:center;margin:0.5rem 0;">'
        '<span class="status-pill">'
        '<span class="status-dot"></span>AI System Online'
        '</span></div>',
        unsafe_allow_html=True
    )

    st.markdown("---")
    st.markdown("### 💬 Quick Questions")
    chips = [
        "Who is Baskar?", "IQAC Coordinator", "CS faculty names",
        "College Vision", "College Anthem", "Attendance policy",
        "Hostel facilities", "Examination rules", "College Mission",
        "When is College Day?"
    ]
    st.markdown(
        "".join(f'<span class="qs-chip">{c}</span>' for c in chips),
        unsafe_allow_html=True
    )

    st.markdown("---")
    st.markdown("### ℹ️ System Info")
    st.markdown("""
<div style="font-size:0.8rem;line-height:2.1;color:#b0c4de;">
  <div>🤖 &nbsp;<span style="color:#D4AF37;font-weight:600;">Model</span>
       &nbsp;&nbsp; Meta Llama 3.3 70B</div>
  <div>📚 &nbsp;<span style="color:#D4AF37;font-weight:600;">Index</span>
       &nbsp;&nbsp;&nbsp; 634 handbook chunks</div>
  <div>🔍 &nbsp;<span style="color:#D4AF37;font-weight:600;">Search</span>
       &nbsp; SQL + Vector hybrid</div>
  <div>✏️ &nbsp;<span style="color:#D4AF37;font-weight:600;">Typo fix</span>
       &nbsp; 5-strategy fuzzy</div>
</div>
""", unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🗑️  Clear Conversation"):
        st.session_state.messages = []
        st.rerun()

    st.markdown(
        '<div style="font-size:0.68rem;color:#4d6280;text-align:center;'
        'margin-top:1.2rem;letter-spacing:0.04em;">Powered by Databricks AI</div>',
        unsafe_allow_html=True
    )

# ============================================================
# MAIN — Welcome screen when no messages
# ============================================================
if not st.session_state.messages:
    st.markdown("""
<div class="welcome-wrap">
  <div class="welcome-icon">🎓</div>
  <div class="welcome-title">Welcome to Don Bosco Handbook AI</div>
  <div class="welcome-sub">
    Ask any question about Don Bosco College of Arts &amp; Science, Yelagiri Hills —
    faculty, policies, vision, anthem, departments, hostel and more.
    Even spelling mistakes are handled automatically!
  </div>
  <div class="suggest-grid">
    <div class="suggest-card"><div class="suggest-card-icon">👤</div>
      <div class="suggest-card-text">Who is Baskar? Who is the HOD of CS?</div></div>
    <div class="suggest-card"><div class="suggest-card-icon">📋</div>
      <div class="suggest-card-text">What is the attendance policy?</div></div>
    <div class="suggest-card"><div class="suggest-card-icon">🎵</div>
      <div class="suggest-card-text">Show me the full College Anthem</div></div>
    <div class="suggest-card"><div class="suggest-card-icon">🔭</div>
      <div class="suggest-card-text">What is the Vision &amp; Mission?</div></div>
    <div class="suggest-card"><div class="suggest-card-icon">👩‍🏫</div>
      <div class="suggest-card-text">List all CS faculty names</div></div>
    <div class="suggest-card"><div class="suggest-card-icon">🏠</div>
      <div class="suggest-card-text">Tell me about hostel facilities</div></div>
    <div class="suggest-card"><div class="suggest-card-icon">📝</div>
      <div class="suggest-card-text">Explain the examination rules</div></div>
    <div class="suggest-card"><div class="suggest-card-icon">🏅</div>
      <div class="suggest-card-text">IQAC Coordinator details</div></div>
  </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# CHAT HISTORY
# ============================================================
for message in st.session_state.messages:
    avatar = "🧑‍🎓" if message["role"] == "user" else "🤖"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# Bottom anchor for auto-scroll
st.markdown('<div id="chat-bottom"></div>', unsafe_allow_html=True)

# ============================================================
# CHAT INPUT
# ============================================================
if prompt := st.chat_input("Type your question about Don Bosco College handbook here…"):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user", avatar="🧑‍🎓"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🤖"):
        # Check cache/greeting first — show thinking only if backend needed
        cache_key = _normalise(prompt)
        is_instant = (cache_key in _GREETINGS) or (cache_key in st.session_state.response_cache)

        if not is_instant:
            thinking_placeholder = st.empty()
            thinking_placeholder.markdown("""
<div class="thinking-wrap">
  <div class="thinking-dots">
    <span></span><span></span><span></span>
  </div>
  <div class="thinking-label">Searching handbook…</div>
</div>
""", unsafe_allow_html=True)

        response, from_cache = get_response(prompt)

        if not is_instant:
            thinking_placeholder.empty()

        st.markdown(response)

        # Show a subtle cache badge so user knows it was instant
        if from_cache:
            st.markdown(
                '<div style="margin-top:0.35rem;">'
                '<span style="font-size:0.7rem;color:#9ca3af;background:#f3f4f6;'
                'border-radius:10px;padding:2px 9px;border:1px solid #e5e7eb;">'
                '⚡ Instant reply</span></div>',
                unsafe_allow_html=True
            )

    st.session_state.messages.append({"role": "assistant", "content": response})

    # Scroll to bottom after new answer
    st.markdown("""
<script>
setTimeout(function(){
    var el = document.getElementById('chat-bottom');
    if(el) el.scrollIntoView({behavior:'smooth',block:'end'});
}, 120);
setTimeout(function(){
    var el = document.getElementById('chat-bottom');
    if(el) el.scrollIntoView({behavior:'smooth',block:'end'});
}, 600);
</script>
""", unsafe_allow_html=True)