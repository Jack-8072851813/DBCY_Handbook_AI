import streamlit as st
import streamlit.components.v1 as components
import re
import requests
import base64
import hashlib
import hmac
import io
import logging
import os
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from dotenv import load_dotenv
from pypdf import PdfReader

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from databricks.vector_search.client import VectorSearchClient
from databricks.sdk import WorkspaceClient

logger = logging.getLogger(__name__)

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Don Bosco College of Arts & Science – Handbook AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="auto"
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
    f'border:3px solid #f5f5f7;box-shadow:0 4px 16px rgba(0,0,0,0.12);" alt="Don Bosco Logo"/>'
    if logo_b64 else
    '<div style="height:76px;width:76px;border-radius:50%;background:linear-gradient(135deg,#f5f5f7,#dedee0);'
    'display:flex;align-items:center;justify-content:center;font-size:2.2rem;'
    'border:3px solid #ffffff;box-shadow:0 4px 16px rgba(0,0,0,0.25);">🎓</div>'
)
sidebar_logo_html = (
    f'<img src="data:image/jpeg;base64,{logo_b64}" '
    f'style="height:64px;width:64px;border-radius:50%;object-fit:cover;'
    f'border:2px solid #f5f5f7;display:block;margin:0 auto;" alt="Logo"/>'
    if logo_b64 else
    '<div style="height:64px;width:64px;border-radius:50%;background:linear-gradient(135deg,#f5f5f7,#dedee0);'
    'display:flex;align-items:center;justify-content:center;font-size:1.8rem;margin:0 auto;">🎓</div>'
)

# ============================================================
# CSS — Professional, clear, animated
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

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
    padding: 1.4rem 1.25rem 1.5rem 2rem;
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

/* ─────────────────────────────────────────
   NEUTRAL, ACCESSIBLE CHAT THEME
───────────────────────────────────────── */
:root {
    color-scheme: light;
    --canvas: #f3f3f3;
    --neutralLayer1: #ffffff;
    --neutralLayer2: #f3f3f3;
    --neutralLayer3: #e9e9e9;
    --neutralLayer4: #dedede;
    --text-primary: #242424;
    --text-secondary: #616161;
    --border-subtle: rgba(36,36,36,0.12);
    --accent: #0078d4;
    --success: #107c41;
    --warning: #d83b01;
    --surface-raised: var(--neutralLayer1);
    --surface: var(--neutralLayer2);
    --shadow-soft: 0 1px 3px rgba(0,0,0,0.08);
    --font-body: "Segoe UI", -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    --font-size-xs: 0.75rem;
    --font-size-sm: 0.875rem;
    --font-size-body: 1rem;
    --font-size-lg: 1.25rem;
    --font-size-title: clamp(1.8rem, 4vw, 2.75rem);
    --line-height-body: 1.5;
}

html, body, [class*="css"] {
    font-family: var(--font-body) !important;
    font-optical-sizing: auto;
    color: var(--text-primary);
    font-size: var(--font-size-body);
    line-height: var(--line-height-body);
}

.stApp {
    background: var(--canvas) !important;
    color: var(--text-primary);
    transition: background-color 0.16s ease, color 0.16s ease;
}

section.main > div,
[data-testid="stMainBlockContainer"] {
    background: transparent;
}

.db-header {
    background: var(--neutralLayer1);
    border: 1px solid var(--border-subtle);
    border-radius: 12px;
    box-shadow: var(--shadow-soft);
    animation-duration: 0.16s;
}
.db-header::before, .db-header::after { display: none; }
.db-header-inner { padding: 1.25rem 1.5rem; }
.db-header img, .db-header > div img {
    border-color: var(--border-subtle) !important;
    box-shadow: none !important;
}
.db-college-name {
    color: var(--text-primary);
    font-family: var(--font-body);
    font-size: clamp(1.25rem, 2vw, 1.75rem);
    font-weight: 700;
    letter-spacing: -0.025em;
    text-shadow: none;
}
.db-college-location {
    color: var(--text-secondary);
    letter-spacing: 0.06em;
}
.db-header-tagline { color: var(--text-secondary); }
.db-live-badge {
    background: color-mix(in srgb, var(--accent) 8%, var(--neutralLayer1));
    border: 1px solid color-mix(in srgb, var(--accent) 24%, transparent);
    color: var(--accent);
}
.db-live-dot { background: var(--success); }

.welcome-wrap { padding: clamp(2rem, 6vw, 5rem) 1rem 2.5rem; }
.welcome-icon { filter: none; }
.welcome-title {
    color: var(--text-primary);
    font-family: var(--font-body);
    font-size: var(--font-size-title);
    font-weight: 700;
    line-height: 1.15;
    letter-spacing: -0.035em;
}
.welcome-sub {
    color: var(--text-secondary);
    font-size: var(--font-size-body);
    line-height: 1.6;
}
.suggest-card {
    background: var(--neutralLayer1);
    border: 1px solid var(--border-subtle);
    border-radius: 10px;
    box-shadow: none;
    transition: border-color 0.14s ease, background-color 0.14s ease, box-shadow 0.14s ease;
}
.suggest-card:hover {
    border-color: color-mix(in srgb, var(--accent) 48%, transparent);
    background: var(--neutralLayer2);
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}
.suggest-card-text {
    color: var(--text-primary);
    font-size: var(--font-size-sm);
    line-height: 1.45;
}
.suggest-grid {
    grid-template-columns: repeat(auto-fit, minmax(min(100%, 220px), 1fr));
    gap: 0.85rem;
    max-width: 920px;
}

.stChatMessage {
    background: var(--neutralLayer1) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 12px !important;
    box-shadow: var(--shadow-soft) !important;
    animation-duration: 0.14s !important;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"])
  div[data-testid="stChatMessageContent"],
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"])
  div[data-testid="stChatMessageContent"] {
    background: transparent !important;
    color: var(--text-primary) !important;
    line-height: 1.6 !important;
}
div[data-testid="stChatMessageContent"] strong,
div[data-testid="stChatMessageContent"] h1,
div[data-testid="stChatMessageContent"] h2,
div[data-testid="stChatMessageContent"] h3 {
    color: var(--text-primary);
    font-family: var(--font-body);
}
div[data-testid="stChatMessageContent"] a {
    color: var(--accent);
    text-underline-offset: 0.15em;
}
div[data-testid="stChatMessageContent"] code {
    background: var(--neutralLayer2);
    color: var(--text-primary);
}

.stChatInputContainer {
    border-top: 1px solid var(--border-subtle) !important;
    background: color-mix(in srgb, var(--neutralLayer1) 92%, transparent) !important;
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
}
.stChatInputContainer textarea {
    border: 1px solid var(--border-subtle) !important;
    border-radius: 8px !important;
    background: var(--neutralLayer1) !important;
    color: var(--text-primary) !important;
    box-shadow: none !important;
    font-family: var(--font-body) !important;
    font-size: var(--font-size-body) !important;
    transition: border-color 0.14s ease, box-shadow 0.14s ease !important;
}
.stChatInputContainer textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px color-mix(in srgb, var(--accent) 24%, transparent) !important;
}
.stChatInputContainer button {
    background: var(--accent) !important;
    border-radius: 8px !important;
    box-shadow: none !important;
    transition: filter 0.14s ease, background-color 0.14s ease !important;
}
.stChatInputContainer button:hover {
    filter: brightness(0.92);
    box-shadow: 0 0 0 2px color-mix(in srgb, var(--accent) 22%, transparent) !important;
}

[data-testid="stSidebar"] {
    background: var(--neutralLayer1) !important;
    border-right: 1px solid var(--border-subtle) !important;
    box-shadow: none !important;
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
}
[data-testid="stSidebar"] * { color: var(--text-primary) !important; }
[data-testid="stSidebar"] h3 {
    color: var(--text-secondary) !important;
    font-family: var(--font-body) !important;
    font-size: var(--font-size-xs) !important;
    letter-spacing: 0.08em !important;
    border-bottom-color: var(--border-subtle) !important;
}
[data-testid="stSidebar"] hr { border-color: var(--border-subtle) !important; }
[data-testid="stSidebar"] .stButton button {
    background: var(--neutralLayer2) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 8px !important;
    transition: background-color 0.14s ease, border-color 0.14s ease !important;
}
[data-testid="stSidebar"] .stButton button:hover {
    background: var(--neutralLayer3) !important;
    border-color: color-mix(in srgb, var(--accent) 40%, transparent) !important;
}
.qs-chip {
    background: var(--surface);
    border-color: var(--border-subtle);
    color: var(--text-secondary) !important;
}
.qs-chip:hover {
    background: color-mix(in srgb, var(--accent) 8%, var(--neutralLayer1));
    border-color: color-mix(in srgb, var(--accent) 30%, transparent);
    color: var(--accent) !important;
}
.status-pill {
    background: color-mix(in srgb, var(--success) 8%, var(--neutralLayer1));
    border-color: color-mix(in srgb, var(--success) 25%, transparent);
    color: var(--success) !important;
}
.status-dot { background: var(--success); }
.thinking-label { color: var(--text-secondary); }
.cache-badge {
    display: inline-block;
    color: var(--text-secondary);
    background: var(--surface);
    border: 1px solid var(--border-subtle);
    border-radius: 10px;
    padding: 2px 9px;
    font-size: 0.7rem;
}
.thinking-dots span,
.thinking-dots span:nth-child(2),
.thinking-dots span:nth-child(3) { background: var(--accent); }
::-webkit-scrollbar-thumb { background: rgba(29,29,31,0.2); }
::-webkit-scrollbar-thumb:hover { background: rgba(29,29,31,0.34); }
.stSpinner > div { border-top-color: var(--accent) !important; }

body:has([data-testid="stToggle"] [role="switch"][aria-checked="true"]) {
    color-scheme: dark;
    --canvas: #111111;
    --neutralLayer1: #1b1b1b;
    --neutralLayer2: #202020;
    --neutralLayer3: #292929;
    --neutralLayer4: #333333;
    --text-primary: #f5f5f5;
    --text-secondary: #c8c8c8;
    --border-subtle: rgba(255,255,255,0.12);
    --accent: #4da6ff;
    --success: #6ccb8b;
    --warning: #ff8c65;
    --surface-raised: var(--neutralLayer1);
    --surface: var(--neutralLayer2);
    --shadow-soft: 0 1px 3px rgba(0,0,0,0.24);
}
body:has([data-testid="stToggle"] [role="switch"][aria-checked="true"]) .db-live-badge {
    background: color-mix(in srgb, var(--accent) 14%, var(--neutralLayer1));
    border-color: color-mix(in srgb, var(--accent) 32%, transparent);
}
body:has([data-testid="stToggle"] [role="switch"][aria-checked="true"])
  [data-testid="stSidebar"] .stButton button:hover {
    background: var(--neutralLayer3) !important;
}

@media (prefers-reduced-motion: reduce) {
    html:focus-within { scroll-behavior: auto !important; }
    .db-header, .welcome-wrap, .stChatMessage,
    .thinking-dots span, .status-dot, .db-live-dot {
        animation: reducedFade 0.12s ease-out both !important;
        transform: none !important;
    }
    *, *::before, *::after {
        scroll-behavior: auto !important;
        transition-duration: 0.01ms !important;
    }
}
@keyframes reducedFade {
    from { opacity: 0.6; }
    to { opacity: 1; }
}
@media (max-width: 640px) {
    .db-header-inner { gap: 0.8rem; padding: 1rem; }
    .db-header-inner > img,
    .db-header-inner > div:first-child { width: 52px !important; height: 52px !important; }
    .db-live-badge { padding: 0.3rem 0.65rem; font-size: var(--font-size-xs); }
    .suggest-grid { grid-template-columns: 1fr; }
    .welcome-wrap { padding-top: 2rem; }
}

/* ─────────────────────────────────────────
   ENTERPRISE CHAT DESIGN TOKENS & COMPONENTS
───────────────────────────────────────── */
:root {
    color-scheme: light;
    --canvas: #EFF6FF;
    --surface: #FFFFFF;
    --surface-muted: #DBEAFE;
    --sidebar: #102A56;
    --text-primary: #0F172A;
    --text-secondary: #334E68;
    --text-placeholder: #647FA3;
    --accent: #1D4ED8;
    --accent-hover: #1E40AF;
    --ai-accent: #2563EB;
    --border-subtle: #BFDBFE;
    --error: #DC2626;
    --warning: #D97706;
    --surface-raised: var(--surface);
    --shadow-soft: 0 1px 3px rgba(15,23,42,0.08);
    --font-body: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    --font-code: "JetBrains Mono", "Cascadia Code", Consolas, monospace;
    --radius-control: 10px;
    --radius-card: 14px;
    --space-1: 4px;
    --space-2: 8px;
    --space-3: 12px;
    --space-4: 16px;
    --space-6: 24px;
}

html, body, [class*="css"], button, input, textarea {
    font-family: var(--font-body) !important;
    color: var(--text-primary);
    -webkit-font-smoothing: antialiased;
}
html, body { background: var(--canvas); }
.stApp {
    background: var(--canvas) !important;
    color: var(--text-primary) !important;
}
section.main > div,
[data-testid="stMainBlockContainer"] { background: transparent !important; }
[data-testid="stMainBlockContainer"] {
    max-width: 1120px;
    padding-left: clamp(1rem, 3vw, 2.5rem);
    padding-right: clamp(1rem, 3vw, 2.5rem);
}

