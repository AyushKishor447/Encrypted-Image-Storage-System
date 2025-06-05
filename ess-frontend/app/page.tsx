'use client';

import dynamic from 'next/dynamic';
import { useState, useEffect } from 'react';
import { Header } from '@/components/Header';
import { Sidebar } from '@/components/Sidebar';
import { UploadButton } from '@/components/UploadButton';
import { listImages, API_BASE } from '@/lib/api';
import { ImageItem } from '@/lib/types';
import { SearchBar } from '@/components/SearchBar';
import { Trash2, Share2 } from 'lucide-react';
import { Modal } from '@/components/Modal';
import ShareDialog from '@/components/ShareDialog';

// Dynamically import components that need to be client-side only
const ImageCard = dynamic(() => import('@/components/ImageCard'), { ssr: false });
const ImageList = dynamic(() => import('@/components/ImageList'), { ssr: false });

type ViewMode = 'grid' | 'list';
type ContentView = 'all' | 'starred' | 'recent' | 'folder' | 'shared';

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
  const [selectedImages, setSelectedImages] = useState<string[]>([]);
  const [showBulkDeleteConfirm, setShowBulkDeleteConfirm] = useState(false);
  const [showShareDialog, setShowShareDialog] = useState(false);

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
      let url = `${API_BASE}/api/items`;
      if (contentView === 'shared') {
        url = `${API_BASE}/api/items?shared=true`;
      } else if (searchQuery && contentView !== 'starred' && contentView !== 'recent') {
        url = `${API_BASE}/api/search?query=` + encodeURIComponent(searchQuery);
        if (contentView === 'folder' && currentFolder) {
          url += `&folder=${encodeURIComponent(currentFolder)}`;
        }
      } else if (contentView === 'starred') {
        url = `${API_BASE}/api/items/starred`;
      } else if (contentView === 'recent') {
        url = `${API_BASE}/api/items/recent`;
      } else if (contentView === 'folder' && currentFolder) {
        url += `?folder=${encodeURIComponent(currentFolder)}`;
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

  const handleViewShared = () => {
    setContentView('shared');
    setCurrentFolder(null);
  };

  const handleStarItem = async (itemId: string, isStarred: boolean) => {
    if (!token) return;
    try {
      const response = await fetch(`${API_BASE}/api/items/${itemId}/${isStarred ? 'unstar' : 'star'}`, {
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

  const handleSelectImage = (id: string, selected: boolean) => {
    setSelectedImages(prev => selected ? [...prev, id] : prev.filter(i => i !== id));
  };

  const handleSelectAll = () => {
    setSelectedImages(images.map(img => img.id));
  };

  const handleDeselectAll = () => {
    setSelectedImages([]);
  };

  const handleBulkDelete = async () => {
    if (!token) return;
    setShowBulkDeleteConfirm(false);
    for (const id of selectedImages) {
      await fetch(`${API_BASE}/api/delete/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` },
      });
    }
    setSelectedImages([]);
    loadImages();
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
      case 'shared':
        return 'Shared Images';
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
        onViewShared={handleViewShared}
      />
      
      <main className="pl-60 pt-16">
        <div className="p-8">
          {/* Bulk action toolbar */}
          {selectedImages.length > 0 && (
            <div className="mb-4 flex items-center gap-4 bg-blue-50 border border-blue-200 rounded p-3">
              <span>{selectedImages.length} selected</span>
              <button onClick={handleSelectAll} className="text-sm text-blue-600 hover:underline">Select all</button>
              <button onClick={handleDeselectAll} className="text-sm text-blue-600 hover:underline">Clear</button>
              <button onClick={() => setShowBulkDeleteConfirm(true)} className="flex items-center gap-1 px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700"><Trash2 className="w-4 h-4" /> Delete</button>
              <button onClick={() => setShowShareDialog(true)} className="flex items-center gap-1 px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"><Share2 className="w-4 h-4" /> Share</button>
            </div>
          )}
          <Modal isOpen={showBulkDeleteConfirm} onClose={() => setShowBulkDeleteConfirm(false)}>
            <div className="w-[400px] p-6">
              <h3 className="text-lg font-medium mb-4">Confirm Delete</h3>
              <p className="mb-4">Are you sure you want to delete <b>{selectedImages.length}</b> images? This action cannot be undone.</p>
              <div className="flex justify-end gap-2">
                <button
                  onClick={() => setShowBulkDeleteConfirm(false)}
                  className="px-4 py-2 text-gray-600 hover:text-gray-800"
                >Cancel</button>
                <button
                  onClick={handleBulkDelete}
                  className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                >Delete</button>
              </div>
            </div>
          </Modal>
          <ShareDialog
            isOpen={showShareDialog}
            onClose={() => setShowShareDialog(false)}
            imageIds={selectedImages}
            onShared={() => {
              setShowShareDialog(false);
              setSelectedImages([]);
            }}
          />
          <div className="mb-6">
            <h2 className="text-lg font-medium text-gray-900">{getViewTitle()}</h2>
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
                  : contentView === 'shared'
                  ? 'No shared images yet'
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
                  selected={selectedImages.includes(image.id)}
                  onSelect={handleSelectImage}
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