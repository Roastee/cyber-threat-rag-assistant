"""
Custom CSS styles for the cybersecurity-themed Streamlit app.

Design Philosophy:
    - Dark background (#0A0E17) mimicking a SOC terminal
    - Neon green (#00FF88) and cyan (#00D4FF) accents for a hacker aesthetic
    - Glassmorphism panels with frosted-glass effect
    - Monospace accents for code/data elements
    - Subtle glow effects and smooth transitions
    - Professional enough for enterprise, cool enough for CTFs
"""

import streamlit as st


def inject_custom_css() -> None:
    """Inject the full custom CSS theme into the Streamlit app."""
    st.markdown(_get_css(), unsafe_allow_html=True)


def _get_css() -> str:
    """Return the complete CSS stylesheet as an HTML <style> block."""
    return """
    <style>
    /* ================================================================
       IMPORTS — Google Fonts
       ================================================================ */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

    /* ================================================================
       ROOT VARIABLES
       ================================================================ */
    :root {
        --bg-primary: #0A0E17;
        --bg-secondary: #111827;
        --bg-tertiary: #1A2332;
        --bg-card: rgba(17, 24, 39, 0.7);
        --bg-glass: rgba(17, 24, 39, 0.5);
        --border-color: rgba(0, 255, 136, 0.15);
        --border-glow: rgba(0, 255, 136, 0.3);

        --text-primary: #E2E8F0;
        --text-secondary: #94A3B8;
        --text-muted: #64748B;

        --accent-green: #00FF88;
        --accent-cyan: #00D4FF;
        --accent-orange: #FF6B35;
        --accent-red: #FF3366;
        --accent-purple: #A855F7;

        --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        --font-mono: 'JetBrains Mono', 'Fira Code', monospace;

        --radius-sm: 8px;
        --radius-md: 12px;
        --radius-lg: 16px;
        --radius-xl: 20px;

        --shadow-glow: 0 0 20px rgba(0, 255, 136, 0.1);
        --shadow-card: 0 4px 24px rgba(0, 0, 0, 0.3);
        --transition-fast: 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        --transition-smooth: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    /* ================================================================
       GLOBAL OVERRIDES
       ================================================================ */
    .stApp {
        background: var(--bg-primary) !important;
        font-family: var(--font-sans) !important;
        color: var(--text-primary) !important;
    }

    /* Main content area */
    .main .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        max-width: 1200px !important;
    }

    /* ================================================================
       SIDEBAR
       ================================================================ */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0D1321 0%, #111827 100%) !important;
        border-right: 1px solid var(--border-color) !important;
    }

    section[data-testid="stSidebar"] .block-container {
        padding-top: 1rem !important;
    }

    /* ================================================================
       HEADER COMPONENT
       ================================================================ */
    .app-header {
        background: linear-gradient(135deg, rgba(0, 255, 136, 0.05) 0%, rgba(0, 212, 255, 0.05) 100%);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        padding: 1.5rem 2rem;
        margin-bottom: 1.5rem;
        backdrop-filter: blur(10px);
        position: relative;
        overflow: hidden;
    }

    .app-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, var(--accent-green), var(--accent-cyan), var(--accent-purple));
    }

    .app-header h1 {
        font-family: var(--font-sans) !important;
        font-weight: 700 !important;
        font-size: 1.75rem !important;
        color: var(--text-primary) !important;
        margin: 0 0 0.25rem 0 !important;
        letter-spacing: -0.02em;
    }

    .app-header .subtitle {
        font-size: 0.9rem;
        color: var(--text-secondary);
        font-weight: 400;
    }

    .header-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        font-family: var(--font-mono);
        letter-spacing: 0.03em;
    }

    .badge-online {
        background: rgba(0, 255, 136, 0.12);
        color: var(--accent-green);
        border: 1px solid rgba(0, 255, 136, 0.25);
    }

    .badge-version {
        background: rgba(0, 212, 255, 0.12);
        color: var(--accent-cyan);
        border: 1px solid rgba(0, 212, 255, 0.25);
    }

    /* ================================================================
       CHAT MESSAGES
       ================================================================ */
    .chat-container {
        display: flex;
        flex-direction: column;
        gap: 1rem;
        padding: 0.5rem 0;
    }

    .chat-message {
        display: flex;
        gap: 0.75rem;
        padding: 1rem 1.25rem;
        border-radius: var(--radius-md);
        animation: messageSlideIn 0.3s ease-out;
        line-height: 1.65;
        font-size: 0.92rem;
    }

    @keyframes messageSlideIn {
        from {
            opacity: 0;
            transform: translateY(8px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .chat-message.user-message {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.08) 0%, rgba(0, 212, 255, 0.03) 100%);
        border: 1px solid rgba(0, 212, 255, 0.15);
        border-left: 3px solid var(--accent-cyan);
    }

    .chat-message.assistant-message {
        background: linear-gradient(135deg, rgba(0, 255, 136, 0.08) 0%, rgba(0, 255, 136, 0.03) 100%);
        border: 1px solid rgba(0, 255, 136, 0.15);
        border-left: 3px solid var(--accent-green);
    }

    .message-avatar {
        font-size: 1.4rem;
        min-width: 32px;
        text-align: center;
        padding-top: 2px;
    }

    .message-content {
        flex: 1;
        color: var(--text-primary);
    }

    .message-content strong {
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        display: block;
        margin-bottom: 4px;
    }

    .user-message .message-content strong {
        color: var(--accent-cyan);
    }

    .assistant-message .message-content strong {
        color: var(--accent-green);
    }

    .message-timestamp {
        font-family: var(--font-mono);
        font-size: 0.7rem;
        color: var(--text-muted);
        margin-top: 6px;
    }

    /* ================================================================
       CHAT INPUT
       ================================================================ */
    .stChatInput {
        border-color: var(--border-color) !important;
    }

    .stChatInput > div {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: var(--radius-md) !important;
        transition: border-color var(--transition-fast) !important;
    }

    .stChatInput > div:focus-within {
        border-color: var(--accent-green) !important;
        box-shadow: var(--shadow-glow) !important;
    }

    .stChatInput textarea {
        color: var(--text-primary) !important;
        font-family: var(--font-sans) !important;
    }

    /* ================================================================
       SIDEBAR COMPONENTS
       ================================================================ */
    .sidebar-section {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        padding: 1rem 1.25rem;
        margin-bottom: 1rem;
        backdrop-filter: blur(8px);
    }

    .sidebar-section h3 {
        font-size: 0.8rem !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--accent-green) !important;
        margin-bottom: 0.75rem !important;
        font-weight: 600 !important;
        font-family: var(--font-mono) !important;
    }

    .nav-button {
        display: flex;
        align-items: center;
        gap: 10px;
        width: 100%;
        padding: 0.65rem 1rem;
        margin: 4px 0;
        border-radius: var(--radius-sm);
        background: transparent;
        color: var(--text-secondary);
        font-size: 0.88rem;
        font-weight: 500;
        cursor: pointer;
        transition: all var(--transition-fast);
        border: 1px solid transparent;
        text-decoration: none;
    }

    .nav-button:hover {
        background: rgba(0, 255, 136, 0.06);
        color: var(--text-primary);
        border-color: var(--border-color);
    }

    .nav-button.active {
        background: rgba(0, 255, 136, 0.1);
        color: var(--accent-green);
        border-color: rgba(0, 255, 136, 0.25);
        font-weight: 600;
    }

    /* ================================================================
       METRIC CARDS
       ================================================================ */
    .metric-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        padding: 1rem 1.25rem;
        text-align: center;
        backdrop-filter: blur(8px);
        transition: all var(--transition-smooth);
    }

    .metric-card:hover {
        border-color: var(--border-glow);
        box-shadow: var(--shadow-glow);
        transform: translateY(-2px);
    }

    .metric-value {
        font-family: var(--font-mono);
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--accent-green);
        margin-bottom: 4px;
    }

    .metric-label {
        font-size: 0.78rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }

    /* ================================================================
       STATUS INDICATOR
       ================================================================ */
    .status-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 6px;
        animation: pulse 2s ease-in-out infinite;
    }

    .status-dot.online {
        background: var(--accent-green);
        box-shadow: 0 0 8px rgba(0, 255, 136, 0.5);
    }

    .status-dot.offline {
        background: var(--accent-red);
        box-shadow: 0 0 8px rgba(255, 51, 102, 0.5);
        animation: none;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }

    /* ================================================================
       INFO / PLACEHOLDER CARDS
       ================================================================ */
    .info-card {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.06) 0%, rgba(168, 85, 247, 0.06) 100%);
        border: 1px solid rgba(0, 212, 255, 0.15);
        border-radius: var(--radius-lg);
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
    }

    .info-card .icon {
        font-size: 2.5rem;
        margin-bottom: 0.75rem;
    }

    .info-card h3 {
        color: var(--text-primary) !important;
        font-size: 1.1rem !important;
        margin-bottom: 0.5rem !important;
    }

    .info-card p {
        color: var(--text-secondary);
        font-size: 0.88rem;
        line-height: 1.6;
    }

    /* ================================================================
       BUTTONS
       ================================================================ */
    .stButton > button {
        background: linear-gradient(135deg, rgba(0, 255, 136, 0.15) 0%, rgba(0, 212, 255, 0.15) 100%) !important;
        border: 1px solid rgba(0, 255, 136, 0.3) !important;
        color: var(--accent-green) !important;
        border-radius: var(--radius-sm) !important;
        font-weight: 600 !important;
        font-family: var(--font-sans) !important;
        transition: all var(--transition-fast) !important;
        padding: 0.5rem 1.25rem !important;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, rgba(0, 255, 136, 0.25) 0%, rgba(0, 212, 255, 0.25) 100%) !important;
        border-color: var(--accent-green) !important;
        box-shadow: var(--shadow-glow) !important;
        transform: translateY(-1px) !important;
    }

    /* ================================================================
       SELECTBOX / SLIDER / INPUT OVERRIDES
       ================================================================ */
    .stSelectbox > div > div,
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: var(--bg-tertiary) !important;
        border-color: var(--border-color) !important;
        color: var(--text-primary) !important;
        border-radius: var(--radius-sm) !important;
    }

    .stSelectbox > div > div:focus-within,
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--accent-green) !important;
        box-shadow: 0 0 0 1px var(--accent-green) !important;
    }

    /* Slider */
    .stSlider > div > div > div > div {
        background: var(--accent-green) !important;
    }

    /* ================================================================
       DIVIDER
       ================================================================ */
    .cyber-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--border-color), transparent);
        margin: 1rem 0;
        border: none;
    }

    /* ================================================================
       SCROLLBAR
       ================================================================ */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }

    ::-webkit-scrollbar-track {
        background: var(--bg-primary);
    }

    ::-webkit-scrollbar-thumb {
        background: var(--bg-tertiary);
        border-radius: 3px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: rgba(0, 255, 136, 0.3);
    }

    /* ================================================================
       MARKDOWN OVERRIDES (for chat content)
       ================================================================ */
    .stMarkdown p {
        color: var(--text-primary);
    }

    .stMarkdown code {
        background: var(--bg-tertiary) !important;
        color: var(--accent-cyan) !important;
        padding: 2px 6px !important;
        border-radius: 4px !important;
        font-family: var(--font-mono) !important;
        font-size: 0.85em !important;
    }

    .stMarkdown pre {
        background: var(--bg-tertiary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: var(--radius-sm) !important;
    }

    /* ================================================================
       EXPANDER
       ================================================================ */
    .streamlit-expanderHeader {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: var(--radius-sm) !important;
        color: var(--text-primary) !important;
    }

    /* ================================================================
       ABOUT PAGE FEATURE GRID
       ================================================================ */
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }

    .feature-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        padding: 1.25rem;
        transition: all var(--transition-smooth);
    }

    .feature-card:hover {
        border-color: var(--border-glow);
        transform: translateY(-2px);
        box-shadow: var(--shadow-glow);
    }

    .feature-card .feature-icon {
        font-size: 1.5rem;
        margin-bottom: 0.5rem;
    }

    .feature-card h4 {
        color: var(--text-primary);
        font-size: 0.95rem;
        margin-bottom: 0.35rem;
    }

    .feature-card p {
        color: var(--text-secondary);
        font-size: 0.82rem;
        line-height: 1.5;
        margin: 0;
    }
    </style>
    """
