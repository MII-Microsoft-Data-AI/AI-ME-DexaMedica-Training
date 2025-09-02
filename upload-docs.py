import sys

from document_upload_cli.utils import file_eligible, ocr, chunk_text, embed, upload_to_ai_search_studio, init_index, upload_to_blob, init_container

from concurrent.futures import ThreadPoolExecutor, as_completed

def main():

    # Environment check (same as in utils.py)
    import os
    required_envs = [
        "DOCUMENT_INTELLIGENCE_ENDPOINT",
        "DOCUMENT_INTELLIGENCE_KEY",
        "OPENAI_KEY",
        "OPENAI_ENDPOINT",
        "AI_SEARCH_KEY",
        "AI_SEARCH_ENDPOINT",
        "AI_SEARCH_INDEX",
        "BLOB_STORAGE_CONNECTION_STRING"
    ]
    missing = [env for env in required_envs if not os.getenv(env)]
    if missing:
        print(f"Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)

    if len(sys.argv) != 2:
        print("Usage: upload-docs.py <path_to_file>")
        sys.exit(1)

    file_path = sys.argv[1]
    file_name = os.path.basename(file_path)

    if not os.path.isfile(file_path):
        print(f"File not found: {file_path}")
        sys.exit(1)

    if not file_eligible(file_path):
        print(f"File is not eligible for upload: {file_path}")
        sys.exit(1)

    print(f"Processing file: {file_path}")
    
    # Upload to Blob
    blob_name, blob_url = upload_to_blob(file_path)
    print(f"Processing file: {file_path} - Blob Upload Done")
    
    ocr_result = ocr(file_path)
    print(f"Processing file: {file_path} - OCR Done")
    chunks = chunk_text(ocr_result)
    print(f"Processing file: {file_path} - Chunking Done")

    print(f"Processing file: {file_path} - Starting Upload")

    def upload_chunk(i, text_chunk):
        print(f"Processing file: {file_path} - Uploading chunk {i+1}/{len(chunks)}")
        embeddings = embed(text_chunk)
        upload_to_ai_search_studio(i, file_name, text_chunk, embeddings, blob_url, blob_name)
        print(f"Processing file: {file_path} - Uploaded chunk {i+1}/{len(chunks)}")


    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(upload_chunk, i, text_chunk) for i, text_chunk in enumerate(chunks)]
        for future in as_completed(futures):
            # Optionally handle exceptions here
            try:
                future.result()
            except Exception as e:
                print(f"Error uploading chunk: {e}")

    print(f"Processing file: {file_path} - Upload Complete")

if __name__ == "__main__":
    init_index()
    init_container()
    main()
