from flask import Blueprint, request, jsonify, session, send_file
import sqlite3
import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from werkzeug.utils import secure_filename

local_storage_bp = Blueprint('local_storage', __name__)

def get_db_connection():
    conn = sqlite3.connect('database/app.db')
    conn.row_factory = sqlite3.Row
    return conn

# Default storage settings
DEFAULT_STORAGE_CONFIG = {
    'base_path': '/home/ubuntu/sstdms_files',
    'use_network_path': False,
    'network_path': '',
    'auto_backup': True,
    'backup_retention_days': 30
}

def get_storage_config():
    """Get current storage configuration"""
    config_file = Path('config/storage_config.json')
    if config_file.exists():
        with open(config_file, 'r') as f:
            return json.load(f)
    return DEFAULT_STORAGE_CONFIG

def save_storage_config(config):
    """Save storage configuration"""
    config_dir = Path('config')
    config_dir.mkdir(exist_ok=True)
    
    config_file = config_dir / 'storage_config.json'
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)

@local_storage_bp.route('/api/storage/config', methods=['GET'])
def get_storage_configuration():
    """Get current storage configuration"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    user = conn.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    
    if user['role'] != 'admin':
        return jsonify({'error': 'Only administrators can view storage configuration'}), 403
    
    config = get_storage_config()
    
    # Add storage usage information
    try:
        base_path = Path(config['base_path'])
        if base_path.exists():
            total_size = sum(f.stat().st_size for f in base_path.rglob('*') if f.is_file())
            file_count = sum(1 for f in base_path.rglob('*') if f.is_file())
            
            config['usage'] = {
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'total_size_gb': round(total_size / (1024 * 1024 * 1024), 2),
                'file_count': file_count
            }
        else:
            config['usage'] = {
                'total_size_bytes': 0,
                'total_size_mb': 0,
                'total_size_gb': 0,
                'file_count': 0
            }
    except Exception as e:
        config['usage'] = {'error': str(e)}
    
    return jsonify(config)

@local_storage_bp.route('/api/storage/config', methods=['POST'])
def update_storage_configuration():
    """Update storage configuration"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    user = conn.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    
    if user['role'] != 'admin':
        return jsonify({'error': 'Only administrators can update storage configuration'}), 403
    
    data = request.get_json()
    
    # Validate the new configuration
    if 'base_path' not in data:
        return jsonify({'error': 'base_path is required'}), 400
    
    # Test if the path is accessible
    try:
        test_path = Path(data['base_path'])
        test_path.mkdir(parents=True, exist_ok=True)
        
        # Test write permissions
        test_file = test_path / 'test_write.tmp'
        test_file.write_text('test')
        test_file.unlink()
        
    except Exception as e:
        return jsonify({'error': f'Cannot access storage path: {str(e)}'}), 400
    
    # Save the new configuration
    config = get_storage_config()
    config.update(data)
    save_storage_config(config)
    
    return jsonify({'message': 'Storage configuration updated successfully'})

