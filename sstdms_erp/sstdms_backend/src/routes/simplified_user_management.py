from flask import Blueprint, request, jsonify, session
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash

simplified_user_bp = Blueprint('simplified_user', __name__)

def get_db_connection():
    conn = sqlite3.connect('database/app.db')
    conn.row_factory = sqlite3.Row
    return conn

@simplified_user_bp.route('/api/users/simplified', methods=['GET'])
def get_all_users():
    """Get all users with simplified role structure"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    current_user = conn.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    if current_user['role'] != 'admin':
        conn.close()
        return jsonify({'error': 'Only administrators can view all users'}), 403
    
    users = conn.execute('''
        SELECT id, username, email, full_name, position, phone, role, is_active, 
               password_change_required, created_at, updated_at
        FROM users 
        ORDER BY role DESC, full_name
    ''').fetchall()
    conn.close()
    
    return jsonify([dict(user) for user in users])

@simplified_user_bp.route('/api/users/project-permissions/<project_id>', methods=['GET'])
def get_project_user_permissions(project_id):
    """Get users and their permissions for a specific project"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    current_user = conn.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    if current_user['role'] != 'admin':
        conn.close()
        return jsonify({'error': 'Only administrators can view project permissions'}), 403
    
    # Get all users with their project permissions
    users_with_permissions = conn.execute('''
        SELECT u.id, u.username, u.email, u.full_name, u.role,
               pp.permission_type, pp.granted_at
        FROM users u
        LEFT JOIN project_permissions pp ON u.id = pp.user_id AND pp.project_id = ?
        WHERE u.role != 'admin'
        ORDER BY u.full_name
    ''', (project_id,)).fetchall()
    
    conn.close()
    
    return jsonify([dict(user) for user in users_with_permissions])

@simplified_user_bp.route('/api/users/project-permissions/<project_id>', methods=['POST'])
def set_project_permissions(project_id):
    """Set project permissions for users"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    current_user = conn.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    if current_user['role'] != 'admin':
        conn.close()
        return jsonify({'error': 'Only administrators can set project permissions'}), 403
    
    data = request.get_json()
    user_permissions = data.get('user_permissions', [])
    
    try:
        # Clear existing permissions for this project
        conn.execute('DELETE FROM project_permissions WHERE project_id = ?', (project_id,))
        
        # Add new permissions
        for user_perm in user_permissions:
            if user_perm.get('has_access'):
                conn.execute('''
                    INSERT INTO project_permissions 
                    (project_id, user_id, permission_type, granted_by, granted_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    project_id,
                    user_perm['user_id'],
                    'full_access',  # Simplified: users either have full access or no access
                    session['user_id'],
                    datetime.now().isoformat()
                ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Project permissions updated successfully'})
        
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

@simplified_user_bp.route('/api/users/register', methods=['POST'])
def register_user():
    """Register a new user (admin only)"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    current_user = conn.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    if current_user['role'] != 'admin':
        conn.close()
        return jsonify({'error': 'Only administrators can register new users'}), 403
    
    data = request.get_json()
    required_fields = ['username', 'email', 'full_name', 'password']
    
    for field in required_fields:
        if field not in data:
            conn.close()
            return jsonify({'error': f'Missing field: {field}'}), 400
    
    # Check if username or email already exists
    existing_user = conn.execute('''
        SELECT id FROM users WHERE username = ? OR email = ?
    ''', (data['username'], data['email'])).fetchone()
    
    if existing_user:
        conn.close()
        return jsonify({'error': 'Username or email already exists'}), 400
    
    try:
        password_hash = generate_password_hash(data['password'])
        
        conn.execute('''
            INSERT INTO users 
            (username, email, password_hash, full_name, position, phone, role, 
             is_active, password_change_required, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['username'],
            data['email'],
            password_hash,
            data['full_name'],
            data.get('position', ''),
            data.get('phone', ''),
            'user',  # All new users are 'user' role by default
            True,
            True,  # Require password change on first login
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'User registered successfully'}), 201
        
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

@simplified_user_bp.route('/api/users/<int:user_id>/toggle-active', methods=['POST'])
def toggle_user_active(user_id):
    """Toggle user active status (admin only)"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    current_user = conn.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    if current_user['role'] != 'admin':
        conn.close()
        return jsonify({'error': 'Only administrators can toggle user status'}), 403
    
    # Don't allow deactivating admin users
    target_user = conn.execute('SELECT role, is_active FROM users WHERE id = ?', (user_id,)).fetchone()
    
    if not target_user:
        conn.close()
        return jsonify({'error': 'User not found'}), 404
    
    if target_user['role'] == 'admin':
        conn.close()
        return jsonify({'error': 'Cannot deactivate admin users'}), 400
    
    new_status = not target_user['is_active']
    
    conn.execute('''
        UPDATE users SET is_active = ?, updated_at = ? WHERE id = ?
    ''', (new_status, datetime.now().isoformat(), user_id))
    
    conn.commit()
    conn.close()
    
    status_text = 'activated' if new_status else 'deactivated'
    return jsonify({'message': f'User {status_text} successfully'})

@simplified_user_bp.route('/api/users/<int:user_id>/reset-password', methods=['POST'])
def reset_user_password(user_id):
    """Reset user password (admin only)"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    current_user = conn.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    if current_user['role'] != 'admin':
        conn.close()
        return jsonify({'error': 'Only administrators can reset passwords'}), 403
    
    data = request.get_json()
    new_password = data.get('new_password', '1234')  # Default password
    
    password_hash = generate_password_hash(new_password)
    
    conn.execute('''
        UPDATE users 
        SET password_hash = ?, password_change_required = ?, updated_at = ?
        WHERE id = ?
    ''', (password_hash, True, datetime.now().isoformat(), user_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Password reset successfully'})

@simplified_user_bp.route('/api/users/my-projects', methods=['GET'])
def get_my_projects():
    """Get projects that the current user has access to"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    current_user = conn.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    if current_user['role'] == 'admin':
        # Admin can see all projects
        projects = conn.execute('''
            SELECT p.*, u.full_name as created_by_name
            FROM projects p
            LEFT JOIN users u ON p.created_by = u.id
            ORDER BY p.created_at DESC
        ''').fetchall()
    else:
        # Regular users can only see projects they have permission for
        projects = conn.execute('''
            SELECT p.*, u.full_name as created_by_name, pp.permission_type
            FROM projects p
            LEFT JOIN users u ON p.created_by = u.id
            INNER JOIN project_permissions pp ON p.id = pp.project_id
            WHERE pp.user_id = ?
            ORDER BY p.created_at DESC
        ''', (session['user_id'],)).fetchall()
    
    conn.close()
    
    return jsonify([dict(project) for project in projects])

@simplified_user_bp.route('/api/users/check-project-access/<project_id>', methods=['GET'])
def check_project_access(project_id):
    """Check if current user has access to a project"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    current_user = conn.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    if current_user['role'] == 'admin':
        # Admin has access to all projects
        has_access = True
        permission_type = 'admin'
    else:
        # Check if user has permission for this project
        permission = conn.execute('''
            SELECT permission_type FROM project_permissions 
            WHERE project_id = ? AND user_id = ?
        ''', (project_id, session['user_id'])).fetchone()
        
        has_access = permission is not None
        permission_type = permission['permission_type'] if permission else None
    
    conn.close()
    
    return jsonify({
        'has_access': has_access,
        'permission_type': permission_type,
        'user_role': current_user['role']
    })

