"""
Page-level layouts for non-chat views.

Each function renders a full page in the main content area:
    - Documents: placeholder for future document ingestion UI
    - Settings:  full configuration panel
    - About:     project info, architecture, and feature grid
"""

import streamlit as st

from src.core.config import app_config
from src.core.state import state_manager


def render_documents_page() -> None:
    """Render the Documents management page with real PDF ingestion."""
    _render_page_header()
    _render_stats_dashboard()
    st.markdown('<div class="cyber-divider"></div>', unsafe_allow_html=True)
    _render_upload_section()
    st.markdown('<div class="cyber-divider"></div>', unsafe_allow_html=True)
    _render_document_list()


# ── Documents Page: Sub-components ───────────────────────────


def _render_page_header() -> None:
    """Render the page title and description."""
    st.markdown(
        '<div class="info-card">'
        '<div class="icon">📄</div>'
        "<h3>Document Ingestion</h3>"
        "<p>Upload PDF threat intelligence documents to extract and index their content.<br/>"
        "Supported: <strong>PDF files up to 50 MB</strong></p>"
        "</div>",
        unsafe_allow_html=True,
    )


def _render_stats_dashboard() -> None:
    """Render document statistics as metric cards."""
    docs = state_manager.get_ingested_docs()
    total_docs = len(docs)
    total_pages = sum(d.page_count for d in docs)
    total_words = sum(d.word_count for d in docs)
    total_size = sum(d.file_size_bytes for d in docs)

    # Format size
    if total_size < 1024:
        size_str = f"{total_size} B"
    elif total_size < 1024 * 1024:
        size_str = f"{total_size / 1024:.1f} KB"
    else:
        size_str = f"{total_size / (1024 * 1024):.2f} MB"

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        st.markdown(
            '<div class="metric-card">'
            f'<div class="metric-value" style="color: #00FF88;">{total_docs}</div>'
            '<div class="metric-label">Documents</div>'
            "</div>",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            '<div class="metric-card">'
            f'<div class="metric-value" style="color: #00D4FF;">{total_pages}</div>'
            '<div class="metric-label">Pages</div>'
            "</div>",
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            '<div class="metric-card">'
            f'<div class="metric-value" style="color: #A855F7;">{total_words:,}</div>'
            '<div class="metric-label">Words</div>'
            "</div>",
            unsafe_allow_html=True,
        )
    with col4:
        total_chunks = state_manager.get_total_chunk_count()
        st.markdown(
            '<div class="metric-card">'
            f'<div class="metric-value" style="color: #FF3366;">{total_chunks}</div>'
            '<div class="metric-label">Chunks</div>'
            "</div>",
            unsafe_allow_html=True,
        )
    with col5:
        total_embeddings = state_manager.get_total_embedding_count()
        st.markdown(
            '<div class="metric-card">'
            f'<div class="metric-value" style="color: #F59E0B;">{total_embeddings}</div>'
            '<div class="metric-label">Embeddings</div>'
            "</div>",
            unsafe_allow_html=True,
        )
    with col6:
        st.markdown(
            '<div class="metric-card">'
            f'<div class="metric-value" style="color: #FF6B35;">{size_str}</div>'
            '<div class="metric-label">Size</div>'
            "</div>",
            unsafe_allow_html=True,
        )


def _render_upload_section() -> None:
    """Render the file upload widget and process uploads."""
    st.markdown("#### ⬆️ Upload PDF Documents")

    uploaded_files = st.file_uploader(
        "Drag and drop PDF files here",
        type=list(app_config.ALLOWED_FILE_TYPES),
        accept_multiple_files=True,
        key="pdf_uploader",
        help=f"Maximum {app_config.MAX_FILE_SIZE_MB} MB per file. PDF only.",
    )

    if uploaded_files:
        # Import here to avoid circular imports at module load time
        from src.ingestion import ingestion_service

        for uploaded_file in uploaded_files:
            # Check if already processed this run (avoid re-processing on rerun)
            existing = state_manager.get_ingested_docs()
            if any(d.filename == uploaded_file.name for d in existing):
                st.info(f"📎 `{uploaded_file.name}` — already ingested.")
                continue

            with st.spinner(f"Processing `{uploaded_file.name}`..."):
                from io import BytesIO

                file_buffer = BytesIO(uploaded_file.getvalue())
                result = ingestion_service.ingest_pdf(
                    file_buffer=file_buffer,
                    filename=uploaded_file.name,
                    file_size_bytes=uploaded_file.size,
                )

            if result.success and result.document:
                doc = result.document
                chunk_info = f", {result.chunk_count} chunks" if result.chunk_count else ""
                emb_info = f", {result.embedding_count} embeddings" if result.embedding_count else ""
                st.success(
                    f"✅ **{doc.filename}** — "
                    f"{doc.page_count} pages, "
                    f"{doc.word_count:,} words{chunk_info}{emb_info}, "
                    f"{doc.file_size_display}"
                )
                if doc.status == "partial":
                    st.warning(
                        f"⚠️ Partial extraction: {doc.error_message}"
                    )
            else:
                st.error(f"❌ **{uploaded_file.name}** — {result.error}")


