import sys
from document_upload_cli.utils import file_eligible, ocr, chunk_text, embed, upload_to_ai_search_studio, init_index

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
        "AI_SEARCH_INDEX"
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
    ocr_result = ocr(file_path)
    chunks = chunk_text(ocr_result)

    for i, text_chunk in enumerate(chunks):
        embeddings = embed(text_chunk)
        upload_to_ai_search_studio(i, file_name, text_chunk, embeddings)
        print(f"Uploaded chunk {i+1}/{len(chunks)}")

    print("Upload complete.")

if __name__ == "__main__":
    init_index()
    main()
