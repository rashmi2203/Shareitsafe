import os
from flask import Flask, request, redirect, url_for, flash
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_flask_secret_key'

# Set up Azure Key Vault
key_vault_url = "https://backend1.vault.azure.net/"  # Replace with your Key Vault URL
credential = DefaultAzureCredential()
secret_client = SecretClient(vault_url=key_vault_url, credential=credential)

# Retrieve the connection string from Key Vault
storage_connection_string = secret_client.get_secret("AZURESTORAGECONNECTIONSTRING").value

# Set up Azure Blob Storage
blob_service_client = BlobServiceClient.from_connection_string(storage_connection_string)
container_name = "uploads"  # Make sure this matches your Azure Blob container

# Homepage with file upload form
@app.route('/')
def index():
    return '''
    <form method="POST" action="/upload" enctype="multipart/form-data">
        <input type="file" name="file" />
        <input type="submit" value="Upload" />
    </form>
    '''

# File upload route
@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    if file:
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=file.filename)
        blob_client.upload_blob(file, overwrite=True)

        # Generate a time-limited URL (valid for 1 hour)
        sas_token = generate_blob_sas(
            account_name=blob_service_client.account_name,
            container_name=container_name,
            blob_name=file.filename,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(hours=1)
        )
        file_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{container_name}/{file.filename}?{sas_token}"

        return f'File uploaded successfully! Shareable link: <a href="{file_url}" target="_blank">Click here</a>'
    else:
        flash('No file selected!')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
