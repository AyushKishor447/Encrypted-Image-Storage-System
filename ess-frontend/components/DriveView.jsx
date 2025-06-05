'use client';
import React, { useState, useEffect } from 'react';
import ImageCard from './ImageCard';
import {
  Dialog,
  DialogTrigger,
  DialogPortal,
  DialogOverlay,
  DialogContent,
} from '@radix-ui/react-dialog';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import axios from "axios";
import { API_BASE } from '@/lib/api';

export default function DriveView() {
  const [items, setItems] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchItems();
  }, []);

  const fetchItems = async () => {
    try {
      setIsLoading(true);
      const token = localStorage.getItem('token');
      const res = await axios.get(`${API_BASE}/api/items`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setItems(res.data);
    } catch (err) {
      console.error("Failed to fetch items", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API_BASE}/api/encrypt`, formData, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      fetchItems(); // Refresh the list after upload
    } catch (err) {
      console.error("Upload failed", err);
      alert("Encryption/upload failed");
    }
  };

  return (
    <div className="p-4">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Encrypted Drive</h1>
        <div className="relative">
          <input
            type="file"
            onChange={handleUpload}
            className="hidden"
            id="file-upload"
            accept="image/*"
          />
          <label
            htmlFor="file-upload"
            className="cursor-pointer bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
          >
            Upload Image
          </label>
        </div>
      </div>

      {isLoading ? (
        <div className="text-center py-8 text-gray-600">Loading...</div>
      ) : items.length === 0 ? (
        <div className="text-center py-8 text-gray-600">
          No images uploaded yet. Upload your first image to get started!
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {items.map((item) => (
            <ImageCard
              key={item.id}
              item={item}
              onDelete={fetchItems}
            />
          ))}
        </div>
      )}
    </div>
  );
}
