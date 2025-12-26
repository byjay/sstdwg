import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { 
  BarChart3, 
  FileText, 
  Calendar, 
  Users, 
  TrendingUp, 
  Download, 
  Plus, 
  Search,
  Bell,
  Settings,
  Menu,
  Folder,
  FolderOpen
} from 'lucide-react';
import ProjectFolderView from '@/components/ProjectFolderView';
import seastargoLogo from './assets/seastargo-logo.png';
import './App.css';

// 헤더 컴포넌트
function Header() {
  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <img src={seastargoLogo} alt="Seastargo" className="h-10 w-auto" />
          <div>
            <h1 className="text-2xl font-bold text-blue-900">SSTDMS</h1>
            <p className="text-sm text-gray-600">Ship Design Document Management System</p>
          </div>
        </div>
        
        <div className="flex items-center space-x-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <Input 
              placeholder="도면 검색..." 
              className="pl-10 w-80"
            />
          </div>
          <Button variant="ghost" size="icon">
            <Bell className="h-5 w-5" />
          </Button>
          <Button variant="ghost" size="icon">
            <Settings className="h-5 w-5" />
          </Button>
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
              <span className="text-white text-sm font-medium">관</span>
            </div>
            <span className="text-sm font-medium">관리자</span>
          </div>
        </div>
      </div>
    </header>
  )
}

// 사이드바 컴포넌트
function Sidebar({ activeMenu, setActiveMenu }) {
  const menuItems = [
    { id: 'dashboard', icon: BarChart3, label: '대시보드' },
    { id: 'projects', icon: Folder, label: '프로젝트 관리' },
    { id: 'documents', icon: FileText, label: '도면 관리' },
    { id: 'schedule', icon: Calendar, label: '스케줄 관리' },
    { id: 'users', icon: Users, label: '사용자 관리' },
    { id: 'analytics', icon: TrendingUp, label: '통계 분석' },
    { id: 'permissions', icon: Settings, label: '권한 관리' },
    { id: 'settings', icon: Settings, label: '시스템 설정' }
  ];

  return (
    <aside className="w-64 bg-gray-50 border-r border-gray-200 h-screen">
      <nav className="p-4">
        <ul className="space-y-2">
          {menuItems.map((item) => (
            <li key={item.id}>
              <Button 
                variant={activeMenu === item.id ? "default" : "ghost"} 
                className={`w-full justify-start ${
                  activeMenu === item.id ? 'bg-blue-600 text-white' : 'text-gray-700'
                }`}
                onClick={() => setActiveMenu(item.id)}
              >
                <item.icon className="mr-3 h-4 w-4" />
                {item.label}
              </Button>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
}

// 대시보드 통계 카드
function StatsCard({ title, value, description, icon: Icon, trend }) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        <p className="text-xs text-muted-foreground">
          {description}
        </p>
        {trend && (
          <Badge variant={trend > 0 ? "default" : "destructive"} className="mt-2">
            {trend > 0 ? '+' : ''}{trend}%
          </Badge>
        )}
      </CardContent>
    </Card>
  )
}

// 최근 활동 컴포넌트
function RecentActivity() {
  const activities = [
    { user: '김철수', action: '선박 A-001 도면 업로드', time: '5분 전', type: 'upload' },
    { user: '이영희', action: '프로젝트 B-002 스케줄 수정', time: '15분 전', type: 'edit' },
    { user: '박민수', action: '도면 C-003 승인 완료', time: '1시간 전', type: 'approve' },
    { user: '정수진', action: '사용자 권한 변경', time: '2시간 전', type: 'permission' }
  ]

  const getActivityIcon = (type) => {
    switch (type) {
      case 'upload': return <Upload className="h-4 w-4 text-blue-500" />
      case 'edit': return <FileText className="h-4 w-4 text-orange-500" />
      case 'approve': return <Shield className="h-4 w-4 text-green-500" />
      case 'permission': return <Users className="h-4 w-4 text-purple-500" />
      default: return <FileText className="h-4 w-4" />
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>최근 활동</CardTitle>
        <CardDescription>시스템의 최근 활동 내역입니다</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {activities.map((activity, index) => (
            <div key={index} className="flex items-center space-x-4">
              {getActivityIcon(activity.type)}
              <div className="flex-1 space-y-1">
                <p className="text-sm font-medium leading-none">
                  {activity.user}
                </p>
                <p className="text-sm text-muted-foreground">
                  {activity.action}
                </p>
              </div>
              <div className="text-sm text-muted-foreground">
                {activity.time}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

// 빠른 액션 컴포넌트
function QuickActions() {
  const actions = [
    { icon: Upload, label: '도면 업로드', color: 'bg-blue-500' },
    { icon: Download, label: '엑셀 다운로드', color: 'bg-green-500' },
    { icon: Calendar, label: '스케줄 추가', color: 'bg-orange-500' },
    { icon: Users, label: '사용자 추가', color: 'bg-purple-500' }
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle>빠른 액션</CardTitle>
        <CardDescription>자주 사용하는 기능들에 빠르게 접근하세요</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4">
          {actions.map((action, index) => (
            <Button 
              key={index} 
              variant="outline" 
              className="h-20 flex-col space-y-2"
            >
              <div className={`p-2 rounded-lg ${action.color}`}>
                <action.icon className="h-6 w-6 text-white" />
              </div>
              <span className="text-sm">{action.label}</span>
            </Button>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

// 메인 대시보드 컴포넌트
function Dashboard() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">대시보드</h2>
        <p className="text-muted-foreground">
          SSTDMS 시스템 현황을 한눈에 확인하세요
        </p>
      </div>

      {/* 통계 카드들 */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="총 도면 수"
          value="1,234"
          description="지난 달 대비"
          icon={FileText}
          trend={12}
        />
        <StatsCard
          title="진행 중인 프로젝트"
          value="23"
          description="활성 프로젝트"
          icon={Ship}
          trend={8}
        />
        <StatsCard
          title="등록된 사용자"
          value="156"
          description="전체 사용자"
          icon={Users}
          trend={5}
        />
        <StatsCard
          title="이번 달 업로드"
          value="89"
          description="새로운 도면"
          icon={Upload}
          trend={-2}
        />
      </div>

      {/* 메인 콘텐츠 영역 */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <RecentActivity />
        </div>
        <div>
          <QuickActions />
        </div>
      </div>
    </div>
  )
}

// 메인 앱 컴포넌트
function App() {
  const [activeMenu, setActiveMenu] = useState('dashboard');

  const renderContent = () => {
    switch (activeMenu) {
      case 'projects':
        return <ProjectFolderView />;
      case 'dashboard':
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="flex">
        <Sidebar activeMenu={activeMenu} setActiveMenu={setActiveMenu} />
        <main className="flex-1 p-6">
          {renderContent()}
        </main>
      </div>
    </div>
  );
}

export default App

