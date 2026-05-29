"""
Chat interface component — Message rendering and input handling.
"""

from __future__ import annotations

import random
import re
import time
from datetime import datetime

import streamlit as st

from src.core.config import app_config
from src.core.state import ChatMessage, state_manager

_MOCK_RESPONSES = [
    "Based on my analysis, this appears related to **APT29 (Cozy Bear)**, "
    "associated with Russian intelligence.\n\n"
    "📎 *Source: MITRE ATT&CK T1566.001*\n\n"
    "⚠️ *Demo response — RAG pipeline not yet connected.*",

    "The CVE is classified as **Critical (CVSS 9.8)** — remote code execution "
    "without authentication.\n\n**Actions:**\n"
    "1. Patch to ≥ 2.4.1\n2. Monitor for IOCs\n3. Review access logs\n\n"
    "⚠️ *Demo response — RAG pipeline not yet connected.*",

    "**T1059.001 (PowerShell)** is used in initial access and execution.\n\n"
    "- Download secondary payloads\n- Establish persistence\n"
    "- Exfiltrate through encoded channels\n\n"
    "**Detection:** Monitor `powershell.exe` spawning from unusual parents.\n\n"
    "⚠️ *Demo response — RAG pipeline not yet connected.*",

    "**3 IOCs** found:\n\n"
    "| Type | Value | Confidence |\n|---|---|---|\n"
    "| IP | `185.220.101.42` | High |\n"
    "| Domain | `c2-update.malware[.]xyz` | Medium |\n"
    "| Hash | `a1b2c3d4e5f6...` | High |\n\n"
    "Associated with **Emotet** malware family.\n\n"
    "⚠️ *Demo response — RAG pipeline not yet connected.*",

    "This aligns with **Living-off-the-Land (LotL)** techniques.\n\n"
    "**Common LOLBins:**\n"
    "- `certutil.exe` — File download\n"
    "- `mshta.exe` — Script execution\n"
    "- `regsvr32.exe` — Proxy execution\n\n"
    "⚠️ *Demo response — RAG pipeline not yet connected.*",
]


def render_chat_interface() -> None:
    """Render the complete chat interface."""
    history = state_manager.get_chat_history()
    if not history:
        _render_welcome()
    _render_chat_history(history)
    _handle_chat_input()


def _render_welcome() -> None:
    st.markdown(
        f'<div class="info-card"><div class="icon">🛡️</div>'
        f"<h3>Threat Intelligence Assistant</h3>"
        f"<p>{app_config.WELCOME_MESSAGE}</p></div>",
        unsafe_allow_html=True,
    )
    suggestions = [
        "Tell me about APT29",
        "What is CVE-2024-3400?",
        "Explain MITRE T1059",
        "List C2 frameworks",
    ]
    cols = st.columns(len(suggestions))
    for i, s in enumerate(suggestions):
        with cols[i]:
            if st.button(s, key=f"sug_{i}", use_container_width=True):
                _process_user_input(s)


def _render_chat_history(history: list[ChatMessage]) -> None:
    if not history:
        return
    parts = ['<div class="chat-container">']
    for msg in history:
        if msg.role == "user":
            parts.append(_fmt_user(msg))
        elif msg.role == "assistant":
            parts.append(_fmt_assistant(msg))
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


def _fmt_user(msg: ChatMessage) -> str:
    safe = _esc(msg.content)
    ts = _fmt_ts(msg.timestamp)
    return (
        '<div class="chat-message user-message">'
        '<div class="message-avatar">👤</div>'
        '<div class="message-content">'
        f"<strong>You</strong>{safe}"
        f'<div class="message-timestamp">{ts}</div>'
        "</div></div>"
    )


def _fmt_assistant(msg: ChatMessage) -> str:
    content = _md_to_html(msg.content)
    ts = _fmt_ts(msg.timestamp)
    src = ""
    if msg.sources:
        items = "".join(f"<li>{s}</li>" for s in msg.sources)
        src = (
            '<div style="margin-top:8px;font-size:0.78rem;color:#64748B;">'
            f"📎 Sources: <ul style='margin:4px 0 0 16px;'>{items}</ul></div>"
        )
    return (
        '<div class="chat-message assistant-message">'
        '<div class="message-avatar">🤖</div>'
        '<div class="message-content">'
        f"<strong>Analyst AI</strong>{content}{src}"
        f'<div class="message-timestamp">{ts}</div>'
        "</div></div>"
    )


def _handle_chat_input() -> None:
    user_input = st.chat_input(
        placeholder="Ask about threats, CVEs, IOCs, or MITRE ATT&CK...",
        key="chat_input",
    )
    if user_input:
        _process_user_input(user_input)


def _process_user_input(text: str) -> None:
    state_manager.add_message(ChatMessage(role="user", content=text))
    state_manager.increment_conversation_count()
    state_manager.set_processing(True)
    response = _generate_response(text)
    state_manager.set_processing(False)
    state_manager.add_message(
        ChatMessage(role="assistant", content=response,
                    sources=["Demo Mode — No documents indexed"])
    )
    st.rerun()


def _generate_response(query: str) -> str:  # noqa: ARG001
    """RAG hook point — returns mock response for now."""
    time.sleep(0.5)
    return random.choice(_MOCK_RESPONSES)


# ── Helpers ──────────────────────────────────────────────────

def _esc(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _md_to_html(text: str) -> str:
    text = _esc(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(
        r"`(.+?)`",
        r'<code style="background:#1A2332;color:#00D4FF;padding:2px 6px;'
        r'border-radius:4px;font-family:JetBrains Mono,monospace;'
        r'font-size:0.85em;">\1</code>',
        text,
    )
    lines = text.split("\n")
    out: list[str] = []
    in_tbl = False
    tbl: list[str] = []
    for ln in lines:
        s = ln.strip()
        if "|" in s and s.startswith("|"):
            if not in_tbl:
                in_tbl = True
                tbl = []
            if re.match(r"^\|[\s\-|]+\|$", s):
                continue
            tbl.append(s)
        else:
            if in_tbl:
                out.append(_html_table(tbl))
                in_tbl = False
                tbl = []
            if s.startswith("- "):
                out.append(f'<div style="padding-left:1rem;margin:2px 0;">'
                           f'<span style="color:#00FF88;">▸</span> {s[2:]}</div>')
            elif re.match(r"^\d+\.\s", s):
                out.append(f'<div style="padding-left:1rem;margin:2px 0;">{s}</div>')
            else:
                out.append(ln)
    if in_tbl:
        out.append(_html_table(tbl))
    text = "\n".join(out).replace("\n\n", "<br/><br/>").replace("\n", "<br/>")
    return text


def _html_table(rows: list[str]) -> str:
    if not rows:
        return ""
    h = '<table style="width:100%;border-collapse:collapse;margin:8px 0;font-size:0.85rem;">'
    for i, r in enumerate(rows):
        cells = [c.strip() for c in r.strip("|").split("|")]
        tag = "th" if i == 0 else "td"
        st_css = ("text-align:left;padding:6px 10px;border-bottom:1px solid "
                  "rgba(0,255,136,0.2);color:#00FF88;font-weight:600;" if i == 0
                  else "padding:6px 10px;border-bottom:1px solid rgba(0,255,136,0.08);color:#E2E8F0;")
        h += "<tr>" + "".join(f'<{tag} style="{st_css}">{c}</{tag}>' for c in cells) + "</tr>"
    return h + "</table>"


def _fmt_ts(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso).strftime("%H:%M:%S UTC")
    except (ValueError, TypeError):
        return ""