.db-header {
    background: var(--surface) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-card) !important;
    box-shadow: var(--shadow-soft) !important;
    margin-bottom: var(--space-6) !important;
    animation: fadeInUp 0.2s ease-out both !important;
}
.db-header::before, .db-header::after { display: none !important; }
.db-header-inner { gap: var(--space-4); padding: 1rem 1.25rem !important; }
.db-header img, .db-header-inner > div:first-child {
    border-color: var(--border-subtle) !important;
    box-shadow: none !important;
}
.db-college-name {
    color: var(--text-primary) !important;
    font: 600 1.2rem/1.3 var(--font-body) !important;
    letter-spacing: -0.025em !important;
    text-shadow: none !important;
}
.db-college-location {
    color: var(--text-secondary) !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.025em !important;
}
.db-header-tagline { color: var(--text-secondary) !important; font-size: 0.8rem !important; }
.db-live-badge {
    color: var(--ai-accent) !important;
    background: rgba(13,148,136,0.08) !important;
    border: 1px solid rgba(13,148,136,0.2) !important;
    font-size: 0.7rem !important;
}
.db-live-dot, .status-dot { background: var(--ai-accent) !important; animation: none !important; }

.welcome-wrap {
    max-width: 920px;
    margin: 0 auto;
    padding: clamp(2rem, 7vh, 4.5rem) 0 2rem !important;
    animation: fadeInUp 0.2s ease-out both !important;
}
.welcome-icon { filter: none !important; }
.welcome-title {
    color: var(--text-primary) !important;
    font: 600 clamp(2rem, 4vw, 2.5rem)/1.2 var(--font-body) !important;
    letter-spacing: -0.04em !important;
}
.welcome-sub {
    color: var(--text-secondary) !important;
    font-size: 1rem !important;
    line-height: 1.65 !important;
    max-width: 620px !important;
}
.suggest-grid {
    grid-template-columns: repeat(auto-fit, minmax(min(100%, 230px), 1fr)) !important;
    gap: var(--space-3) !important;
    max-width: 920px !important;
}
.suggest-card {
    min-height: 100%;
    padding: var(--space-4) !important;
    background: var(--surface) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-card) !important;
    box-shadow: none !important;
    transition: background-color 0.18s ease, border-color 0.18s ease,
                box-shadow 0.18s ease, transform 0.18s ease !important;
}
.suggest-card:hover {
    background: var(--surface-muted) !important;
    border-color: rgba(37,99,235,0.35) !important;
    box-shadow: 0 3px 10px rgba(15,23,42,0.07) !important;
    transform: translateY(-1px) !important;
}
.suggest-card-icon { font-size: 1.15rem !important; }
.suggest-card-text {
    color: var(--text-secondary) !important;
    font-size: 0.875rem !important;
    line-height: 1.5 !important;
}

.stChatMessage {
    background: var(--surface) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-card) !important;
    box-shadow: var(--shadow-soft) !important;
    margin-bottom: var(--space-3) !important;
    animation: fadeInUp 0.2s ease-out both !important;
}
[data-testid="stChatMessageContent"] {
    color: var(--text-primary) !important;
    font-size: 0.96rem !important;
    line-height: 1.65 !important;
    overflow-wrap: anywhere;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"])
  div[data-testid="stChatMessageContent"],
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"])
  div[data-testid="stChatMessageContent"] {
    background: transparent !important;
    border: 0 !important;
    color: var(--text-primary) !important;
}
[data-testid="stChatMessageContent"] p { margin: 0.45rem 0 !important; }
[data-testid="stChatMessageContent"] h1,
[data-testid="stChatMessageContent"] h2,
[data-testid="stChatMessageContent"] h3,
[data-testid="stChatMessageContent"] h4 {
    color: var(--text-primary) !important;
    font-family: var(--font-body) !important;
    font-weight: 600 !important;
    line-height: 1.35 !important;
    margin: 1rem 0 0.5rem !important;
}
[data-testid="stChatMessageContent"] ul,
[data-testid="stChatMessageContent"] ol { padding-left: 1.5rem !important; }
[data-testid="stChatMessageContent"] li { margin: 0.25rem 0 !important; }
[data-testid="stChatMessageContent"] a {
    color: var(--accent) !important;
    text-underline-offset: 0.15em;
}
[data-testid="stChatMessageContent"] a:hover { color: var(--accent-hover) !important; }
[data-testid="stChatMessageContent"] blockquote {
    border-left: 3px solid var(--accent) !important;
    background: var(--surface-muted);
    color: var(--text-secondary) !important;
    margin: 0.75rem 0 !important;
    padding: 0.5rem 1rem !important;
}
[data-testid="stChatMessageContent"] table {
    display: block;
    max-width: 100%;
    overflow-x: auto;
    border-collapse: collapse;
    border: 1px solid var(--border-subtle);
}
[data-testid="stChatMessageContent"] th,
[data-testid="stChatMessageContent"] td {
    padding: 0.55rem 0.75rem !important;
    border: 1px solid var(--border-subtle) !important;
    text-align: left;
}
[data-testid="stChatMessageContent"] th {
    background: var(--surface-muted) !important;
    font-weight: 600 !important;
}
[data-testid="stChatMessageContent"] pre,
[data-testid="stChatMessageContent"] code,
[data-testid="stCodeBlock"] code {
    font-family: var(--font-code) !important;
    font-size: 0.84rem !important;
}
[data-testid="stChatMessageContent"] pre {
    max-width: 100%;
    overflow-x: auto;
    background: var(--surface-muted) !important;
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-control) !important;
    padding: 0.85rem 1rem !important;
}
[data-testid="stChatMessageContent"] :not(pre) > code {
    background: var(--surface-muted) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border-subtle);
    border-radius: 5px;
    padding: 0.1rem 0.35rem;
}

.stChatInputContainer {
    border-top: 1px solid var(--border-subtle) !important;
    background: rgba(248,250,252,0.94) !important;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    padding-top: var(--space-3) !important;
}
.stChatInputContainer textarea {
    background: var(--surface) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-control) !important;
    box-shadow: 0 1px 3px rgba(15,23,42,0.06) !important;
    font: 400 0.96rem/1.5 var(--font-body) !important;
    transition: border-color 0.16s ease, box-shadow 0.16s ease !important;
}
.stChatInputContainer textarea::placeholder { color: var(--text-placeholder) !important; }
.stChatInputContainer textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.14) !important;
}

[data-testid="stSidebar"] {
    background: var(--sidebar) !important;
    border-right: 1px solid rgba(226,232,240,0.12) !important;
    box-shadow: none !important;
    transition: background-color 0.18s ease !important;
}
[data-testid="stSidebar"] *,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    color: #F8FAFC !important;
}
[data-testid="stSidebar"] h3 {
    color: #CBD5E1 !important;
    font: 600 0.78rem/1.4 var(--font-body) !important;
    letter-spacing: 0.025em !important;
    text-transform: none !important;
    border-bottom: 1px solid rgba(226,232,240,0.16) !important;
}
[data-testid="stSidebar"] hr { border-color: rgba(226,232,240,0.16) !important; }
[data-testid="stSidebar"] .stButton button {
    width: 100% !important;
    color: #F8FAFC !important;
    background: rgba(248,250,252,0.06) !important;
    border: 1px solid rgba(226,232,240,0.16) !important;
    border-radius: var(--radius-control) !important;
    font: 500 0.875rem var(--font-body) !important;
    transition: background-color 0.16s ease, border-color 0.16s ease,
                transform 0.12s ease !important;
}
[data-testid="stSidebar"] .stButton button:hover {
    background: rgba(248,250,252,0.12) !important;
    border-color: rgba(248,250,252,0.3) !important;
}
[data-testid="stSidebar"] .stButton button:active { transform: scale(0.985); }
[data-testid="stSidebar"] [data-testid="stToggle"] label,
[data-testid="stSidebar"] [data-testid="stToggle"] label p {
    color: #CBD5E1 !important;
    font-size: 0.85rem !important;
}
.qs-chip {
    color: #CBD5E1 !important;
    background: rgba(248,250,252,0.06) !important;
    border: 1px solid rgba(226,232,240,0.14) !important;
    border-radius: 999px !important;
    transition: background-color 0.16s ease, border-color 0.16s ease !important;
}
.qs-chip:hover {
    color: #FFFFFF !important;
    background: rgba(37,99,235,0.24) !important;
    border-color: rgba(96,165,250,0.45) !important;
}
.status-pill {
    color: #5EEAD4 !important;
    background: rgba(13,148,136,0.16) !important;
    border-color: rgba(13,148,136,0.36) !important;
    font-size: 0.75rem !important;
}
.cache-badge {
    color: var(--text-secondary) !important;
    background: var(--surface-muted) !important;
    border: 1px solid var(--border-subtle) !important;
}

.stButton button, .stDownloadButton button {
    border-radius: var(--radius-control) !important;
    transition: background-color 0.16s ease, border-color 0.16s ease,
                box-shadow 0.16s ease, transform 0.12s ease !important;
}
.stButton button:active, .stDownloadButton button:active,
.stChatInputContainer button:active { transform: scale(0.98); }
.stButton button:disabled, .stDownloadButton button:disabled,
.stChatInputContainer button:disabled {
    opacity: 0.55 !important;
    cursor: not-allowed !important;
}
button:focus-visible, textarea:focus-visible, input:focus-visible,
[role="switch"]:focus-visible {
    outline: 3px solid rgba(37,99,235,0.65) !important;
    outline-offset: 2px !important;
}
.stChatInputContainer button {
    color: #FFFFFF !important;
    background: var(--accent) !important;
    border: 1px solid var(--accent) !important;
    border-radius: var(--radius-control) !important;
    box-shadow: 0 1px 2px rgba(15,23,42,0.12) !important;
    transition: background-color 0.16s ease, border-color 0.16s ease,
                box-shadow 0.16s ease, transform 0.12s ease !important;
}
.stChatInputContainer button:hover {
    background: var(--accent-hover) !important;
    border-color: var(--accent-hover) !important;
    box-shadow: 0 2px 5px rgba(15,23,42,0.16) !important;
}

