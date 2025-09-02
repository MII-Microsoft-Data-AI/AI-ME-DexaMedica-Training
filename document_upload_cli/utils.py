import os
import re
import uuid

import mimetypes
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.storage.blob import BlobServiceClient
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from langchain_text_splitters.character import RecursiveCharacterTextSplitter
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchFieldDataType,
    SearchField,
    SearchableField,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchAlgorithmKind,
    VectorSearchProfile
)

from dotenv import load_dotenv
load_dotenv()  # take environment variables

ELIGIBLE_EXTENSIONS_MIME = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain"
]

# Document Intelligence
DOCUMENT_INTELLIGENCE_ENDPOINT = os.getenv("DOCUMENT_INTELLIGENCE_ENDPOINT")
DOCUMENT_INTELLIGENCE_KEY = os.getenv("DOCUMENT_INTELLIGENCE_KEY")
document_intelligence_client = DocumentIntelligenceClient(
    endpoint=DOCUMENT_INTELLIGENCE_ENDPOINT, credential=AzureKeyCredential(DOCUMENT_INTELLIGENCE_KEY)
)

# Azure OpenAI
OPENAI_KEY = os.getenv("OPENAI_KEY")
OPENAI_ENDPOINT = os.getenv("OPENAI_ENDPOINT")
embedding_client = AzureOpenAI(
    api_version="2024-12-01-preview",
    azure_endpoint=OPENAI_ENDPOINT,
    api_key=OPENAI_KEY
)

# Azure AISearch
AI_SEARCH_ENDPOINT = os.getenv("AI_SEARCH_ENDPOINT")
AI_SEARCH_KEY = os.getenv("AI_SEARCH_KEY")
AI_SEARCH_INDEX = os.getenv("AI_SEARCH_INDEX")
aisearch_client = SearchClient(AI_SEARCH_ENDPOINT, AI_SEARCH_INDEX, AzureKeyCredential(AI_SEARCH_KEY))
aisearch_index_client = SearchIndexClient(endpoint=AI_SEARCH_ENDPOINT, credential=AzureKeyCredential(AI_SEARCH_KEY))

# Azure Blob Storage
BLOB_STORAGE_CONNECTION_STRING = os.getenv("BLOB_STORAGE_CONNECTION_STRING")
BLOB_CONTAINER_NAME = os.getenv("BLOB_CONTAINER_NAME", "kaenovatesting")
blob_service_client = BlobServiceClient.from_connection_string(BLOB_STORAGE_CONNECTION_STRING)


# Helper to encode file name before ingested to the ID
def encode_key(file_name: str, chunk_num: int) -> str:
    # Replace spaces and periods with underscores
    sanitized = file_name.replace(" ", "_").replace(".", "_")
    
    # Remove any characters not in the allowed set: letters, digits, _, -, =
    sanitized = re.sub(r"[^a-zA-Z0-9_\-=]", "", sanitized)
    
    # Append the chunk number
    key = f"{sanitized}_{chunk_num}"
    
    return key

def init_index():
    # Define vector search configuration
    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(
                name="vector-algo",
                kind=VectorSearchAlgorithmKind.HNSW
            )
        ],
        profiles=[
            VectorSearchProfile(
                name="vector-profile",
                algorithm_configuration_name="vector-algo"
            )
        ]
    )

    # Define fields
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SimpleField(name="chunk_num", type=SearchFieldDataType.Int64, filterable=True),
        SimpleField(name="file_name", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="blob_url", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="title", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="content", type=SearchFieldDataType.String, searchable=True),
        SearchField(name="content_vector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True, vector_search_dimensions=1536, vector_search_profile_name="vector-profile"),
    ]

    # Create the index
    index = SearchIndex(name=AI_SEARCH_INDEX, fields=fields, vector_search=vector_search)
    aisearch_index_client.create_or_update_index(index)

def init_container():
    try:
        container_service_client = blob_service_client.get_container_client(BLOB_CONTAINER_NAME)
        container_service_client.create_container()
    except Exception as e:
        print(f"Container {BLOB_CONTAINER_NAME} may already exist. {e}")


def file_eligible(file_path: str) -> bool:
    # Check extension
    _, ext = os.path.splitext(file_path)
    if ext.lower() in ELIGIBLE_EXTENSIONS_MIME:
        return True

    # Check mimetype
    mimetype, _ = mimetypes.guess_type(file_path)
    if mimetype:
        if mimetype in ELIGIBLE_EXTENSIONS_MIME:
            return True
    return False


def ocr(file_path: str) -> str:
    file_bytes = open(file_path, "rb").read()
    analyzer = document_intelligence_client.begin_analyze_document(
        "prebuilt-read", analyze_request=AnalyzeDocumentRequest(
            bytes_source=file_bytes
        )
    )
    results = analyzer.result()
    return results.content

def chunk_text(text: str) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""]
    )
    return splitter.split_text(text=text)

def embed(text: str) -> list[float]:
    deployment = "main-text-embeddings-small"
    response = embedding_client.embeddings.create(
        input=[text],
        model=deployment
    )
    return response.data[0].embedding   

def upload_to_blob(file_path: str) -> str:
    container_service_client = blob_service_client.get_container_client(BLOB_CONTAINER_NAME)

    file_extension = os.path.splitext(file_path)[1]
    file_name = str(uuid.uuid4())
    blob_file_name = f"{file_name}{file_extension}"
    
    blob_client = container_service_client.get_blob_client(blob_file_name)
    with open(file_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)

    return blob_client.url

def upload_to_ai_search_studio(chunk_num: int, file_name: str, content: str, embeddings: list[float], blob_url: str) -> None:
    document = {
        "id": encode_key(file_name, chunk_num),
        "file_name": file_name,
        "chunk_num": chunk_num,
        "content": content,
        "content_vector": embeddings,
        "title": file_name,
        "blob_url": blob_url
    }

    aisearch_client.upload_documents([document])

def main():
    # check env
    if not all([DOCUMENT_INTELLIGENCE_ENDPOINT, DOCUMENT_INTELLIGENCE_KEY, OPENAI_KEY, OPENAI_ENDPOINT, AI_SEARCH_KEY, AI_SEARCH_ENDPOINT, AI_SEARCH_INDEX]):
        raise ValueError("Missing required environment variables")

    # Load Document
    dir_contents = os.listdir('./data')
    eligible_files = [f for f in dir_contents if file_eligible(f)]

    for file in eligible_files:
        file_path = os.path.join('./data', file)

        # Upload to Blob
        blob_url = upload_to_blob(file_path)

        # Do OCR
        ocr_result = ocr(file_path)

        # Split Document
        chunks = chunk_text(ocr_result)

        for text_chunk in chunks:
            embeddings = embed(text_chunk)

            upload_to_ai_search_studio(file_path, text_chunk, embeddings, blob_url)

if __name__ == "__main__":
    init_index()
    init_container()