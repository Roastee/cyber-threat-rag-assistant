"""
Application configuration module.

Centralizes all configuration constants and settings for the Streamlit app.
Uses dataclasses instead of pydantic-settings for zero-dependency config
at this stage. Will migrate to pydantic-settings when .env loading is needed.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AppConfig:
    """Immutable application-level configuration."""

    APP_TITLE: str = "🛡️ Threat Intelligence RAG Chatbot"
    APP_ICON: str = "🛡️"
    APP_VERSION: str = "0.5.0"
    APP_DESCRIPTION: str = (
        "AI-powered threat intelligence assistant using "
        "Retrieval-Augmented Generation."
    )

    # --- Layout ---
    SIDEBAR_WIDTH: int = 300
    MAX_CHAT_HISTORY: int = 100

    # --- Chat Defaults ---
    SYSTEM_PROMPT: str = (
        "You are a cybersecurity threat intelligence analyst assistant. "
        "You provide accurate, detailed, and actionable threat intelligence "
        "based on the documents and data available to you. "
        "Always cite your sources when possible. "
        "If you don't have enough information, say so clearly."
    )
    WELCOME_MESSAGE: str = (
        "Welcome, analyst. I'm your Threat Intelligence assistant. "
        "Ask me about CVEs, threat actors, MITRE ATT&CK techniques, "
        "or any indexed security data.\n\n"
        "📄 *Upload PDFs on the Documents page to get started.*"
    )

    # --- Ingestion ---
    ALLOWED_FILE_TYPES: tuple = ("pdf",)
    MAX_FILE_SIZE_MB: int = 50
    MAX_FILES_PER_UPLOAD: int = 10
    CONTENT_PREVIEW_LENGTH: int = 500

    # --- Model Defaults (for future RAG integration) ---
    DEFAULT_MODEL: str = "gpt-4"
    DEFAULT_TEMPERATURE: float = 0.1
    DEFAULT_TOP_K: int = 5
    DEFAULT_CHUNK_SIZE: int = 1000
    DEFAULT_CHUNK_OVERLAP: int = 200

    # --- Embeddings ---
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSIONS: int = 384
    EMBEDDING_BATCH_SIZE: int = 32

    # --- Vector Store ---
    CHROMA_PERSIST_DIR: str = "chroma_db"
    CHROMA_COLLECTION_NAME: str = "threat_intel_docs"

    # --- Theme ---
    PRIMARY_COLOR: str = "#00FF88"
    BACKGROUND_COLOR: str = "#0A0E17"
    SECONDARY_BG: str = "#111827"
    TEXT_COLOR: str = "#E2E8F0"
    ACCENT_COLOR: str = "#00D4FF"
    WARNING_COLOR: str = "#FF6B35"
    DANGER_COLOR: str = "#FF3366"


@dataclass(frozen=True)
class NavigationConfig:
    """Sidebar navigation pages and their icons."""

    PAGES: dict = field(default_factory=lambda: {
        "💬 Chat": "chat",
        "📄 Documents": "documents",
        "⚙️ Settings": "settings",
        "ℹ️ About": "about",
    })
    DEFAULT_PAGE: str = "chat"


# --- Singleton instances ---
app_config = AppConfig()
nav_config = NavigationConfig()