.thinking-label { color: var(--text-secondary) !important; font-size: 0.8rem !important; }
.thinking-dots span,
.thinking-dots span:nth-child(2),
.thinking-dots span:nth-child(3) {
    background: var(--ai-accent) !important;
    animation-name: dotBounce;
    animation-duration: 1.1s;
}
@keyframes dotBounce {
    0%, 80%, 100% { opacity: 0.5; transform: translateY(0); }
    40% { opacity: 1; transform: translateY(-3px); }
}
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(4px); }
    to { opacity: 1; transform: translateY(0); }
}
.stAlert [data-testid="stAlertContentError"] { color: var(--error) !important; }
.stAlert [data-testid="stAlertContentWarning"] { color: var(--warning) !important; }
.stSpinner > div { border-top-color: var(--accent) !important; }
::-webkit-scrollbar-thumb { background: #CBD5E1 !important; border-radius: 6px; }
::-webkit-scrollbar-thumb:hover { background: #94A3B8 !important; }

body:has([data-testid="stToggle"] [role="switch"][aria-checked="true"]) {
    color-scheme: dark;
    --canvas: #0B1730;
    --surface: #102347;
    --surface-muted: #173461;
    --sidebar: #08152D;
    --text-primary: #F8FAFC;
    --text-secondary: #D5E5FF;
    --text-placeholder: #9DB8E2;
    --accent: #60A5FA;
    --accent-hover: #93C5FD;
    --ai-accent: #60A5FA;
    --border-subtle: #294B7B;
    --surface-raised: var(--surface);
    --shadow-soft: 0 1px 3px rgba(0,0,0,0.28);
}
body:has([data-testid="stToggle"] [role="switch"][aria-checked="true"])
  .stChatInputContainer { background: rgba(11,18,32,0.94) !important; }
body:has([data-testid="stToggle"] [role="switch"][aria-checked="true"])
  [data-testid="stSidebar"] .stButton button:hover {
    background: rgba(248,250,252,0.14) !important;
}

/* ─────────────────────────────────────────
   BLUE IDENTITY AND HIGH-CLARITY TYPOGRAPHY
───────────────────────────────────────── */
html, body, [class*="css"], button, input, textarea,
[data-testid="stMarkdownContainer"] {
    font-family: var(--font-body) !important;
}
body, [data-testid="stMarkdownContainer"] p,
[data-testid="stChatMessageContent"] p,
.suggest-card-text, .welcome-sub {
    font-weight: 500 !important;
}
.db-header {
    background: #163B78 !important;
    border-color: #1D4ED8 !important;
    box-shadow: 0 4px 14px rgba(29,78,216,0.16) !important;
}
.db-college-name { color: #FFFFFF !important; font-weight: 700 !important; }
.db-college-location, .db-header-tagline { color: #DBEAFE !important; font-weight: 500 !important; }
.db-header-tagline::after { content: none !important; }
.db-live-badge {
    color: #FFFFFF !important;
    background: rgba(255,255,255,0.12) !important;
    border-color: rgba(255,255,255,0.3) !important;
    font-weight: 700 !important;
}
.welcome-title {
    color: var(--accent) !important;
    font-weight: 700 !important;
    letter-spacing: -0.025em !important;
}
.welcome-sub { color: var(--text-secondary) !important; }
.suggest-card {
    border-color: #BFDBFE !important;
    box-shadow: 0 2px 8px rgba(30,64,175,0.06) !important;
}
.suggest-card:hover {
    background: #EFF6FF !important;
    border-color: var(--accent) !important;
    box-shadow: 0 4px 12px rgba(30,64,175,0.14) !important;
}
.suggest-card-text { color: var(--text-primary) !important; font-weight: 600 !important; }
.suggest-card-icon { color: var(--accent) !important; }
.stChatMessage {
    border-color: var(--border-subtle) !important;
    box-shadow: 0 2px 8px rgba(30,64,175,0.07) !important;
}
[data-testid="stChatMessageContent"] {
    color: var(--text-primary) !important;
    font-weight: 500 !important;
}
[data-testid="stChatMessageContent"] strong,
[data-testid="stChatMessageContent"] h1,
[data-testid="stChatMessageContent"] h2,
[data-testid="stChatMessageContent"] h3,
[data-testid="stChatMessageContent"] h4 {
    color: var(--accent-hover) !important;
    font-weight: 700 !important;
}
.stChatInputContainer textarea { font-weight: 500 !important; }
.stChatInputContainer textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.2) !important;
}
.stChatInputContainer button {
    background: var(--accent) !important;
    border-color: var(--accent) !important;
    font-weight: 700 !important;
}
.stChatInputContainer button:hover {
    background: var(--accent-hover) !important;
    border-color: var(--accent-hover) !important;
}
[data-testid="stSidebar"] {
    background: var(--sidebar) !important;
    border-right-color: #1E3A66 !important;
}
[data-testid="stSidebar"] h3 {
    color: #BFDBFE !important;
    font-weight: 700 !important;
}
[data-testid="stSidebar"] .stButton button {
    border-color: rgba(191,219,254,0.24) !important;
    font-weight: 600 !important;
}
[data-testid="stSidebar"] .stButton button:hover {
    background: rgba(37,99,235,0.28) !important;
    border-color: #60A5FA !important;
}
.qs-chip { font-weight: 600 !important; }
.status-pill {
    color: #DBEAFE !important;
    background: rgba(37,99,235,0.26) !important;
    border-color: rgba(147,197,253,0.46) !important;
    font-weight: 700 !important;
}
.cache-badge { color: var(--text-secondary) !important; font-weight: 600 !important; }
button:focus-visible, textarea:focus-visible, input:focus-visible,
[role="switch"]:focus-visible {
    outline-color: #3B82F6 !important;
}
body:has([data-testid="stToggle"] [role="switch"][aria-checked="true"]) .db-header {
    background: #102B55 !important;
    border-color: #3B82F6 !important;
}
body:has([data-testid="stToggle"] [role="switch"][aria-checked="true"]) .suggest-card:hover {
    background: #173461 !important;
}
body:has([data-testid="stToggle"] [role="switch"][aria-checked="true"]) .stChatInputContainer {
    background: rgba(11,23,48,0.96) !important;
}
body:has([data-testid="stToggle"] [role="switch"][aria-checked="true"])
  [data-testid="stChatMessageContent"] h1,
body:has([data-testid="stToggle"] [role="switch"][aria-checked="true"])
  [data-testid="stChatMessageContent"] h2,
body:has([data-testid="stToggle"] [role="switch"][aria-checked="true"])
  [data-testid="stChatMessageContent"] h3,
body:has([data-testid="stToggle"] [role="switch"][aria-checked="true"])
  [data-testid="stChatMessageContent"] h4 {
    color: #93C5FD !important;
}

/* ─────────────────────────────────────────
   RESPONSIVE LAYOUT REFINEMENTS
───────────────────────────────────────── */
[data-testid="stMainBlockContainer"] {
    width: min(100%, 1360px) !important;
    max-width: 1360px !important;
    padding: 1.25rem clamp(1rem, 3vw, 2.5rem) 7.5rem !important;
}
.db-header {
    width: 100%;
    max-width: none;
    margin: 0 auto 1.25rem !important;
    position: fixed;
    top: 0;
    z-index: 1001;
    padding-top: 0.25rem;
    background: var(--canvas);
}
.welcome-wrap {
    width: 100%;
    max-width: 1000px;
    padding-top: clamp(1rem, 4vh, 2.5rem) !important;
}
.suggest-grid {
    width: 100%;
    grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
}
.suggest-card {
    min-width: 0;
    overflow-wrap: anywhere;
}
.stChatInputContainer {
    z-index: 100;
    padding: 0.75rem clamp(1rem, 3vw, 2.5rem) 1rem !important;
}
.stChatInputContainer textarea {
    min-height: 48px !important;
}
[data-testid="stChatMessageContent"] table { width: 100%; }
.db-live-badge { margin-right: 3.5rem; }
.st-key-pdf_upload_control {
    position: fixed !important;
    z-index: 1003 !important;
    width: 44px !important;
    min-width: 44px !important;
    margin: 0 !important;
    padding: 0 !important;
}
.st-key-pdf_upload_control [data-testid="stButton"] { width: 44px !important; }
.st-key-pdf_upload_control button {
    width: 44px !important;
    min-height: 44px !important;
    padding: 0 !important;
    border: 1px solid rgba(255,255,255,0.48) !important;
    border-radius: 14px !important;
    background: linear-gradient(145deg, #f5d978, #d4af37) !important;
    color: #102b55 !important;
    font-size: 1.5rem !important;
    font-weight: 700 !important;
    box-shadow: 0 5px 16px rgba(0,0,0,0.2) !important;
    transition: transform 160ms ease, box-shadow 160ms ease !important;
}
.st-key-pdf_upload_control button:hover {
    transform: translateY(-1px);
    box-shadow: 0 8px 20px rgba(0,0,0,0.24) !important;
}
.pdf-upload-dialog-copy {
    color: #52627a;
    font-size: 0.92rem;
    line-height: 1.6;
    margin-bottom: 0.8rem;
}

@media (min-width: 1440px) {
    [data-testid="stMainBlockContainer"] { max-width: 1440px !important; }
    .welcome-wrap { max-width: 1080px; }
}
@media (min-width: 641px) and (max-width: 1024px) {
    [data-testid="stMainBlockContainer"] {
        padding: 1rem 1.25rem 7rem !important;
    }
    .suggest-grid { grid-template-columns: repeat(2, minmax(0, 1fr)) !important; }
    .welcome-wrap { padding-top: 1.5rem !important; }
    .db-header-inner { padding: 1rem 1.15rem !important; }
    .stChatInputContainer { padding-left: 1.25rem !important; padding-right: 1.25rem !important; }
}
@media (max-width: 640px) {
    [data-testid="stMainBlockContainer"] {
        padding: 0.75rem 0.75rem 6.5rem !important;
    }
    .db-header { margin-bottom: 0.75rem !important; border-radius: 12px !important; }
    .db-header-inner { gap: 0.55rem; padding: 0.75rem !important; }
    .db-header-inner > img,
    .db-header-inner > div:first-child { width: 48px !important; height: 48px !important; }
    .db-college-name { font-size: clamp(0.9rem, 4vw, 1.05rem) !important; }
    .db-college-location { font-size: 0.62rem !important; line-height: 1.3 !important; }
    .db-header-tagline { font-size: 0.72rem !important; }
    .db-live-badge { padding: 0.2rem 0.45rem; font-size: 0.58rem !important; }
    .db-live-badge { margin-right: 3rem; }
    .st-key-pdf_upload_control,
    .st-key-pdf_upload_control [data-testid="stButton"],
    .st-key-pdf_upload_control button { width: 38px !important; min-width: 38px !important; }
    .st-key-pdf_upload_control button { min-height: 38px !important; font-size: 1.3rem !important; }
    .welcome-wrap { padding: 1.25rem 0.25rem 1rem !important; }
    .welcome-icon { font-size: 2.25rem !important; margin-bottom: 0.4rem !important; }
    .welcome-title { font-size: clamp(1.65rem, 7.5vw, 2rem) !important; }
    .welcome-sub { font-size: 0.9rem !important; margin-bottom: 1.25rem !important; }
    .suggest-grid { grid-template-columns: 1fr !important; gap: 0.6rem !important; }
    .suggest-card { padding: 0.8rem 0.9rem !important; }
    .suggest-card-icon { font-size: 1rem !important; margin-bottom: 0.2rem !important; }
    .suggest-card-text { font-size: 0.84rem !important; }
    .stChatMessage { padding: 0.75rem !important; }
    [data-testid="stChatMessageContent"] { font-size: 0.92rem !important; }
    .stChatInputContainer { padding: 0.6rem 0.75rem 0.75rem !important; }
    .stChatInputContainer textarea { font-size: 0.9rem !important; }
}
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        scroll-behavior: auto !important;
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
}

/* Final viewport rules override earlier theme-specific sizing. */
[data-testid="stMainBlockContainer"] {
    box-sizing: border-box !important;
    width: 100% !important;
    max-width: 1280px !important;
    margin-inline: auto !important;
    padding: 1.25rem clamp(1rem, 3vw, 2rem) 7rem !important;
}
.st-key-selected_handbook_edition {
    width: min(100%, 28rem);
}
[data-testid="stChatMessage"] {
    box-sizing: border-box;
    max-width: 100%;
}
[data-testid="stChatMessageContent"] {
    min-width: 0;
    overflow-wrap: anywhere;
}
[data-testid="stChatMessageContent"] table {
    display: block;
    max-width: 100%;
    overflow-x: auto;
}
.stChatInputContainer {
    box-sizing: border-box !important;
    width: 100% !important;
}
.db-header-inner,
.db-header-text {
    min-width: 0;
}
.db-college-name,
.db-college-location {
    overflow-wrap: anywhere;
}

@media (min-width: 1025px) {
    .st-key-selected_handbook_edition { margin-inline: auto; }
    .db-header-inner { padding-inline: clamp(1.25rem, 3vw, 2.5rem) !important; }
}
@media (min-width: 641px) and (max-width: 1024px) {
    [data-testid="stMainBlockContainer"] {
        padding: 1rem 1.25rem 7rem !important;
    }
    .st-key-selected_handbook_edition { width: min(100%, 24rem); }
    .db-header-inner { gap: 0.85rem; }
    .stChatMessage { padding: 0.9rem !important; }
    .stChatInputContainer { padding-inline: 1.25rem !important; }
}
@media (max-width: 640px) {
    [data-testid="stMainBlockContainer"] {
        padding: 0.75rem 0.65rem calc(6.5rem + env(safe-area-inset-bottom)) !important;
    }
    .st-key-selected_handbook_edition { width: 100%; }
    .db-header-inner { gap: 0.5rem !important; padding: 0.7rem !important; }
    .db-header-inner > img,
    .db-header-inner > div:first-child {
        flex: 0 0 42px;
        width: 42px !important;
        height: 42px !important;
    }
    .db-college-name { font-size: clamp(0.82rem, 4vw, 1rem) !important; }
    .db-college-location { font-size: 0.6rem !important; }
    .db-header-tagline { font-size: 0.68rem !important; }
    .db-live-badge { margin-right: 2.5rem !important; }
    .stChatMessage {
        gap: 0.45rem !important;
        padding: 0.65rem !important;
        margin-bottom: 0.6rem !important;
    }
    [data-testid="stChatMessageContent"] {
        font-size: 0.91rem !important;
        line-height: 1.55 !important;
    }
    [data-testid="stChatMessageContent"] ul,
    [data-testid="stChatMessageContent"] ol { padding-left: 1.2rem !important; }
    .stChatInputContainer {
        padding: 0.55rem 0.65rem calc(0.65rem + env(safe-area-inset-bottom)) !important;
    }
    .stChatInputContainer textarea {
        min-height: 2.8rem !important;
        padding: 0.7rem 0.8rem !important;
        font-size: 0.92rem !important;
    }
    .stChatInputContainer button { min-width: 2.6rem !important; }
}
.st-key-handbook_year_filter {
    box-sizing: border-box;
    width: 100%;
    max-width: 56rem;
    margin: 0 auto 1rem;
    padding: 0.9rem 1rem 0.65rem;
    border: 1px solid var(--border-subtle);
    border-radius: 12px;
    background: var(--surface);
    box-shadow: var(--shadow-soft);
}
.st-key-handbook_year_filter [data-testid="stSelectbox"] {
    width: 100% !important;
}
.st-key-handbook_year_filter [data-testid="stCaptionContainer"] {
    margin-top: 0.3rem;
    color: var(--text-secondary);
}
@media (max-width: 640px) {
    .st-key-handbook_year_filter {
        margin-bottom: 0.75rem;
        padding: 0.7rem 0.75rem 0.5rem;
        border-radius: 10px;
    }
}
</style>
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
      <div class="db-header-tagline">Handbook AI Assistant</div>
    </div>
    <div class="db-live-badge">
      <span class="db-live-dot"></span> AI LIVE
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

components.html("""
<script>
const host = window.parent;
const doc = host.document;
const syncHeader = () => {
  const header = doc.querySelector(".db-header");
  const main = doc.querySelector('[data-testid="stMainBlockContainer"]');
  if (!header || !main) return;
  const rect = main.getBoundingClientRect();
  const style = host.getComputedStyle(main);
  const leftPadding = parseFloat(style.paddingLeft) || 0;
  const rightPadding = parseFloat(style.paddingRight) || 0;
  header.style.left = `${rect.left + leftPadding}px`;
  header.style.width = `${rect.width - leftPadding - rightPadding}px`;
  const spacer = header.closest('[data-testid="stElementContainer"]');
  if (spacer) {
    const marginBottom = parseFloat(host.getComputedStyle(header).marginBottom) || 0;
    spacer.style.minHeight = `${header.offsetHeight + marginBottom}px`;
  }
};
if (host.__dbcyHeaderResizeObserver) {
  host.__dbcyHeaderResizeObserver.disconnect();
}
if (host.__dbcyHeaderResizeHandler) {
  host.removeEventListener("resize", host.__dbcyHeaderResizeHandler);
}
syncHeader();
const syncUploadButton = () => {
  const header = doc.querySelector(".db-header");
  const control = doc.querySelector(".st-key-pdf_upload_control");
  const button = control && Array.from(control.querySelectorAll("button")).find(
    candidate => candidate.getBoundingClientRect().width > 0
  );
  if (!header || !control || !button) return;
  const rect = header.getBoundingClientRect();
  control.style.left = `${rect.right - 18 - button.offsetWidth}px`;
  control.style.top = `${rect.top + (rect.height - button.offsetHeight) / 2}px`;
};
let syncFrame;
const scheduleLayoutSync = () => {
  if (syncFrame) host.cancelAnimationFrame(syncFrame);
  syncFrame = host.requestAnimationFrame(() => {
    syncHeader();
    syncUploadButton();
  });
};
if (host.__dbcyUploadObserver) {
  host.__dbcyUploadObserver.disconnect();
}
host.__dbcyUploadObserver = new host.MutationObserver(scheduleLayoutSync);
host.__dbcyUploadObserver.observe(doc.body, { childList: true, subtree: true });
host.__dbcyHeaderResizeObserver = new host.ResizeObserver(scheduleLayoutSync);
host.__dbcyHeaderResizeObserver.observe(
  doc.querySelector('[data-testid="stMainBlockContainer"]')
);
host.__dbcyHeaderResizeHandler = scheduleLayoutSync;
host.removeEventListener("resize", host.__dbcyHeaderResizeHandler);
host.addEventListener("resize", scheduleLayoutSync);
scheduleLayoutSync();
</script>
""", height=0, scrolling=False)

# ============================================================
# CONFIGURATION  ← UNTOUCHED
# ============================================================
VECTOR_ENDPOINT_NAME = os.getenv("DATABRICKS_VECTOR_SEARCH_ENDPOINT", "aichatbot-vs-endpoint")
VECTOR_INDEX_NAME    = "aichatbot.gold.handbook_vector_index_v2"
GOLD_TABLE           = "aichatbot.gold.vector_source_chunks"
SOURCE_TABLE         = GOLD_TABLE
BRONZE_TABLE         = "aichatbot.bronze.handbook_pdf_parsed"
SILVER_TABLE         = "aichatbot.silver.handbook_cleaned"
PDF_VOLUME_PATH      = os.getenv(
    "DATABRICKS_PDF_VOLUME_PATH",
    "/Volumes/aichatbot/raw/pdf_files"
).rstrip("/")
MAX_PDF_SIZE_BYTES   = 50 * 1024 * 1024
ALL_HANDBOOKS        = "All years"
LEGACY_HANDBOOK_EDITION = "2024-2025"
HANDBOOK_EDITION_SQL_REGEX = (
    r"Handbook edition: ([0-9]{4}(?:-[0-9]{4}|-[0-9]{2})?)"
)
HANDBOOK_EDITION_PATH_REGEX = (
    r"(?<![0-9])([0-9]{4}[-_](?:[0-9]{2}|[0-9]{4}))(?![0-9])"
)
ANSWER_CACHE_VERSION = "complete-handbook-answers-v7"
LLM_MODEL            = os.getenv(
    "DATABRICKS_AI_GATEWAY_MODEL",
    "system.ai.meta-llama-3-3-70b-instruct"
)

# ============================================================
# SESSION STATE  ← UNTOUCHED
# ============================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Response cache: selected edition + normalised query → answer ──
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
def run_sql(sql: str, workspace=None, warehouse_id=None) -> list:
    try:
        if workspace is None:
            workspace = st.session_state.w
        if warehouse_id is None:
            warehouse_id = _get_warehouse_id()
        response = workspace.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=sql,
            wait_timeout="30s"
        )
        deadline = time.monotonic() + 60
        while True:
            status = getattr(response, "status", None)
            state = getattr(status, "state", None)
            state_value = str(getattr(state, "value", state)).upper()
            if state_value.endswith("SUCCEEDED"):
                break
            if state_value.endswith(("FAILED", "CANCELED", "CLOSED")):
                error = getattr(status, "error", None)
                detail = getattr(error, "message", None) or state_value
                raise RuntimeError(f"Databricks SQL statement failed: {detail}")

            statement_id = getattr(response, "statement_id", None)
            if not statement_id or time.monotonic() >= deadline:
                raise TimeoutError("Timed out waiting for the handbook database query.")
            time.sleep(1)
            response = workspace.statement_execution.get_statement(statement_id)

        rows = []
        if (response.result and response.result.data_array):
            for row in response.result.data_array:
                rows.append(list(row))
        return rows
    except Exception as error:
        logger.exception("Databricks SQL query failed.")
        raise RuntimeError("The handbook database query failed.") from error

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

def _execute_upload_sql(sql: str, workspace, warehouse_id: str) -> None:
    if not warehouse_id:
        raise RuntimeError(
            "No SQL warehouse is available. Start a Databricks SQL warehouse and try again."
        )

    response = workspace.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=sql,
        wait_timeout="50s"
    )
    deadline = time.monotonic() + 60
    while True:
        status = getattr(response, "status", None)
        state = getattr(status, "state", None)
        state_value = str(getattr(state, "value", state)).upper()
        if state_value.endswith("SUCCEEDED"):
            return
        if state_value.endswith(("FAILED", "CANCELED", "CLOSED")):
            error = getattr(status, "error", None)
            detail = getattr(error, "message", None) or state_value
            raise RuntimeError(f"Databricks SQL statement failed: {detail}")

        statement_id = getattr(response, "statement_id", None)
        if not statement_id or time.monotonic() >= deadline:
            raise TimeoutError("Timed out waiting for the Databricks SQL statement.")
        time.sleep(1)
        response = workspace.statement_execution.get_statement(statement_id)

