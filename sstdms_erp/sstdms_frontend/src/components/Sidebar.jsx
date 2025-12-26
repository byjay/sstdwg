import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { cn } from '../lib/utils';
import { 
  Home, 
  FolderOpen, 
  FileText, 
  Calendar, 
  Users, 
  Settings,
  BarChart3
} from 'lucide-react';

const Sidebar = ({ user }) => {
  const location = useLocation();

  const navigation = [
    { name: '대시보드', href: '/', icon: Home },
    { name: '프로젝트', href: '/projects', icon: FolderOpen },
    { name: '문서관리', href: '/documents', icon: FileText },
    { name: '일정관리', href: '/schedules', icon: Calendar },
    { name: '보고서', href: '/reports', icon: BarChart3 },
  ];

  // 관리자 전용 메뉴
  if (user.role === 'admin') {
    navigation.push(
      { name: '사용자관리', href: '/users', icon: Users },
      { name: '시스템설정', href: '/settings', icon: Settings }
    );
  }

  return (
    <div className="w-64 bg-white shadow-sm border-r min-h-screen">
      <div className="p-6">
        <nav className="space-y-2">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href;
            return (
              <Link
                key={item.name}
                to={item.href}
                className={cn(
                  'flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors',
                  isActive
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                )}
              >
                <item.icon className="mr-3 h-5 w-5" />
                {item.name}
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="absolute bottom-0 w-64 p-6 border-t">
        <div className="text-xs text-gray-500">
          <p>SSTDMS v1.0.0</p>
          <p>© 2024 Seastar Design</p>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;

