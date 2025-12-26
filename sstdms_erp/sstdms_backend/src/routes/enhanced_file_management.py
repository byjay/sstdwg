from flask import Blueprint, request, jsonify, session, send_file, abort
import sqlite3
import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from utils.file_manager import EnhancedFileManager

enhanced_file_bp = Blueprint('enhanced_file', __name__)
file_manager = EnhancedFileManager()

def get_db_connection():
    conn = sqlite3.connect('database/app.db')
    conn.row_factory = sqlite3.Row
    return conn

@enhanced_file_bp.route('/api/projects/<project_id>/folders/init', methods=['POST'])
def initialize_project_folders(project_id):
    """Initialize folder structure for a project"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    user = conn.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    if user['role'] != 'admin':
        conn.close()
        return jsonify({'error': 'Only administrators can initialize project folders'}), 403
    
    try:
        # Create physical folder structure
        created_folders = file_manager.create_project_structure(project_id)
        
        # Create folder records in database
        for folder_info in created_folders:
            conn.execute('''
                INSERT OR IGNORE INTO project_folders_enhanced 
                (project_id, folder_name, folder_type, folder_path, created_by, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                project_id,
                folder_info['name'],
                folder_info['type'],
                folder_info['relative_path'],
                session['user_id'],
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': 'Project folders initialized successfully',
            'folders': created_folders
        }), 201
        
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

@enhanced_file_bp.route('/api/projects/<project_id>/folders', methods=['GET'])
def get_project_folders(project_id):
    """Get folder structure for a project"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    folders = conn.execute('''
        SELECT pf.*, u.full_name as created_by_name
        FROM project_folders_enhanced pf
        LEFT JOIN users u ON pf.created_by = u.id
        WHERE pf.project_id = ?
        ORDER BY pf.folder_type, pf.folder_name
    ''', (project_id,)).fetchall()
    conn.close()
    
    return jsonify([dict(folder) for folder in folders])

@enhanced_file_bp.route('/api/projects/<project_id>/files/upload', methods=['POST'])
def upload_file(project_id):
    """Upload a file to a project folder"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    folder_id = request.form.get('folder_id')
    access_level = request.form.get('access_level', 'project')
    encrypt_file = request.form.get('encrypt', 'false').lower() == 'true'
    apply_watermark = request.form.get('watermark', 'false').lower() == 'true'
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not folder_id:
        return jsonify({'error': 'Folder ID required'}), 400
    
    conn = get_db_connection()
    
    # Get folder information
    folder = conn.execute('''
        SELECT * FROM project_folders_enhanced WHERE id = ? AND project_id = ?
    ''', (folder_id, project_id)).fetchone()
    
    if not folder:
        conn.close()
        return jsonify({'error': 'Folder not found'}), 404
    
    try:
        # Secure filename
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        
        # Create file path
        project_path = file_manager.base_path / project_id / folder['folder_path']
        project_path.mkdir(parents=True, exist_ok=True)
        file_path = project_path / unique_filename
        
        # Save file
        file.save(str(file_path))
        
        # Get file metadata
        metadata = file_manager.get_file_metadata(file_path)
        
        # Apply encryption if requested
        if encrypt_file:
            encrypted_path = file_manager.encrypt_file(str(file_path))
            os.remove(str(file_path))  # Remove original
            file_path = encrypted_path
            unique_filename += '.encrypted'
        
        # Apply watermark if requested and file is an image
        if apply_watermark and metadata['mime_type'].startswith('image/'):
            watermarked_path = file_manager.apply_watermark(str(file_path))
            if watermarked_path != str(file_path):
                os.remove(str(file_path))  # Remove original
                file_path = watermarked_path
                unique_filename = unique_filename.replace('.', '_watermarked.')
        
        # Create backup
        backup_path = file_manager.create_backup(file_path)
        
        # Save file record to database
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO project_files_enhanced 
            (project_id, folder_id, file_name, original_name, file_path, file_size, 
             file_type, mime_type, file_hash, is_encrypted, watermark_applied, 
             access_level, metadata, created_by, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            project_id, folder_id, unique_filename, filename, str(file_path),
            metadata['size'], os.path.splitext(filename)[1], metadata['mime_type'],
            metadata['hash'], encrypt_file, apply_watermark, access_level,
            json.dumps(metadata), session['user_id'], 
            datetime.now().isoformat(), datetime.now().isoformat()
        ))
        
        file_id = cursor.lastrowid
        conn.commit()
        
        # Log file upload
        file_manager.log_file_access(
            file_id, session['user_id'], 'upload',
            request.remote_addr, request.headers.get('User-Agent')
        )
        
        conn.close()
        
        return jsonify({
            'message': 'File uploaded successfully',
            'file_id': file_id,
            'filename': unique_filename,
            'size': metadata['size'],
            'backup_path': backup_path
        }), 201
        
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

@enhanced_file_bp.route('/api/projects/<project_id>/files', methods=['GET'])
def get_project_files(project_id):
    """Get files for a project"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    folder_id = request.args.get('folder_id')
    
    conn = get_db_connection()
    
    query = '''
        SELECT pf.*, u.full_name as created_by_name, folder.folder_name
        FROM project_files_enhanced pf
        LEFT JOIN users u ON pf.created_by = u.id
        LEFT JOIN project_folders_enhanced folder ON pf.folder_id = folder.id
        WHERE pf.project_id = ?
    '''
    params = [project_id]
    
    if folder_id:
        query += ' AND pf.folder_id = ?'
        params.append(folder_id)
    
    query += ' ORDER BY pf.created_at DESC'
    
    files = conn.execute(query, params).fetchall()
    conn.close()
    
    return jsonify([dict(file) for file in files])

@enhanced_file_bp.route('/api/files/<int:file_id>/download', methods=['GET'])
def download_file(file_id):
    """Download a file"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    file_record = conn.execute('''
        SELECT * FROM project_files_enhanced WHERE id = ?
    ''', (file_id,)).fetchone()
    
    if not file_record:
        conn.close()
        return jsonify({'error': 'File not found'}), 404
    
    # Check permissions
    if not file_manager.check_permissions(session['user_id'], file_record['file_path'], 'read'):
        conn.close()
        return jsonify({'error': 'Permission denied'}), 403
    
    try:
        file_path = file_record['file_path']
        
        # Decrypt if necessary
        if file_record['is_encrypted']:
            temp_path = file_manager.base_path / 'temp' / f"temp_{file_id}_{file_record['original_name']}"
            temp_path.parent.mkdir(exist_ok=True)
            file_path = file_manager.decrypt_file(file_record['file_path'], str(temp_path))
        
        # Update download count and last accessed
        conn.execute('''
            UPDATE project_files_enhanced 
            SET download_count = download_count + 1, last_accessed = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), file_id))
        conn.commit()
        
        # Log file access
        file_manager.log_file_access(
            file_id, session['user_id'], 'download',
            request.remote_addr, request.headers.get('User-Agent')
        )
        
        conn.close()
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=file_record['original_name']
        )
        
    except Exception as e:
        conn.close()
        file_manager.log_file_access(
            file_id, session['user_id'], 'download',
            request.remote_addr, request.headers.get('User-Agent'),
            success=False, error_message=str(e)
        )
        return jsonify({'error': str(e)}), 500