_HANDBOOK_LANGUAGE_MARKERS = frozenset(
    "a about academic admission after all an and are as at attendance be before "
    "between by calendar can college committee course department education every "
    "examination faculty first foremost for from have head hostel in is it its love "
    "may members mission must not of on or policy principal programme realize rules "
    "shall staff student students teaching that the their this to university was "
    "were will with"
    .split()
)
_PDF_ROTATION_MINUS_THREE = str.maketrans(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
    "XYZABCDEFGHIJKLMNOPQRSTUVWxyzabcdefghijklmnopqrstuvw"
)

def _pdf_language_score(text: str) -> int:
    return sum(
        word in _HANDBOOK_LANGUAGE_MARKERS
        for word in re.findall(r"[A-Za-z]{2,}", text.lower())
    )

def _clean_pdf_text(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", " ", text)
    text = re.sub(r"[ \t\f\v]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    decoded_text = text.translate(_PDF_ROTATION_MINUS_THREE)
    raw_score = _pdf_language_score(text)
    decoded_score = _pdf_language_score(decoded_text)
    if decoded_score >= max(3, raw_score * 2) and decoded_score - raw_score >= 2:
        text = decoded_text
    return re.sub(r"\n{3,}", "\n\n", text).strip()

def _normalise_handbook_edition(edition: str, allow_legacy: bool = False) -> str:
    edition = edition.strip().replace("/", "-")
    if not re.fullmatch(r"\d{4}(?:-\d{2}|-\d{4})?", edition):
        raise ValueError("Enter the handbook year as YYYY, YYYY-YY, or YYYY-YYYY.")
    if allow_legacy and "-" in edition:
        start, end = edition.split("-")
        next_year = int(start) + 1
        if len(end) == 2 and end == f"{next_year:04d}"[:2]:
            return f"{start}-{next_year:04d}"
    if "-" in edition and not allow_legacy:
        start, end = edition.split("-")
        next_year = int(start) + 1
        expected_end = f"{next_year:04d}" if len(end) == 4 else f"{next_year % 100:02d}"
        if end != expected_end:
            raise ValueError("The end year must be the year immediately after the start year.")
    if "-" in edition:
        start, end = edition.split("-")
        next_year = int(start) + 1
        if len(end) == 2 and end == f"{next_year % 100:02d}":
            edition = f"{start}-{next_year:04d}"
    return edition

def _make_pdf_chunks(
    pdf_bytes: bytes,
    filename: str,
    document_id: str,
    edition: str,
    document_name: Optional[str] = None
) -> list:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    if reader.is_encrypted:
        raise ValueError("This PDF is encrypted. Upload an unlocked PDF.")

    chunks = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = _clean_pdf_text(page.extract_text() or "")
        start = 0
        page_chunk = 0
        while start < len(text):
            end = min(start + 1200, len(text))
            if end < len(text):
                boundary = max(
                    text.rfind("\n", start + 800, end),
                    text.rfind(" ", start + 800, end)
                )
                if boundary > start:
                    end = boundary

            chunk_text = text[start:end].strip()
            if chunk_text:
                page_chunk += 1
                chunks.append((
                    f"Handbook edition: {edition}\n"
                    f"Document: {filename} | Page {page_number}\n{chunk_text}",
                    "PDF Page",
                    f"pdf_{document_id}_{page_number:04d}_{page_chunk:04d}",
                    document_name or filename
                ))
            if end >= len(text):
                break
            start = max(end - 150, start + 1)

    if not chunks:
        raise ValueError(
            "No selectable text was found in this PDF. Scanned PDFs need OCR before upload."
        )
    return chunks

def _sql_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"

def _edition_sql_condition(edition: str) -> Optional[str]:
    if edition == ALL_HANDBOOKS:
        if st.session_state.get("handbook_volume_index_complete", False):
            document_names = [
                name
                for names in st.session_state.get(
                    "handbook_document_names_by_edition", {}
                ).values()
                for name in names
            ]
            if document_names:
                names = ", ".join(_sql_string(name) for name in document_names)
                return (
                    f"(chunk_text LIKE '%Handbook edition:%' "
                    f"OR document_name IN ({names}))"
                )
            return "chunk_text LIKE '%Handbook edition:%'"
        return None

    edition = _normalise_handbook_edition(edition, allow_legacy=True)
    extracted_edition = (
        "regexp_extract(chunk_text, "
        f"{_sql_string(HANDBOOK_EDITION_SQL_REGEX)}, 1)"
    )
    equivalent_labels = [edition]
    if "-" in edition and len(edition.split("-")[1]) == 4:
        start, end = edition.split("-")
        equivalent_labels.append(f"{start}-{end[-2:]}")
        if edition == LEGACY_HANDBOOK_EDITION:
            equivalent_labels.append("2024-20")
    labels = ", ".join(_sql_string(label) for label in equivalent_labels)
    edition_match = f"{extracted_edition} IN ({labels})"
    document_names = st.session_state.get(
        "handbook_document_names_by_edition", {}
    ).get(edition, [])
    if document_names:
        names = ", ".join(_sql_string(name) for name in document_names)
        edition_match = (
            f"({edition_match} OR (chunk_text NOT LIKE '%Handbook edition:%' "
            f"AND document_name IN ({names})))"
        )
    if (
        edition == LEGACY_HANDBOOK_EDITION
        and not st.session_state.get("handbook_volume_index_complete", False)
    ):
        return (
            f"({edition_match} OR (chunk_text NOT LIKE '%Handbook edition:%' "
            "AND (document_name IS NULL OR TRIM(document_name) = '')))"
        )
    return edition_match

def _list_stored_handbook_pdfs(workspace=None) -> list[tuple[str, str]]:
    if workspace is None:
        workspace = st.session_state.w

    pdfs = []
    try:
        entries = workspace.files.list_directory_contents(PDF_VOLUME_PATH)
        for entry in entries:
            path = str(getattr(entry, "path", "") or "")
            filename = path.rsplit("/", 1)[-1]
            if getattr(entry, "is_directory", False) or not filename.lower().endswith(".pdf"):
                continue

            match = re.search(
                r"(?<!\d)(\d{4})[-_](\d{2}|\d{4})(?!\d)",
                filename,
                re.IGNORECASE
            )
            if not match:
                logger.warning("Ignoring handbook PDF without a year in its filename: %s", filename)
                continue

            try:
                edition = _normalise_handbook_edition(
                    f"{match.group(1)}-{match.group(2)}",
                    allow_legacy=True
                )
            except ValueError:
                logger.warning("Ignoring handbook PDF with an invalid year: %s", filename)
                continue
            pdfs.append((path, edition))
    except Exception as error:
        logger.exception("Could not list handbook PDFs from the Databricks volume.")
        raise RuntimeError(
            f"Could not check stored handbook PDFs in {PDF_VOLUME_PATH}: {error}"
        ) from error

    return sorted(pdfs, key=lambda item: (item[1], item[0]), reverse=True)

def _get_handbook_index_metadata() -> tuple[dict[str, int], dict[str, list[str]]]:
    rows = run_sql(
        f"""
        WITH handbook_chunks AS (
            SELECT document_name,
                   CASE WHEN chunk_text LIKE '%Handbook edition:%'
                        THEN TRIM(SUBSTRING(
                            chunk_text,
                            LOCATE('Handbook edition: ', chunk_text) + 18,
                            9
                        ))
                        ELSE ''
                   END AS edition
            FROM {SOURCE_TABLE}
        )
        SELECT document_name, edition, COUNT(*) AS chunk_count
        FROM handbook_chunks
        GROUP BY document_name, edition
        """
    )
    editions = {}
    document_names = {}
    for row in rows:
        if not row:
            continue
        document_name = str(row[0]).strip() if row[0] else ""
        raw_label = str(row[1]).strip().splitlines()[0] if row[1] else ""
        if raw_label:
            try:
                label = _normalise_handbook_edition(raw_label, allow_legacy=True)
            except ValueError:
                logger.warning(
                    "Ignoring invalid handbook year label in stored chunks: %r",
                    raw_label
                )
            else:
                editions[label] = editions.get(label, 0) + int(row[2] or 0)

        if document_name:
            named_edition = _handbook_edition_from_document_name(document_name)
            if named_edition:
                document_names.setdefault(named_edition, set()).add(document_name)
    return editions, {
        edition: sorted(names)
        for edition, names in document_names.items()
    }

def _has_untagged_handbook_chunks() -> bool:
    rows = run_sql(
        f"""
        SELECT 1
        FROM {SOURCE_TABLE}
        WHERE chunk_text IS NOT NULL
          AND chunk_text NOT LIKE '%Handbook edition:%'
        LIMIT 1
        """
    )
    return bool(rows)

def _get_available_editions() -> dict[str, int]:
    try:
        stored_pdfs = _list_stored_handbook_pdfs()
    except RuntimeError as error:
        stored_pdfs = []
        st.session_state.handbook_volume_error = str(error)
    else:
        st.session_state.handbook_volume_error = None
    sql_error = None
    try:
        tagged_editions, document_names_by_edition = _get_handbook_index_metadata()
    except RuntimeError as error:
        tagged_editions = {}
        document_names_by_edition = {}
        sql_error = str(error)
    editions = dict(tagged_editions)
    for edition in document_names_by_edition:
        editions.setdefault(edition, 0)
    for _, edition in stored_pdfs:
        editions.setdefault(edition, 0)

    if not stored_pdfs and not tagged_editions and not sql_error:
        try:
            if _has_untagged_handbook_chunks():
                editions[LEGACY_HANDBOOK_EDITION] = 0
        except RuntimeError as error:
            sql_error = str(error)

    st.session_state.handbook_volume_pdfs = stored_pdfs
    st.session_state.tagged_handbook_editions = tagged_editions
    st.session_state.handbook_document_names_by_edition = document_names_by_edition
    st.session_state.handbook_sql_error = sql_error
    volume_editions = {edition for _, edition in stored_pdfs}
    st.session_state.handbook_volume_index_complete = bool(volume_editions) and (
        volume_editions.issubset(tagged_editions)
    )
    return dict(sorted(
        editions.items(),
        key=lambda item: _handbook_edition_sort_key(item[0]),
        reverse=True
    ))

def _handbook_edition_sort_key(edition: str) -> tuple[int, int]:
    parts = edition.split("-")
    start = int(parts[0])
    return start, int(parts[1]) if len(parts) == 2 else start

def _handbook_edition_from_chunk(chunk_text: str) -> str:
    match = re.search(
        r"^Handbook edition: ([0-9]{4}(?:-[0-9]{4}|-[0-9]{2})?)$",
        chunk_text,
        re.MULTILINE
    )
    if not match:
        return LEGACY_HANDBOOK_EDITION
    return _normalise_handbook_edition(match.group(1), allow_legacy=True)

def _handbook_edition_from_document_name(document_name: str) -> Optional[str]:
    match = re.search(HANDBOOK_EDITION_PATH_REGEX, document_name, re.IGNORECASE)
    if not match:
        return None
    try:
        return _normalise_handbook_edition(
            match.group(1).replace("_", "-"),
            allow_legacy=True
        )
    except ValueError:
        return None

def _handbook_edition_for_chunk(chunk: list) -> str:
    chunk_text = str(chunk[0])
    if "Handbook edition:" in chunk_text:
        return _handbook_edition_from_chunk(chunk_text)
    if len(chunk) > 3 and chunk[3]:
        named_edition = _handbook_edition_from_document_name(str(chunk[3]))
        if named_edition:
            return named_edition
    return LEGACY_HANDBOOK_EDITION

def _move_handbook_edition(source: str, destination: str) -> Optional[str]:
    source = _normalise_handbook_edition(source, allow_legacy=True)
    destination = _normalise_handbook_edition(destination)
    if source == destination:
        raise ValueError("Choose a different destination year.")

    source_prefix = f"Handbook edition: {source}"
    destination_prefix = f"Handbook edition: {destination}"
    warehouse_id = _get_warehouse_id()
    _execute_upload_sql(
        f"UPDATE {SOURCE_TABLE} "
        f"SET chunk_text = CONCAT({_sql_string(destination_prefix)}, "
        f"SUBSTRING(chunk_text, LENGTH({_sql_string(source_prefix)}) + 1)) "
        f"WHERE chunk_text LIKE {_sql_string(source_prefix + chr(10) + '%')}",
        st.session_state.w,
        warehouse_id
    )
    try:
        st.session_state.index.sync()
    except Exception as error:
        return str(error)
    return None

def _edition_delete_aliases(edition: str) -> list[str]:
    edition = _normalise_handbook_edition(edition, allow_legacy=True)
    aliases = [edition]
    if "-" in edition:
        start, end = edition.split("-")
        aliases.extend((
            f"{start}-{end[-2:]}",
            f"{start}_{end}",
            f"{start}_{end[-2:]}",
        ))
    return list(dict.fromkeys(aliases))

def _edition_delete_condition(columns: tuple[str, ...], edition: str) -> str:
    allowed_columns = {"path", "document_name"}
    if not columns or any(column not in allowed_columns for column in columns):
        raise ValueError("Unsupported handbook data column for year-scoped deletion.")

    labels = ", ".join(
        _sql_string(label) for label in _edition_delete_aliases(edition)
    )
    return "(" + " OR ".join(
        f"regexp_extract(COALESCE({column}, ''), "
        f"{_sql_string(HANDBOOK_EDITION_PATH_REGEX)}, 1) IN ({labels})"
        for column in columns
    ) + ")"

def _get_edition_delete_preview(edition: str) -> dict:
    edition = _normalise_handbook_edition(edition, allow_legacy=True)
    workspace = st.session_state.w
    table_conditions = {
        BRONZE_TABLE: _edition_delete_condition(("path",), edition),
        SILVER_TABLE: _edition_delete_condition(("path", "document_name"), edition),
        GOLD_TABLE: _edition_delete_condition(("document_name",), edition),
    }
    counts = {}
    for table, condition in table_conditions.items():
        rows = run_sql(f"SELECT COUNT(*) FROM {table} WHERE {condition}")
        if not rows or not rows[0]:
            raise RuntimeError(f"Could not count {table} rows for {edition}.")
        counts[table] = int(rows[0][0] or 0)

    pdfs = [
        path for path, pdf_edition in _list_stored_handbook_pdfs(workspace)
        if pdf_edition == edition
    ]
    return {
        "edition": edition,
        "counts": counts,
        "pdf_paths": pdfs,
    }

def _delete_handbook_edition(edition: str, reviewed_preview: dict) -> Optional[str]:
    admin_password_secret = os.getenv("HANDBOOK_ADMIN_PASSWORD", "")
    admin_secret_fingerprint = hashlib.sha256(
        admin_password_secret.encode("utf-8")
    ).hexdigest()
    if (
        len(admin_password_secret) < 16
        or not st.session_state.get("handbook_delete_admin", False)
        or st.session_state.get("handbook_delete_admin_secret_fingerprint")
        != admin_secret_fingerprint
    ):
        raise PermissionError("Admin authentication is required to delete handbook data.")

    edition = _normalise_handbook_edition(edition, allow_legacy=True)
    current_preview = _get_edition_delete_preview(edition)
    if (
        reviewed_preview.get("edition") != edition
        or reviewed_preview.get("counts") != current_preview["counts"]
        or reviewed_preview.get("pdf_paths") != current_preview["pdf_paths"]
    ):
        raise RuntimeError(
            "The handbook data changed after the review. Review the deletion again "
            "before confirming."
        )

    workspace = st.session_state.w
    warehouse_id = _get_warehouse_id()
    if not warehouse_id:
        raise RuntimeError(
            "No SQL warehouse is available. Start a Databricks SQL warehouse and try again."
        )

    completed = []
    index_sync_error = None

    def sync_after_partial_delete() -> Optional[str]:
        try:
            st.session_state.index.sync()
        except Exception as error:
            return str(error)
        return None

    table_conditions = (
        (GOLD_TABLE, ("document_name",)),
        (SILVER_TABLE, ("path", "document_name")),
        (BRONZE_TABLE, ("path",)),
    )
    for table, columns in table_conditions:
        if current_preview["counts"][table] == 0:
            completed.append(f"{table} (0 rows)")
            continue
        condition = _edition_delete_condition(columns, edition)
        try:
            _execute_upload_sql(
                f"DELETE FROM {table} WHERE {condition}",
                workspace,
                warehouse_id
            )
            completed.append(f"{table} ({current_preview['counts'][table]} rows)")
        except Exception as error:
            index_sync_error = sync_after_partial_delete()
            raise RuntimeError(
                f"Deletion stopped while removing {table}. Completed steps: "
                f"{', '.join(completed) or 'none'}. Some data for {edition} may remain. "
                f"Databricks error: {error}"
                + (
                    f" Vector Search sync also failed: {index_sync_error}"
                    if index_sync_error else ""
                )
            ) from error

    for file_path in current_preview["pdf_paths"]:
        try:
            workspace.files.delete(file_path)
            completed.append(file_path.rsplit("/", 1)[-1])
        except Exception as error:
            index_sync_error = sync_after_partial_delete()
            raise RuntimeError(
                f"Could not delete PDF {file_path.rsplit('/', 1)[-1]}. Completed steps: "
                f"{', '.join(completed) or 'none'}. Some PDF files may remain: "
                f"{error}"
                + (
                    f" Vector Search sync also failed: {index_sync_error}"
                    if index_sync_error else ""
                )
            ) from error

    logger.info(
        "Removed handbook edition %s from Bronze, Silver, Gold, and PDF storage.",
        edition
    )
    try:
        st.session_state.index.sync()
    except Exception as error:
        return str(error)
    return None

def _is_valid_handbook_edition(edition: str) -> bool:
    try:
        _normalise_handbook_edition(edition)
        return True
    except ValueError:
        return False

def _insert_pdf_chunks(chunks: list, workspace, warehouse_id: str) -> None:
    for offset in range(0, len(chunks), 100):
        values = []
        for chunk_text, element_type, chunk_id, document_name in chunks[offset:offset + 100]:
            encoded_text = base64.b64encode(chunk_text.encode("utf-8")).decode("ascii")
            values.append(
                f"('{encoded_text}', "
                f"{_sql_string(element_type)}, {_sql_string(chunk_id)}, "
                f"{_sql_string(document_name)})"
            )
        _execute_upload_sql(
            f"INSERT INTO {SOURCE_TABLE} "
            "(chunk_text, element_type, chunk_id, document_name) "
            "SELECT decode(unbase64(encoded_text), 'UTF-8'), "
            "element_type, chunk_id, document_name "
            f"FROM VALUES {', '.join(values)} "
            "AS uploaded_chunks(encoded_text, element_type, chunk_id, document_name)",
            workspace,
            warehouse_id
        )

def _merge_pdf_chunks(chunks: list, workspace, warehouse_id: str) -> None:
    for offset in range(0, len(chunks), 100):
        values = []
        for chunk_text, element_type, chunk_id, document_name in chunks[offset:offset + 100]:
            encoded_text = base64.b64encode(chunk_text.encode("utf-8")).decode("ascii")
            values.append(
                f"({_sql_string(encoded_text)}, "
                f"{_sql_string(element_type)}, {_sql_string(chunk_id)}, "
                f"{_sql_string(document_name)})"
            )
        _execute_upload_sql(
            f"""
            MERGE INTO {SOURCE_TABLE} AS target
            USING (
                SELECT decode(unbase64(encoded_text), 'UTF-8') AS chunk_text,
                       element_type, chunk_id, document_name
                FROM VALUES {', '.join(values)}
                AS stored_pdf_chunks(encoded_text, element_type, chunk_id, document_name)
            ) AS incoming
            ON target.chunk_id = incoming.chunk_id
            WHEN MATCHED THEN
              UPDATE SET chunk_text = incoming.chunk_text,
                         element_type = incoming.element_type,
                         document_name = incoming.document_name
            WHEN NOT MATCHED THEN
              INSERT (chunk_text, element_type, chunk_id, document_name)
              VALUES (
                incoming.chunk_text, incoming.element_type,
                incoming.chunk_id, incoming.document_name
              )
            """,
            workspace,
            warehouse_id
        )
    document_prefix = chunks[0][2].rsplit("_", 2)[0]
    retained_chunk_ids = ", ".join(_sql_string(chunk[2]) for chunk in chunks)
    _execute_upload_sql(
        f"DELETE FROM {SOURCE_TABLE} "
        f"WHERE SUBSTRING(chunk_id, 1, {len(document_prefix)}) = "
        f"{_sql_string(document_prefix)} "
        f"AND chunk_id NOT IN ({retained_chunk_ids})",
        workspace,
        warehouse_id
    )

def _index_stored_handbook_pdfs() -> tuple[int, Optional[str]]:
    workspace = st.session_state.w
    warehouse_id = _get_warehouse_id()
    if not warehouse_id:
        raise RuntimeError(
            "No SQL warehouse is available. Start a Databricks SQL warehouse and try again."
        )

    stored_pdfs = _list_stored_handbook_pdfs(workspace)
    if not stored_pdfs:
        raise RuntimeError(
            f"No year-labeled PDF files were found in {PDF_VOLUME_PATH}."
        )

    prepared_chunks = 0
    for file_path, edition in stored_pdfs:
        download = workspace.files.download(file_path)
        contents = download.contents
        pdf_bytes = contents.read() if hasattr(contents, "read") else bytes(contents)
        if not pdf_bytes or not pdf_bytes.startswith(b"%PDF-"):
            raise ValueError(
                f"The stored file {file_path.rsplit('/', 1)[-1]} is not a readable PDF."
            )
        if len(pdf_bytes) > MAX_PDF_SIZE_BYTES:
            raise ValueError(
                f"The stored PDF {file_path.rsplit('/', 1)[-1]} exceeds the 50 MB limit."
            )

        filename = file_path.rsplit("/", 1)[-1]
        document_id = "volume_" + hashlib.sha256(pdf_bytes).hexdigest()[:24]
        chunks = _make_pdf_chunks(pdf_bytes, filename, document_id, edition)
        _merge_pdf_chunks(chunks, workspace, warehouse_id)
        prepared_chunks += len(chunks)

    try:
        st.session_state.index.sync()
    except Exception as error:
        return prepared_chunks, str(error)
    return prepared_chunks, None

def _ingest_pdf(uploaded_file, edition: str) -> tuple[int, Optional[str]]:
    edition = _normalise_handbook_edition(edition)
    pdf_bytes = uploaded_file.getvalue()
    if not pdf_bytes:
        raise ValueError("The selected PDF is empty.")
    if len(pdf_bytes) > MAX_PDF_SIZE_BYTES:
        raise ValueError("The PDF exceeds the 50 MB upload limit.")
    if not pdf_bytes.startswith(b"%PDF-"):
        raise ValueError("The selected file is not a valid PDF.")

    original_name = os.path.basename(uploaded_file.name)
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", original_name).strip("._")
    if not safe_name:
        raise ValueError("The PDF filename must contain letters or numbers.")

    document_id = uuid.uuid4().hex
    document_name = f"HANDBOOK-{edition}-{safe_name}"
    chunks = _make_pdf_chunks(
        pdf_bytes, safe_name, document_id, edition, document_name
    )
    volume_path = f"{PDF_VOLUME_PATH}/{document_id}_{safe_name}"
    workspace = st.session_state.w
    warehouse_id = _get_warehouse_id()
    if not warehouse_id:
        raise RuntimeError(
            "No SQL warehouse is available. Start a Databricks SQL warehouse and try again."
        )

    workspace.files.upload(
        file_path=volume_path,
        contents=io.BytesIO(pdf_bytes),
        overwrite=False
    )

    try:
        _insert_pdf_chunks(chunks, workspace, warehouse_id)
    except Exception as insert_error:
        try:
            chunk_ids = ", ".join(_sql_string(chunk[2]) for chunk in chunks)
            _execute_upload_sql(
                f"DELETE FROM {SOURCE_TABLE} WHERE chunk_id IN ({chunk_ids})",
                workspace,
                warehouse_id
            )
        except Exception as cleanup_error:
            raise RuntimeError(
                "The PDF was uploaded, but chunk insertion failed and automatic cleanup "
                f"also failed: {cleanup_error}"
            ) from insert_error
        raise RuntimeError(
            f"The PDF was uploaded, but its chunks could not be stored: {insert_error}"
        ) from insert_error

    sync_error = None
    try:
        st.session_state.index.sync()
    except Exception as error:
        sync_error = str(error)

    return len(chunks), sync_error

def _matches_handbook_edition(
    chunk_text: str, edition: str, document_name: str = ""
) -> bool:
    tagged_edition = "Handbook edition:" in chunk_text
    named_edition = _handbook_edition_from_document_name(document_name)
    if edition == ALL_HANDBOOKS:
        if tagged_edition or named_edition:
            return True
        if st.session_state.get("handbook_volume_index_complete", False):
            return False
        return True
    if tagged_edition:
        try:
            return _handbook_edition_from_chunk(chunk_text) == _normalise_handbook_edition(
                edition, allow_legacy=True
            )
        except ValueError:
            return False
    if named_edition:
        try:
            return named_edition == _normalise_handbook_edition(
                edition, allow_legacy=True
            )
        except ValueError:
            return False
    try:
        return _handbook_edition_from_chunk(chunk_text) == _normalise_handbook_edition(
            edition, allow_legacy=True
        )
    except ValueError:
        return False

def _is_comprehensive_list_query(query: str) -> bool:
    return bool(re.search(
        r"\b(list|all|names?|faculty|staff|teachers|professors|who are)\b",
        query,
        re.IGNORECASE
    ))

def _department_search_terms(query: str) -> Optional[tuple[str, str]]:
    department_aliases = (
        (r"\bcs\b", "cs", "computer science"),
        (r"\bca\b", "ca", "computer applications"),
        (r"\bbca\b", "bca", "bachelor of computer applications"),
        (r"\bmca\b", "mca", "master of computer applications"),
    )
    for abbreviation_pattern, abbreviation, phrase in department_aliases:
        if re.search(abbreviation_pattern, query, re.IGNORECASE) or phrase in query.lower():
            return abbreviation, phrase
    return None

def _department_search_condition(query: str) -> Optional[str]:
    department = _department_search_terms(query)
    if not department:
        return None
    abbreviation, phrase = department
    abbreviation_pattern = f"(^|[^a-z]){abbreviation}([^a-z]|$)"
    return (
        f"(LOWER(chunk_text) LIKE {_sql_string('%' + phrase + '%')} "
        f"OR LOWER(chunk_text) RLIKE {_sql_string(abbreviation_pattern)})"
    )

def _matches_department_section(query: str, chunk_text: str) -> bool:
    department = _department_search_terms(query)
    if not department:
        return True
    abbreviation, phrase = department
    abbreviation_pattern = rf"(?<![a-z]){re.escape(abbreviation)}(?![a-z])"
    return (
        phrase in chunk_text.lower()
        or re.search(abbreviation_pattern, chunk_text, re.IGNORECASE) is not None
    )

def vsearch(
    query: str,
    n: int,
    seen: set,
    index=None,
    edition: str = ALL_HANDBOOKS,
    document_name: Optional[str] = None
) -> list:
    try:
        if index is None:
            index = st.session_state.index

        def run_vector_search(apply_document_filter: bool):
            filters = (
                {"document_name": document_name}
                if apply_document_filter and document_name
                else {}
            )
            try:
                return index.similarity_search(
                    query_text=query,
                    columns=[
                        "chunk_text", "element_type", "chunk_id", "document_name"
                    ],
                    num_results=n,
                    query_type="HYBRID",
                    query_columns=["chunk_text"],
                    **({"filters": filters} if filters else {})
                )
            except Exception:
                logger.warning(
                    "Hybrid handbook search failed; retrying with semantic search.",
                    exc_info=True
                )
                return index.similarity_search(
                    query_text=query,
                    columns=[
                        "chunk_text", "element_type", "chunk_id", "document_name"
                    ],
                    num_results=n,
                    query_type="ANN",
                    query_columns=["chunk_text"],
                    **({"filters": filters} if filters else {})
                )

        try:
            result = run_vector_search(apply_document_filter=bool(document_name))
        except Exception:
            if not document_name:
                raise
            logger.warning(
                "Filtered handbook search failed for %s; retrying with a guarded "
                "unfiltered search.",
                document_name,
                exc_info=True
            )
            result = run_vector_search(apply_document_filter=False)
        rows = result.get("result", {}).get("data_array", [])
    except Exception as error:
        logger.exception("Both hybrid and semantic handbook searches failed.")
        raise RuntimeError(
            "Handbook search is temporarily unavailable. Please try again."
        ) from error

    try:
        fresh = []
        for row in rows:
            chunk_text = str(row[0])
            row_document_name = str(row[3] or "") if len(row) > 3 else ""
            if (
                document_name
                and row_document_name != document_name
            ):
                continue
            cid = row[2]
            if (
                cid not in seen
                and _matches_handbook_edition(
                    chunk_text, edition, row_document_name
                )
            ):
                seen.add(cid)
                fresh.append(list(row))
        return fresh
    except Exception as error:
        logger.exception("Could not process handbook search results.")
        raise RuntimeError(
            "Handbook search returned data that could not be processed."
        ) from error

def _chunk_expansion_condition(chunk_id: str) -> Optional[str]:
    legacy_match = re.fullmatch(r"chunk_(\d+)", chunk_id)
    if legacy_match:
        number = int(legacy_match.group(1))
        lower_bound = max(1, number - 2)
        upper_bound = number + 15
        return (
            "(chunk_id RLIKE '^chunk_[0-9]+$' AND "
            "CAST(SUBSTRING(chunk_id, 7) AS INT) "
            f"BETWEEN {lower_bound} AND {upper_bound})"
        )

    pdf_match = re.fullmatch(r"(pdf_.+?)_(\d{4})_(\d{4})", chunk_id)
    if pdf_match:
        document_prefix, page_text, _ = pdf_match.groups()
        page = int(page_text)
        lower_bound = max(1, page - 1)
        upper_bound = page + 1
        page_offset = len(document_prefix) + 2
        return (
            f"(SUBSTRING(chunk_id, 1, {len(document_prefix)}) = "
            f"{_sql_string(document_prefix)} AND "
            f"CAST(SUBSTRING(chunk_id, {page_offset}, 4) AS INT) "
            f"BETWEEN {lower_bound} AND {upper_bound})"
        )
    return None

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
    Result from step 3 is cached for the selected edition and query.
    """
    normalised_query = _normalise(query_text)

    # 1. Greeting check
    if normalised_query in _GREETINGS:
        return _GREETINGS[normalised_query], True

    edition = st.session_state.get("selected_handbook_edition", ALL_HANDBOOKS)
    key = f"{ANSWER_CACHE_VERSION}:{edition}:{normalised_query}"

    # 2. Cache hit
    if key in st.session_state.response_cache:
        return st.session_state.response_cache[key], True

    # 3. Backend call
    answer = ask_handbook(query_text, edition=edition)

    # Store in cache (don't cache errors)
    if not answer.startswith("❌"):
        st.session_state.response_cache[key] = answer

    return answer, False

# ============================================================
# ASK_HANDBOOK — year-aware hybrid retrieval
# ============================================================
def ask_handbook(
    query_text: str, num_results: int = 10, edition: str = ALL_HANDBOOKS
) -> str:
    try:
        is_list_query = _is_comprehensive_list_query(query_text)
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
        workspace = st.session_state.w
        warehouse_id = _get_warehouse_id()
        vector_index = st.session_state.index
        edition_condition = _edition_sql_condition(edition)

        cleaned  = re.sub(r'[^\w\s]', '', query_text)
        keywords = [w.strip() for w in cleaned.split() if len(w.strip()) > 2]
        keywords = [w for w in keywords if w.lower() not in
                    ['who','what','when','where','why','how','are','the',
                     'tell','give','show','about']]

        def search_keyword_chunks():
            if not keywords:
                return []
            try:
                if is_list_query:
                    department_condition = _department_search_condition(query_text)
                    if department_condition:
                        list_conditions = [department_condition]
                    else:
                        list_conditions = [
                            "LOWER(chunk_text) LIKE '%faculty%'",
                            "LOWER(chunk_text) LIKE '%teaching staff%'",
                            "LOWER(chunk_text) LIKE '%teachers%'",
                            "LOWER(chunk_text) LIKE '%professor%'",
                            "LOWER(chunk_text) LIKE '%staff members%'",
                        ]
                    where_conditions = [f"({' OR '.join(list_conditions)})"]
                    if edition_condition:
                        where_conditions.append(edition_condition)
                    faculty_relevance = (
                        "CASE WHEN LOWER(chunk_text) LIKE '%faculty%' "
                        "OR LOWER(chunk_text) LIKE '%teaching staff%' "
                        "OR LOWER(chunk_text) LIKE '%teachers%' "
                        "OR LOWER(chunk_text) LIKE '%professor%' "
                        "OR LOWER(chunk_text) LIKE '%staff members%' "
                        "THEN 0 ELSE 1 END"
                    )
                    if edition == ALL_HANDBOOKS:
                        extracted_source_edition = (
                            "COALESCE(NULLIF(regexp_extract(chunk_text, "
                            f"{_sql_string(HANDBOOK_EDITION_SQL_REGEX)}, 1), ''), "
                            "NULLIF(regexp_replace(regexp_extract(document_name, "
                            f"{_sql_string(HANDBOOK_EDITION_PATH_REGEX)}, 0), "
                            "'_', '-'), ''), "
                            f"{_sql_string(LEGACY_HANDBOOK_EDITION)})"
                        )
                        source_edition = (
                            f"CASE WHEN {extracted_source_edition} "
                            f"IN ('2024-20', '2024-25', "
                            f"{_sql_string(LEGACY_HANDBOOK_EDITION)}) "
                            f"THEN {_sql_string(LEGACY_HANDBOOK_EDITION)} "
                            f"ELSE {extracted_source_edition} END"
                        )
                        sql = f"""
                            WITH ranked_chunks AS (
                                SELECT chunk_text, element_type, chunk_id, document_name,
                                       ROW_NUMBER() OVER (
                                           PARTITION BY {source_edition}
                                           ORDER BY {faculty_relevance}, chunk_id
                                       ) AS edition_rank
                                FROM {SOURCE_TABLE}
                                WHERE {' AND '.join(where_conditions)}
                            )
                            SELECT chunk_text, element_type, chunk_id, document_name
                            FROM ranked_chunks
                            WHERE edition_rank <= 40
                            ORDER BY edition_rank, {faculty_relevance}, chunk_id
                            LIMIT 240
                        """
                    else:
                        sql = f"""
                            SELECT chunk_text, element_type, chunk_id, document_name
                            FROM {SOURCE_TABLE}
                            WHERE {' AND '.join(where_conditions)}
                            ORDER BY {faculty_relevance}, chunk_id
                            LIMIT 200
                        """
                    return run_sql(sql, workspace, warehouse_id)

                fuzzy_conditions = []
                for kw in keywords[:3]:
                    kw_lower = kw.lower()
                    fuzzy_conditions.append(
                        f"LOWER(chunk_text) LIKE {_sql_string('%' + kw_lower + '%')}"
                    )
                    if len(kw_lower) >= 5:
                        prefix = kw_lower[:int(len(kw_lower)*0.8)]
                        fuzzy_conditions.append(
                            f"LOWER(chunk_text) LIKE {_sql_string('%' + prefix + '%')}"
                        )
                    if len(kw_lower) >= 4:
                        fuzzy_conditions.append(
                            f"LOWER(chunk_text) LIKE {_sql_string('%' + kw_lower[:3] + '%')}"
                        )
                    if len(kw_lower) >= 6:
                        s = int(len(kw_lower)*0.2); e = int(len(kw_lower)*0.8)
                        mid = kw_lower[s:e]
                        if len(mid) >= 3:
                            fuzzy_conditions.append(
                                f"LOWER(chunk_text) LIKE {_sql_string('%' + mid + '%')}"
                            )
                    if len(kw_lower) >= 6:
                        fuzzy_conditions.append(
                            f"LOWER(chunk_text) LIKE {_sql_string('%' + kw_lower[-4:] + '%')}"
                        )

                limit    = 25 if is_person_query else 20
                first_kw = keywords[0].lower()
                where_conditions = [f"({' OR '.join(fuzzy_conditions)})"]
                if edition_condition:
                    where_conditions.append(edition_condition)
                match_score = (
                    "CASE WHEN LOWER(chunk_text) LIKE "
                    f"{_sql_string('%' + first_kw + '%')} THEN 1 ELSE 2 END"
                )
                if edition == ALL_HANDBOOKS:
                    extracted_source_edition = (
                        "COALESCE(NULLIF(regexp_extract(chunk_text, "
                        f"{_sql_string(HANDBOOK_EDITION_SQL_REGEX)}, 1), ''), "
                        "NULLIF(regexp_replace(regexp_extract(document_name, "
                        f"{_sql_string(HANDBOOK_EDITION_PATH_REGEX)}, 0), "
                        "'_', '-'), ''), "
                        f"{_sql_string(LEGACY_HANDBOOK_EDITION)})"
                    )
                    source_edition = (
                        f"CASE WHEN {extracted_source_edition} "
                        f"IN ('2024-20', '2024-25', "
                        f"{_sql_string(LEGACY_HANDBOOK_EDITION)}) "
                        f"THEN {_sql_string(LEGACY_HANDBOOK_EDITION)} "
                        f"ELSE {extracted_source_edition} END"
                    )
                    sql = f"""
                        WITH ranked_chunks AS (
                            SELECT chunk_text, element_type, chunk_id, document_name,
                                   {match_score} AS match_score,
                                   ROW_NUMBER() OVER (
                                       PARTITION BY {source_edition}
                                       ORDER BY {match_score}, chunk_id
                                   ) AS edition_rank
                            FROM {SOURCE_TABLE}
                            WHERE {' AND '.join(where_conditions)}
                        )
                        SELECT chunk_text, element_type, chunk_id, document_name
                        FROM ranked_chunks
                        WHERE edition_rank <= 8
                        ORDER BY edition_rank, match_score, chunk_id
                        LIMIT 50
                    """
                else:
                    sql = f"""
                        SELECT chunk_text, element_type, chunk_id, document_name,
                               {match_score} AS match_score
                        FROM {SOURCE_TABLE}
                        WHERE {' AND '.join(where_conditions)}
                        ORDER BY match_score, chunk_id
                        LIMIT {limit}
                    """
                rows = run_sql(sql, workspace, warehouse_id)
                return [row[:4] for row in rows]
            except Exception:
                logger.warning(
                    "Primary handbook keyword query failed; retrying with basic matching.",
                    exc_info=True
                )
                try:
                    conditions = [
                        f"LOWER(chunk_text) LIKE {_sql_string('%' + kw.lower() + '%')}"
                        for kw in keywords[:3]
                    ]
                    where_conditions = [f"({' OR '.join(conditions)})"]
                    if edition_condition:
                        where_conditions.append(edition_condition)
                    limit = 20 if is_person_query else 10
                    sql = f"""
                        SELECT chunk_text, element_type, chunk_id, document_name
                        FROM {SOURCE_TABLE}
                        WHERE {' AND '.join(where_conditions)}
                        LIMIT {limit}
                    """
                    return run_sql(sql, workspace, warehouse_id)
                except Exception as fallback_error:
                    logger.exception("Handbook keyword search fallback failed.")
                    raise RuntimeError(
                        "Handbook keyword search is temporarily unavailable."
                    ) from fallback_error

        def search_semantic_chunks():
            chunks = []
            seen_sem = set()
            search_limit = min(max(num_results, 80), 200)
            semantic_queries = list(dict.fromkeys((
                query_text.strip(),
                transformed_query,
                f"What does the handbook say about {transformed_query}? "
                "Include relevant details and explanations.",
            )))
            if edition == ALL_HANDBOOKS:
                search_editions = list(available_editions)
                if not st.session_state.get("handbook_volume_index_complete", False):
                    search_editions.append(LEGACY_HANDBOOK_EDITION)
            else:
                search_editions = [edition]

            document_names_by_edition = st.session_state.get(
                "handbook_document_names_by_edition", {}
            )
            for search_edition in dict.fromkeys(search_editions):
                for semantic_query in semantic_queries:
                    if semantic_query:
                        edition_query = f"{search_edition} {semantic_query}"
                        document_names = document_names_by_edition.get(
                            search_edition, []
                        )
                        if document_names:
                            for document_name in document_names:
                                chunks.extend(
                                    vsearch(
                                        edition_query,
                                        search_limit,
                                        seen_sem,
                                        vector_index,
                                        search_edition,
                                        document_name
                                    )
                                )
                        else:
                            chunks.extend(
                                vsearch(
                                    edition_query,
                                    search_limit,
                                    seen_sem,
                                    vector_index,
                                    search_edition
                                )
                            )
            return chunks

        with ThreadPoolExecutor(max_workers=2) as executor:
            keyword_future = executor.submit(search_keyword_chunks)
            semantic_future = executor.submit(search_semantic_chunks)
            keyword_chunks = keyword_future.result()
            semantic_chunks = semantic_future.result()

        if is_list_query and _department_search_terms(query_text):
            semantic_chunks = [
                chunk for chunk in semantic_chunks
                if _matches_department_section(query_text, chunk[0])
            ]

        expanded_chunks     = []
        chunk_ids_to_expand = []
        seen_expansion_ids = set()
        for chunk in (keyword_chunks + semantic_chunks):
            if len(chunk) > 2 and chunk[2]:
                if (
                    is_list_query
                    or chunk[1] == "Section Header"
                    or len(chunk[0]) < 150
                ):
                    if chunk[2] not in seen_expansion_ids:
                        chunk_ids_to_expand.append(chunk[2])
                        seen_expansion_ids.add(chunk[2])

        if chunk_ids_to_expand:
            try:
                conditions = []
                expansion_limit = 25 if is_list_query else 5
                for cid in chunk_ids_to_expand[:expansion_limit]:
                    condition = _chunk_expansion_condition(cid)
                    if condition:
                        conditions.append(condition)
                if conditions:
                    where_conditions = [f"({' OR '.join(conditions)})"]
                    if edition_condition:
                        where_conditions.append(edition_condition)
                    sql = f"""
                        SELECT chunk_id, chunk_text, element_type, document_name
                        FROM {SOURCE_TABLE}
                        WHERE {' AND '.join(where_conditions)}
                        ORDER BY chunk_id
                        LIMIT 300
                    """
                    for row in run_sql(sql, workspace, warehouse_id):
                        expanded_chunks.append([row[1], row[2], row[0], row[3]])
            except Exception:
                logger.warning(
                    "Could not load neighboring handbook sections; continuing with matched sections.",
                    exc_info=True
                )

        final_chunks = []
        seen         = set()
        max_chunks = 100 if is_list_query else 70
        priority_order = (
            [keyword_chunks, semantic_chunks, expanded_chunks]
            if is_list_query else
            [semantic_chunks, keyword_chunks, expanded_chunks]
        )
        for chunk_list in priority_order:
            for chunk in chunk_list:
                cid = chunk[2] if len(chunk) > 2 else chunk[0][:50]
                if cid not in seen:
                    final_chunks.append(chunk)
                    seen.add(cid)
                    if len(final_chunks) >= max_chunks:
                        break
            if len(final_chunks) >= max_chunks:
                break

        if not final_chunks:
            if edition == ALL_HANDBOOKS:
                return (
                    f"I couldn't find relevant information in the **{edition}**. "
                    "Choose a specific handbook year or try rephrasing your question."
                )
            if not _is_valid_handbook_edition(edition):
                return (
                    f"I couldn't find relevant information under the stored year "
                    f"**{edition}**. This year label appears incorrect; use **Correct a "
                    "handbook year label** in the sidebar to relabel the stored PDF "
                    "without uploading it again."
                )
            return (
                f"I couldn't find relevant information in the **{edition}** handbook. "
                "Choose another year or try rephrasing your question."
            )

        context_parts = []
        context_size = 0
        max_context_chars = 50000 if is_list_query else 40000
        for doc in final_chunks[:max_chunks]:
            source_text = (
                f"[Handbook year: {_handbook_edition_for_chunk(doc)}]\n"
                f"{doc[0]}\n"
            )
            if context_parts and context_size + len(source_text) > max_context_chars:
                break
            context_parts.append(source_text)
            context_size += len(source_text)
        context = "\n".join(context_parts)

        edition_instruction = (
            "The user selected all handbook years. If editions differ, explain the difference "
            "and mention the year. Unlabeled legacy information belongs to "
            f"{LEGACY_HANDBOOK_EDITION}."
            if edition == ALL_HANDBOOKS else
            f"Use only information from the {edition} handbook. "
            "If it does not contain the answer, say so."
        )
        list_instruction = (
            "- The user asked for a list. Include every relevant name or item in the handbook "
            "information below; do not stop after a few examples.\n"
            "- Do not add names, departments, qualifications, or roles that are not stated.\n"
            "- Include each name only once, and do not add placeholders such as '(not mentioned)'.\n"
            if is_list_query else
            "- Answer the question first, then explain relevant details, conditions, steps, "
            "exceptions, or related information found in the handbook.\n"
            "- Keep simple answers brief, but do not omit useful details that clarify the answer.\n"
        )
        department_instruction = (
            "- For this department-specific list, use names only from information that explicitly "
            "identify the requested department; do not use general staff lists or infer a "
            "person's department.\n"
            if is_list_query and _department_search_terms(query_text) else
            ""
        )
        prompt = f"""You are the Don Bosco College handbook assistant. Answer clearly in everyday language.
{edition_instruction}

{list_instruction}
{department_instruction}
- Use only facts stated in the handbook; never guess missing details.
- Do not merge people, job titles, or facts from different years or unrelated handbook entries.
- Treat names and roles as historical handbook entries, not proof of who currently holds a role.
- If handbook information conflicts, describe the difference and identify each source year.
- Write a complete, clear answer directly for the user. Do not use the word "section" or
  "sections", include numbered handbook references, say information appears in a location,
  or repeat internal source labels.
- Do not mention technical terms such as "context", "retrieval", "chunks", or "search results".
- Do not add "not specified" fields unless the user asks about those details.
- Use a short introduction and readable bullets for lists.
- For an all-years question, mention the year next to facts when years differ.
- Cite the handbook year and page beside key facts when the source includes a page number.
- Only cite a page that appears in the supplied handbook information.
- If the handbook does not contain the answer, say that plainly.

User Question: {query_text}

Handbook information:
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
                  "max_tokens": 3500 if is_list_query else 3000,
                  "temperature": 0.1},
            timeout=(10, 180)
        )
        response.raise_for_status()
        answer = response.json()["choices"][0]["message"]["content"].strip()
        if edition == ALL_HANDBOOKS:
            source_editions = list(dict.fromkeys(
                _handbook_edition_for_chunk(doc) for doc in final_chunks
            ))
            answer += (
                "\n\n**Handbook sources:** "
                + ", ".join(source_editions)
            )
        return answer

    except requests.exceptions.Timeout:
        logger.exception("Databricks AI Gateway request timed out.")
        return (
            "The handbook response took too long to generate. Please try again; "
            "if this keeps happening, ask a shorter or more focused question."
        )
    except Exception as e:
        logger.exception("Handbook answer generation failed.")
        return f"❌ Error: {str(e)}"

