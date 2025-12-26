import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Input } from './ui/input';
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogHeader, 
  DialogTitle, 
  DialogTrigger 
} from './ui/dialog';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select';
import { 
  Plus, 
  Search, 
  FolderOpen, 
  Calendar,
  Building,
  Ship
} from 'lucide-react';

const ProjectList = ({ user }) => {
  const [projects, setProjects] = useState([]);
  const [filteredProjects, setFilteredProjects] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newProject, setNewProject] = useState({
    id: '',
    name: '',
    description: '',
    ship_type: '',
    client: '',
    start_date: '',
    end_date: '',
    status: 'active'
  });

  useEffect(() => {
    fetchProjects();
  }, []);

  useEffect(() => {
    const filtered = projects.filter(project =>
      project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      project.client.toLowerCase().includes(searchTerm.toLowerCase()) ||
      project.ship_type.toLowerCase().includes(searchTerm.toLowerCase())
    );
    setFilteredProjects(filtered);
  }, [projects, searchTerm]);

  const fetchProjects = async () => {
    try {
      const response = await fetch('/api/projects', {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        setProjects(data.projects);
      }
    } catch (error) {
      console.error('프로젝트 목록 조회 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateProject = async (e) => {
    e.preventDefault();
    
    try {
      const response = await fetch('/api/projects', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(newProject)
      });

      if (response.ok) {
        const data = await response.json();
        setProjects([...projects, data.project]);
        setShowCreateDialog(false);
        setNewProject({
          id: '',
          name: '',
          description: '',
          ship_type: '',
          client: '',
          start_date: '',
          end_date: '',
          status: 'active'
        });
      } else {
        const errorData = await response.json();
        alert(errorData.error || '프로젝트 생성에 실패했습니다.');
      }
    } catch (error) {
      console.error('프로젝트 생성 실패:', error);
      alert('프로젝트 생성 중 오류가 발생했습니다.');
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'active':
        return <Badge className="bg-green-100 text-green-800">진행중</Badge>;
      case 'completed':
        return <Badge className="bg-blue-100 text-blue-800">완료</Badge>;
      case 'suspended':
        return <Badge className="bg-yellow-100 text-yellow-800">중단</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">프로젝트 관리</h1>
          <p className="text-gray-600">선박 설계 프로젝트를 관리합니다.</p>
        </div>
        
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              새 프로젝트
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[600px]">
            <DialogHeader>
              <DialogTitle>새 프로젝트 생성</DialogTitle>
              <DialogDescription>
                새로운 선박 설계 프로젝트를 생성합니다.
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleCreateProject} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="project-id">프로젝트 ID</Label>
                  <Input
                    id="project-id"
                    placeholder="PRJ_2024_001"
                    value={newProject.id}
                    onChange={(e) => setNewProject({...newProject, id: e.target.value})}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="project-name">프로젝트명</Label>
                  <Input
                    id="project-name"
                    placeholder="컨테이너선 A호 설계"
                    value={newProject.name}
                    onChange={(e) => setNewProject({...newProject, name: e.target.value})}
                    required
                  />
                </div>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="description">설명</Label>
                <Textarea
                  id="description"
                  placeholder="프로젝트에 대한 상세 설명을 입력하세요"
                  value={newProject.description}
                  onChange={(e) => setNewProject({...newProject, description: e.target.value})}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="ship-type">선박 유형</Label>
                  <Select value={newProject.ship_type} onValueChange={(value) => setNewProject({...newProject, ship_type: value})}>
                    <SelectTrigger>
                      <SelectValue placeholder="선박 유형 선택" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="컨테이너선">컨테이너선</SelectItem>
                      <SelectItem value="벌크선">벌크선</SelectItem>
                      <SelectItem value="탱커">탱커</SelectItem>
                      <SelectItem value="LNG선">LNG선</SelectItem>
                      <SelectItem value="크루즈선">크루즈선</SelectItem>
                      <SelectItem value="기타">기타</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="client">고객사</Label>
                  <Input
                    id="client"
                    placeholder="현대상선"
                    value={newProject.client}
                    onChange={(e) => setNewProject({...newProject, client: e.target.value})}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="start-date">시작일</Label>
                  <Input
                    id="start-date"
                    type="date"
                    value={newProject.start_date}
                    onChange={(e) => setNewProject({...newProject, start_date: e.target.value})}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="end-date">종료일</Label>
                  <Input
                    id="end-date"
                    type="date"
                    value={newProject.end_date}
                    onChange={(e) => setNewProject({...newProject, end_date: e.target.value})}
                  />
                </div>
              </div>

              <div className="flex justify-end space-x-2">
                <Button type="button" variant="outline" onClick={() => setShowCreateDialog(false)}>
                  취소
                </Button>
                <Button type="submit">
                  생성
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* 검색 */}
      <div className="flex items-center space-x-2">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
          <Input
            placeholder="프로젝트 검색..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {/* 프로젝트 목록 */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {filteredProjects.map((project) => (
          <Card key={project.id} className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">{project.name}</CardTitle>
                {getStatusBadge(project.status)}
              </div>
              <CardDescription className="text-sm text-gray-600">
                {project.description}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center text-sm text-gray-600">
                  <Ship className="mr-2 h-4 w-4" />
                  {project.ship_type}
                </div>
                <div className="flex items-center text-sm text-gray-600">
                  <Building className="mr-2 h-4 w-4" />
                  {project.client}
                </div>
                {project.start_date && (
                  <div className="flex items-center text-sm text-gray-600">
                    <Calendar className="mr-2 h-4 w-4" />
                    {new Date(project.start_date).toLocaleDateString('ko-KR')}
                  </div>
                )}
              </div>
              
              <div className="mt-4 pt-4 border-t">
                <Link to={`/projects/${project.id}`}>
                  <Button variant="outline" className="w-full">
                    <FolderOpen className="mr-2 h-4 w-4" />
                    프로젝트 열기
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredProjects.length === 0 && (
        <div className="text-center py-12">
          <FolderOpen className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">프로젝트가 없습니다</h3>
          <p className="mt-1 text-sm text-gray-500">
            새 프로젝트를 생성하여 시작하세요.
          </p>
        </div>
      )}
    </div>
  );
};

export default ProjectList;

