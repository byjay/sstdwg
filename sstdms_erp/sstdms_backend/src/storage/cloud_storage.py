# cloud_storage.py

import boto3
import os
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)

class CloudStorageManager:
    """Manages cloud storage operations for AWS S3 and other cloud providers."""
    
    def __init__(self, provider: str = "aws_s3", **config):
        self.provider = provider.lower()
        self.config = config
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the appropriate cloud storage client."""
        if self.provider == "aws_s3":
            self._initialize_s3_client()
        elif self.provider == "google_cloud":
            self._initialize_gcs_client()
        elif self.provider == "azure_blob":
            self._initialize_azure_client()
        else:
            logger.error(f"Unsupported cloud storage provider: {self.provider}")
    
    def _initialize_s3_client(self):
        """Initialize AWS S3 client."""
        try:
            self.client = boto3.client(
                's3',
                aws_access_key_id=self.config.get('aws_access_key_id'),
                aws_secret_access_key=self.config.get('aws_secret_access_key'),
                region_name=self.config.get('region_name', 'us-east-1')
            )
            self.bucket_name = self.config.get('bucket_name')
            logger.info("AWS S3 client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AWS S3 client: {str(e)}")
            self.client = None
    
    def _initialize_gcs_client(self):
        """Initialize Google Cloud Storage client."""
        try:
            from google.cloud import storage
            
            # Initialize with service account key file or default credentials
            if 'service_account_path' in self.config:
                self.client = storage.Client.from_service_account_json(
                    self.config['service_account_path']
                )
            else:
                self.client = storage.Client()
            
            self.bucket_name = self.config.get('bucket_name')
            logger.info("Google Cloud Storage client initialized successfully")
        except ImportError:
            logger.error("Google Cloud Storage library not installed. Install with: pip install google-cloud-storage")
            self.client = None
        except Exception as e:
            logger.error(f"Failed to initialize Google Cloud Storage client: {str(e)}")
            self.client = None
    
    def _initialize_azure_client(self):
        """Initialize Azure Blob Storage client."""
        try:
            from azure.storage.blob import BlobServiceClient
            
            connection_string = self.config.get('connection_string')
            if connection_string:
                self.client = BlobServiceClient.from_connection_string(connection_string)
            else:
                account_name = self.config.get('account_name')
                account_key = self.config.get('account_key')
                self.client = BlobServiceClient(
                    account_url=f"https://{account_name}.blob.core.windows.net",
                    credential=account_key
                )
            
            self.container_name = self.config.get('container_name')
            logger.info("Azure Blob Storage client initialized successfully")
        except ImportError:
            logger.error("Azure Storage library not installed. Install with: pip install azure-storage-blob")
            self.client = None
        except Exception as e:
            logger.error(f"Failed to initialize Azure Blob Storage client: {str(e)}")
            self.client = None
    
    def upload_file(self, local_path: str, remote_key: str, metadata: Dict[str, str] = None) -> bool:
        """Upload a file to cloud storage."""
        if not self.client:
            logger.error("Cloud storage client not initialized")
            return False
        
        if not os.path.exists(local_path):
            logger.error(f"Local file does not exist: {local_path}")
            return False
        
        try:
            if self.provider == "aws_s3":
                return self._upload_to_s3(local_path, remote_key, metadata)
            elif self.provider == "google_cloud":
                return self._upload_to_gcs(local_path, remote_key, metadata)
            elif self.provider == "azure_blob":
                return self._upload_to_azure(local_path, remote_key, metadata)
            else:
                logger.error(f"Upload not implemented for provider: {self.provider}")
                return False
        except Exception as e:
            logger.error(f"Failed to upload file {local_path}: {str(e)}")
            return False
    
    def _upload_to_s3(self, local_path: str, remote_key: str, metadata: Dict[str, str] = None) -> bool:
        """Upload file to AWS S3."""
        try:
            extra_args = {}
            if metadata:
                extra_args['Metadata'] = metadata
            
            self.client.upload_file(local_path, self.bucket_name, remote_key, ExtraArgs=extra_args)
            logger.info(f"File uploaded to S3: {local_path} -> s3://{self.bucket_name}/{remote_key}")
            return True
        except ClientError as e:
            logger.error(f"S3 upload failed: {str(e)}")
            return False
    
    def _upload_to_gcs(self, local_path: str, remote_key: str, metadata: Dict[str, str] = None) -> bool:
        """Upload file to Google Cloud Storage."""
        try:
            bucket = self.client.bucket(self.bucket_name)
            blob = bucket.blob(remote_key)
            
            if metadata:
                blob.metadata = metadata
            
            blob.upload_from_filename(local_path)
            logger.info(f"File uploaded to GCS: {local_path} -> gs://{self.bucket_name}/{remote_key}")
            return True
        except Exception as e:
            logger.error(f"GCS upload failed: {str(e)}")
            return False
    
    def _upload_to_azure(self, local_path: str, remote_key: str, metadata: Dict[str, str] = None) -> bool:
        """Upload file to Azure Blob Storage."""
        try:
            blob_client = self.client.get_blob_client(
                container=self.container_name,
                blob=remote_key
            )
            
            with open(local_path, "rb") as data:
                blob_client.upload_blob(data, metadata=metadata, overwrite=True)
            
            logger.info(f"File uploaded to Azure: {local_path} -> {self.container_name}/{remote_key}")
            return True
        except Exception as e:
            logger.error(f"Azure upload failed: {str(e)}")
            return False
    
    def download_file(self, remote_key: str, local_path: str) -> bool:
        """Download a file from cloud storage."""
        if not self.client:
            logger.error("Cloud storage client not initialized")
            return False
        
        try:
            # Create local directory if it doesn't exist
            local_dir = os.path.dirname(local_path)
            if local_dir and not os.path.exists(local_dir):
                os.makedirs(local_dir)
            
            if self.provider == "aws_s3":
                return self._download_from_s3(remote_key, local_path)
            elif self.provider == "google_cloud":
                return self._download_from_gcs(remote_key, local_path)
            elif self.provider == "azure_blob":
                return self._download_from_azure(remote_key, local_path)
            else:
                logger.error(f"Download not implemented for provider: {self.provider}")
                return False
        except Exception as e:
            logger.error(f"Failed to download file {remote_key}: {str(e)}")
            return False
    
    def _download_from_s3(self, remote_key: str, local_path: str) -> bool:
        """Download file from AWS S3."""
        try:
            self.client.download_file(self.bucket_name, remote_key, local_path)
            logger.info(f"File downloaded from S3: s3://{self.bucket_name}/{remote_key} -> {local_path}")
            return True
        except ClientError as e:
            logger.error(f"S3 download failed: {str(e)}")
            return False
    
    def _download_from_gcs(self, remote_key: str, local_path: str) -> bool:
        """Download file from Google Cloud Storage."""
        try:
            bucket = self.client.bucket(self.bucket_name)
            blob = bucket.blob(remote_key)
            blob.download_to_filename(local_path)
            logger.info(f"File downloaded from GCS: gs://{self.bucket_name}/{remote_key} -> {local_path}")
            return True
        except Exception as e:
            logger.error(f"GCS download failed: {str(e)}")
            return False
    
    def _download_from_azure(self, remote_key: str, local_path: str) -> bool:
        """Download file from Azure Blob Storage."""
        try:
            blob_client = self.client.get_blob_client(
                container=self.container_name,
                blob=remote_key
            )
            
            with open(local_path, "wb") as download_file:
                download_file.write(blob_client.download_blob().readall())
            
            logger.info(f"File downloaded from Azure: {self.container_name}/{remote_key} -> {local_path}")
            return True
        except Exception as e:
            logger.error(f"Azure download failed: {str(e)}")
            return False
    
    def list_files(self, prefix: str = "") -> List[Dict[str, Any]]:
        """List files in cloud storage."""
        if not self.client:
            logger.error("Cloud storage client not initialized")
            return []
        
        try:
            if self.provider == "aws_s3":
                return self._list_s3_files(prefix)
            elif self.provider == "google_cloud":
                return self._list_gcs_files(prefix)
            elif self.provider == "azure_blob":
                return self._list_azure_files(prefix)
            else:
                logger.error(f"List files not implemented for provider: {self.provider}")
                return []
        except Exception as e:
            logger.error(f"Failed to list files: {str(e)}")
            return []
    
    def _list_s3_files(self, prefix: str = "") -> List[Dict[str, Any]]:
        """List files in AWS S3."""
        files = []
        try:
            response = self.client.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat(),
                        'etag': obj['ETag'].strip('"')
                    })
            
            logger.info(f"Listed {len(files)} files from S3 with prefix: {prefix}")
            return files
        except ClientError as e:
            logger.error(f"S3 list files failed: {str(e)}")
            return []
    
    def _list_gcs_files(self, prefix: str = "") -> List[Dict[str, Any]]:
        """List files in Google Cloud Storage."""
        files = []
        try:
            bucket = self.client.bucket(self.bucket_name)
            blobs = bucket.list_blobs(prefix=prefix)
            
            for blob in blobs:
                files.append({
                    'key': blob.name,
                    'size': blob.size,
                    'last_modified': blob.time_created.isoformat(),
                    'etag': blob.etag
                })
            
            logger.info(f"Listed {len(files)} files from GCS with prefix: {prefix}")
            return files
        except Exception as e:
            logger.error(f"GCS list files failed: {str(e)}")
            return []
    
    def _list_azure_files(self, prefix: str = "") -> List[Dict[str, Any]]:
        """List files in Azure Blob Storage."""
        files = []
        try:
            container_client = self.client.get_container_client(self.container_name)
            blobs = container_client.list_blobs(name_starts_with=prefix)
            
            for blob in blobs:
                files.append({
                    'key': blob.name,
                    'size': blob.size,
                    'last_modified': blob.last_modified.isoformat(),
                    'etag': blob.etag
                })
            
            logger.info(f"Listed {len(files)} files from Azure with prefix: {prefix}")
            return files
        except Exception as e:
            logger.error(f"Azure list files failed: {str(e)}")
            return []
    
    def delete_file(self, remote_key: str) -> bool:
        """Delete a file from cloud storage."""
        if not self.client:
            logger.error("Cloud storage client not initialized")
            return False
        
        try:
            if self.provider == "aws_s3":
                return self._delete_from_s3(remote_key)
            elif self.provider == "google_cloud":
                return self._delete_from_gcs(remote_key)
            elif self.provider == "azure_blob":
                return self._delete_from_azure(remote_key)
            else:
                logger.error(f"Delete not implemented for provider: {self.provider}")
                return False
        except Exception as e:
            logger.error(f"Failed to delete file {remote_key}: {str(e)}")
            return False
    
    def _delete_from_s3(self, remote_key: str) -> bool:
        """Delete file from AWS S3."""
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=remote_key)
            logger.info(f"File deleted from S3: s3://{self.bucket_name}/{remote_key}")
            return True
        except ClientError as e:
            logger.error(f"S3 delete failed: {str(e)}")
            return False
    
    def _delete_from_gcs(self, remote_key: str) -> bool:
        """Delete file from Google Cloud Storage."""
        try:
            bucket = self.client.bucket(self.bucket_name)
            blob = bucket.blob(remote_key)
            blob.delete()
            logger.info(f"File deleted from GCS: gs://{self.bucket_name}/{remote_key}")
            return True
        except Exception as e:
            logger.error(f"GCS delete failed: {str(e)}")
            return False
    
    def _delete_from_azure(self, remote_key: str) -> bool:
        """Delete file from Azure Blob Storage."""
        try:
            blob_client = self.client.get_blob_client(
                container=self.container_name,
                blob=remote_key
            )
            blob_client.delete_blob()
            logger.info(f"File deleted from Azure: {self.container_name}/{remote_key}")
            return True
        except Exception as e:
            logger.error(f"Azure delete failed: {str(e)}")
            return False
    
    def file_exists(self, remote_key: str) -> bool:
        """Check if a file exists in cloud storage."""
        if not self.client:
            logger.error("Cloud storage client not initialized")
            return False
        
        try:
            if self.provider == "aws_s3":
                return self._s3_file_exists(remote_key)
            elif self.provider == "google_cloud":
                return self._gcs_file_exists(remote_key)
            elif self.provider == "azure_blob":
                return self._azure_file_exists(remote_key)
            else:
                logger.error(f"File exists check not implemented for provider: {self.provider}")
                return False
        except Exception as e:
            logger.error(f"Failed to check file existence {remote_key}: {str(e)}")
            return False
    
    def _s3_file_exists(self, remote_key: str) -> bool:
        """Check if file exists in AWS S3."""
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=remote_key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            else:
                raise
    
    def _gcs_file_exists(self, remote_key: str) -> bool:
        """Check if file exists in Google Cloud Storage."""
        try:
            bucket = self.client.bucket(self.bucket_name)
            blob = bucket.blob(remote_key)
            return blob.exists()
        except Exception:
            return False
    
    def _azure_file_exists(self, remote_key: str) -> bool:
        """Check if file exists in Azure Blob Storage."""
        try:
            blob_client = self.client.get_blob_client(
                container=self.container_name,
                blob=remote_key
            )
            return blob_client.exists()
        except Exception:
            return False

# Example usage
if __name__ == "__main__":
    # AWS S3 example
    s3_config = {
        'aws_access_key_id': 'YOUR_ACCESS_KEY',
        'aws_secret_access_key': 'YOUR_SECRET_KEY',
        'region_name': 'us-east-1',
        'bucket_name': 'your-bucket-name'
    }
    
    # Google Cloud Storage example
    gcs_config = {
        'service_account_path': '/path/to/service-account.json',
        'bucket_name': 'your-bucket-name'
    }
    
    # Azure Blob Storage example
    azure_config = {
        'connection_string': 'your-connection-string',
        'container_name': 'your-container-name'
    }
    
    # Initialize cloud storage manager
    # cloud_storage = CloudStorageManager('aws_s3', **s3_config)
    # cloud_storage = CloudStorageManager('google_cloud', **gcs_config)
    # cloud_storage = CloudStorageManager('azure_blob', **azure_config)
    
    print("Cloud storage manager example - replace configuration with actual values to test")
    
    # Example operations (uncomment to test with real configuration)
    # cloud_storage.upload_file('/local/path/file.txt', 'remote/path/file.txt')
    # cloud_storage.download_file('remote/path/file.txt', '/local/path/downloaded_file.txt')
    # files = cloud_storage.list_files('remote/path/')
    # print(f"Found {len(files)} files")
    # cloud_storage.delete_file('remote/path/file.txt')

