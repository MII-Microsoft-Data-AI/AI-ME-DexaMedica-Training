import os
import streamlit as st
import tempfile

# Import document processing utilities
from document_upload_cli.utils import (
    file_eligible, ocr, chunk_text, embed, upload_to_ai_search_studio, init_index
)

# Document processing function
def process_document(uploaded_file, progress_callback=None):
    """
    Process an uploaded document through OCR, chunking, embedding, and upload to AI Search
    """
    try:
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
        missing = [env for env in required_envs if not os.getenv(env)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

        # Save uploaded file to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            temp_file_path = tmp_file.name

        try:
            # Check if file is eligible
            if not file_eligible(temp_file_path):
                raise ValueError(f"File type not supported: {uploaded_file.type}")

            if progress_callback:
                progress_callback(10, "Starting OCR processing...")

            # Perform OCR
            ocr_result = ocr(temp_file_path)

            if progress_callback:
                progress_callback(30, "OCR complete, chunking text...")

            # Chunk the text
            chunks = chunk_text(ocr_result)

            if progress_callback:
                progress_callback(40, f"Text chunked into {len(chunks)} pieces, starting upload...")

            # Process chunks sequentially
            for i, text_chunk in enumerate(chunks):
                if progress_callback:
                    progress = 40 + (i + 1) / len(chunks) * 50
                    progress_callback(progress, f"Processing chunk {i+1}/{len(chunks)}...")

                # Generate embeddings and upload
                embeddings = embed(text_chunk)
                upload_to_ai_search_studio(i, uploaded_file.name, text_chunk, embeddings)

            if progress_callback:
                progress_callback(100, "Upload complete!")

            return {
                "success": True,
                "message": f"Successfully processed {uploaded_file.name}",
                "chunks_processed": len(chunks),
                "total_characters": len(ocr_result)
            }

        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    except Exception as e:
        return {
            "success": False,
            "message": f"Error processing {uploaded_file.name}: {str(e)}",
            "chunks_processed": 0,
            "total_characters": 0
        }

def process_single_file(uploaded_file):
    """Process a single uploaded file"""
    # Create progress bar and status container
    progress_bar = st.progress(0)
    status_text = st.empty()
    result_container = st.empty()

    def update_progress(progress, message):
        progress_bar.progress(progress / 100)
        status_text.text(message)

    # Process the file
    result = process_document(uploaded_file, update_progress)

    # Show results
    with result_container.container():
        if result["success"]:
            st.success(f"✅ {result['message']}")

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Chunks Created", result["chunks_processed"])
            with col2:
                st.metric("Characters Processed", f"{result['total_characters']:,}")
        else:
            st.error(f"❌ {result['message']}")

    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()

def process_all_files(uploaded_files):
    """Process all uploaded files sequentially"""
    st.markdown("### 🚀 Processing All Files")

    overall_progress = st.progress(0)
    overall_status = st.empty()

    results = []
    total_files = len(uploaded_files)

    for i, uploaded_file in enumerate(uploaded_files):
        overall_status.text(f"Processing file {i+1}/{total_files}: {uploaded_file.name}")

        # Create individual progress for this file
        st.markdown(f"**Processing:** {uploaded_file.name}")
        file_progress = st.progress(0)
        file_status = st.empty()

        def update_progress(progress, message):
            file_progress.progress(progress / 100)
            file_status.text(message)

        # Process the file
        result = process_document(uploaded_file, update_progress)
        results.append(result)

        # Show individual result
        if result["success"]:
            st.success(f"✅ {uploaded_file.name}: {result['chunks_processed']} chunks processed")
        else:
            st.error(f"❌ {uploaded_file.name}: {result['message']}")

        # Update overall progress
        overall_progress.progress((i + 1) / total_files)

        # Clean up individual progress bars
        file_progress.empty()
        file_status.empty()

    # Show final summary
    overall_status.text("All files processed!")

    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Files", total_files)
    with col2:
        st.metric("Successful", len(successful))
    with col3:
        st.metric("Failed", len(failed))
    with col4:
        total_chunks = sum(r["chunks_processed"] for r in successful)
        st.metric("Total Chunks", total_chunks)

    if failed:
        with st.expander("❌ Failed Files", expanded=True):
            for result in failed:
                st.error(result["message"])