@enhanced_file_bp.route('/api/files/<int:file_id>/versions', methods=['GET'])
def get_file_versions(file_id):
    """Get version history of a file"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    versions = conn.execute('''
        SELECT fv.*, u.full_name as created_by_name
        FROM file_versions fv
        LEFT JOIN users u ON fv.created_by = u.id
        WHERE fv.file_id = ?
        ORDER BY fv.created_at DESC
    ''', (file_id,)).fetchall()
    conn.close()
    
    return jsonify([dict(version) for version in versions])

@enhanced_file_bp.route('/api/projects/<project_id>/storage', methods=['GET'])
def get_storage_usage(project_id):
    """Get storage usage for a project"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    usage = file_manager.get_storage_usage(project_id)
    
    # Get file count by type
    conn = get_db_connection()
    file_types = conn.execute('''
        SELECT file_type, COUNT(*) as count, SUM(file_size) as total_size
        FROM project_files_enhanced
        WHERE project_id = ?
        GROUP BY file_type
        ORDER BY total_size DESC
    ''', (project_id,)).fetchall()
    conn.close()
    
    usage['file_types'] = [dict(ft) for ft in file_types]
    
    return jsonify(usage)

@enhanced_file_bp.route('/api/files/<int:file_id>/permissions', methods=['GET', 'POST'])
def manage_file_permissions(file_id):
    """Get or set file permissions"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    user = conn.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    if user['role'] != 'admin':
        conn.close()
        return jsonify({'error': 'Only administrators can manage permissions'}), 403
    
    if request.method == 'GET':
        permissions = conn.execute('''
            SELECT fp.*, u.full_name as user_name
            FROM file_permissions_enhanced fp
            LEFT JOIN users u ON fp.user_id = u.id
            WHERE fp.file_id = ?
        ''', (file_id,)).fetchall()
        conn.close()
        return jsonify([dict(perm) for perm in permissions])
    
    elif request.method == 'POST':
        data = request.get_json()
        
        conn.execute('''
            INSERT OR REPLACE INTO file_permissions_enhanced
            (file_id, user_id, role, permission_type, granted_by, granted_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            file_id, data.get('user_id'), data.get('role'), data['permission_type'],
            session['user_id'], datetime.now().isoformat(), data.get('expires_at')
        ))
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Permission updated successfully'})

@enhanced_file_bp.route('/api/files/cleanup', methods=['POST'])
def cleanup_temp_files():
    """Clean up temporary files"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    user = conn.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    
    if user['role'] != 'admin':
        return jsonify({'error': 'Only administrators can perform cleanup'}), 403
    
    max_age_hours = request.json.get('max_age_hours', 24)
    file_manager.cleanup_temp_files(max_age_hours)
    
    return jsonify({'message': 'Cleanup completed successfully'})

