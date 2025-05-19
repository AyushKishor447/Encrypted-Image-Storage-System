'use client';

import dynamic from 'next/dynamic';
import { useState, useEffect } from 'react';
import { Header } from '@/components/Header';
import { Sidebar } from '@/components/Sidebar';
import { UploadButton } from '@/components/UploadButton';
import { listImages } from '@/lib/api';
import { ImageItem } from '@/lib/types';
import { SearchBar } from '@/components/SearchBar';

// Dynamically import components that need to be client-side only
const ImageCard = dynamic(() => import('@/components/ImageCard'), { ssr: false });
const ImageList = dynamic(() => import('@/components/ImageList'), { ssr: false });

type ViewMode = 'grid' | 'list';
type ContentView = 'all' | 'starred' | 'recent' | 'folder';

export default function Home() {
  const [images, setImages] = useState<ImageItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [contentView, setContentView] = useState<ContentView>('all');
  const [currentFolder, setCurrentFolder] = useState<string | null>(null);
  const [folders, setFolders] = useState<Array<{id: string, name: string}>>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [ready, setReady] = useState(false);
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      setToken(localStorage.getItem('token'));
      setReady(true);
    }
  }, []);

  const loadImages = async () => {
    if (!token) return;
    
    try {
      setIsLoading(true);
      let url = 'http://localhost:8000/api/items';
      if (contentView === 'starred') {
        url = 'http://localhost:8000/api/items/starred';
      } else if (contentView === 'recent') {
        url = 'http://localhost:8000/api/items/recent';
      } else if (contentView === 'folder' && currentFolder) {
        url += `?folder=${currentFolder}`;
      }
      if (searchQuery && contentView !== 'starred' && contentView !== 'recent') {
        url += (url.includes('?') ? '&' : '?') + `search=${searchQuery}`;
      }

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch images');
      }

      const data = await response.json();
      setImages(data);
    } catch (error) {
      console.error('Failed to load images:', error);
      setImages([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      loadImages();
    }
  }, [token, contentView, currentFolder, searchQuery]);

  const handleFolderSelect = (folderId: string | null) => {
    setCurrentFolder(folderId);
    setContentView(folderId ? 'folder' : 'all');
  };

  const handleViewStarred = () => {
    setContentView('starred');
    setCurrentFolder(null);
  };

  const handleViewRecent = () => {
    setContentView('recent');
    setCurrentFolder(null);
  };

  const handleStarItem = async (itemId: string, isStarred: boolean) => {
    if (!token) return;
    try {
      const response = await fetch(`http://localhost:8000/api/items/${itemId}/${isStarred ? 'unstar' : 'star'}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (!response.ok) throw new Error('Failed to update star status');
      
      // Refresh the images to update the UI
      loadImages();
    } catch (error) {
      console.error('Failed to update star status:', error);
      alert('Failed to update star status');
    }
  };

  const handleSearch = (query: string) => {
    setSearchQuery(query);
  };

  if (!ready) {
    return null; // Only render after client-side mount and token is available
  }

  const getViewTitle = () => {
    switch (contentView) {
      case 'starred':
        return 'Starred Images';
      case 'recent':
        return 'Recent Images';
      case 'folder':
        return currentFolder || 'My Images';
      default:
        return 'My Images';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header 
        viewMode={viewMode} 
        onViewModeChange={setViewMode} 
        onSearch={handleSearch}
        currentFolder={contentView === 'folder' ? currentFolder : null}
        searchQuery={searchQuery}
      />
      <Sidebar
        currentFolder={currentFolder}
        onFolderSelect={handleFolderSelect}
        onViewStarred={handleViewStarred}
        onViewRecent={handleViewRecent}
      />
      
      <main className="pl-60 pt-16">
        <div className="p-8">
          <div className="mb-6 flex items-center justify-between">
            <h2 className="text-lg font-medium text-gray-900">{getViewTitle()}</h2>
            <div className="flex items-center gap-4">
              <button className="text-sm text-gray-600 hover:text-gray-900">
                Last modified ▼
              </button>
            </div>
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
            </div>
          ) : images.length === 0 ? (
            <div className="text-center py-12 bg-white rounded-lg shadow">
              <svg
                className="mx-auto h-12 w-12 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                />
              </svg>
              <h3 className="mt-4 text-lg font-medium text-gray-900">No images yet</h3>
              <p className="mt-2 text-gray-600">
                {contentView === 'starred'
                  ? 'Star some images to see them here'
                  : contentView === 'recent'
                  ? 'Recently viewed images will appear here'
                  : 'Upload your first image to get started'}
              </p>
            </div>
          ) : viewMode === 'grid' ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
              {images.map((image) => (
                <ImageCard
                  key={image.id}
                  item={image}
                  onDelete={loadImages}
                  onStar={() => handleStarItem(image.id, image.starred)}
                  folders={folders}
                />
              ))}
            </div>
          ) : (
            <ImageList
              images={images}
              onDelete={loadImages}
            />
          )}
        </div>
      </main>

      <UploadButton 
        onUploadComplete={loadImages} 
        currentFolder={contentView === 'folder' ? currentFolder : null} 
      />
    </div>
  );
} 