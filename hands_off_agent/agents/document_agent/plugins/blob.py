import os
from semantic_kernel.functions import kernel_function
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta, timezone



class BlobPlugin:
    def __init__(self):
        BLOB_STORAGE_CONNECTION_STRING = os.getenv("BLOB_STORAGE_CONNECTION_STRING")
        BLOB_CONTAINER_NAME = os.getenv("BLOB_CONTAINER_NAME", "kaenovatesting")
        self.service_client = BlobServiceClient.from_connection_string(BLOB_STORAGE_CONNECTION_STRING)
        self.container_client = self.service_client.get_container_client(BLOB_CONTAINER_NAME)

    @kernel_function(
        name="public_blob_url",
        description="Get a public URL of a blob by its blob name. Will give none if the blob does not exist in a container. This public URL only valid for 1 day",
    )
    def get_state(
        self,
        name: str
    ) -> str | None:
        """Get a blob by its blob name. Will give none if the blob does not exist in a container. This public URL only valid for 1 day"""
        self.service_client
        blob = self.container_client.get_blob_client(name)

        if not blob.exists():
            return None
        
        # Get current time
        current_time = datetime.now(timezone.utc)
        start_time = current_time - timedelta(minutes=5)
        expiry_time = current_time + timedelta(days=1)

        sas_token = generate_blob_sas(
            account_name=blob.account_name,
            container_name=blob.container_name,
            blob_name=blob.blob_name,
            account_key=self.service_client.credential.account_key,
            permission=BlobSasPermissions(read=True),
            expiry=expiry_time,
            start=start_time
        )

        return f"{blob.url}?{sas_token}"