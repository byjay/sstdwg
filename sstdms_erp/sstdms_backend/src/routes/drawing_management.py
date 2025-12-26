from flask import Blueprint, request, jsonify, session
import sqlite3
from datetime import datetime
import json

drawing_bp = Blueprint('drawing', __name__)

def get_db_connection():
    conn = sqlite3.connect('database/app.db')
    conn.row_factory = sqlite3.Row
    return conn

@drawing_bp.route('/api/drawings/<project_id>', methods=['GET'])
def get_project_drawings(project_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    drawings = conn.execute('''
        SELECT d.*, u.full_name as assigned_name
        FROM drawings d
        LEFT JOIN users u ON d.assigned_to = u.id
        WHERE d.project_id = ?
        ORDER BY d.category, d.dwg_no
    ''', (project_id,)).fetchall()
    conn.close()
    
    return jsonify([dict(drawing) for drawing in drawings])

@drawing_bp.route('/api/drawings', methods=['POST'])
def create_drawing():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    required_fields = ['project_id', 'category', 'dwg_no', 'name', 'type', 'start_date', 'end_date']
    
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400
    
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO drawings 
            (project_id, category, dwg_no, name, type, start_date, end_date, progress, status, created_by, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['project_id'],
            data['category'],
            data['dwg_no'],
            data['name'],
            data['type'],
            data['start_date'],
            data['end_date'],
            data.get('progress', 0),
            data.get('status', 'planned'),
            session['user_id'],
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        conn.commit()
        return jsonify({'message': 'Drawing created successfully'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Drawing number already exists'}), 400
    finally:
        conn.close()

@drawing_bp.route('/api/drawings/<int:drawing_id>', methods=['PUT'])
def update_drawing(drawing_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    
    # Check if user has permission to edit
    conn = get_db_connection()
    user = conn.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    if user['role'] != 'admin':
        # Check if user is assigned to this drawing or is project member
        drawing = conn.execute('SELECT assigned_to FROM drawings WHERE id = ?', (drawing_id,)).fetchone()
        if not drawing or (drawing['assigned_to'] != session['user_id']):
            conn.close()
            return jsonify({'error': 'Permission denied'}), 403
    
    # Update drawing
    update_fields = []
    values = []
    
    allowed_fields = ['category', 'name', 'type', 'start_date', 'end_date', 'progress', 'status', 'assigned_to', 'remarks']
    for field in allowed_fields:
        if field in data:
            update_fields.append(f'{field} = ?')
            values.append(data[field])
    
    if update_fields:
        update_fields.append('updated_at = ?')
        values.append(datetime.now().isoformat())
        values.append(drawing_id)
        
        conn.execute(f'''
            UPDATE drawings 
            SET {', '.join(update_fields)}
            WHERE id = ?
        ''', values)
        conn.commit()
    
    conn.close()
    return jsonify({'message': 'Drawing updated successfully'})

@drawing_bp.route('/api/drawings/<int:drawing_id>', methods=['DELETE'])
def delete_drawing(drawing_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    user = conn.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    if user['role'] != 'admin':
        conn.close()
        return jsonify({'error': 'Only administrators can delete drawings'}), 403
    
    conn.execute('DELETE FROM drawings WHERE id = ?', (drawing_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Drawing deleted successfully'})

@drawing_bp.route('/api/drawings/gantt/<project_id>', methods=['GET'])
def get_gantt_data(project_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    drawings = conn.execute('''
        SELECT d.*, u.full_name as assigned_name
        FROM drawings d
        LEFT JOIN users u ON d.assigned_to = u.id
        WHERE d.project_id = ?
        ORDER BY d.start_date, d.category, d.dwg_no
    ''', (project_id,)).fetchall()
    conn.close()
    
    gantt_data = []
    for drawing in drawings:
        gantt_data.append({
            'id': drawing['id'],
            'name': f"{drawing['dwg_no']} - {drawing['name']}",
            'start': drawing['start_date'],
            'end': drawing['end_date'],
            'progress': drawing['progress'],
            'category': drawing['category'],
            'type': drawing['type'],
            'status': drawing['status'],
            'assigned_to': drawing['assigned_name'] or 'Unassigned'
        })
    
    return jsonify(gantt_data)

