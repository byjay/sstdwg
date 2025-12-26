import React, { useState, useEffect } from 'react';

const ManualModal = ({ isOpen, onClose, userCategory = 'user' }) => {
  const [manualData, setManualData] = useState(null);
  const [currentSection, setCurrentSection] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);

  useEffect(() => {
    if (isOpen) {
      fetchManual();
    }
  }, [isOpen, userCategory]);

  const fetchManual = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/manual', {
        headers: {
          'Authorization': localStorage.getItem('session_token') || ''
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setManualData(data.manual);
        setCurrentSection(data.manual.sections[0]); // 첫 번째 섹션을 기본으로 설정
      } else {
        console.error('매뉴얼 로드 실패');
      }
    } catch (error) {
      console.error('매뉴얼 로드 오류:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSectionClick = (section) => {
    setCurrentSection(section);
    setSearchResults([]);
    setSearchQuery('');
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    try {
      const response = await fetch(`/api/manual/search?q=${encodeURIComponent(searchQuery)}`, {
        headers: {
          'Authorization': localStorage.getItem('session_token') || ''
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setSearchResults(data.results);
      }
    } catch (error) {
      console.error('검색 오류:', error);
    }
  };

  const handleDownload = async () => {
    try {
      const response = await fetch('/api/manual/download', {
        headers: {
          'Authorization': localStorage.getItem('session_token') || ''
        }
      });
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `SSTDMS_${userCategory}_manual.json`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (error) {
      console.error('다운로드 오류:', error);
    }
  };

  const formatContent = (content) => {
    // 마크다운 스타일 텍스트를 HTML로 간단 변환
    return content
      .replace(/^# (.*$)/gm, '<h1 class="text-2xl font-bold mb-4 text-blue-600">$1</h1>')
      .replace(/^## (.*$)/gm, '<h2 class="text-xl font-semibold mb-3 text-blue-500">$1</h2>')
      .replace(/^### (.*$)/gm, '<h3 class="text-lg font-medium mb-2 text-blue-400">$1</h3>')
      .replace(/^\- (.*$)/gm, '<li class="ml-4 mb-1">• $1</li>')
      .replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold">$1</strong>')
      .replace(/\*(.*?)\*/g, '<em class="italic">$1</em>')
      .replace(/`(.*?)`/g, '<code class="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono">$1</code>')
      .replace(/\n\n/g, '</p><p class="mb-4">')
      .replace(/\n/g, '<br>');
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full h-5/6 flex flex-col">
        {/* 헤더 */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <img 
                src="/assets/seastar_logo_compact.png" 
                alt="Seastar Design" 
                className="h-8 w-auto"
              />
              <div>
                <h2 className="text-2xl font-bold text-gray-800">
                  {manualData?.title || 'SSTDMS 매뉴얼'}
                </h2>
                <p className="text-sm text-gray-600">
                  개발자: {manualData?.developer || 'Seastar Design - 김봉정 (designsir@seastargo.com)'}
                </p>
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-500">
              v{manualData?.version || '1.0.0'}
            </span>
            <button
              onClick={handleDownload}
              className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 transition-colors text-sm"
              title="매뉴얼 다운로드"
            >
              다운로드
            </button>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* 검색 바 */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex space-x-2">
            <input
              type="text"
              placeholder="매뉴얼 내용 검색..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={handleSearch}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              검색
            </button>
          </div>
        </div>

        {/* 메인 콘텐츠 */}
        <div className="flex flex-1 overflow-hidden">
          {/* 사이드바 - 목차 */}
          <div className="w-1/3 border-r border-gray-200 overflow-y-auto">
            <div className="p-4">
              <h3 className="font-semibold text-gray-800 mb-3">목차</h3>
              
              {loading ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                  <p className="mt-2 text-gray-600">로딩 중...</p>
                </div>
              ) : (
                <ul className="space-y-1">
                  {manualData?.sections?.map((section) => (
                    <li key={section.id}>
                      <button
                        onClick={() => handleSectionClick(section)}
                        className={`w-full text-left px-3 py-2 rounded-md transition-colors ${
                          currentSection?.id === section.id
                            ? 'bg-blue-100 text-blue-700 font-medium'
                            : 'text-gray-700 hover:bg-gray-100'
                        }`}
                      >
                        {section.title}
                      </button>
                    </li>
                  ))}
                </ul>
              )}

              {/* 검색 결과 */}
              {searchResults.length > 0 && (
                <div className="mt-6">
                  <h4 className="font-semibold text-gray-800 mb-2">검색 결과</h4>
                  <ul className="space-y-1">
                    {searchResults.map((result, index) => (
                      <li key={index}>
                        <button
                          onClick={() => {
                            const section = manualData.sections.find(s => s.id === result.section_id);
                            if (section) handleSectionClick(section);
                          }}
                          className="w-full text-left px-3 py-2 rounded-md text-sm text-gray-600 hover:bg-gray-100"
                        >
                          <div className="font-medium">{result.title}</div>
                          <div className="text-xs text-gray-500 mt-1">{result.preview}</div>
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>

          {/* 메인 콘텐츠 영역 */}
          <div className="flex-1 overflow-y-auto">
            <div className="p-6">
              {loading ? (
                <div className="text-center py-12">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                  <p className="mt-4 text-gray-600">매뉴얼을 불러오는 중...</p>
                </div>
              ) : currentSection ? (
                <div>
                  <div className="mb-6 p-4 bg-blue-50 rounded-lg border-l-4 border-blue-400">
                    <div className="flex items-center space-x-2 mb-2">
                      <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span className="text-sm font-medium text-blue-800">
                        {userCategory === 'admin' || userCategory === 'registrar' ? '등록자용' : '사용자용'} 매뉴얼
                      </span>
                    </div>
                    <p className="text-sm text-blue-700">
                      {manualData.description}
                    </p>
                  </div>

                  <div 
                    className="prose prose-blue max-w-none"
                    dangerouslySetInnerHTML={{ 
                      __html: `<p class="mb-4">${formatContent(currentSection.content)}</p>` 
                    }}
                  />
                </div>
              ) : (
                <div className="text-center py-12">
                  <svg className="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                  <p className="text-gray-600">좌측 목차에서 섹션을 선택해주세요.</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* 푸터 */}
        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <div>
              <span className="font-medium">SSTDMS</span> - Seastar Design Technical Document Management System
            </div>
            <div>
              최종 업데이트: {manualData?.last_updated || '2025-07-31'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ManualModal;