# ============================================================
# PDF UPLOAD
# ============================================================
if "pdf_upload_generation" not in st.session_state:
    st.session_state.pdf_upload_generation = 0
if "pdf_upload_notice" in st.session_state:
    notice_kind, notice_text = st.session_state.pop("pdf_upload_notice")
    if notice_kind == "warning":
        st.warning(notice_text)
    else:
        st.success(notice_text)

@st.dialog("Add a PDF to the handbook", width="small")
def _show_pdf_upload_dialog() -> None:
    st.markdown(
        '<div class="pdf-upload-dialog-copy">'
        "Add a PDF as a separate searchable handbook edition. "
        "PDFs must contain selectable text; scanned PDFs need OCR first."
        "</div>",
        unsafe_allow_html=True
    )
    edition_input = st.text_input(
        "Handbook year",
        placeholder="2026-2027",
        help="Use YYYY, YYYY-YY, or YYYY-YYYY. For example, 2026-2027."
    )
    handbook_edition = None
    try:
        handbook_edition = _normalise_handbook_edition(edition_input)
    except ValueError:
        if edition_input.strip():
            st.caption("Enter the year as YYYY, YYYY-YY, or YYYY-YYYY.")

    uploaded_pdf = st.file_uploader(
        "Choose a PDF",
        type=["pdf"],
        max_upload_size=50,
        key=f"pdf_uploader_{st.session_state.pdf_upload_generation}"
    )
    if st.button(
        "Add to handbook",
        type="primary",
        disabled=uploaded_pdf is None or handbook_edition is None,
        use_container_width=True,
        key="upload_pdf_submit"
    ):
        try:
            with st.spinner("Uploading and indexing the PDF..."):
                chunk_count, sync_error = _ingest_pdf(uploaded_pdf, handbook_edition)
            st.session_state.response_cache.clear()
            st.session_state.selected_handbook_edition = handbook_edition
            st.session_state.pdf_upload_generation += 1
            if sync_error:
                st.session_state.pdf_upload_notice = (
                    "warning",
                    f"{chunk_count} sections for {handbook_edition} were added. Keyword search can find the "
                    f"new content, but Vector Search synchronization failed: {sync_error}"
                )
            else:
                st.session_state.pdf_upload_notice = (
                    "success",
                    f"{handbook_edition} handbook added ({chunk_count} text sections)."
                )
            st.rerun()
        except Exception as error:
            st.error(f"PDF upload failed: {error}")

