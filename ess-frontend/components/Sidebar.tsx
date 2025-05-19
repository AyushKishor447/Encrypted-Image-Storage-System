'use client';

import React, { useState, useEffect } from 'react';
import { Star, Clock, FolderIcon, Plus, ChevronRight, ChevronDown } from 'lucide-react';
import { Modal } from './Modal';
import axios from 'axios';

interface Folder {
  id: string;
  name: string;
  type: string;
  parent_folder: string | null;
  created_at: string;
}

interface SidebarProps {
  currentFolder: string | null;
  onFolderSelect: (folderId: string | null) => void;
  onViewStarred: () => void;
  onViewRecent: () => void;
}

export function Sidebar({ currentFolder, onFolderSelect, onViewStarred, onViewRecent }: SidebarProps) {
  const [folders, setFolders] = useState<Folder[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showNewFolderDialog, setShowNewFolderDialog] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());
  const [token, setToken] = useState<string | null>(null);
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      setIsClient(true);
      const t = localStorage.getItem('token');
      setToken(t);
    }
  }, []);

  useEffect(() => {
    if (isClient && token) {
      console.log('Token in Sidebar:', token);
      fetchFolders(token);
    }
  }, [isClient, token]);

  const fetchFolders = async (token: string) => {
    try {
      setIsLoading(true);
      setError(null);
      console.log('About to fetch folders with token:', token);
      const res = await axios.get('http://localhost:8000/api/folders', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      console.log('Fetched folders:', res.data);
      // Ensure we're working with an array of valid folder objects
      const validFolders = Array.isArray(res.data) ? res.data.filter((folder): folder is Folder => {
        return folder &&
          typeof folder === 'object' &&
          typeof folder.id === 'string' &&
          typeof folder.name === 'string';
      }) : [];
      setFolders(validFolders);
    } catch (error) {
      console.error('Failed to fetch folders:', error);
      setError('Failed to load folders');
      setFolders([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateFolder = async () => {
    if (!newFolderName.trim()) return;

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('No authentication token found');
      }

      console.log('Creating folder:', newFolderName);
      const formData = new FormData();
      formData.append('name', newFolderName);
      if (currentFolder) {
        formData.append('parent_folder', currentFolder);
      }

      const response = await fetch('http://localhost:8000/api/folders', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Error response:', errorText);
        try {
          const error = JSON.parse(errorText);
          throw new Error(error.detail || 'Failed to create folder');
        } catch (e) {
          throw new Error(errorText || 'Failed to create folder');
        }
      }

      const newFolder = await response.json();
      console.log('Created new folder:', newFolder);
      setFolders(prevFolders => [...prevFolders, newFolder]);
      setShowNewFolderDialog(false);
      setNewFolderName('');
      
      // Refresh the folders list
      await fetchFolders(token);
    } catch (error) {
      console.error('Failed to create folder:', error);
      alert(error instanceof Error ? error.message : 'Failed to create folder');
    }
  };

  const toggleFolder = (folderId: string) => {
    const newExpanded = new Set(expandedFolders);
    if (newExpanded.has(folderId)) {
      newExpanded.delete(folderId);
    } else {
      newExpanded.add(folderId);
    }
    setExpandedFolders(newExpanded);
  };

  const renderFolderTree = (parentId: string | null = null, level = 0) => {
    const childFolders = folders.filter(f => f.parent_folder === parentId);
    
    if (childFolders.length === 0) {
      return null;
    }
    
    return childFolders.map(folder => (
      <div key={folder.id} style={{ marginLeft: `${level * 16}px` }}>
        <button
          onClick={() => onFolderSelect(folder.id)}
          className={`flex items-center gap-2 w-full px-4 py-2 text-sm ${
            currentFolder === folder.id ? 'bg-blue-50 text-blue-600' : 'text-gray-700 hover:bg-gray-50'
          }`}
        >
          {folders.some(f => f.parent_folder === folder.id) && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                toggleFolder(folder.id);
              }}
              className="p-1"
            >
              {expandedFolders.has(folder.id) ? (
                <ChevronDown className="w-4 h-4" />
              ) : (
                <ChevronRight className="w-4 h-4" />
              )}
            </button>
          )}
          <FolderIcon className="w-4 h-4" />
          <span className="truncate">{folder.name}</span>
        </button>
        {expandedFolders.has(folder.id) && renderFolderTree(folder.id, level + 1)}
      </div>
    ));
  };

  // Only render sidebar if token is present and we're on the client
  if (!isClient || !token) {
    return null;
  }

  return (
    <div className="w-60 h-screen bg-white border-r border-gray-200 flex-shrink-0 fixed left-0 top-0 pt-16">
      <div className="p-4">
        <button
          onClick={() => setShowNewFolderDialog(true)}
          className="flex items-center gap-3 px-6 py-3 rounded-full shadow-sm bg-white hover:bg-gray-50 border border-gray-300 w-full"
        >
          <Plus className="w-5 h-5" />
          <span className="font-medium">New</span>
        </button>
      </div>
      
      <nav className="mt-2">
        <button
          onClick={() => onFolderSelect(null)}
          className={`flex items-center gap-3 px-6 py-2 w-full ${
            currentFolder === null ? 'text-blue-600 bg-blue-50' : 'text-gray-700 hover:bg-gray-50'
          }`}
        >
          <FolderIcon className="w-5 h-5" />
          <span>All Images</span>
        </button>

        <button
          onClick={onViewStarred}
          className="flex items-center gap-3 px-6 py-2 w-full text-gray-700 hover:bg-gray-50"
        >
          <Star className="w-5 h-5" />
          <span>Starred</span>
        </button>

        <button
          onClick={onViewRecent}
          className="flex items-center gap-3 px-6 py-2 w-full text-gray-700 hover:bg-gray-50"
        >
          <Clock className="w-5 h-5" />
          <span>Recent</span>
        </button>

        <div className="mt-4">
          <div className="px-6 py-2 text-xs font-semibold text-gray-500 uppercase">Folders</div>
          {isLoading ? (
            <div className="px-6 py-4 text-sm text-gray-500">Loading folders...</div>
          ) : error ? (
            <div className="px-6 py-4 text-sm text-red-500">{error}</div>
          ) : folders.length === 0 ? (
            <div className="px-6 py-4 text-sm text-gray-500">No folders yet</div>
          ) : (
            renderFolderTree()
          )}
        </div>
      </nav>

      <Modal
        isOpen={showNewFolderDialog}
        onClose={() => {
          setShowNewFolderDialog(false);
          setNewFolderName('');
        }}
      >
        <div className="w-[400px] p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Create New Folder</h3>
          <input
            type="text"
            value={newFolderName}
            onChange={(e) => setNewFolderName(e.target.value)}
            placeholder="Enter folder name"
            className="w-full p-2 border border-gray-300 rounded-md mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500"
            autoFocus
          />
          <div className="flex justify-end gap-2">
            <button
              onClick={() => {
                setShowNewFolderDialog(false);
                setNewFolderName('');
              }}
              className="px-4 py-2 text-gray-600 hover:text-gray-800 font-medium"
            >
              Cancel
            </button>
            <button
              onClick={handleCreateFolder}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium transition-colors"
            >
              Create
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
} 