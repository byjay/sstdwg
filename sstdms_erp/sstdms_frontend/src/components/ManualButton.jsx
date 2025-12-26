import React, { useState } from 'react';
import ManualModal from './ManualModal';

const ManualButton = ({ userCategory = 'user' }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleOpenManual = () => {
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
  };

  return (
    <>
      {/* 매뉴얼 버튼 - 우하단 고정 */}
      <div className="fixed bottom-6 right-6 z-50">
        <button
          onClick={handleOpenManual}
          className="bg-blue-600 hover:bg-blue-700 text-white p-4 rounded-full shadow-lg transition-all duration-300 hover:scale-110 group"
          title="사용자 매뉴얼"
        >
          <svg 
            className="w-6 h-6" 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" 
            />
          </svg>
          
          {/* 툴팁 */}
          <div className="absolute bottom-full right-0 mb-2 px-3 py-1 bg-gray-800 text-white text-sm rounded opacity-0 group-hover:opacity-100 transition-opacity duration-300 whitespace-nowrap">
            {userCategory === 'admin' || userCategory === 'registrar' 
              ? '등록자 매뉴얼' 
              : '사용자 매뉴얼'
            }
            <div className="absolute top-full right-4 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-800"></div>
          </div>
        </button>
      </div>

      {/* 매뉴얼 모달 */}
      {isModalOpen && (
        <ManualModal 
          isOpen={isModalOpen}
          onClose={handleCloseModal}
          userCategory={userCategory}
        />
      )}
    </>
  );
};

export default ManualButton;

