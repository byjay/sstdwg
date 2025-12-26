# session_handler.py

import secrets
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import json

class SessionHandler:
    """Enhanced session management system with security features."""
    
    def __init__(self, session_timeout: int = 3600):  # 1 hour default
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.session_timeout = session_timeout
    
    def create_session(self, user_id: int, username: str, role: str = 'user') -> str:
        """Create a new session for a user."""
        session_id = secrets.token_urlsafe(32)
        
        session_data = {
            'user_id': user_id,
            'username': username,
            'role': role,
            'created_at': time.time(),
            'last_accessed': time.time(),
            'ip_address': None,  # To be set by the calling function
            'user_agent': None,  # To be set by the calling function
            'is_active': True
        }
        
        self.sessions[session_id] = session_data
        return session_id
    
    def validate_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Validate a session and return session data if valid."""
        if not session_id or session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        current_time = time.time()
        
        # Check if session has expired
        if current_time - session['last_accessed'] > self.session_timeout:
            self.destroy_session(session_id)
            return None
        
        # Check if session is active
        if not session.get('is_active', False):
            return None
        
        # Update last accessed time
        session['last_accessed'] = current_time
        
        return session
    
    def destroy_session(self, session_id: str) -> bool:
        """Destroy a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def update_session_info(self, session_id: str, ip_address: str = None, user_agent: str = None) -> bool:
        """Update session information like IP address and user agent."""
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        if ip_address:
            session['ip_address'] = ip_address
        if user_agent:
            session['user_agent'] = user_agent
        
        return True
    
    def get_user_sessions(self, user_id: int) -> list[str]:
        """Get all active sessions for a user."""
        user_sessions = []
        for session_id, session_data in self.sessions.items():
            if session_data['user_id'] == user_id and session_data.get('is_active', False):
                user_sessions.append(session_id)
        return user_sessions
    
    def destroy_user_sessions(self, user_id: int) -> int:
        """Destroy all sessions for a user. Returns number of sessions destroyed."""
        user_sessions = self.get_user_sessions(user_id)
        destroyed_count = 0
        
        for session_id in user_sessions:
            if self.destroy_session(session_id):
                destroyed_count += 1
        
        return destroyed_count
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions. Returns number of sessions cleaned up."""
        current_time = time.time()
        expired_sessions = []
        
        for session_id, session_data in self.sessions.items():
            if current_time - session_data['last_accessed'] > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.destroy_session(session_id)
        
        return len(expired_sessions)
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed session information."""
        session = self.validate_session(session_id)
        if not session:
            return None
        
        return {
            'user_id': session['user_id'],
            'username': session['username'],
            'role': session['role'],
            'created_at': datetime.fromtimestamp(session['created_at']).isoformat(),
            'last_accessed': datetime.fromtimestamp(session['last_accessed']).isoformat(),
            'ip_address': session.get('ip_address'),
            'user_agent': session.get('user_agent'),
            'is_active': session.get('is_active', False)
        }
    
    def get_all_active_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all active sessions."""
        active_sessions = {}
        current_time = time.time()
        
        for session_id, session_data in self.sessions.items():
            if (session_data.get('is_active', False) and 
                current_time - session_data['last_accessed'] <= self.session_timeout):
                active_sessions[session_id] = self.get_session_info(session_id)
        
        return active_sessions
    
    def deactivate_session(self, session_id: str) -> bool:
        """Deactivate a session without destroying it."""
        if session_id in self.sessions:
            self.sessions[session_id]['is_active'] = False
            return True
        return False
    
    def reactivate_session(self, session_id: str) -> bool:
        """Reactivate a deactivated session."""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            current_time = time.time()
            
            # Check if session hasn't expired
            if current_time - session['last_accessed'] <= self.session_timeout:
                session['is_active'] = True
                session['last_accessed'] = current_time
                return True
        
        return False

# Global session handler instance
session_handler = SessionHandler()

# Example usage and testing
if __name__ == '__main__':
    sh = SessionHandler(session_timeout=300)  # 5 minutes for testing
    
    # Create a session
    session_id = sh.create_session(user_id=1, username='testuser', role='admin')
    print(f"Created session: {session_id}")
    
    # Update session info
    sh.update_session_info(session_id, ip_address='192.168.1.1', user_agent='Test Browser')
    
    # Validate session
    session_data = sh.validate_session(session_id)
    print(f"Session data: {session_data}")
    
    # Get session info
    session_info = sh.get_session_info(session_id)
    print(f"Session info: {json.dumps(session_info, indent=2)}")
    
    # Test session expiration (simulate)
    time.sleep(1)
    session_data = sh.validate_session(session_id)
    print(f"Session still valid: {session_data is not None}")
    
    # Get all active sessions
    active_sessions = sh.get_all_active_sessions()
    print(f"Active sessions: {len(active_sessions)}")
    
    # Destroy session
    destroyed = sh.destroy_session(session_id)
    print(f"Session destroyed: {destroyed}")

