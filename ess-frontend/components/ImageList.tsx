'use client';

import React, { useState } from 'react';
import { ImageItem } from '@/lib/types';
import { downloadEncrypted, downloadDecrypted, deleteImage } from '@/lib/api';
import { saveAs } from 'file-saver';
import { Trash2 } from 'lucide-react';

interface ImageListProps {
  images: ImageItem[];
  onDelete?: () => void;
}

export default function ImageList({ images, onDelete }: ImageListProps) {
  const [isDeleting, setIsDeleting] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null);

  const handleEncryptedDownload = async (item: ImageItem) => {
    try {
      const blob = await downloadEncrypted(item.name);
      saveAs(blob, `${item.name}_encrypted.tiff`);
    } catch (error) {
      console.error('Download failed:', error);
      alert('Failed to download encrypted image');
    }
  };

  const handleDecryptedDownload = async (item: ImageItem) => {
    const key = prompt('Enter decryption key:');
    if (!key) return;

    try {
      const baseFilename = item.name.replace(/_preview$/, '').replace(/_encrypted$/, '');
      const blob = await downloadDecrypted(baseFilename, key);
      saveAs(blob, `${baseFilename}_decrypted.tiff`);
    } catch (error) {
      console.error('Decryption failed:', error);
      alert('Failed to decrypt image. Please check your key.');
    }
  };

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <table className="min-w-full">
        <thead>
          <tr className="bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
            <th className="px-6 py-3">Name</th>
            <th className="px-6 py-3">Preview</th>
            <th className="px-6 py-3">Last Modified</th>
            <th className="px-6 py-3">Actions</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {images.map((image) => (
            <tr key={image.id} className="hover:bg-gray-50">
              <td className="px-6 py-4">
                <div className="flex items-center">
                  <svg className="w-5 h-5 text-gray-400 mr-2" viewBox="0 0 20 20" fill="currentColor">
                    <path d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" />
                  </svg>
                  <span className="text-sm font-medium text-gray-900">{image.name}</span>
                </div>
              </td>
              <td className="px-6 py-4">
                <img
                  src={`http://localhost:8000${image.preview}`}
                  alt={image.name}
                  className="h-12 w-12 object-cover rounded"
                />
              </td>
              <td className="px-6 py-4 text-sm text-gray-500">
                {new Date().toLocaleDateString()}
              </td>
              <td className="px-6 py-4 text-sm">
                <div className="flex gap-2">
                  <button
                    onClick={() => handleEncryptedDownload(image)}
                    className="text-gray-600 hover:text-gray-900"
                  >
                    Download Encrypted
                  </button>
                  <button
                    onClick={() => handleDecryptedDownload(image)}
                    className="text-blue-600 hover:text-blue-900"
                  >
                    Decrypt & Download
                  </button>
                  <button
                    onClick={() => setShowDeleteConfirm(image.id)}
                    className="text-red-600 hover:text-red-900"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-medium mb-4">Confirm Delete</h3>
            <p className="text-gray-600 mb-4">
              Are you sure you want to delete this image? This action cannot be undone.
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowDeleteConfirm(null)}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
                disabled={isDeleting !== null}
              >
                Cancel
              </button>
              <button
                onClick={async () => {
                  const image = images.find(img => img.id === showDeleteConfirm);
                  if (!image) return;

                  try {
                    setIsDeleting(image.id);
                    await deleteImage(image.id);
                    setShowDeleteConfirm(null);
                    onDelete?.();
                  } catch (error) {
                    console.error('Delete failed:', error);
                    alert('Failed to delete image');
                  } finally {
                    setIsDeleting(null);
                  }
                }}
                disabled={isDeleting !== null}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
              >
                {isDeleting === showDeleteConfirm ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 