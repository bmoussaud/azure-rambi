from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
import requests
import datetime
from azure.storage.blob import (
    BlobServiceClient,
    ContainerClient,
    BlobClient,
    BlobSasPermissions,
    ContainerSasPermissions,
    ResourceTypes,
    AccountSasPermissions,
    UserDelegationKey,
    generate_account_sas,
    generate_container_sas,
    generate_blob_sas
)

load_dotenv()


def create_service_sas_blob(blob_client: BlobClient, account_key: str):
        """Create a SAS token that's valid for one day, as an example"""
        start_time = datetime.datetime.now(datetime.timezone.utc)
        expiry_time = start_time + datetime.timedelta(days=1)

        sas_token = generate_blob_sas(
            account_name=blob_client.account_name,
            container_name=blob_client.container_name,
            blob_name=blob_client.blob_name,
            account_key=account_key,
            permission=BlobSasPermissions(read=True),
            expiry=expiry_time,
            start=start_time
        )
        return sas_token

token_credential = DefaultAzureCredential()
print(token_credential)

# 1. az ad sp create-for-rbac --name azure-rambi-sa-local 
# 2. az role assignment create --assignee c557ff49-ad14-4554-b73b-29403f13cfbb --role "Storage Blob Data Contributor" --scope /subscriptions/9479b396-5d3e-467a-b89f-ba8400aeb7dd/resourcegroups/azrdev/providers/Microsoft.Storage/storageAccounts/azrambitfnbpycbnkdum
blob_service_client = BlobServiceClient(
    account_url="https://azrambitfnbpycbnkdum.blob.core.windows.net",
    credential=token_credential
)
container_client = blob_service_client.get_container_client("movieposters")
blob_name= "x.png"
blob_client = container_client.get_blob_client(blob_name)
url="https://www.themoviedb.org/t/p/w600_and_h900_bestv2/6Wdl9N6dL0Hi0T1qJLWSz6gMLbd.jpg"
print(f"Blob {blob_name} uploaded to {container_client.container_name} container.")
blob_client.upload_blob(requests.get(url,timeout=100).content, overwrite=True,blob_type="BlockBlob" )

# Download the content of the blob and store it as a file
downloaded_blob = blob_client.download_blob()
with open("downloaded_x.png", "wb") as file:
    file.write(downloaded_blob.readall())

print("Blob content downloaded and stored as 'downloaded_x.png'.")
