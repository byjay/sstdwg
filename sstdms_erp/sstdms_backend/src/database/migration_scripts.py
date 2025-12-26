# migration_scripts.py

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any

class DatabaseMigration:
    """Database migration system for SSTDMS."""
    
    def __init__(self, db_path: str = "./src/database/app.db"):
        self.db_path = db_path
        self.migration_table = "schema_migrations"
        self.ensure_migration_table()
    
    def ensure_migration_table(self):
        """Create migration tracking table if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.migration_table} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version TEXT UNIQUE NOT NULL,
                    description TEXT,
                    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    success BOOLEAN DEFAULT TRUE
                )
            """)
            conn.commit()
    
    def get_executed_migrations(self) -> List[str]:
        """Get list of already executed migrations."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT version FROM {self.migration_table} WHERE success = 1")
            return [row[0] for row in cursor.fetchall()]
    
    def execute_migration(self, version: str, description: str, sql_commands: List[str]) -> bool:
        """Execute a migration and record it."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Execute migration commands
                for command in sql_commands:
                    cursor.execute(command)
                
                # Record migration
                cursor.execute(f"""
                    INSERT INTO {self.migration_table} (version, description, success)
                    VALUES (?, ?, 1)
                """, (version, description))
                
                conn.commit()
                print(f"Migration {version} executed successfully: {description}")
                return True
                
        except Exception as e:
            print(f"Migration {version} failed: {str(e)}")
            # Record failed migration
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    INSERT INTO {self.migration_table} (version, description, success)
                    VALUES (?, ?, 0)
                """, (version, f"{description} - FAILED: {str(e)}"))
                conn.commit()
            return False
    
    def run_migrations(self):
        """Run all pending migrations."""
        executed_migrations = self.get_executed_migrations()
        
        # Define migrations in order
        migrations = [
            {
                "version": "001_create_users_enhanced",
                "description": "Create enhanced users table",
                "commands": [
                    """
                    CREATE TABLE IF NOT EXISTS users_enhanced (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        hashed_password TEXT NOT NULL,
                        salt TEXT NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        is_active BOOLEAN DEFAULT 1,
                        is_admin BOOLEAN DEFAULT 0,
                        role TEXT DEFAULT 'user',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """,
                    "CREATE INDEX IF NOT EXISTS idx_users_enhanced_username ON users_enhanced(username)",
                    "CREATE INDEX IF NOT EXISTS idx_users_enhanced_email ON users_enhanced(email)",
                    "CREATE INDEX IF NOT EXISTS idx_users_enhanced_role ON users_enhanced(role)"
                ]
            },
            {
                "version": "002_create_projects_enhanced",
                "description": "Create enhanced projects table",
                "commands": [
                    """
                    CREATE TABLE IF NOT EXISTS projects_enhanced (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        created_by INTEGER NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (created_by) REFERENCES users_enhanced(id)
                    )
                    """,
                    "CREATE INDEX IF NOT EXISTS idx_projects_enhanced_status ON projects_enhanced(status)",
                    "CREATE INDEX IF NOT EXISTS idx_projects_enhanced_created_by ON projects_enhanced(created_by)"
                ]
            },
            {
                "version": "003_create_documents_enhanced",
                "description": "Create enhanced documents table",
                "commands": [
                    """
                    CREATE TABLE IF NOT EXISTS documents_enhanced (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        project_id INTEGER NOT NULL,
                        filename TEXT NOT NULL,
                        original_filename TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        file_size INTEGER,
                        mime_type TEXT,
                        uploaded_by INTEGER NOT NULL,
                        version INTEGER DEFAULT 1,
                        status TEXT DEFAULT 'active',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (project_id) REFERENCES projects_enhanced(id),
                        FOREIGN KEY (uploaded_by) REFERENCES users_enhanced(id)
                    )
                    """,
                    "CREATE INDEX IF NOT EXISTS idx_documents_enhanced_project_id ON documents_enhanced(project_id)",
                    "CREATE INDEX IF NOT EXISTS idx_documents_enhanced_uploaded_by ON documents_enhanced(uploaded_by)",
                    "CREATE INDEX IF NOT EXISTS idx_documents_enhanced_status ON documents_enhanced(status)"
                ]
            },
            {
                "version": "004_create_audit_log",
                "description": "Create audit log table for security tracking",
                "commands": [
                    """
                    CREATE TABLE IF NOT EXISTS audit_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        action TEXT NOT NULL,
                        resource_type TEXT,
                        resource_id INTEGER,
                        details TEXT,
                        ip_address TEXT,
                        user_agent TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users_enhanced(id)
                    )
                    """,
                    "CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id)",
                    "CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action)",
                    "CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at)"
                ]
            },
            {
                "version": "005_create_notifications",
                "description": "Create notifications table",
                "commands": [
                    """
                    CREATE TABLE IF NOT EXISTS notifications (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        title TEXT NOT NULL,
                        message TEXT NOT NULL,
                        type TEXT DEFAULT 'info',
                        is_read BOOLEAN DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users_enhanced(id)
                    )
                    """,
                    "CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id)",
                    "CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read)"
                ]
            }
        ]
        
        # Execute pending migrations
        for migration in migrations:
            if migration["version"] not in executed_migrations:
                success = self.execute_migration(
                    migration["version"],
                    migration["description"],
                    migration["commands"]
                )
                if not success:
                    print(f"Migration failed: {migration['version']}")
                    break
        
        print("Migration process completed.")
    
    def rollback_migration(self, version: str) -> bool:
        """Rollback a specific migration (basic implementation)."""
        # This is a simplified rollback - in production, you'd want more sophisticated rollback scripts
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(f"DELETE FROM {self.migration_table} WHERE version = ?", (version,))
                conn.commit()
                print(f"Migration {version} rolled back from tracking table")
                return True
        except Exception as e:
            print(f"Rollback failed for {version}: {str(e)}")
            return False
    
    def get_migration_status(self) -> List[Dict[str, Any]]:
        """Get status of all migrations."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT version, description, executed_at, success 
                FROM {self.migration_table} 
                ORDER BY executed_at
            """)
            
            migrations = []
            for row in cursor.fetchall():
                migrations.append({
                    "version": row[0],
                    "description": row[1],
                    "executed_at": row[2],
                    "success": bool(row[3])
                })
            
            return migrations

# Utility functions for common database operations
def backup_database(db_path: str, backup_path: str = None) -> str:
    """Create a backup of the database."""
    if backup_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{db_path}.backup_{timestamp}"
    
    try:
        # Simple file copy for SQLite
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"Database backed up to: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"Backup failed: {str(e)}")
        raise

def optimize_database(db_path: str):
    """Optimize database performance."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Analyze tables for query optimization
        cursor.execute("ANALYZE")
        
        # Vacuum to reclaim space
        cursor.execute("VACUUM")
        
        # Update statistics
        cursor.execute("PRAGMA optimize")
        
        conn.commit()
        print("Database optimization completed")

# Example usage and testing
if __name__ == "__main__":
    # Initialize migration system
    migration = DatabaseMigration()
    
    # Run all pending migrations
    migration.run_migrations()
    
    # Show migration status
    status = migration.get_migration_status()
    print("\nMigration Status:")
    for m in status:
        print(f"  {m['version']}: {m['description']} - {'SUCCESS' if m['success'] else 'FAILED'}")
    
    # Optimize database
    optimize_database("./src/database/app.db")

