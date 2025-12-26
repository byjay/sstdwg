import React, { useState, useEffect } from 'react';
import { Edit, Plus, Trash2, Calendar, BarChart3, FileText } from 'lucide-react';

const DrawingManagement = ({ projectId }) => {
  const [drawings, setDrawings] = useState([]);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [editingDrawing, setEditingDrawing] = useState(null);
  const [currentUser, setCurrentUser] = useState(null);
  const [ganttView, setGanttView] = useState(false);

  useEffect(() => {
    fetchDrawings();
    fetchCurrentUser();
  }, [projectId]);

  const fetchCurrentUser = async () => {
    try {
      const response = await fetch('/api/user/profile');
      if (response.ok) {
        const user = await response.json();
        setCurrentUser(user);
      }
    } catch (error) {
      console.error('Error fetching user:', error);
    }
  };

  const fetchDrawings = async () => {
    try {
      const response = await fetch(`/api/drawings/${projectId}`);
      if (response.ok) {
        const data = await response.json();
        setDrawings(data);
      }
    } catch (error) {
      console.error('Error fetching drawings:', error);
    }
  };

  const handleAddDrawing = async (drawingData) => {
    try {
      const response = await fetch('/api/drawings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ...drawingData, project_id: projectId }),
      });

      if (response.ok) {
        fetchDrawings();
        setShowAddDialog(false);
      } else {
        const error = await response.json();
        alert(error.error || 'Failed to create drawing');
      }
    } catch (error) {
      console.error('Error creating drawing:', error);
      alert('Failed to create drawing');
    }
  };

  const handleUpdateDrawing = async (drawingId, updateData) => {
    try {
      const response = await fetch(`/api/drawings/${drawingId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updateData),
      });

      if (response.ok) {
        fetchDrawings();
        setEditingDrawing(null);
      } else {
        const error = await response.json();
        alert(error.error || 'Failed to update drawing');
      }
    } catch (error) {
      console.error('Error updating drawing:', error);
      alert('Failed to update drawing');
    }
  };

  const handleDeleteDrawing = async (drawingId) => {
    if (!confirm('Are you sure you want to delete this drawing?')) return;

    try {
      const response = await fetch(`/api/drawings/${drawingId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        fetchDrawings();
      } else {
        const error = await response.json();
        alert(error.error || 'Failed to delete drawing');
      }
    } catch (error) {
      console.error('Error deleting drawing:', error);
      alert('Failed to delete drawing');
    }
  };

  const canEdit = (drawing) => {
    return currentUser && (
      currentUser.role === 'admin' || 
      drawing.assigned_to === currentUser.id
    );
  };

  const canDelete = () => {
    return currentUser && currentUser.role === 'admin';
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'in_progress': return 'bg-blue-100 text-blue-800';
      case 'on_hold': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getTypeColor = (type) => {
    switch (type) {
      case 'BASIC': return 'bg-blue-100 text-blue-800';
      case 'APPROVAL': return 'bg-orange-100 text-orange-800';
      case 'PRODUCTION': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (ganttView) {
    return <GanttChart projectId={projectId} onBack={() => setGanttView(false)} />;
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">도면 관리</h2>
        <div className="flex space-x-2">
          <button
            onClick={() => setGanttView(true)}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <BarChart3 className="w-4 h-4 mr-2" />
            간트차트
          </button>
          {currentUser && currentUser.role === 'admin' && (
            <button
              onClick={() => setShowAddDialog(true)}
              className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
            >
              <Plus className="w-4 h-4 mr-2" />
              도면 추가
            </button>
          )}
        </div>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  카테고리
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  도면번호
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  도면명
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  유형
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  진행률
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  상태
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  시작일
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  종료일
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  작업
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {drawings.map((drawing) => (
                <tr key={drawing.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {drawing.category}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {drawing.dwg_no}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    {drawing.name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getTypeColor(drawing.type)}`}>
                      {drawing.type}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div className="flex items-center">
                      <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full" 
                          style={{ width: `${drawing.progress}%` }}
                        ></div>
                      </div>
                      <span>{drawing.progress}%</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(drawing.status)}`}>
                      {drawing.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {drawing.start_date}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {drawing.end_date}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex space-x-2">
                      {canEdit(drawing) && (
                        <button
                          onClick={() => setEditingDrawing(drawing)}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          <Edit className="w-4 h-4" />
                        </button>
                      )}
                      {canDelete() && (
                        <button
                          onClick={() => handleDeleteDrawing(drawing.id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {showAddDialog && (
        <DrawingDialog
          onSave={handleAddDrawing}
          onCancel={() => setShowAddDialog(false)}
        />
      )}

      {editingDrawing && (
        <DrawingDialog
          drawing={editingDrawing}
          onSave={(data) => handleUpdateDrawing(editingDrawing.id, data)}
          onCancel={() => setEditingDrawing(null)}
        />
      )}
    </div>
  );
};

const DrawingDialog = ({ drawing, onSave, onCancel }) => {
  const [formData, setFormData] = useState({
    category: drawing?.category || 'COMMON',
    dwg_no: drawing?.dwg_no || '',
    name: drawing?.name || '',
    type: drawing?.type || 'BASIC',
    start_date: drawing?.start_date || '',
    end_date: drawing?.end_date || '',
    progress: drawing?.progress || 0,
    status: drawing?.status || 'planned',
    remarks: drawing?.remarks || ''
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h3 className="text-lg font-semibold mb-4">
          {drawing ? '도면 수정' : '새 도면 추가'}
        </h3>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              카테고리
            </label>
            <select
              value={formData.category}
              onChange={(e) => setFormData({ ...formData, category: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
              required
            >
              <option value="COMMON">COMMON</option>
              <option value="HULL">HULL</option>
              <option value="ACCOMMODATION">ACCOMMODATION</option>
              <option value="OUTFITTING">OUTFITTING</option>
              <option value="PIPING">PIPING</option>
              <option value="ELECTRICAL">ELECTRICAL</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              도면번호
            </label>
            <input
              type="text"
              value={formData.dwg_no}
              onChange={(e) => setFormData({ ...formData, dwg_no: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              도면명
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              유형
            </label>
            <select
              value={formData.type}
              onChange={(e) => setFormData({ ...formData, type: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
              required
            >
              <option value="BASIC">BASIC</option>
              <option value="APPROVAL">APPROVAL</option>
              <option value="PRODUCTION">PRODUCTION</option>
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                시작일
              </label>
              <input
                type="date"
                value={formData.start_date}
                onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                className="w-full border border-gray-300 rounded-md px-3 py-2"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                종료일
              </label>
              <input
                type="date"
                value={formData.end_date}
                onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                className="w-full border border-gray-300 rounded-md px-3 py-2"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                진행률 (%)
              </label>
              <input
                type="number"
                min="0"
                max="100"
                value={formData.progress}
                onChange={(e) => setFormData({ ...formData, progress: parseInt(e.target.value) })}
                className="w-full border border-gray-300 rounded-md px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                상태
              </label>
              <select
                value={formData.status}
                onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                className="w-full border border-gray-300 rounded-md px-3 py-2"
              >
                <option value="planned">계획됨</option>
                <option value="in_progress">진행중</option>
                <option value="completed">완료</option>
                <option value="on_hold">보류</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              비고
            </label>
            <textarea
              value={formData.remarks}
              onChange={(e) => setFormData({ ...formData, remarks: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
              rows="3"
            />
          </div>

          <div className="flex justify-end space-x-2 pt-4">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              취소
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              저장
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const GanttChart = ({ projectId, onBack }) => {
  const [ganttData, setGanttData] = useState([]);

  useEffect(() => {
    fetchGanttData();
  }, [projectId]);

  const fetchGanttData = async () => {
    try {
      const response = await fetch(`/api/drawings/gantt/${projectId}`);
      if (response.ok) {
        const data = await response.json();
        setGanttData(data);
      }
    } catch (error) {
      console.error('Error fetching gantt data:', error);
    }
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">간트차트</h2>
        <button
          onClick={onBack}
          className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
        >
          목록으로
        </button>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <div className="overflow-x-auto">
          <div className="min-w-full">
            {ganttData.map((item, index) => (
              <div key={item.id} className="flex items-center py-2 border-b border-gray-200">
                <div className="w-64 pr-4">
                  <div className="text-sm font-medium text-gray-900 truncate">
                    {item.name}
                  </div>
                  <div className="text-xs text-gray-500">
                    {item.category} - {item.type}
                  </div>
                </div>
                <div className="flex-1 relative">
                  <div className="h-6 bg-gray-200 rounded">
                    <div 
                      className="h-6 bg-blue-500 rounded flex items-center justify-center text-xs text-white"
                      style={{ width: `${Math.max(item.progress, 10)}%` }}
                    >
                      {item.progress}%
                    </div>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {item.start} ~ {item.end}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DrawingManagement;