with st.container(key="pdf_upload_control"):
    if st.button("+", key="add_pdf_button", help="Add a PDF to the handbook"):
        _show_pdf_upload_dialog()

available_editions = _get_available_editions()
stored_handbook_pdfs = st.session_state.handbook_volume_pdfs
tagged_handbook_editions = st.session_state.tagged_handbook_editions
handbook_volume_error = st.session_state.handbook_volume_error
handbook_sql_error = st.session_state.handbook_sql_error
unindexed_handbook_pdfs = [
    (path, edition)
    for path, edition in stored_handbook_pdfs
    if edition not in tagged_handbook_editions
]
if available_editions:
    edition_options = [ALL_HANDBOOKS, *available_editions]
    latest_edition = next(iter(available_editions))
    if st.session_state.get("selected_handbook_edition") not in edition_options:
        st.session_state.selected_handbook_edition = latest_edition

    with st.container(key="handbook_year_filter"):
        st.selectbox(
            "Year",
            edition_options,
            key="selected_handbook_edition",
            width="stretch",
            format_func=lambda value: (
                f"{value} (check year label)"
                if value in available_editions and not _is_valid_handbook_edition(value)
                else value
            ),
            help="Choose one uploaded handbook year, or All years to compare uploaded handbooks."
        )
        selected_edition = st.session_state.selected_handbook_edition
        if selected_edition == ALL_HANDBOOKS:
            st.caption(
                "Answers may combine editions. Each answer lists its handbook sources and years."
            )
        elif not _is_valid_handbook_edition(selected_edition):
            st.warning(
                f"The stored year **{selected_edition}** looks incorrect. Use "
                "**Correct a handbook year label** in the sidebar to relabel it."
            )
        else:
            st.caption(f"Answers search only the {selected_edition} handbook.")
