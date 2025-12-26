# backup_manager.py

import os
import shutil
import sqlite3
import gzip
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import schedule
import time
import threading

class BackupManager:
    """Comprehensive backup management system for SSTDMS database."""
    
    def __init__(self, db_path: str = "./src/database/app.db", backup_dir: str = "./backups"):
        self.db_path = db_path
        self.backup_dir = backup_dir
        self.ensure_backup_directory()
        self.backup_metadata_file = os.path.join(backup_dir, "backup_metadata.json")
        self.load_metadata()
    
    def ensure_backup_directory(self):
        """Create backup directory if it doesn't exist."""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
            print(f"Created backup directory: {self.backup_dir}")
    
    def load_metadata(self):
        """Load backup metadata from file."""
        if os.path.exists(self.backup_metadata_file):
            try:
                with open(self.backup_metadata_file, 'r') as f:
                    self.metadata = json.load(f)
            except Exception as e:
                print(f"Error loading backup metadata: {e}")
                self.metadata = {"backups": []}
        else:
            self.metadata = {"backups": []}
    
    def save_metadata(self):
        """Save backup metadata to file."""
        try:
            with open(self.backup_metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            print(f"Error saving backup metadata: {e}")
    
    def create_backup(self, backup_type: str = "manual", compress: bool = True) -> Optional[str]:
        """Create a database backup."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"sstdms_backup_{timestamp}.db"
            
            if compress:
                backup_filename += ".gz"
            
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Create backup
            if compress:
                self._create_compressed_backup(backup_path)
            else:
                shutil.copy2(self.db_path, backup_path)
            
            # Get file size
            file_size = os.path.getsize(backup_path)
            
            # Update metadata
            backup_info = {
                "filename": backup_filename,
                "path": backup_path,
                "created_at": datetime.now().isoformat(),
                "type": backup_type,
                "size": file_size,
                "compressed": compress,
                "checksum": self._calculate_checksum(backup_path)
            }
            
            self.metadata["backups"].append(backup_info)
            self.save_metadata()
            
            print(f"Backup created successfully: {backup_path}")
            print(f"Backup size: {self._format_size(file_size)}")
            
            return backup_path
            
        except Exception as e:
            print(f"Backup creation failed: {str(e)}")
            return None
    
    def _create_compressed_backup(self, backup_path: str):
        """Create a compressed backup."""
        with open(self.db_path, 'rb') as f_in:
            with gzip.open(backup_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate MD5 checksum of a file."""
        import hashlib
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def restore_backup(self, backup_filename: str) -> bool:
        """Restore database from backup."""
        try:
            backup_info = self._get_backup_info(backup_filename)
            if not backup_info:
                print(f"Backup not found: {backup_filename}")
                return False
            
            backup_path = backup_info["path"]
            
            # Verify backup integrity
            if not self._verify_backup_integrity(backup_info):
                print("Backup integrity check failed")
                return False
            
            # Create a backup of current database before restore
            current_backup = self.create_backup("pre_restore")
            if not current_backup:
                print("Failed to create pre-restore backup")
                return False
            
            # Restore from backup
            if backup_info["compressed"]:
                self._restore_compressed_backup(backup_path)
            else:
                shutil.copy2(backup_path, self.db_path)
            
            print(f"Database restored successfully from: {backup_filename}")
            return True
            
        except Exception as e:
            print(f"Restore failed: {str(e)}")
            return False
    
    def _restore_compressed_backup(self, backup_path: str):
        """Restore from compressed backup."""
        with gzip.open(backup_path, 'rb') as f_in:
            with open(self.db_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
    
    def _get_backup_info(self, backup_filename: str) -> Optional[Dict]:
        """Get backup information by filename."""
        for backup in self.metadata["backups"]:
            if backup["filename"] == backup_filename:
                return backup
        return None
    
    def _verify_backup_integrity(self, backup_info: Dict) -> bool:
        """Verify backup file integrity using checksum."""
        try:
            current_checksum = self._calculate_checksum(backup_info["path"])
            return current_checksum == backup_info["checksum"]
        except Exception as e:
            print(f"Integrity check failed: {e}")
            return False
    
    def list_backups(self) -> List[Dict]:
        """List all available backups."""
        # Sort by creation date (newest first)
        backups = sorted(self.metadata["backups"], 
                        key=lambda x: x["created_at"], reverse=True)
        return backups
    
    def delete_backup(self, backup_filename: str) -> bool:
        """Delete a specific backup."""
        try:
            backup_info = self._get_backup_info(backup_filename)
            if not backup_info:
                print(f"Backup not found: {backup_filename}")
                return False
            
            # Remove file
            if os.path.exists(backup_info["path"]):
                os.remove(backup_info["path"])
            
            # Remove from metadata
            self.metadata["backups"] = [
                b for b in self.metadata["backups"] 
                if b["filename"] != backup_filename
            ]
            self.save_metadata()
            
            print(f"Backup deleted: {backup_filename}")
            return True
            
        except Exception as e:
            print(f"Failed to delete backup: {str(e)}")
            return False
    
    def cleanup_old_backups(self, keep_days: int = 30, keep_count: int = 10):
        """Clean up old backups based on age and count."""
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        backups = self.list_backups()
        
        deleted_count = 0
        
        # Keep the most recent backups regardless of age
        backups_to_keep = backups[:keep_count]
        backups_to_check = backups[keep_count:]
        
        for backup in backups_to_check:
            backup_date = datetime.fromisoformat(backup["created_at"])
            if backup_date < cutoff_date:
                if self.delete_backup(backup["filename"]):
                    deleted_count += 1
        
        print(f"Cleaned up {deleted_count} old backups")
        return deleted_count
    
    def get_backup_statistics(self) -> Dict:
        """Get backup statistics."""
        backups = self.metadata["backups"]
        
        if not backups:
            return {
                "total_backups": 0,
                "total_size": 0,
                "oldest_backup": None,
                "newest_backup": None,
                "backup_types": {}
            }
        
        total_size = sum(b["size"] for b in backups)
        backup_types = {}
        
        for backup in backups:
            backup_type = backup["type"]
            if backup_type not in backup_types:
                backup_types[backup_type] = 0
            backup_types[backup_type] += 1
        
        sorted_backups = sorted(backups, key=lambda x: x["created_at"])
        
        return {
            "total_backups": len(backups),
            "total_size": total_size,
            "total_size_formatted": self._format_size(total_size),
            "oldest_backup": sorted_backups[0]["created_at"],
            "newest_backup": sorted_backups[-1]["created_at"],
            "backup_types": backup_types
        }
    
    def setup_automatic_backups(self, interval_hours: int = 24):
        """Setup automatic backup scheduling."""
        def backup_job():
            print(f"Running automatic backup at {datetime.now()}")
            self.create_backup("automatic")
            self.cleanup_old_backups()
        
        # Schedule backup
        schedule.every(interval_hours).hours.do(backup_job)
        
        # Start scheduler in background thread
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        print(f"Automatic backups scheduled every {interval_hours} hours")
    
    def export_backup_report(self, output_file: str = None) -> str:
        """Export backup report to file."""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(self.backup_dir, f"backup_report_{timestamp}.txt")
        
        stats = self.get_backup_statistics()
        backups = self.list_backups()
        
        report_lines = [
            "SSTDMS Database Backup Report",
            "=" * 40,
            f"Generated: {datetime.now().isoformat()}",
            f"Database: {self.db_path}",
            f"Backup Directory: {self.backup_dir}",
            "",
            "Statistics:",
            f"  Total Backups: {stats['total_backups']}",
            f"  Total Size: {stats['total_size_formatted']}",
            f"  Oldest Backup: {stats['oldest_backup']}",
            f"  Newest Backup: {stats['newest_backup']}",
            "",
            "Backup Types:",
        ]
        
        for backup_type, count in stats['backup_types'].items():
            report_lines.append(f"  {backup_type}: {count}")
        
        report_lines.extend([
            "",
            "Backup List:",
            "-" * 20
        ])
        
        for backup in backups:
            report_lines.append(
                f"  {backup['filename']} - {backup['created_at']} - "
                f"{self._format_size(backup['size'])} - {backup['type']}"
            )
        
        report_content = "\n".join(report_lines)
        
        with open(output_file, 'w') as f:
            f.write(report_content)
        
        print(f"Backup report exported to: {output_file}")
        return output_file

# Example usage and testing
if __name__ == "__main__":
    # Initialize backup manager
    backup_manager = BackupManager()
    
    # Create a manual backup
    backup_path = backup_manager.create_backup("manual", compress=True)
    
    # List all backups
    backups = backup_manager.list_backups()
    print(f"\nAvailable backups: {len(backups)}")
    for backup in backups:
        print(f"  {backup['filename']} - {backup['created_at']} - {backup['type']}")
    
    # Get statistics
    stats = backup_manager.get_backup_statistics()
    print(f"\nBackup Statistics:")
    print(f"  Total: {stats['total_backups']}")
    print(f"  Size: {stats['total_size_formatted']}")
    
    # Export report
    report_file = backup_manager.export_backup_report()
    
    # Setup automatic backups (commented out for testing)
    # backup_manager.setup_automatic_backups(interval_hours=6)

