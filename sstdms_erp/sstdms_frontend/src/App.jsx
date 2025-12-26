import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';

// Components
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import ProjectList from './components/ProjectList';
import ProjectDetail from './components/ProjectDetail';
import UserManagement from './components/UserManagement';
import DocumentManagement from './components/DocumentManagement';
import ScheduleManagement from './components/ScheduleManagement';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import PasswordChangeDialog from './components/PasswordChangeDialog';

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showPasswordChange, setShowPasswordChange] = useState(false);
  const [passwordChangeRequired, setPasswordChangeRequired] = useState(false);

  useEffect(() => {
    // 세션 확인
    checkSession();
  }, []);

  const checkSession = async () => {
    try {
      const response = await fetch('/api/profile', {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        setUser(data.user);
        if (data.user.password_change_required) {
          setPasswordChangeRequired(true);
          setShowPasswordChange(true);
        }
      }
    } catch (error) {
      console.error('세션 확인 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = (userData, passwordChangeReq = false) => {
    setUser(userData);
    if (passwordChangeReq) {
      setPasswordChangeRequired(true);
      setShowPasswordChange(true);
    }
  };

  const handleLogout = async () => {
    try {
      await fetch('/api/logout', {
        method: 'POST',
        credentials: 'include'
      });
      setUser(null);
      setPasswordChangeRequired(false);
      setShowPasswordChange(false);
    } catch (error) {
      console.error('로그아웃 실패:', error);
    }
  };

  const handlePasswordChangeSuccess = (message) => {
    alert(message);
    setPasswordChangeRequired(false);
    setShowPasswordChange(false);
    // 사용자 정보 업데이트
    if (user) {
      setUser({
        ...user,
        password_change_required: false
      });
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!user) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Navbar user={user} onLogout={handleLogout} />
        <div className="flex">
          <Sidebar user={user} />
          <main className="flex-1 p-6">
            <Routes>
              <Route path="/" element={<Dashboard user={user} />} />
              <Route path="/projects" element={<ProjectList user={user} />} />
              <Route path="/projects/:projectId" element={<ProjectDetail user={user} />} />
              <Route path="/documents" element={<DocumentManagement user={user} />} />
              <Route path="/schedules" element={<ScheduleManagement user={user} />} />
              {user.role === 'admin' && (
                <Route path="/users" element={<UserManagement user={user} />} />
              )}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
        </div>
        
        {/* 비밀번호 변경 다이얼로그 */}
        <PasswordChangeDialog
          open={showPasswordChange}
          onClose={() => {
            if (!passwordChangeRequired) {
              setShowPasswordChange(false);
            }
          }}
          onSuccess={handlePasswordChangeSuccess}
          required={passwordChangeRequired}
        />
      </div>
    </Router>
  );
}

export default App;