@local_storage_bp.route('/api/storage/browse', methods=['POST'])
def browse_local_folders():
    """Browse local folders for storage path selection"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    user = conn.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    
    if user['role'] != 'admin':
        return jsonify({'error': 'Only administrators can browse folders'}), 403
    
    data = request.get_json()
    current_path = data.get('path', '/home/ubuntu')
    
    try:
        path = Path(current_path)
        if not path.exists() or not path.is_dir():
            return jsonify({'error': 'Invalid path'}), 400
        
        folders = []
        files = []
        
        # Add parent directory option
        if path.parent != path:
            folders.append({
                'name': '..',
                'path': str(path.parent),
                'type': 'directory',
                'size': 0,
                'modified': ''
            })
        
        # List directories and files
        for item in sorted(path.iterdir()):
            try:
                stat = item.stat()
                item_info = {
                    'name': item.name,
                    'path': str(item),
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                }
                
                if item.is_dir():
                    item_info['type'] = 'directory'
                    folders.append(item_info)
                else:
                    item_info['type'] = 'file'
                    files.append(item_info)
            except (PermissionError, OSError):
                # Skip items we can't access
                continue
        
        return jsonify({
            'current_path': str(path),
            'folders': folders,
            'files': files[:50]  # Limit files shown
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@local_storage_bp.route('/api/storage/create-folder', methods=['POST'])
def create_storage_folder():
    """Create a new folder in the storage location"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    user = conn.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    
    if user['role'] != 'admin':
        return jsonify({'error': 'Only administrators can create folders'}), 403
    
    data = request.get_json()
    parent_path = data.get('parent_path')
    folder_name = data.get('folder_name')
    
    if not parent_path or not folder_name:
        return jsonify({'error': 'parent_path and folder_name are required'}), 400
    
    try:
        # Sanitize folder name
        safe_folder_name = secure_filename(folder_name)
        if not safe_folder_name:
            return jsonify({'error': 'Invalid folder name'}), 400
        
        new_folder_path = Path(parent_path) / safe_folder_name
        new_folder_path.mkdir(parents=True, exist_ok=True)
        
        return jsonify({
            'message': 'Folder created successfully',
            'path': str(new_folder_path)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@local_storage_bp.route('/api/storage/projects/<project_id>/init', methods=['POST'])
def initialize_project_storage(project_id):
    """Initialize storage structure for a project"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Check if user has access to this project
    conn = get_db_connection()
    user = conn.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    if user['role'] != 'admin':
        # Check project permission
        permission = conn.execute('''
            SELECT permission_type FROM project_permissions 
            WHERE project_id = ? AND user_id = ?
        ''', (project_id, session['user_id'])).fetchone()
        
        if not permission:
            conn.close()
            return jsonify({'error': 'No permission for this project'}), 403
    
    conn.close()
    
    try:
        config = get_storage_config()
        base_path = Path(config['base_path'])
        project_path = base_path / project_id
        
        # Create project folder structure
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
            'backups'
        ]
        
        created_folders = []
        for folder in folders:
            folder_path = project_path / folder
            folder_path.mkdir(parents=True, exist_ok=True)
            created_folders.append(str(folder_path))
        
        return jsonify({
            'message': 'Project storage initialized successfully',
            'project_path': str(project_path),
            'folders': created_folders
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@local_storage_bp.route('/api/storage/projects/<project_id>/upload', methods=['POST'])
def upload_file_to_project(project_id):
    """Upload a file to project storage"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    folder_type = request.form.get('folder_type', 'documents')
    subfolder = request.form.get('subfolder', '')
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Check project access
    conn = get_db_connection()
    user = conn.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    if user['role'] != 'admin':
        permission = conn.execute('''
            SELECT permission_type FROM project_permissions 
            WHERE project_id = ? AND user_id = ?
        ''', (project_id, session['user_id'])).fetchone()
        
        if not permission:
            conn.close()
            return jsonify({'error': 'No permission for this project'}), 403
    
    try:
        config = get_storage_config()
        base_path = Path(config['base_path'])
        
        # Determine upload path
        if subfolder:
            upload_path = base_path / project_id / folder_type / subfolder
        else:
            upload_path = base_path / project_id / folder_type
        
        upload_path.mkdir(parents=True, exist_ok=True)
        
        # Secure filename with timestamp
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        file_path = upload_path / unique_filename
        
        # Save file
        file.save(str(file_path))
        
        # Get file info
        file_stat = file_path.stat()
        
        # Create backup if enabled
        backup_path = None
        if config.get('auto_backup', True):
            backup_dir = base_path / project_id / 'backups'
            backup_dir.mkdir(exist_ok=True)
            backup_path = backup_dir / unique_filename
            shutil.copy2(file_path, backup_path)
        
        # Record in database
        conn.execute('''
            INSERT INTO project_files_enhanced 
            (project_id, folder_id, file_name, original_name, file_path, file_size, 
             file_type, created_by, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            project_id, 0, unique_filename, filename, str(file_path),
            file_stat.st_size, os.path.splitext(filename)[1],
            session['user_id'], datetime.now().isoformat(), datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': 'File uploaded successfully',
            'filename': unique_filename,
            'path': str(file_path),
            'size': file_stat.st_size,
            'backup_path': str(backup_path) if backup_path else None
        })
        
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

@local_storage_bp.route('/api/storage/projects/<project_id>/files', methods=['GET'])
def list_project_files(project_id):
    """List files in project storage"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    folder_type = request.args.get('folder_type', '')
    subfolder = request.args.get('subfolder', '')
    
    # Check project access
    conn = get_db_connection()
    user = conn.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    if user['role'] != 'admin':
        permission = conn.execute('''
            SELECT permission_type FROM project_permissions 
            WHERE project_id = ? AND user_id = ?
        ''', (project_id, session['user_id'])).fetchone()
        
        if not permission:
            conn.close()
            return jsonify({'error': 'No permission for this project'}), 403
    
    conn.close()
    
    try:
        config = get_storage_config()
        base_path = Path(config['base_path'])
        
        if folder_type:
            if subfolder:
                list_path = base_path / project_id / folder_type / subfolder
            else:
                list_path = base_path / project_id / folder_type
        else:
            list_path = base_path / project_id
        
        if not list_path.exists():
            return jsonify({'files': [], 'folders': []})
        
        files = []
        folders = []
        
        for item in sorted(list_path.iterdir()):
            try:
                stat = item.stat()
                item_info = {
                    'name': item.name,
                    'path': str(item.relative_to(base_path)),
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                }
                
                if item.is_dir():
                    item_info['type'] = 'directory'
                    folders.append(item_info)
                else:
                    item_info['type'] = 'file'
                    item_info['extension'] = item.suffix.lower()
                    files.append(item_info)
            except (PermissionError, OSError):
                continue
        
        return jsonify({
            'current_path': str(list_path.relative_to(base_path)),
            'files': files,
            'folders': folders
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@local_storage_bp.route('/api/storage/download', methods=['POST'])
def download_file():
    """Download a file from storage"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    file_path = data.get('file_path')
    
    if not file_path:
        return jsonify({'error': 'file_path is required'}), 400
    
    try:
        config = get_storage_config()
        base_path = Path(config['base_path'])
        full_path = base_path / file_path
        
        if not full_path.exists() or not full_path.is_file():
            return jsonify({'error': 'File not found'}), 404
        
        # Check if user has access to this project
        project_id = file_path.split('/')[0]
        
        conn = get_db_connection()
        user = conn.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        
        if user['role'] != 'admin':
            permission = conn.execute('''
                SELECT permission_type FROM project_permissions 
                WHERE project_id = ? AND user_id = ?
            ''', (project_id, session['user_id'])).fetchone()
            
            if not permission:
                conn.close()
                return jsonify({'error': 'No permission for this project'}), 403
        
        conn.close()
        
        return send_file(
            str(full_path),
            as_attachment=True,
            download_name=full_path.name
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

