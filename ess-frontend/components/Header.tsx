import React, { useState, useEffect } from 'react';
import { SearchBar } from './SearchBar';
import { useRouter } from 'next/navigation';
import { API_BASE } from '@/lib/api';

interface HeaderProps {
  viewMode: 'grid' | 'list';
  onViewModeChange: (mode: 'grid' | 'list') => void;
  onSearch: (query: string) => void;
  currentFolder: string | null;
  searchQuery: string;
}

export function Header({ viewMode, onViewModeChange, onSearch, currentFolder, searchQuery }: HeaderProps) {
  const router = useRouter();
  const [userEmail, setUserEmail] = useState('');

  useEffect(() => {
    const fetchUser = async () => {
      const token = localStorage.getItem('token');
      if (!token) return;

      try {
        const response = await fetch(`${API_BASE}/api/users/me`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
        
        if (response.ok) {
          const data = await response.json();
          setUserEmail(data.email);
        }
      } catch (error) {
        console.error('Failed to fetch user info:', error);
      }
    };

    fetchUser();
  }, []);

  const handleLogout = () => {
    // Remove token from localStorage
    localStorage.removeItem('token');
    // Remove token from cookies
    document.cookie = 'token=; Max-Age=0; path=/;';
    // Redirect to login page
    router.push('/login');
  };

  return (
    <header className="h-16 bg-white border-b border-gray-200 fixed top-0 left-0 right-0 z-10">
      <div className="flex items-center h-full px-6">
        <div className="flex items-center gap-2 w-60">
          <img src="/logo.svg" alt="Logo" className="w-10 h-10" />
          <span className="text-xl text-gray-800">Secure Drive</span>
        </div>

        <div className="flex-1 max-w-2xl mx-4">
          <SearchBar onSearch={onSearch} currentFolder={currentFolder} />
        </div>

        <div className="flex items-center gap-4">
          <button
            onClick={() => onViewModeChange('grid')}
            className={`p-2 rounded-full ${
              viewMode === 'grid' ? 'bg-gray-100' : 'hover:bg-gray-100'
            }`}
          >
            <svg className="w-6 h-6 text-gray-700" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1v-4zM14 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM14 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
            </svg>
          </button>
          <button
            onClick={() => onViewModeChange('list')}
            className={`p-2 rounded-full ${
              viewMode === 'list' ? 'bg-gray-100' : 'hover:bg-gray-100'
            }`}
          >
            <svg className="w-6 h-6 text-gray-700" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <div className="text-sm text-gray-600 mr-4">
            {userEmail}
          </div>
          <button
            onClick={handleLogout}
            className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
          >
            Logout
          </button>
        </div>
      </div>
    </header>
  );
} 