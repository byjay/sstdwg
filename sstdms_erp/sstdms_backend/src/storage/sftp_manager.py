# sftp_manager.py

import paramiko
import os
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class SFTPManager:
    """Manages SFTP connections and file operations."""
    
    def __init__(self, hostname: str, port: int = 22, username: str = None, password: str = None, private_key_path: str = None):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.private_key_path = private_key_path
        self.client = None
        self.sftp = None
        self.is_connected = False

    def connect(self) -> bool:
        """Establishes an SFTP connection."""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Prepare authentication
            auth_kwargs = {
                "hostname": self.hostname,
                "port": self.port,
                "username": self.username
            }
            
            if self.private_key_path and os.path.exists(self.private_key_path):
                # Use private key authentication
                private_key = paramiko.RSAKey.from_private_key_file(self.private_key_path)
                auth_kwargs["pkey"] = private_key
                logger.info(f"Using private key authentication: {self.private_key_path}")
            elif self.password:
                # Use password authentication
                auth_kwargs["password"] = self.password
                logger.info("Using password authentication")
            else:
                logger.error("No authentication method provided (password or private key)")
                return False
            
            # Connect
            self.client.connect(**auth_kwargs)
            self.sftp = self.client.open_sftp()
            self.is_connected = True
            logger.info(f"Successfully connected to SFTP server: {self.hostname}:{self.port}")
            return True
            
        except paramiko.AuthenticationException:
            logger.error("SFTP authentication failed")
            return False
        except paramiko.SSHException as e:
            logger.error(f"SFTP SSH error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"SFTP connection error: {str(e)}")
            return False

    def disconnect(self):
        """Closes the SFTP connection."""
        if self.sftp:
            self.sftp.close()
            self.sftp = None
        if self.client:
            self.client.close()
            self.client = None
        self.is_connected = False
        logger.info("SFTP connection closed")

    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Uploads a file to the remote server."""
        if not self.is_connected:
            logger.error("SFTP not connected")
            return False
        
        if not os.path.exists(local_path):
            logger.error(f"Local file does not exist: {local_path}")
            return False
        
        try:
            # Create remote directory if it doesn't exist
            remote_dir = os.path.dirname(remote_path)
            if remote_dir:
                self._create_remote_directory(remote_dir)
            
            self.sftp.put(local_path, remote_path)
            logger.info(f"File uploaded successfully: {local_path} -> {remote_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upload file {local_path} to {remote_path}: {str(e)}")
            return False

    def download_file(self, remote_path: str, local_path: str) -> bool:
        """Downloads a file from the remote server."""
        if not self.is_connected:
            logger.error("SFTP not connected")
            return False
        
        try:
            # Create local directory if it doesn't exist
            local_dir = os.path.dirname(local_path)
            if local_dir and not os.path.exists(local_dir):
                os.makedirs(local_dir)
            
            self.sftp.get(remote_path, local_path)
            logger.info(f"File downloaded successfully: {remote_path} -> {local_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download file {remote_path} to {local_path}: {str(e)}")
            return False

    def list_directory(self, remote_path: str = ".") -> List[Dict[str, Any]]:
        """Lists contents of a remote directory."""
        if not self.is_connected:
            logger.error("SFTP not connected")
            return []
        
        try:
            files = []
            for item in self.sftp.listdir_attr(remote_path):
                file_info = {
                    "name": item.filename,
                    "size": item.st_size,
                    "is_directory": self._is_directory(item),
                    "modified_time": datetime.fromtimestamp(item.st_mtime).isoformat() if item.st_mtime else None,
                    "permissions": oct(item.st_mode)[-3:] if item.st_mode else None
                }
                files.append(file_info)
            
            logger.info(f"Listed {len(files)} items in directory: {remote_path}")
            return files
            
        except Exception as e:
            logger.error(f"Failed to list directory {remote_path}: {str(e)}")
            return []

    def _is_directory(self, file_attr) -> bool:
        """Check if a file attribute represents a directory."""
        import stat
        return stat.S_ISDIR(file_attr.st_mode) if file_attr.st_mode else False

    def delete_file(self, remote_path: str) -> bool:
        """Deletes a file on the remote server."""
        if not self.is_connected:
            logger.error("SFTP not connected")
            return False
        
        try:
            self.sftp.remove(remote_path)
            logger.info(f"File deleted successfully: {remote_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete file {remote_path}: {str(e)}")
            return False

    def create_directory(self, remote_path: str) -> bool:
        """Creates a directory on the remote server."""
        if not self.is_connected:
            logger.error("SFTP not connected")
            return False
        
        return self._create_remote_directory(remote_path)

    def _create_remote_directory(self, remote_path: str) -> bool:
        """Helper method to create remote directory recursively."""
        try:
            # Try to create the directory
            self.sftp.mkdir(remote_path)
            logger.info(f"Directory created: {remote_path}")
            return True
        except IOError:
            # Directory might already exist or parent doesn't exist
            try:
                # Check if directory already exists
                self.sftp.stat(remote_path)
                logger.info(f"Directory already exists: {remote_path}")
                return True
            except IOError:
                # Parent directory doesn't exist, create it recursively
                parent_dir = os.path.dirname(remote_path)
                if parent_dir and parent_dir != remote_path:
                    if self._create_remote_directory(parent_dir):
                        return self._create_remote_directory(remote_path)
                return False
        except Exception as e:
            logger.error(f"Failed to create directory {remote_path}: {str(e)}")
            return False

    def delete_directory(self, remote_path: str) -> bool:
        """Deletes a directory on the remote server."""
        if not self.is_connected:
            logger.error("SFTP not connected")
            return False
        
        try:
            self.sftp.rmdir(remote_path)
            logger.info(f"Directory deleted successfully: {remote_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete directory {remote_path}: {str(e)}")
            return False

    def file_exists(self, remote_path: str) -> bool:
        """Checks if a file exists on the remote server."""
        if not self.is_connected:
            logger.error("SFTP not connected")
            return False
        
        try:
            self.sftp.stat(remote_path)
            return True
        except IOError:
            return False
        except Exception as e:
            logger.error(f"Error checking file existence {remote_path}: {str(e)}")
            return False

    def get_file_info(self, remote_path: str) -> Optional[Dict[str, Any]]:
        """Gets information about a remote file."""
        if not self.is_connected:
            logger.error("SFTP not connected")
            return None
        
        try:
            stat_info = self.sftp.stat(remote_path)
            return {
                "size": stat_info.st_size,
                "modified_time": datetime.fromtimestamp(stat_info.st_mtime).isoformat() if stat_info.st_mtime else None,
                "permissions": oct(stat_info.st_mode)[-3:] if stat_info.st_mode else None,
                "is_directory": self._is_directory(stat_info)
            }
        except Exception as e:
            logger.error(f"Failed to get file info for {remote_path}: {str(e)}")
            return None

    def sync_directory(self, local_dir: str, remote_dir: str, direction: str = "upload") -> Dict[str, Any]:
        """Synchronizes a directory between local and remote."""
        if not self.is_connected:
            logger.error("SFTP not connected")
            return {"success": False, "error": "Not connected"}
        
        sync_stats = {
            "uploaded": 0,
            "downloaded": 0,
            "skipped": 0,
            "errors": 0,
            "success": True
        }
        
        try:
            if direction == "upload":
                sync_stats = self._sync_upload(local_dir, remote_dir, sync_stats)
            elif direction == "download":
                sync_stats = self._sync_download(local_dir, remote_dir, sync_stats)
            else:
                sync_stats["success"] = False
                sync_stats["error"] = "Invalid direction. Use 'upload' or 'download'"
            
            return sync_stats
            
        except Exception as e:
            logger.error(f"Directory sync failed: {str(e)}")
            sync_stats["success"] = False
            sync_stats["error"] = str(e)
            return sync_stats

    def _sync_upload(self, local_dir: str, remote_dir: str, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Helper method for uploading directory contents."""
        for root, dirs, files in os.walk(local_dir):
            # Calculate relative path
            rel_path = os.path.relpath(root, local_dir)
            if rel_path == ".":
                remote_root = remote_dir
            else:
                remote_root = os.path.join(remote_dir, rel_path).replace("\\", "/")
            
            # Create remote directory
            self._create_remote_directory(remote_root)
            
            # Upload files
            for file in files:
                local_file = os.path.join(root, file)
                remote_file = os.path.join(remote_root, file).replace("\\", "/")
                
                if self.upload_file(local_file, remote_file):
                    stats["uploaded"] += 1
                else:
                    stats["errors"] += 1
        
        return stats

    def _sync_download(self, local_dir: str, remote_dir: str, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Helper method for downloading directory contents."""
        # This is a simplified implementation
        # A full implementation would recursively traverse remote directories
        remote_files = self.list_directory(remote_dir)
        
        for file_info in remote_files:
            if not file_info["is_directory"]:
                remote_file = os.path.join(remote_dir, file_info["name"]).replace("\\", "/")
                local_file = os.path.join(local_dir, file_info["name"])
                
                if self.download_file(remote_file, local_file):
                    stats["downloaded"] += 1
                else:
                    stats["errors"] += 1
        
        return stats

    def __enter__(self):
        """Context manager entry."""
        if self.connect():
            return self
        else:
            raise Exception("Failed to connect to SFTP server")

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()

# Example usage
if __name__ == "__main__":
    # Example configuration (replace with your actual SFTP server details)
    SFTP_CONFIG = {
        "hostname": "your-sftp-server.com",
        "port": 22,
        "username": "your-username",
        "password": "your-password",  # or use private_key_path instead
        # "private_key_path": "/path/to/your/private/key"
    }
    
    # Using context manager (recommended)
    try:
        with SFTPManager(**SFTP_CONFIG) as sftp:
            # List remote directory
            files = sftp.list_directory("/")
            print(f"Remote files: {len(files)}")
            for file in files[:5]:  # Show first 5 files
                print(f"  {file['name']} - {file['size']} bytes")
            
            # Example file operations (uncomment to test)
            # sftp.upload_file("/local/path/file.txt", "/remote/path/file.txt")
            # sftp.download_file("/remote/path/file.txt", "/local/path/downloaded_file.txt")
            # sftp.create_directory("/remote/new_directory")
            
    except Exception as e:
        print(f"SFTP operation failed: {e}")
    
    # Manual connection management
    # sftp_manager = SFTPManager(**SFTP_CONFIG)
    # if sftp_manager.connect():
    #     print("Connected to SFTP server")
    #     # Perform operations...
    #     sftp_manager.disconnect()
    # else:
    #     print("Failed to connect to SFTP server")

