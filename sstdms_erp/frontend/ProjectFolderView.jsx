import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { 
  Folder, 
  FolderOpen, 
  File, 
  Plus, 
  Users, 
  Lock, 
  Unlock,
  ChevronRight,
  ChevronDown,
  Settings
} from 'lucide-react';

const ProjectFolderView = () => {
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [folders, setFolders] = useState([]);
  const [expandedFolders, setExpandedFolders] = useState(new Set());
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchAccessibleProjects();
  }, []);

  const fetchAccessibleProjects = async () => {
    try {
      const response = await fetch('/api/projects/accessible');
      const data = await response.json();
      if (data.success) {
        setProjects(data.projects);
        if (data.projects.length > 0) {
          setSelectedProject(data.projects[0]);
          fetchProjectFolders(data.projects[0].id);
        }
      }
    } catch (error) {
      console.error('프로젝트 조회 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchProjectFolders = async (projectId) => {
    try {
      const response = await fetch(`/api/projects/${projectId}/folders`);
      const data = await response.json();
      if (data.success) {
        setFolders(data.folders);
      }
    } catch (error) {
      console.error('폴더 조회 실패:', error);
    }
  };

  const toggleFolder = (folderId) => {
    const newExpanded = new Set(expandedFolders);
    if (newExpanded.has(folderId)) {
      newExpanded.delete(folderId);
    } else {
      newExpanded.add(folderId);
    }
    setExpandedFolders(newExpanded);
  };

  const getPermissionBadge = (permission) => {
    const badges = {
      'admin': { label: '관리자', variant: 'destructive' },
      'write': { label: '편집', variant: 'default' },
      'read': { label: '읽기', variant: 'secondary' },
      'none': { label: '권한없음', variant: 'outline' }
    };
    
    const badge = badges[permission] || badges['none'];
    return (
      <Badge variant={badge.variant} className="text-xs">
        {badge.label}
      </Badge>
    );
  };

  const getProjectIcon = (permission) => {
    if (permission === 'admin' || permission === 'write') {
      return <Unlock className="h-4 w-4 text-green-500" />;
    }
    return <Lock className="h-4 w-4 text-gray-400" />;
  };

  const buildFolderTree = (folders) => {
    const folderMap = new Map();
    const rootFolders = [];

    // 폴더 맵 생성
    folders.forEach(folder => {
      folderMap.set(folder.id, { ...folder, children: [] });
    });

    // 트리 구조 생성
    folders.forEach(folder => {
      if (folder.parent_folder_id) {
        const parent = folderMap.get(folder.parent_folder_id);
        if (parent) {
          parent.children.push(folderMap.get(folder.id));
        }
      } else {
        rootFolders.push(folderMap.get(folder.id));
      }
    });

    return rootFolders;
  };

  const renderFolderTree = (folders, level = 0) => {
    return folders.map(folder => (
      <div key={folder.id} className="select-none">
        <div 
          className={`flex items-center gap-2 p-2 hover:bg-gray-50 cursor-pointer rounded-md ${
            level > 0 ? 'ml-' + (level * 4) : ''
          }`}
          onClick={() => toggleFolder(folder.id)}
        >
          {folder.children.length > 0 && (
            expandedFolders.has(folder.id) ? 
              <ChevronDown className="h-4 w-4 text-gray-500" /> :
              <ChevronRight className="h-4 w-4 text-gray-500" />
          )}
          {folder.children.length === 0 && <div className="w-4" />}
          
          {expandedFolders.has(folder.id) ? 
            <FolderOpen className="h-4 w-4 text-blue-500" /> :
            <Folder className="h-4 w-4 text-blue-500" />
          }
          
          <span className="text-sm font-medium">{folder.folder_name}</span>
          
          {folder.description && (
            <span className="text-xs text-gray-500 ml-2">
              ({folder.description})
            </span>
          )}
        </div>
        
        {expandedFolders.has(folder.id) && folder.children.length > 0 && (
          <div className="ml-4">
            {renderFolderTree(folder.children, level + 1)}
          </div>
        )}
      </div>
    ));
  };

  const filteredProjects = projects.filter(project =>
    project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    project.client.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-2 text-gray-500">프로젝트를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">프로젝트 관리</h2>
        <div className="flex gap-2">
          <Button size="sm">
            <Plus className="h-4 w-4 mr-2" />
            새 프로젝트
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 프로젝트 목록 */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">내 프로젝트</CardTitle>
              <Input
                placeholder="프로젝트 검색..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="mt-2"
              />
            </CardHeader>
            <CardContent className="p-0">
              <div className="max-h-96 overflow-y-auto">
                {filteredProjects.map(project => (
                  <div
                    key={project.id}
                    className={`p-4 border-b cursor-pointer hover:bg-gray-50 ${
                      selectedProject?.id === project.id ? 'bg-blue-50 border-l-4 border-l-blue-500' : ''
                    }`}
                    onClick={() => {
                      setSelectedProject(project);
                      fetchProjectFolders(project.id);
                    }}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          {getProjectIcon(project.user_permission)}
                          <h3 className="font-medium text-sm">{project.name}</h3>
                        </div>
                        <p className="text-xs text-gray-500 mb-2">{project.client}</p>
                        <div className="flex items-center gap-2">
                          {getPermissionBadge(project.user_permission)}
                          <Badge variant="outline" className="text-xs">
                            {project.ship_type}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* 선택된 프로젝트 상세 */}
        <div className="lg:col-span-2">
          {selectedProject ? (
            <div className="space-y-4">
              {/* 프로젝트 정보 */}
              <Card>
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle className="text-xl">{selectedProject.name}</CardTitle>
                      <p className="text-gray-600 mt-1">{selectedProject.description}</p>
                    </div>
                    <div className="flex gap-2">
                      {getPermissionBadge(selectedProject.user_permission)}
                      <Button size="sm" variant="outline">
                        <Settings className="h-4 w-4 mr-2" />
                        설정
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">고객사</span>
                      <p className="font-medium">{selectedProject.client}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">선박 유형</span>
                      <p className="font-medium">{selectedProject.ship_type}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">상태</span>
                      <Badge variant={selectedProject.status === 'active' ? 'default' : 'secondary'}>
                        {selectedProject.status === 'active' ? '진행중' : '완료'}
                      </Badge>
                    </div>
                    <div>
                      <span className="text-gray-500">생성일</span>
                      <p className="font-medium">
                        {new Date(selectedProject.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* 폴더 구조 */}
              <Card>
                <CardHeader>
                  <div className="flex justify-between items-center">
                    <CardTitle className="text-lg">폴더 구조</CardTitle>
                    <div className="flex gap-2">
                      <Button size="sm" variant="outline">
                        <Plus className="h-4 w-4 mr-2" />
                        폴더 추가
                      </Button>
                      <Button size="sm" variant="outline">
                        <Users className="h-4 w-4 mr-2" />
                        권한 관리
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  {folders.length > 0 ? (
                    <div className="space-y-1">
                      {renderFolderTree(buildFolderTree(folders))}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-gray-500">
                      <Folder className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                      <p>폴더가 없습니다.</p>
                      <p className="text-sm">새 폴더를 추가해보세요.</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          ) : (
            <Card>
              <CardContent className="flex items-center justify-center h-64">
                <div className="text-center text-gray-500">
                  <Folder className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                  <p>프로젝트를 선택해주세요.</p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProjectFolderView;