else:
    st.session_state.selected_handbook_edition = ALL_HANDBOOKS
    selected_edition = ALL_HANDBOOKS
    st.caption("Upload a handbook PDF to show the year selector.")

if handbook_sql_error:
    st.warning(
        "The handbook database could not be checked. Search errors will be shown "
        f"instead of treating the year as empty. Details: {handbook_sql_error}"
    )

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown(
        f'<div style="padding:0.6rem 0 0.4rem;">{sidebar_logo_html}</div>',
        unsafe_allow_html=True
    )
    st.toggle("Dark appearance", key="dark_appearance")
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

    if handbook_volume_error:
        st.warning(
            "Could not read the Databricks PDF volume. Showing only years found "
            f"in the indexed handbook data. {handbook_volume_error}"
        )

    if unindexed_handbook_pdfs:
        missing_years = ", ".join(sorted({
            edition for _, edition in unindexed_handbook_pdfs
        }))
        st.warning(
            f"{len(unindexed_handbook_pdfs)} PDF(s) are in Databricks storage but "
            f"their year-tagged search sections are missing ({missing_years})."
        )
        if st.button(
            "Index stored handbook PDFs",
            use_container_width=True,
            key="index_stored_handbook_pdfs"
        ):
            try:
                with st.spinner("Indexing the stored handbook PDFs by year..."):
                    indexed_chunks, sync_error = _index_stored_handbook_pdfs()
                st.session_state.response_cache.clear()
                if sync_error:
                    st.session_state.pdf_upload_notice = (
                        "warning",
                        f"Prepared {indexed_chunks} handbook sections with year labels. "
                        f"Vector Search synchronization is pending: {sync_error}"
                    )
                else:
                    st.session_state.pdf_upload_notice = (
                        "success",
                        f"Indexed the stored handbook PDFs with year labels "
                        f"({indexed_chunks} sections checked)."
                    )
                st.rerun()
            except Exception as error:
                st.error(f"Could not index stored handbook PDFs: {error}")

    admin_password_secret = os.getenv("HANDBOOK_ADMIN_PASSWORD", "")
    admin_secret_fingerprint = hashlib.sha256(
        admin_password_secret.encode("utf-8")
    ).hexdigest()
    if (
        st.session_state.get("handbook_delete_admin")
        or st.session_state.pop("clear_handbook_admin_password", False)
    ):
        st.session_state.pop("handbook_admin_password_input", None)
    if (
        st.session_state.get("handbook_delete_admin")
        and st.session_state.get("handbook_delete_admin_secret_fingerprint")
        != admin_secret_fingerprint
    ):
        st.session_state.handbook_delete_admin = False
        st.session_state.pop("handbook_delete_admin_secret_fingerprint", None)
        st.session_state.pop("handbook_delete_preview", None)
    if not admin_password_secret:
        st.session_state.handbook_delete_admin = False
        st.session_state.pop("handbook_delete_admin_secret_fingerprint", None)
        st.session_state.pop("handbook_delete_preview", None)

    with st.expander("Delete a handbook year"):
        st.warning(
            "This permanently removes the selected year's PDF and matching records "
            "from Bronze, Silver, Gold, and the Vector Search index."
        )
        if not admin_password_secret:
            st.info(
                "Deletion is disabled. Configure HANDBOOK_ADMIN_PASSWORD as an "
                "environment secret (at least 16 characters; do not commit it) "
                "to enable admin access."
            )
        elif len(admin_password_secret) < 16:
            st.error(
                "Deletion is disabled because HANDBOOK_ADMIN_PASSWORD must be at "
                "least 16 characters long."
            )
        elif not st.session_state.get("handbook_delete_admin", False):
            password_input = st.text_input(
                "Admin password",
                type="password",
                key="handbook_admin_password_input"
            )
            if st.button("Unlock delete controls", key="unlock_handbook_delete"):
                if hmac.compare_digest(password_input, admin_password_secret):
                    st.session_state.handbook_delete_admin = True
                    st.session_state.handbook_delete_admin_secret_fingerprint = (
                        admin_secret_fingerprint
                    )
                    st.session_state.pop("handbook_delete_auth_error", None)
                else:
                    st.session_state.handbook_delete_auth_error = (
                        "The admin password is incorrect."
                    )
                    st.session_state.clear_handbook_admin_password = True
                st.rerun()
            if st.session_state.get("handbook_delete_auth_error"):
                st.error(st.session_state.handbook_delete_auth_error)
        else:
            if st.button("Lock delete controls", key="lock_handbook_delete"):
                st.session_state.handbook_delete_admin = False
                st.session_state.pop(
                    "handbook_delete_admin_secret_fingerprint", None
                )
                st.session_state.pop("handbook_delete_preview", None)
                st.rerun()

            if selected_edition == ALL_HANDBOOKS:
                st.info("Select one handbook year in the Year menu before deleting.")
            elif selected_edition not in available_editions:
                st.info("There is no selected handbook year to delete.")
            else:
                st.caption(
                    f"Only **{selected_edition}** will be removed. Other years are kept."
                )
                if st.button(
                    f"Review {selected_edition} data",
                    key="review_handbook_delete"
                ):
                    try:
                        with st.spinner("Checking the selected year's stored data..."):
                            deletion_preview = _get_edition_delete_preview(selected_edition)
                        deletion_preview["confirmation_key"] = uuid.uuid4().hex
                        st.session_state.handbook_delete_preview = deletion_preview
                        st.rerun()
                    except Exception as error:
                        st.error(f"Could not review handbook data for deletion: {error}")

                deletion_preview = st.session_state.get("handbook_delete_preview")
                if (
                    deletion_preview
                    and deletion_preview.get("edition") == selected_edition
                ):
                    counts = deletion_preview["counts"]
                    pdf_count = len(deletion_preview["pdf_paths"])
                    st.markdown(
                        f"- PDF files: **{pdf_count}**\n"
                        f"- Bronze records: **{counts[BRONZE_TABLE]}**\n"
                        f"- Silver records: **{counts[SILVER_TABLE]}**\n"
                        f"- Gold records: **{counts[GOLD_TABLE]}**"
                    )
                    has_data = pdf_count > 0 or any(counts.values())
                    if not has_data:
                        st.info(f"No matching stored data was found for {selected_edition}.")
                    else:
                        confirmed = st.checkbox(
                            f"I understand this permanently deletes all listed "
                            f"{selected_edition} data.",
                            key=deletion_preview["confirmation_key"]
                        )
                        if st.button(
                            f"Permanently delete {selected_edition}",
                            type="primary",
                            disabled=not confirmed,
                            key=f"delete_handbook_{selected_edition}"
                        ):
                            try:
                                with st.spinner(
                                    f"Deleting {selected_edition} handbook data..."
                                ):
                                    sync_error = _delete_handbook_edition(
                                        selected_edition,
                                        deletion_preview
                                    )
                                st.session_state.response_cache.clear()
                                st.session_state.messages = []
                                st.session_state.pop("handbook_delete_preview", None)
                                if sync_error:
                                    st.session_state.pdf_upload_notice = (
                                        "warning",
                                        f"{selected_edition} was removed from Bronze, Silver, "
                                        "Gold, and PDF storage, but Vector Search sync failed: "
                                        f"{sync_error}. Use Retry Vector Search sync."
                                    )
                                else:
                                    st.session_state.pdf_upload_notice = (
                                        "success",
                                        f"{selected_edition} handbook data was deleted from "
                                        "Bronze, Silver, Gold, PDF storage, and Vector Search."
                                    )
                                st.rerun()
                            except Exception as error:
                                logger.exception(
                                    "Handbook edition deletion failed for %s.",
                                    selected_edition
                                )
                                st.session_state.response_cache.clear()
                                st.session_state.messages = []
                                st.error(
                                    "Deletion did not fully complete. Review the error and "
                                    f"refresh the preview before retrying: {error}"
                                )

    if not st.session_state.messages:
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
    if selected_edition in available_editions and not _is_valid_handbook_edition(selected_edition):
        st.warning(
            f"The stored year **{selected_edition}** does not look like a valid academic year. "
            "You can correct its label below without uploading the PDF again."
        )

    invalid_editions = [
        edition for edition in available_editions
        if not _is_valid_handbook_edition(edition)
    ]
    if invalid_editions:
        with st.expander("Correct a handbook year label"):
            st.caption(
                "This relabels the stored sections; it does not upload another copy of the PDF."
            )
            source_edition = st.selectbox(
                "Year label to correct",
                invalid_editions,
                key="source_handbook_edition_to_correct"
            )
            corrected_year = st.text_input(
                "Correct year",
                placeholder="2024-2025",
                key="corrected_handbook_edition"
            )
            try:
                corrected_edition = _normalise_handbook_edition(corrected_year)
                correction_valid = True
            except ValueError:
                corrected_edition = ""
                correction_valid = False
            if corrected_year and not correction_valid:
                st.caption(
                    "Use a year (YYYY) or consecutive academic years "
                    "(for example, 2024-2025 or 2024-25)."
                )
            if st.button(
                f"Correct {source_edition} to {corrected_edition or 'the selected year'}",
                disabled=not correction_valid,
                key="correct_handbook_edition"
            ):
                try:
                    with st.spinner("Correcting the stored year label..."):
                        sync_error = _move_handbook_edition(
                            source_edition, corrected_edition
                        )
                    st.session_state.response_cache.clear()
                    st.session_state.selected_handbook_edition = corrected_edition
                    if sync_error:
                        st.session_state.pdf_upload_notice = (
                            "warning",
                            f"Stored sections are now labeled {corrected_edition}. "
                            f"Vector Search sync is pending: {sync_error}"
                        )
                    else:
                        st.session_state.pdf_upload_notice = (
                            "success",
                            f"Stored sections are now labeled {corrected_edition}."
                        )
                    st.rerun()
                except Exception as error:
                    st.error(f"Could not correct the handbook year: {error}")

    if st.button(
        "Retry Vector Search sync",
        help="Sync already-uploaded handbook sections. Do not upload the PDF again."
    ):
        try:
            with st.spinner("Syncing handbook sections to Vector Search..."):
                st.session_state.index.sync()
            st.session_state.response_cache.clear()
            st.success("Vector Search synchronization started.")
        except Exception as error:
            st.error(
                "The handbook sections remain available for keyword search, but Vector "
                f"Search is not ready to sync yet: {error}"
            )

    st.markdown("---")
    st.markdown("### ℹ️ System Info")
    st.markdown("""
<div style="font-size:0.8rem;line-height:2.1;color:#b0c4de;">
  <div>🤖 &nbsp;<span style="color:#D4AF37;font-weight:600;">Model</span>
       &nbsp;&nbsp; Meta Llama 3.3 70B</div>
  <div>📚 &nbsp;<span style="color:#D4AF37;font-weight:600;">Index</span>
       &nbsp;&nbsp;&nbsp; Searchable handbook editions</div>
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
  Choose a handbook year from the Year menu above to keep answers focused on that edition.
  New uploads are kept separate, and the newest edition is selected by default.
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
        if message.get("handbook_edition"):
            st.caption(f"Handbook used: {message['handbook_edition']}")

# ============================================================
# CHAT PROCESSING AND INPUT
# ============================================================
if prompt := st.chat_input("Type your question about Don Bosco College handbook here…"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.pending_prompt = prompt
    st.rerun()

if pending_prompt := st.session_state.pop("pending_prompt", None):
    selected_edition = st.session_state.get(
        "selected_handbook_edition", ALL_HANDBOOKS
    )
    response_edition = (
        None
        if _normalise(pending_prompt) in _GREETINGS
        else selected_edition
    )
    with st.chat_message("assistant", avatar="🤖"):
        cache_key = (
            f"{ANSWER_CACHE_VERSION}:{selected_edition}:{_normalise(pending_prompt)}"
        )
        is_instant = (
            _normalise(pending_prompt) in _GREETINGS
            or cache_key in st.session_state.response_cache
        )

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

        response, from_cache = get_response(pending_prompt)

        if not is_instant:
            thinking_placeholder.empty()

        st.markdown(response)
        if response_edition:
            st.caption(f"Handbook used: {response_edition}")

        # Show a subtle cache badge so user knows it was instant
        if from_cache:
            st.markdown(
                '<div style="margin-top:0.35rem;">'
                '<span class="cache-badge">'
                '⚡ Instant reply</span></div>',
                unsafe_allow_html=True
            )

    st.session_state.messages.append({
        "role": "assistant",
        "content": response,
        "handbook_edition": response_edition
    })
    st.markdown('<div id="chat-bottom"></div>', unsafe_allow_html=True)

    components.html("""
<script>
const scrollToLatestMessage = () => {
  const doc = window.parent.document;
  const target = doc.getElementById("chat-bottom");
  if (!target) return;
  const behavior = window.matchMedia("(prefers-reduced-motion: reduce)").matches
    ? "auto"
    : "smooth";
  for (let container = target.parentElement; container; container = container.parentElement) {
    const overflowY = window.parent.getComputedStyle(container).overflowY;
    if (container.scrollHeight > container.clientHeight && /auto|scroll/.test(overflowY)) {
      container.scrollTo({ top: container.scrollHeight, behavior });
      return;
    }
  }
  target.scrollIntoView({ behavior, block: "end" });
};
setTimeout(scrollToLatestMessage, 100);
setTimeout(scrollToLatestMessage, 450);
</script>
""", height=0, scrolling=False)