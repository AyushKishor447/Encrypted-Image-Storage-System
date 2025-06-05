import React, { useState } from 'react';
import { Modal } from './Modal';
import axios from 'axios';
import { API_BASE } from '@/lib/api';

interface ShareDialogProps {
  isOpen: boolean;
  onClose: () => void;
  imageIds: string[];
  onShared: () => void;
}

export default function ShareDialog({ isOpen, onClose, imageIds, onShared }: ShareDialogProps) {
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleShare = async () => {
    if (!email.trim()) {
      setError('Please enter an email address');
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API_BASE}/api/share`, {
        image_ids: imageIds,
        email,
      }, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      setSuccess(true);
      setTimeout(() => {
        setSuccess(false);
        setEmail('');
        onShared();
      }, 1200);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to share images');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <div className="w-[400px] p-6">
        <h3 className="text-lg font-medium mb-4">Share Images</h3>
        <p className="mb-2 text-gray-700">Share <b>{imageIds.length}</b> image{imageIds.length > 1 ? 's' : ''} with:</p>
        <input
          type="email"
          value={email}
          onChange={e => setEmail(e.target.value)}
          placeholder="Recipient's email"
          className="w-full p-2 border border-gray-300 rounded mb-4"
          disabled={isLoading || success}
        />
        {error && <div className="text-red-600 mb-2 text-sm">{error}</div>}
        {success && <div className="text-green-600 mb-2 text-sm">Images shared!</div>}
        <div className="flex justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-600 hover:text-gray-800"
            disabled={isLoading || success}
          >Cancel</button>
          <button
            onClick={handleShare}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            disabled={isLoading || success}
          >{isLoading ? 'Sharing...' : 'Share'}</button>
        </div>
      </div>
    </Modal>
  );
} 