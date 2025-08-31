import streamlit as st
import os

# Import document processing
from ..document import process_single_file, process_all_files, init_index

# Import config
from ..config import COMPANY_LOGO_URL, COMPANY_NAME, COMPANY_TAGLINE

def upload_page():
    # Minimal header
    st.title("📁 Upload")

    # Agent selection in sidebar instead of main area

    # Header with company branding
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image(COMPANY_LOGO_URL)
    with col2:
        st.title("📁 Document Upload")
        st.markdown(f'<p class="company-info">{COMPANY_NAME} - Multi-Agent System</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="company-info">{COMPANY_TAGLINE}</p>', unsafe_allow_html=True)

    st.markdown("Upload documents to be processed by the document search agent.")
    st.markdown("---")

    # Check environment variables
    required_envs = [
        "DOCUMENT_INTELLIGENCE_ENDPOINT",
        "DOCUMENT_INTELLIGENCE_KEY",
        "OPENAI_KEY",
        "OPENAI_ENDPOINT",
        "AI_SEARCH_KEY",
        "AI_SEARCH_ENDPOINT",
        "AI_SEARCH_INDEX"
    ]
    missing_envs = [env for env in required_envs if not os.getenv(env)]

    if missing_envs:
        st.error(f"❌ **Missing Environment Variables:** {', '.join(missing_envs)}")
        st.markdown("Please configure the required environment variables to enable document upload functionality.")
        return

    # Upload instructions
    st.info("📝 **Instructions:** Upload PDF, DOCX, or TXT files. The documents will be processed using OCR, chunked, embedded, and uploaded to Azure AI Search for the document search agent to query.")

    # Initialize AI Search index button
    if st.button("🔧 Initialize AI Search Index", help="Initialize or update the AI Search index"):
        with st.spinner("Initializing AI Search index..."):
            try:
                init_index()
                st.success("✅ AI Search index initialized successfully!")
            except Exception as e:
                st.error(f"❌ Failed to initialize index: {str(e)}")

    # File uploader
    uploaded_files = st.file_uploader(
        "Choose document files",
        type=['pdf', 'docx', 'txt'],
        accept_multiple_files=True,
        help="Upload PDF, DOCX, or TXT files for document processing"
    )

    if uploaded_files:
        st.subheader("📋 Uploaded Files:")

        # Process all files button
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("🚀 Process All Files", help="Process all uploaded files at once"):
                process_all_files(uploaded_files)

        with col2:
            clear_files = st.button("🗑️ Clear All", help="Clear all uploaded files")
            if clear_files:
                st.rerun()

        # Individual file processing
        for uploaded_file in uploaded_files:
            with st.expander(f"📄 {uploaded_file.name} ({uploaded_file.type}) - {uploaded_file.size:,} bytes"):
                # File details
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"**File:** {uploaded_file.name}")
                    st.markdown(f"**Type:** {uploaded_file.type}")
                    st.markdown(f"**Size:** {uploaded_file.size:,} bytes")

                    # Check if file is eligible
                    file_extension = uploaded_file.name.split('.')[-1].lower()
                    eligible_extensions = ['pdf', 'docx', 'txt']

                    if file_extension in eligible_extensions:
                        st.success("✅ File type supported")
                    else:
                        st.warning("⚠️ File type may not be fully supported")

                with col2:
                    st.markdown("**Actions:**")

                    # Process individual file
                    if st.button(f"⚙️ Process", key=f"process_{uploaded_file.name}"):
                        process_single_file(uploaded_file)
    else:
        st.markdown("### 🎯 No files uploaded yet")
        st.markdown("Use the file uploader above to get started with document processing.")

        # Example of supported file types
        st.markdown("### 📚 Supported File Types")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**📄 PDF**\n- Research papers\n- Reports\n- Documentation")
        with col2:
            st.markdown("**📝 DOCX**\n- Word documents\n- Proposals\n- Manuscripts")
        with col3:
            st.markdown("**📋 TXT**\n- Plain text files\n- Code documentation\n- Notes")

    # Add footer at bottom of sidebar for upload page
    with st.sidebar:
        st.markdown("---")
        st.markdown(f"""
        <div style="text-align: center; color: #666; font-size: 0.8rem; padding: 10px 0;">
            © 2025 {COMPANY_NAME}<br>
            All rights reserved<br>
            <small>{COMPANY_TAGLINE}</small>
        </div>
        """, unsafe_allow_html=True)