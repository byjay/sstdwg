import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { 
  FolderOpen, 
  FileText, 
  Calendar, 
  Users,
  TrendingUp,
  Clock,
  CheckCircle,
  AlertCircle
} from 'lucide-react';

const Dashboard = ({ user }) => {
  const [stats, setStats] = useState({
    projects: 0,
    documents: 0,
    schedules: 0,
    users: 0
  });
  const [recentProjects, setRecentProjects] = useState([]);
  const [recentDocuments, setRecentDocuments] = useState([]);
  const [upcomingSchedules, setUpcomingSchedules] = useState([]);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      // 프로젝트 목록 조회
      const projectsResponse = await fetch('/api/projects', {
        credentials: 'include'
      });
      if (projectsResponse.ok) {
        const projectsData = await projectsResponse.json();
        setStats(prev => ({ ...prev, projects: projectsData.projects.length }));
        setRecentProjects(projectsData.projects.slice(0, 5));
      }

      // 사용자가 관리자인 경우 사용자 통계 조회
      if (user.role === 'admin') {
        const usersResponse = await fetch('/api/users', {
          credentials: 'include'
        });
        if (usersResponse.ok) {
          const usersData = await usersResponse.json();
          setStats(prev => ({ ...prev, users: usersData.total }));
        }
      }
    } catch (error) {
      console.error('대시보드 데이터 조회 실패:', error);
    }
  };

  const StatCard = ({ title, value, icon: Icon, description, trend }) => (
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
          <div className="flex items-center pt-1">
            <TrendingUp className="h-3 w-3 text-green-500 mr-1" />
            <span className="text-xs text-green-500">{trend}</span>
          </div>
        )}
      </CardContent>
    </Card>
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">대시보드</h1>
        <p className="text-gray-600">
          안녕하세요, {user.full_name}님! 오늘도 좋은 하루 되세요.
        </p>
      </div>

      {/* 통계 카드 */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="총 프로젝트"
          value={stats.projects}
          icon={FolderOpen}
          description="진행 중인 프로젝트"
          trend="+2.5%"
        />
        <StatCard
          title="총 문서"
          value={stats.documents}
          icon={FileText}
          description="업로드된 문서"
          trend="+12.3%"
        />
        <StatCard
          title="일정"
          value={stats.schedules}
          icon={Calendar}
          description="예정된 일정"
          trend="+5.1%"
        />
        {user.role === 'admin' && (
          <StatCard
            title="사용자"
            value={stats.users}
            icon={Users}
            description="등록된 사용자"
            trend="+1.2%"
          />
        )}
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* 최근 프로젝트 */}
        <Card>
          <CardHeader>
            <CardTitle>최근 프로젝트</CardTitle>
            <CardDescription>
              최근에 업데이트된 프로젝트 목록입니다.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentProjects.length > 0 ? (
                recentProjects.map((project) => (
                  <div key={project.id} className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <FolderOpen className="h-5 w-5 text-blue-500" />
                      <div>
                        <p className="text-sm font-medium">{project.name}</p>
                        <p className="text-xs text-gray-500">{project.client}</p>
                      </div>
                    </div>
                    <Badge variant={project.status === 'active' ? 'default' : 'secondary'}>
                      {project.status === 'active' ? '진행중' : '완료'}
                    </Badge>
                  </div>
                ))
              ) : (
                <p className="text-sm text-gray-500">프로젝트가 없습니다.</p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* 최근 활동 */}
        <Card>
          <CardHeader>
            <CardTitle>최근 활동</CardTitle>
            <CardDescription>
              시스템에서 발생한 최근 활동 내역입니다.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center space-x-3">
                <CheckCircle className="h-5 w-5 text-green-500" />
                <div>
                  <p className="text-sm font-medium">문서 업로드 완료</p>
                  <p className="text-xs text-gray-500">2시간 전</p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <Clock className="h-5 w-5 text-yellow-500" />
                <div>
                  <p className="text-sm font-medium">일정 알림</p>
                  <p className="text-xs text-gray-500">4시간 전</p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <AlertCircle className="h-5 w-5 text-red-500" />
                <div>
                  <p className="text-sm font-medium">검토 요청</p>
                  <p className="text-xs text-gray-500">1일 전</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 빠른 액션 */}
      <Card>
        <CardHeader>
          <CardTitle>빠른 액션</CardTitle>
          <CardDescription>
            자주 사용하는 기능에 빠르게 접근할 수 있습니다.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="flex items-center space-x-3 p-3 border rounded-lg hover:bg-gray-50 cursor-pointer">
              <FolderOpen className="h-6 w-6 text-blue-500" />
              <div>
                <p className="text-sm font-medium">새 프로젝트</p>
                <p className="text-xs text-gray-500">프로젝트 생성</p>
              </div>
            </div>
            <div className="flex items-center space-x-3 p-3 border rounded-lg hover:bg-gray-50 cursor-pointer">
              <FileText className="h-6 w-6 text-green-500" />
              <div>
                <p className="text-sm font-medium">문서 업로드</p>
                <p className="text-xs text-gray-500">파일 업로드</p>
              </div>
            </div>
            <div className="flex items-center space-x-3 p-3 border rounded-lg hover:bg-gray-50 cursor-pointer">
              <Calendar className="h-6 w-6 text-purple-500" />
              <div>
                <p className="text-sm font-medium">일정 등록</p>
                <p className="text-xs text-gray-500">새 일정 추가</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Dashboard;

