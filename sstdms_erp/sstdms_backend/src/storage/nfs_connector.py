# nfs_connector.py

import os
import subprocess
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class NFSConnector:
    """Manages NFS (Network File System) connections and operations."""
    
    def __init__(self):
        # Check if NFS client utilities are installed
        if not self._is_nfs_client_installed():
            logger.warning("NFS client utilities (nfs-common/nfs-utils) are not installed. NFS operations may fail.")

    def _is_nfs_client_installed(self) -> bool:
        """Check if NFS client utilities are installed."""
        try:
            subprocess.run(["which", "mount.nfs"], check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def mount_nfs_share(self, remote_host: str, remote_path: str, local_mount_point: str, options: Optional[List[str]] = None) -> bool:
        """Mounts a remote NFS share to a local directory."""
        if not os.path.exists(local_mount_point):
            try:
                os.makedirs(local_mount_point)
                logger.info(f"Created local mount point: {local_mount_point}")
            except OSError as e:
                logger.error(f"Failed to create local mount point {local_mount_point}: {e}")
                return False

        nfs_source = f"{remote_host}:{remote_path}"
        cmd = ["sudo", "mount", "-t", "nfs", nfs_source, local_mount_point]
        if options:
            cmd.extend(["-o", ",".join(options)])

        try:
            logger.info(f"Attempting to mount NFS share: {" ".join(cmd)}")
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"Successfully mounted {nfs_source} to {local_mount_point}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to mount NFS share {nfs_source} to {local_mount_point}. Error: {e.stderr.decode()}")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred during NFS mount: {e}")
            return False

    def unmount_nfs_share(self, local_mount_point: str) -> bool:
        """Unmounts a mounted NFS share."""
        cmd = ["sudo", "umount", local_mount_point]
        try:
            logger.info(f"Attempting to unmount NFS share: {" ".join(cmd)}")
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"Successfully unmounted {local_mount_point}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to unmount {local_mount_point}. Error: {e.stderr.decode()}")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred during NFS unmount: {e}")
            return False

    def is_mounted(self, local_mount_point: str) -> bool:
        """Checks if an NFS share is currently mounted at the given point."""
        try:
            output = subprocess.run(["mount"], check=True, capture_output=True, text=True).stdout
            return local_mount_point in output and "nfs" in output
        except subprocess.CalledProcessError:
            return False

    def list_mounted_nfs_shares(self) -> List[Dict[str, str]]:
        """Lists all currently mounted NFS shares."""
        mounted_shares = []
        try:
            output = subprocess.run(["mount", "-t", "nfs"], check=True, capture_output=True, text=True).stdout
            for line in output.splitlines():
                parts = line.split(" ")
                if len(parts) >= 3:
                    mounted_shares.append({
                        "source": parts[0],
                        "mount_point": parts[2]
                    })
        except subprocess.CalledProcessError:
            pass # No NFS shares mounted or mount command failed
        return mounted_shares

    def get_share_contents(self, mount_point: str) -> List[str]:
        """Lists the contents of a mounted NFS share."""
        if not self.is_mounted(mount_point):
            logger.warning(f"Share not mounted at {mount_point}")
            return []
        try:
            return os.listdir(mount_point)
        except OSError as e:
            logger.error(f"Error listing contents of {mount_point}: {e}")
            return []

# Example usage
if __name__ == "__main__":
    nfs_connector = NFSConnector()
    
    # Example: Mount an NFS share (replace with your actual NFS server details)
    # remote_host = "192.168.1.100"
    # remote_path = "/mnt/nfs_share"
    # local_mount_point = "/tmp/my_nfs_data"
    
    # if not nfs_connector.is_mounted(local_mount_point):
    #     print(f"Attempting to mount {remote_host}:{remote_path} to {local_mount_point}")
    #     if nfs_connector.mount_nfs_share(remote_host, remote_path, local_mount_point):
    #         print("NFS share mounted successfully.")
    #         print("Contents:", nfs_connector.get_share_contents(local_mount_point))
    #     else:
    #         print("Failed to mount NFS share.")
    # else:
    #     print(f"NFS share already mounted at {local_mount_point}")
    #     print("Contents:", nfs_connector.get_share_contents(local_mount_point))

    print("\nCurrently mounted NFS shares:")
    for share in nfs_connector.list_mounted_nfs_shares():
        print(f"  Source: {share["source"]}, Mount Point: {share["mount_point"]}")

    # Example: Unmount the NFS share
    # if nfs_connector.is_mounted(local_mount_point):
    #     print(f"\nAttempting to unmount {local_mount_point}")
    #     if nfs_connector.unmount_nfs_share(local_mount_point):
    #         print("NFS share unmounted successfully.")
    #     else:
    #         print("Failed to unmount NFS share.")

from typing import List # Added for List in mount_nfs_share options