def _render_document_list() -> None:
    """Render the list of ingested documents with details."""
    docs = state_manager.get_ingested_docs()

    col_title, col_action = st.columns([3, 1])
    with col_title:
        st.markdown(f"#### 📂 Ingested Documents ({len(docs)})")
    with col_action:
        if docs and st.button("🗑️ Clear All", key="btn_clear_docs", use_container_width=True):
            state_manager.clear_ingested_docs()
            st.rerun()

    if not docs:
        st.info("No documents ingested yet. Upload PDF files above to get started.")
        return

    for i, doc in enumerate(docs):
        with st.expander(
            f"📄 {doc.filename}  —  {doc.page_count} pages  |  "
            f"{doc.word_count:,} words  |  {doc.file_size_display}",
            expanded=False,
        ):
            # Metadata row
            meta_col1, meta_col2, meta_col3 = st.columns(3)
            with meta_col1:
                st.markdown(f"**Document ID:** `{doc.doc_id}`")
                st.markdown(f"**Status:** {_status_badge(doc.status)}")
            with meta_col2:
                st.markdown(f"**Pages:** {doc.page_count}")
                st.markdown(f"**Characters:** {doc.char_count:,}")
            with meta_col3:
                st.markdown(f"**Uploaded:** {_format_timestamp(doc.upload_timestamp)}")
                st.markdown(f"**Size:** {doc.file_size_display}")

            # PDF metadata (if available)
            if doc.metadata:
                st.markdown("**PDF Metadata:**")
                for key, value in doc.metadata.items():
                    st.markdown(f"- *{key.title()}:* {value}")

            # Content preview
            st.markdown("---")
            st.markdown("**Content Preview:**")
            preview = doc.content_preview or "(No text content)"
            st.text_area(
                "Preview",
                value=preview,
                height=150,
                disabled=True,
                key=f"preview_{doc.doc_id}",
                label_visibility="collapsed",
            )

            # Delete button
            if st.button(
                f"🗑️ Remove Document",
                key=f"del_{doc.doc_id}",
                use_container_width=True,
            ):
                state_manager.remove_ingested_doc(doc.doc_id)
                state_manager.clear_chunks(doc.doc_id)
                state_manager.clear_embeddings(doc.doc_id)
                st.rerun()

            # Chunk preview
            doc_chunks = state_manager.get_chunks(doc.doc_id)
            if doc_chunks:
                st.markdown("---")
                st.markdown(f"**Chunks ({len(doc_chunks)}):**")
                for ci, chunk in enumerate(doc_chunks[:5]):
                    st.markdown(
                        f"**Chunk {chunk.chunk_index + 1}/{chunk.total_chunks}** "
                        f"({chunk.char_count} chars, {chunk.word_count} words, "
                        f"page {chunk.page_number})"
                    )
                    st.text_area(
                        f"Chunk {ci}",
                        value=chunk.preview,
                        height=80,
                        disabled=True,
                        key=f"chunk_{doc.doc_id}_{ci}",
                        label_visibility="collapsed",
                    )
                if len(doc_chunks) > 5:
                    st.caption(f"... and {len(doc_chunks) - 5} more chunks.")

            # Embedding info
            if state_manager.has_embeddings(doc.doc_id):
                emb_stats = state_manager.get_embedding_stats(doc.doc_id)
                emb_records = state_manager.get_embeddings(doc.doc_id)
                st.markdown("---")
                st.markdown(f"**🧠 Embeddings ({len(emb_records)}):**")
                if emb_stats:
                    ec1, ec2, ec3 = st.columns(3)
                    with ec1:
                        st.markdown(f"**Model:** `{emb_stats.model_name}`")
                    with ec2:
                        st.markdown(f"**Dimensions:** {emb_stats.dimensions}")
                    with ec3:
                        st.markdown(f"**Speed:** {emb_stats.chunks_per_sec:.1f} chunks/sec")
                # Show first 3 vector previews
                for ei, rec in enumerate(emb_records[:3]):
                    st.markdown(
                        f"Chunk `{rec.chunk_id[:8]}...` → `{rec.vector_preview}`"
                    )
                if len(emb_records) > 3:
                    st.caption(f"... and {len(emb_records) - 3} more vectors.")


