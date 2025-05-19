'use client';

import { useState, useEffect } from 'react';
import { ImageItem } from '@/lib/types';
import { downloadEncrypted, downloadDecrypted, deleteImage } from '@/lib/api';
import { saveAs } from 'file-saver';
import { Trash2, Star, FolderIcon } from 'lucide-react';

interface ImageCardProps {
  item: ImageItem;
  onDelete?: () => void;
  onStar?: () => void;
  folders?: Array<{ id: string; name: string }>;
}

export default function ImageCard({ item, onDelete, onStar, folders = [] }: ImageCardProps) {
  const [isDownloading, setIsDownloading] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showKeyDialog, setShowKeyDialog] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showMoveDialog, setShowMoveDialog] = useState(false);
  const [key, setKey] = useState('');

  useEffect(() => {
    // Log item details when component mounts
    console.log('ImageCard mounted with item:', {
      id: item.id,
      name: item.name,
      preview: item.preview,
      type: item.type
    });
  }, [item]);

  // Get base filename without any suffixes
  const baseFilename = item.name.replace(/_preview$/, '').replace(/_encrypted$/, '');

  const handleEncryptedDownload = async () => {
    if (isDownloading) return;
    
    try {
      setIsDownloading(true);
      const blob = await downloadEncrypted(item.name);
      
      // Only try to save if we got a valid blob
      if (blob.size > 0) {
        saveAs(blob, `${baseFilename}_encrypted.tiff`);
      } else {
        console.warn('Received empty blob, skipping save');
      }
    } catch (error) {
      console.error('Download failed:', error);
      // Only show alert for actual errors, not for successful downloads
      if (error instanceof Error && 
          !error.message.includes('NetworkError') && 
          !error.message.includes('Failed to fetch')) {
        alert(error.message);
      }
    } finally {
      setIsDownloading(false);
    }
  };

  const handleDecryptedDownload = async () => {
    if (!key.trim()) {
      alert('Please enter a decryption key');
      return;
    }

    if (isDownloading) return;

    try {
      setIsDownloading(true);
      const blob = await downloadDecrypted(baseFilename, key);
      
      // Only try to save if we got a valid blob
      if (blob.size > 0) {
        saveAs(blob, `${baseFilename}_decrypted.tiff`);
        setShowKeyDialog(false);
        setKey('');
      } else {
        console.warn('Received empty blob, skipping save');
      }
    } catch (error: any) {
      console.error('Decryption failed:', error);
      // Only show alert for actual errors
      if (error.message && 
          !error.message.includes('NetworkError') && 
          !error.message.includes('Failed to fetch')) {
        alert(error.message);
      }
    } finally {
      setIsDownloading(false);
    }
  };

  const handleDelete = async () => {
    if (isDeleting) return;

    try {
      setIsDeleting(true);
      console.log('Starting delete operation:', {
        itemId: item.id,        // This contains the full filename with suffixes
        itemName: item.name,    // This is the clean filename
        baseFilename,           // Same as item.name
        preview: item.preview
      });

      // Pass the clean filename to deleteImage
      await deleteImage(baseFilename);
      console.log('Delete operation completed successfully');
      setShowDeleteConfirm(false);
      onDelete?.();
    } catch (error) {
      console.error('Delete operation failed:', {
        error,
        itemId: item.id,
        itemName: item.name,
        baseFilename
      });
      if (error instanceof Error) {
        alert(`Failed to delete image: ${error.message}`);
      }
    } finally {
      setIsDeleting(false);
    }
  };

  const handleMove = async (folderId: string | null) => {
    try {
      const formData = new FormData();
      if (folderId) {
        formData.append('folder_id', folderId);
      }

      const response = await fetch(`http://localhost:8000/api/items/${item.id}/move`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to move item');
      }

      // Close the dialog and refresh the view
      setShowMoveDialog(false);
      onDelete?.(); // Use the onDelete callback to refresh the view
    } catch (error) {
      console.error('Failed to move item:', error);
      alert('Failed to move item to folder');
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      <div className="aspect-square relative group">
        <img
          src={`http://localhost:8000${item.preview}`}
          alt={baseFilename}
          className="w-full h-full object-cover"
          onError={(e) => {
            console.error('Image preview failed to load:', {
              src: e.currentTarget.src,
              itemPreview: item.preview,
              itemId: item.id
            });
          }}
        />
        <div className="absolute top-2 right-2 flex gap-2">
          <button
            onClick={() => setShowMoveDialog(true)}
            className="p-2 bg-white/80 text-gray-600 rounded-full opacity-0 group-hover:opacity-100 transition-opacity hover:bg-white"
            title="Move to folder"
          >
            <FolderIcon className="w-4 h-4" />
          </button>
          <button
            onClick={() => onStar?.()}
            className={`p-2 rounded-full ${
              item.starred
                ? 'bg-yellow-400 text-white'
                : 'bg-white/80 text-gray-600'
            } opacity-0 group-hover:opacity-100 transition-opacity hover:scale-110`}
            title={item.starred ? 'Unstar image' : 'Star image'}
          >
            <Star className="w-4 h-4" fill={item.starred ? 'currentColor' : 'none'} />
          </button>
          <button
            onClick={() => setShowDeleteConfirm(true)}
            className="p-2 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-600"
            title="Delete image"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
      <div className="p-4">
        <h3 className="font-medium text-gray-900 truncate">{baseFilename}</h3>
        {item.parent_folder && (
          <p className="text-sm text-gray-500 mt-1">
            In folder: {folders.find(f => f.id === item.parent_folder)?.name || item.parent_folder}
          </p>
        )}
        <div className="mt-4 flex gap-2">
          <button
            onClick={handleEncryptedDownload}
            disabled={isDownloading || isDeleting}
            className="px-3 py-1 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 text-sm disabled:opacity-50"
          >
            {isDownloading ? 'Downloading...' : 'Download Encrypted'}
          </button>
          <button
            onClick={() => setShowKeyDialog(true)}
            disabled={isDownloading || isDeleting}
            className="px-3 py-1 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm disabled:opacity-50"
          >
            Decrypt & Download
          </button>
        </div>
      </div>

      {showKeyDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-medium mb-4">Enter Decryption Key</h3>
            <input
              type="text"
              value={key}
              onChange={(e) => setKey(e.target.value)}
              placeholder="Enter key (e.g., 1.23, 4.56, 7.89, 0.12, 3.45)"
              className="w-full p-2 border rounded mb-4"
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={() => {
                  setShowKeyDialog(false);
                  setKey('');
                }}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                Cancel
              </button>
              <button
                onClick={handleDecryptedDownload}
                disabled={isDownloading}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                {isDownloading ? 'Decrypting...' : 'Decrypt & Download'}
              </button>
            </div>
          </div>
        </div>
      )}

      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-medium mb-4">Confirm Delete</h3>
            <p className="text-gray-600 mb-4">
              Are you sure you want to delete this image? This action cannot be undone.
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
                disabled={isDeleting}
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                disabled={isDeleting}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
              >
                {isDeleting ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}

      {showMoveDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-[99999]">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-medium mb-4">Move to Folder</h3>
            <div className="space-y-2 max-h-60 overflow-y-auto">
              <button
                onClick={() => handleMove(null)}
                className="w-full text-left px-4 py-2 hover:bg-gray-50 rounded-md"
              >
                Root (No folder)
              </button>
              {folders.map(folder => (
                <button
                  key={folder.id}
                  onClick={() => handleMove(folder.id)}
                  className="w-full text-left px-4 py-2 hover:bg-gray-50 rounded-md"
                >
                  {folder.name}
                </button>
              ))}
            </div>
            <div className="flex justify-end gap-2 mt-4">
              <button
                onClick={() => setShowMoveDialog(false)}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 