import os

from langchain_text_splitters.character import RecursiveCharacterTextSplitter

from dotenv import load_dotenv
load_dotenv()  # take environment variables

ELIGIBLE_EXTENSIONS = [
    ".pdf",
    ".docx",
    ".txt"
]

def file_eligible(filename: str) -> bool:
    return any(filename.endswith(ext) for ext in ELIGIBLE_EXTENSIONS)

def ocr(file_path: str) -> str:
    pass

def chunk_text(text: str) -> list[str]:
    return RecursiveCharacterTextSplitter.split_text(text)

def embed(text: str) -> list[float]:
    pass

def upload_to_ai_search_studio(file_path: str, content: str, embeddings: list[float]) -> None:
    pass

def main():
    # Load Document
    dir_contents = os.listdir('./data')
    eligible_files = [f for f in dir_contents if file_eligible(f)]

    for file in eligible_files:
        file_path = os.path.join('./data', file)

        # Do OCR
        ocr_result = ocr(file_path)

        # Split Document
        chunks = chunk_text(file_path)

        for text_chunk in chunks:
            embeddings = embed(text_chunk)

            upload_to_ai_search_studio(file_path, text_chunk, embeddings)

if __name__ == "__main__":
    main()
