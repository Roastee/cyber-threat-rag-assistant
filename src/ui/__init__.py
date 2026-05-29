"""
UI package — Modular Streamlit components.

This package provides reusable UI components organized by function:
    - styles:     CSS theming and custom styling
    - header:     App header / banner component
    - sidebar:    Navigation and settings sidebar
    - chat:       Chat interface with message rendering
    - pages:      Page-level layouts (documents, settings, about)
    - components: Small reusable widgets (badges, cards, metrics)
"""

from src.ui.styles import inject_custom_css
from src.ui.header import render_header
from src.ui.sidebar import render_sidebar
from src.ui.chat import render_chat_interface
from src.ui.pages import render_documents_page, render_settings_page, render_about_page

__all__ = [
    "inject_custom_css",
    "render_header",
    "render_sidebar",
    "render_chat_interface",
    "render_documents_page",
    "render_settings_page",
    "render_about_page",
]