def _status_badge(status: str) -> str:
    """Return a colored status string."""
    colors = {"success": "🟢 Success", "partial": "🟡 Partial", "failed": "🔴 Failed"}
    return colors.get(status, f"⚪ {status}")


def _format_timestamp(iso_ts: str) -> str:
    """Format ISO timestamp for display."""
    from datetime import datetime
    try:
        dt = datetime.fromisoformat(iso_ts)
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except (ValueError, TypeError):
        return iso_ts


def render_settings_page() -> None:
    """Render the full Settings configuration page."""
    st.markdown("### ⚙️ Configuration")
    st.markdown(
        '<div class="cyber-divider"></div>',
        unsafe_allow_html=True,
    )

    config = state_manager.get_session_config()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🤖 Model Settings")

        model = st.selectbox(
            "LLM Model",
            options=["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "local-model"],
            index=["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "local-model"].index(
                config.model
            ),
            key="settings_model",
        )

        temperature = st.slider(
            "Temperature",
            0.0, 1.0, config.temperature, 0.05,
            key="settings_temp",
            help="Controls response randomness. Lower = more deterministic.",
        )

        top_k = st.slider(
            "Top-K Retrieval",
            1, 20, config.top_k, 1,
            key="settings_topk",
            help="Number of document chunks retrieved per query.",
        )

    with col2:
        st.markdown("#### 📝 System Prompt")

        system_prompt = st.text_area(
            "System Prompt",
            value=config.system_prompt,
            height=200,
            key="settings_prompt",
            help="Instructions given to the AI before every query.",
        )

    # RAG settings (preview, not functional yet)
    st.markdown("---")
    st.markdown("#### 🔗 RAG Pipeline Settings")

    rc1, rc2 = st.columns(2)
    with rc1:
        chunk_size = st.number_input(
            "Chunk Size (tokens)",
            100, 4000, app_config.DEFAULT_CHUNK_SIZE, 100,
            key="settings_chunk",
        )
    with rc2:
        chunk_overlap = st.number_input(
            "Chunk Overlap (tokens)",
            0, 1000, app_config.DEFAULT_CHUNK_OVERLAP, 50,
            key="settings_overlap",
        )

    st.caption("⚠️ RAG pipeline settings will take effect once ingestion is implemented.")

    # Save button
    st.markdown("---")
    if st.button("💾 Save Settings", key="btn_save_settings", use_container_width=True):
        state_manager.update_session_config(
            model=model,
            temperature=temperature,
            top_k=top_k,
            system_prompt=system_prompt,
        )
        st.success("✅ Settings saved successfully.")


def render_about_page() -> None:
    """Render the About / project info page."""
    st.markdown("### ℹ️ About")
    st.markdown(
        '<div class="cyber-divider"></div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div class="info-card">'
        f'<div class="icon">🛡️</div>'
        f"<h3>{app_config.APP_TITLE}</h3>"
        f"<p>{app_config.APP_DESCRIPTION}<br/>"
        f"<strong>Version:</strong> {app_config.APP_VERSION}</p>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # Feature grid
    st.markdown("#### 🚀 Features")
    features = [
        ("🧠", "RAG Pipeline", "Retrieval-augmented generation grounded in your threat data"),
        ("🔍", "Semantic Search", "Find relevant intelligence using natural language queries"),
        ("📄", "Multi-Format Ingestion", "Support for PDF, DOCX, TXT, HTML, and more"),
        ("💬", "Conversational AI", "Multi-turn chat with context-aware responses"),
        ("📊", "Source Citations", "Every answer includes traceable source references"),
        ("🛡️", "MITRE ATT&CK", "Automatic mapping to ATT&CK techniques and tactics"),
    ]

    feature_html = '<div class="feature-grid">'
    for icon, title, desc in features:
        feature_html += (
            '<div class="feature-card">'
            f'<div class="feature-icon">{icon}</div>'
            f"<h4>{title}</h4>"
            f"<p>{desc}</p>"
            "</div>"
        )
    feature_html += "</div>"
    st.markdown(feature_html, unsafe_allow_html=True)

    # Architecture
    st.markdown("---")
    st.markdown("#### 🏗️ Architecture")
    st.code(
        "User Query → Embedding → Vector Search → "
        "Context Retrieval → Prompt Assembly → LLM → Cited Response",
        language=None,
    )

    # Tech stack
    st.markdown("#### 🔧 Tech Stack")
    tech = {
        "Frontend": "Streamlit",
        "LLM Orchestration": "LangChain",
        "LLM Provider": "OpenAI (GPT-4)",
        "Vector Store": "ChromaDB",
        "Embeddings": "OpenAI text-embedding-3-small",
        "Language": "Python ≥ 3.10",
    }
    for k, v in tech.items():
        st.markdown(f"- **{k}:** {v}")
