import React from 'react';
import { SearchBar } from './SearchBar';

interface HeaderProps {
  viewMode: 'grid' | 'list';
  onViewModeChange: (mode: 'grid' | 'list') => void;
  onSearch: (query: string) => void;
  currentFolder: string | null;
  searchQuery: string;
}

export function Header({ viewMode, onViewModeChange, onSearch, currentFolder, searchQuery }: HeaderProps) {
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
        </div>
      </div>
    </header>
  );
} 