import os
import hashlib
import shutil
import json
from datetime import datetime
from pathlib import Path
from cryptography.fernet import Fernet
from PIL import Image, ImageDraw, ImageFont
import sqlite3

class EnhancedFileManager:
    def __init__(self, base_path='/home/ubuntu/sstdms_files'):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        self.encryption_key = self._get_or_create_encryption_key()
        
    def _get_or_create_encryption_key(self):
        """Get or create encryption key for file encryption"""
        key_file = self.base_path / '.encryption_key'
        if key_file.exists():
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)  # Restrict access
            return key
    
    def create_project_structure(self, project_id):
        """Create standardized folder structure for a project"""
        project_path = self.base_path / project_id
        
        folders = [
            'drawings/COMMON',
            'drawings/HULL', 
            'drawings/ACCOMMODATION',
            'drawings/OUTFITTING',
            'drawings/PIPING',
            'drawings/ELECTRICAL',
            'documents/specifications',
            'documents/calculations',
            'documents/reports',
            'documents/correspondence',
            'exports/pdf',
            'exports/excel',
            'exports/gantt',
            'backups',
            'temp'
        ]
        
        created_folders = []
        for folder in folders:
            folder_path = project_path / folder
            folder_path.mkdir(parents=True, exist_ok=True)
            created_folders.append({
                'path': str(folder_path),
                'type': folder.split('/')[0],
                'name': folder.split('/')[-1],
                'relative_path': folder
            })
        
        return created_folders
    
    def get_file_hash(self, file_path):
        """Calculate SHA-256 hash of a file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def encrypt_file(self, file_path, output_path=None):
        """Encrypt a file using Fernet encryption"""
        if output_path is None:
            output_path = file_path + '.encrypted'
        
        fernet = Fernet(self.encryption_key)
        
        with open(file_path, 'rb') as file:
            file_data = file.read()
        
        encrypted_data = fernet.encrypt(file_data)
        
        with open(output_path, 'wb') as file:
            file.write(encrypted_data)
        
        return output_path
    
    def decrypt_file(self, encrypted_file_path, output_path=None):
        """Decrypt a file using Fernet encryption"""
        if output_path is None:
            output_path = encrypted_file_path.replace('.encrypted', '')
        
        fernet = Fernet(self.encryption_key)
        
        with open(encrypted_file_path, 'rb') as file:
            encrypted_data = file.read()
        
        decrypted_data = fernet.decrypt(encrypted_data)
        
        with open(output_path, 'wb') as file:
            file.write(decrypted_data)
        
        return output_path
    
    def apply_watermark(self, image_path, watermark_text="SEASTAR DESIGN", output_path=None):
        """Apply watermark to an image file"""
        if output_path is None:
            name, ext = os.path.splitext(image_path)
            output_path = f"{name}_watermarked{ext}"
        
        try:
            with Image.open(image_path) as img:
                # Convert to RGBA if not already
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # Create watermark overlay
                overlay = Image.new('RGBA', img.size, (255, 255, 255, 0))
                draw = ImageDraw.Draw(overlay)
                
                # Try to use a font, fallback to default if not available
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
                except:
                    font = ImageFont.load_default()
                
                # Calculate text size and position
                bbox = draw.textbbox((0, 0), watermark_text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                # Position watermark in bottom right
                x = img.width - text_width - 20
                y = img.height - text_height - 20
                
                # Draw watermark with transparency
                draw.text((x, y), watermark_text, font=font, fill=(255, 255, 255, 128))
                
                # Combine original image with watermark
                watermarked = Image.alpha_composite(img, overlay)
                
                # Convert back to RGB if needed
                if watermarked.mode == 'RGBA':
                    watermarked = watermarked.convert('RGB')
                
                watermarked.save(output_path)
                return output_path
        except Exception as e:
            print(f"Error applying watermark: {e}")
            return image_path
    
    def create_backup(self, file_path, backup_dir=None):
        """Create a backup of a file with timestamp"""
        if backup_dir is None:
            backup_dir = self.base_path / 'backups'
        
        backup_dir = Path(backup_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = Path(file_path)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        backup_path = backup_dir / backup_name
        
        shutil.copy2(file_path, backup_path)
        return str(backup_path)
    
    def get_file_metadata(self, file_path):
        """Extract metadata from a file"""
        file_path = Path(file_path)
        stat = file_path.stat()
        
        metadata = {
            'size': stat.st_size,
            'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'accessed': datetime.fromtimestamp(stat.st_atime).isoformat(),
            'hash': self.get_file_hash(file_path),
            'extension': file_path.suffix.lower(),
            'mime_type': self._get_mime_type(file_path.suffix)
        }
        
        # Add image-specific metadata if it's an image
        if metadata['mime_type'].startswith('image/'):
            try:
                with Image.open(file_path) as img:
                    metadata.update({
                        'width': img.width,
                        'height': img.height,
                        'format': img.format,
                        'mode': img.mode
                    })
            except:
                pass
        
        return metadata
    
    def _get_mime_type(self, extension):
        """Get MIME type based on file extension"""
        mime_types = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xls': 'application/vnd.ms-excel',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.ppt': 'application/vnd.ms-powerpoint',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.tiff': 'image/tiff',
            '.dwg': 'application/acad',
            '.dxf': 'application/dxf',
            '.txt': 'text/plain',
            '.csv': 'text/csv',
            '.zip': 'application/zip',
            '.rar': 'application/x-rar-compressed'
        }
        return mime_types.get(extension.lower(), 'application/octet-stream')
    
    def check_permissions(self, user_id, file_path, action='read'):
        """Check if user has permission to perform action on file"""
        # This would integrate with the database permission system
        # For now, return True for admin users
        conn = sqlite3.connect('database/app.db')
        cursor = conn.cursor()
        
        user = cursor.execute('SELECT role FROM users WHERE id = ?', (user_id,)).fetchone()
        conn.close()
        
        if user and user[0] == 'admin':
            return True
        
        # Add more sophisticated permission checking here
        return True
    
    def log_file_access(self, file_id, user_id, action, ip_address=None, user_agent=None, success=True, error_message=None):
        """Log file access for audit purposes"""
        conn = sqlite3.connect('database/app.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO file_access_logs 
            (file_id, user_id, action, ip_address, user_agent, success, error_message, accessed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            file_id, user_id, action, ip_address, user_agent, 
            success, error_message, datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def cleanup_temp_files(self, max_age_hours=24):
        """Clean up temporary files older than specified hours"""
        temp_dir = self.base_path / 'temp'
        if not temp_dir.exists():
            return
        
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        
        for file_path in temp_dir.rglob('*'):
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                except:
                    pass
    
    def get_storage_usage(self, project_id=None):
        """Get storage usage statistics"""
        if project_id:
            base_dir = self.base_path / project_id
        else:
            base_dir = self.base_path
        
        if not base_dir.exists():
            return {'total_size': 0, 'file_count': 0}
        
        total_size = 0
        file_count = 0
        
        for file_path in base_dir.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
                file_count += 1
        
        return {
            'total_size': total_size,
            'file_count': file_count,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'total_size_gb': round(total_size / (1024 * 1024 * 1024), 2)
        }

