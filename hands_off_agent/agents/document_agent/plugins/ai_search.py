import os

from typing import Annotated, Any
from semantic_kernel.functions import KernelParameterMetadata, KernelPlugin
from semantic_kernel.connectors.azure_ai_search import AzureAISearchCollection
from semantic_kernel.connectors.ai.open_ai import AzureTextEmbedding

from pydantic import BaseModel, ConfigDict
from semantic_kernel.data.vector import VectorStoreField, vectorstoremodel

from dotenv import load_dotenv
load_dotenv()  # take environment variables

import logging
from semantic_kernel.utils.logging import setup_logging
setup_logging()
logging.getLogger("kernel").setLevel(logging.DEBUG)

# Import all environment variable
OPENAI_KEY = os.getenv("OPENAI_KEY")
OPENAI_ENDPOINT = os.getenv("OPENAI_ENDPOINT")
DOCUMENT_INTELLIGENCE_ENDPOINT = os.getenv("DOCUMENT_INTELLIGENCE_ENDPOINT")
DOCUMENT_INTELLIGENCE_KEY = os.getenv("DOCUMENT_INTELLIGENCE_KEY")
AI_SEARCH_ENDPOINT = os.getenv("AI_SEARCH_ENDPOINT")
AI_SEARCH_KEY = os.getenv("AI_SEARCH_KEY")
AI_SEARCH_INDEX = os.getenv("AI_SEARCH_INDEX")

# Define the collection model
@vectorstoremodel(collection_name=AI_SEARCH_INDEX)
class DocumentBaseClass(BaseModel):
    id: Annotated[str, VectorStoreField("key")]
    chunk_num: Annotated[int, VectorStoreField("data")]
    file_name: Annotated[str, VectorStoreField("data")]
    content: Annotated[str, VectorStoreField("data", is_full_text_indexed=True)]
    # Need to be defined as type float and initialized None
    content_vector: Annotated[list[float], VectorStoreField("vector", dimensions=1536, type='float')] = None

    model_config = ConfigDict(extra="ignore")

    def model_post_init(self, context: Any) -> None:
        if self.content_vector is None:
            self.content_vector = self.content

# Define the collection
collection = AzureAISearchCollection[str, DocumentBaseClass](
    record_type=DocumentBaseClass, 
    embedding_generator=AzureTextEmbedding(
        deployment_name="main-text-embeddings-small",
        endpoint=OPENAI_ENDPOINT,
        api_key=OPENAI_KEY,
        api_version="2024-12-01-preview",
    ),
    search_endpoint=AI_SEARCH_ENDPOINT,
    api_key=AI_SEARCH_KEY,

)

search_plugin = KernelPlugin(
    name="azure_ai_search_document",
    description="A plugin that allows you to search for documents in Azure AI Search.",
    functions=[
        # General search function based on query 
        collection.create_search_function(
            # this create search method uses the `search` method of the text search object.
            # remember that the text_search object for this sample is based on
            # the text_search method of the Azure AI Search.
            # but it can also be used with the other vector search methods.
            # This method's description, name and parameters are what will be serialized as part of the tool
            # call functionality of the LLM.
            # And crafting these should be part of the prompt design process.
            # The default parameters are `query`, `top`, and `skip`, but you specify your own.
            # The default parameters match the parameters of the VectorSearchOptions class.
            description="A document search engine, allows searching for many documents, "
            "you do not have to specify that you are searching for documents, for all, use `*`.",
            search_type="keyword_hybrid",
            # Next to the dynamic filters based on parameters, I can specify options that are always used.
            # this can include the `top`
            parameters=[
                KernelParameterMetadata(
                    name="query",
                    description="What to search for.",
                    type="str",
                    is_required=True,
                    type_object=str,
                ),

                KernelParameterMetadata(
                    name="file_name",
                    description="The document name to search within.",
                    type="str",
                    type_object=str,
                ),

                KernelParameterMetadata(
                    name="top",
                    description="Number of results to return.",
                    type="int",
                    default_value=5,
                    type_object=int,
                ),
            ],

            # and here the above created function is passed in.
            # finally, we specify the `string_mapper` function that is used to convert the record to a string.
            # This is used to make sure the relevant information from the record is passed to the LLM.
            # string_mapper=lambda x: f"(hotel_id :{x.record.HotelId}) {x.record.HotelName} (rating {x.record.Rating}) - {x.record.Description}. Address: {x.record.Address.StreetAddress}, {x.record.Address.City}, {x.record.Address.StateProvince}, {x.record.Address.Country}. Number of room types: {len(x.record.Rooms)}. Last renovated: {x.record.LastRenovationDate}.",  # noqa: E501

            string_mapper=lambda x: f"(file_name :{x.record.file_name}) (chunk_num: {x.record.chunk_num}) (content: {x.record.content}).",
        ),

        collection.create_search_function(
            function_name="get_all_content",
            description="Get all the content for a document.",
            parameters=[
                KernelParameterMetadata(
                    name="file_name",
                    description="The file name to get all the content for.",
                    type="str",
                    is_required=True,
                    type_object=str,
                ),
            ],
            # string_mapper=lambda x: f"(file_name :{x.record.file_name}) (chunk_num: {x.record.chunk_num}) (content: {x.record.content}).",
        ),
    ],
)