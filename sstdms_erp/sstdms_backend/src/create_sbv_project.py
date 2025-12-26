import sqlite3
from datetime import datetime, timedelta
import json

def create_sbv_project():
    # Connect to database
    conn = sqlite3.connect('database/app.db')
    cursor = conn.cursor()
    
    # Create drawings table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS drawings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id VARCHAR(50) NOT NULL,
            category VARCHAR(50) NOT NULL,
            dwg_no VARCHAR(100) NOT NULL UNIQUE,
            name VARCHAR(200) NOT NULL,
            type VARCHAR(20) NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            progress INTEGER DEFAULT 0,
            status VARCHAR(20) DEFAULT 'planned',
            revision VARCHAR(10) DEFAULT 'A',
            assigned_to INTEGER,
            remarks TEXT,
            created_by INTEGER NOT NULL,
            created_at DATETIME,
            updated_at DATETIME,
            FOREIGN KEY(project_id) REFERENCES projects(id),
            FOREIGN KEY(assigned_to) REFERENCES users(id),
            FOREIGN KEY(created_by) REFERENCES users(id)
        )
    ''')
    
    # Create SBV project
    project_data = {
        'project_id': 'SBV_2025_001',
        'name': 'SBV (SCF Conversion)',
        'description': 'Ship-to-Ship Cargo Transfer Vessel Conversion Project',
        'ship_type': '기타',
        'client': 'Seastar Design',
        'start_date': '2025-01-01',
        'end_date': '2025-12-31',
        'status': 'active',
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    cursor.execute('''
        INSERT OR REPLACE INTO projects 
        (id, name, description, ship_type, client, start_date, end_date, status, created_by, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        project_data['project_id'],
        project_data['name'],
        project_data['description'],
        project_data['ship_type'],
        project_data['client'],
        project_data['start_date'],
        project_data['end_date'],
        project_data['status'],
        1,  # created_by admin user (id=1)
        project_data['created_at'],
        project_data['updated_at']
    ))
    
    # Sample drawing data based on the uploaded files
    drawings = [
        # COMMON drawings
        {'category': 'COMMON', 'dwg_no': 'D.512.0000.001.001', 'name': 'POS (Purchase Order Specification)', 'type': 'BASIC', 'start_date': '2025-01-01', 'duration': 30, 'progress': 0},
        {'category': 'COMMON', 'dwg_no': 'D.512.0000.001.002', 'name': 'General Arrangement', 'type': 'BASIC', 'start_date': '2025-01-15', 'duration': 45, 'progress': 0},
        {'category': 'COMMON', 'dwg_no': 'D.512.0000.001.003', 'name': 'Trim & Stability Booklet', 'type': 'APPROVAL', 'start_date': '2025-02-01', 'duration': 60, 'progress': 0},
        
        # HULL drawings
        {'category': 'HULL', 'dwg_no': 'D.512.1000.001.001', 'name': 'Hull Scantling Calculation', 'type': 'BASIC', 'start_date': '2025-02-15', 'duration': 30, 'progress': 0},
        {'category': 'HULL', 'dwg_no': 'D.512.1000.001.002', 'name': 'Structural Strength Analysis', 'type': 'APPROVAL', 'start_date': '2025-03-01', 'duration': 45, 'progress': 0},
        {'category': 'HULL', 'dwg_no': 'D.512.1000.001.003', 'name': 'Hull Production Drawing', 'type': 'PRODUCTION', 'start_date': '2025-04-01', 'duration': 60, 'progress': 0},
        
        # ACCOMMODATION drawings
        {'category': 'ACCOMMODATION', 'dwg_no': 'D.512.2000.001.001', 'name': 'Accommodation Plan', 'type': 'BASIC', 'start_date': '2025-03-15', 'duration': 30, 'progress': 0},
        {'category': 'ACCOMMODATION', 'dwg_no': 'D.512.2000.001.002', 'name': 'Outfittings of Accommodation', 'type': 'APPROVAL', 'start_date': '2025-04-01', 'duration': 45, 'progress': 0},
        {'category': 'ACCOMMODATION', 'dwg_no': 'D.512.2000.001.003', 'name': 'HVAC Layout', 'type': 'PRODUCTION', 'start_date': '2025-05-01', 'duration': 30, 'progress': 0},
        
        # OUTFITTING drawings
        {'category': 'OUTFITTING', 'dwg_no': 'D.512.3000.001.001', 'name': 'Equipment Number Calculation', 'type': 'BASIC', 'start_date': '2025-04-15', 'duration': 30, 'progress': 0},
        {'category': 'OUTFITTING', 'dwg_no': 'D.512.3000.001.002', 'name': 'Fire Safety Action Plan', 'type': 'APPROVAL', 'start_date': '2025-05-15', 'duration': 45, 'progress': 0},
        
        # PIPING drawings
        {'category': 'PIPING', 'dwg_no': 'D.512.4000.001.001', 'name': 'Piping System Diagram', 'type': 'BASIC', 'start_date': '2025-05-01', 'duration': 45, 'progress': 0},
        {'category': 'PIPING', 'dwg_no': 'D.512.4000.001.002', 'name': 'Valve List', 'type': 'APPROVAL', 'start_date': '2025-06-01', 'duration': 30, 'progress': 0},
        {'category': 'PIPING', 'dwg_no': 'D.512.4000.001.003', 'name': 'Piping Production Drawing', 'type': 'PRODUCTION', 'start_date': '2025-07-01', 'duration': 60, 'progress': 0},
        
        # ELECTRICAL drawings
        {'category': 'ELECTRICAL', 'dwg_no': 'D.512.5000.001.001', 'name': 'Electric Wiring Diagram', 'type': 'BASIC', 'start_date': '2025-06-15', 'duration': 45, 'progress': 0},
        {'category': 'ELECTRICAL', 'dwg_no': 'D.512.5000.001.002', 'name': 'Electric Equipment Arrangement', 'type': 'APPROVAL', 'start_date': '2025-07-15', 'duration': 30, 'progress': 0},
        {'category': 'ELECTRICAL', 'dwg_no': 'D.512.5000.001.003', 'name': 'Cable Route Plan', 'type': 'PRODUCTION', 'start_date': '2025-08-15', 'duration': 45, 'progress': 0},
    ]
    
    # Insert drawings
    for drawing in drawings:
        start_date = datetime.strptime(drawing['start_date'], '%Y-%m-%d')
        end_date = start_date + timedelta(days=drawing['duration'])
        
        cursor.execute('''
            INSERT OR REPLACE INTO drawings 
            (project_id, category, dwg_no, name, type, start_date, end_date, progress, status, created_by, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'SBV_2025_001',
            drawing['category'],
            drawing['dwg_no'],
            drawing['name'],
            drawing['type'],
            drawing['start_date'],
            end_date.strftime('%Y-%m-%d'),
            drawing['progress'],
            'planned',
            1,  # created_by admin user (id=1)
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
    
    conn.commit()
    conn.close()
    print(f"SBV project created successfully with {len(drawings)} drawings!")

if __name__ == '__main__':
    create_sbv_project()

