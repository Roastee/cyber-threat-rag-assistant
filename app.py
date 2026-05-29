"""
Threat Intelligence RAG Chatbot — Main Application Entry Point.

This is the Streamlit app runner. It:
    1. Configures the Streamlit page (title, icon, layout)
    2. Injects the custom cybersecurity CSS theme
    3. Initializes session state
    4. Renders the sidebar (navigation + settings)
    5. Routes to the selected page (chat, documents, settings, about)

Run with:
    streamlit run app.py

Architecture Notes:
    - All UI components are in src/ui/ (modular, single-responsibility)
    - All state management goes through src/core/state.py (no raw st.session_state)
    - All configuration lives in src/core/config.py (single source of truth)
    - The app is a thin orchestrator — it delegates everything to modules
"""

import streamlit as st

from src.core.config import app_config
from src.core.state import state_manager
from src.ui import (
    inject_custom_css,
    render_header,
    render_sidebar,
    render_chat_interface,
    render_documents_page,
    render_settings_page,
    render_about_page,
)


def main() -> None:
    """Application entry point."""

    # ── Page Configuration (must be first Streamlit call) ────
    st.set_page_config(
        page_title=app_config.APP_TITLE,
        page_icon=app_config.APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            "Get Help": "https://github.com/your-username/threat-intel-rag-chatbot",
            "Report a bug": "https://github.com/your-username/threat-intel-rag-chatbot/issues",
            "About": app_config.APP_DESCRIPTION,
        },
    )

    # ── Theme & Styling ──────────────────────────────────────
    inject_custom_css()

    # ── Initialize Session State ─────────────────────────────
    state_manager.initialize()

    # ── Sidebar (returns selected page) ──────────────────────
    current_page = render_sidebar()

    # ── Main Content Area ────────────────────────────────────
    render_header()

    # Route to the selected page
    if current_page == "chat":
        render_chat_interface()
    elif current_page == "documents":
        render_documents_page()
    elif current_page == "settings":
        render_settings_page()
    elif current_page == "about":
        render_about_page()
    else:
        render_chat_interface()  # Fallback to chat


if __name__ == "__main__":
    main()
