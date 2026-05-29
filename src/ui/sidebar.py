"""
Sidebar component — Navigation, session info, and quick-settings.

The sidebar provides:
    1. Branding/logo area
    2. Navigation buttons for page switching
    3. Quick settings (model selector, temperature)
    4. Session metadata (session ID, message count)
    5. Clear chat / reset actions
"""

import streamlit as st

from src.core.config import app_config, nav_config
from src.core.state import state_manager, StateKeys


def render_sidebar() -> str:
    """Render the sidebar and return the selected page identifier.

    Returns:
        str: The page key (e.g. "chat", "documents", "settings", "about").
    """
    with st.sidebar:
        _render_branding()
        st.markdown('<div class="cyber-divider"></div>', unsafe_allow_html=True)

        selected_page = _render_navigation()
        st.markdown('<div class="cyber-divider"></div>', unsafe_allow_html=True)

        _render_quick_settings()
        st.markdown('<div class="cyber-divider"></div>', unsafe_allow_html=True)

        _render_session_info()
        st.markdown('<div class="cyber-divider"></div>', unsafe_allow_html=True)

        _render_actions()

    return selected_page


def _render_branding() -> None:
    """Render the sidebar branding / logo area."""
    st.markdown(
        """
        <div style="text-align: center; padding: 0.5rem 0 0.25rem 0;">
            <div style="font-size: 2.5rem; margin-bottom: 0.25rem;">🛡️</div>
            <div style="
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.7rem;
                color: #00FF88;
                letter-spacing: 0.15em;
                text-transform: uppercase;
            ">Threat Intel RAG</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_navigation() -> str:
    """Render navigation buttons and return the selected page.

    Uses Streamlit radio buttons styled as a vertical nav menu.
    """
    st.markdown(
        '<div class="sidebar-section">'
        '<h3>Navigation</h3>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Get page labels and their identifiers
    page_labels = list(nav_config.PAGES.keys())
    page_ids = list(nav_config.PAGES.values())

    # Determine current selection index
    current_page = state_manager.get_current_page()
    current_index = page_ids.index(current_page) if current_page in page_ids else 0

    selected_label = st.radio(
        label="Navigate",
        options=page_labels,
        index=current_index,
        label_visibility="collapsed",
        key="nav_radio",
    )

    # Map label back to page ID
    selected_page = nav_config.PAGES.get(selected_label, nav_config.DEFAULT_PAGE)
    state_manager.set_current_page(selected_page)

    return selected_page


def _render_quick_settings() -> None:
    """Render quick-access model settings.

    These mirror the full settings page but provide fast access
    to the most commonly changed parameters.
    """
    st.markdown(
        '<div class="sidebar-section">'
        '<h3>⚡ Quick Settings</h3>'
        '</div>',
        unsafe_allow_html=True,
    )

    config = state_manager.get_session_config()

    # Model selector
    model_options = ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "local-model"]
    current_model_idx = (
        model_options.index(config.model)
        if config.model in model_options
        else 0
    )

    selected_model = st.selectbox(
        "Model",
        options=model_options,
        index=current_model_idx,
        key="sidebar_model",
    )

    # Temperature slider
    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=config.temperature,
        step=0.05,
        key="sidebar_temperature",
        help="Lower = more focused & deterministic. Higher = more creative.",
    )

    # Top-K slider
    top_k = st.slider(
        "Retrieved Chunks (Top-K)",
        min_value=1,
        max_value=20,
        value=config.top_k,
        step=1,
        key="sidebar_top_k",
        help="Number of document chunks to retrieve for context.",
    )

    # Persist changes
    state_manager.update_session_config(
        model=selected_model,
        temperature=temperature,
        top_k=top_k,
    )


def _render_session_info() -> None:
    """Render session metadata (ID, message count, status)."""
    session_id = state_manager.get_session_id()
    chat_history = state_manager.get_chat_history()
    doc_count = len(state_manager.get_ingested_docs())

    st.markdown(
        f"""
        <div class="sidebar-section">
            <h3>📊 Session Info</h3>
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; color: #94A3B8; line-height: 2;">
                <div>Session: <span style="color: #00D4FF;">{session_id[:8]}…</span></div>
                <div>Messages: <span style="color: #00FF88;">{len(chat_history)}</span></div>
                <div>Documents: <span style="color: #FF6B35;">{doc_count}</span></div>
                <div>Status: <span class="status-dot online"></span><span style="color: #00FF88;">Active</span></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_actions() -> None:
    """Render action buttons (clear chat, etc.)."""
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🗑️ Clear Chat", use_container_width=True, key="btn_clear"):
            state_manager.clear_chat_history()
            st.rerun()

    with col2:
        if st.button("🔄 New Session", use_container_width=True, key="btn_new"):
            # Reset all state keys
            for key in [
                StateKeys.CHAT_HISTORY,
                StateKeys.SESSION_ID,
                StateKeys.CONVERSATION_COUNT,
                StateKeys.IS_PROCESSING,
            ]:
                if key in st.session_state:
                    del st.session_state[key]
            state_manager.initialize()
            st.rerun()
