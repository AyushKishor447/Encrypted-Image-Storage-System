import { ImageItem, EncryptionResponse } from './types';

const API_BASE = 'http://localhost:8000';

export async function listImages(): Promise<ImageItem[]> {
  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}/api/items`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  if (!response.ok) throw new Error('Failed to fetch images');
  const items = await response.json();
  console.log('Fetched items:', items);
  return items;
}

export async function uploadImage(file: File): Promise<EncryptionResponse> {
  const token = localStorage.getItem('token');
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE}/api/encrypt`, {
    method: 'POST',
    body: formData,
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) throw new Error('Failed to upload image');
  return response.json();
}

export async function deleteImage(imageId: string): Promise<void> {
  const token = localStorage.getItem('token');
  const url = `${API_BASE}/api/delete/${imageId}`;
  
  console.log('Sending delete request:', {
    imageId,
    url
  });
  
  const response = await fetch(url, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  const responseText = await response.text();
  console.log('Delete response:', {
    status: response.status,
    statusText: response.statusText,
    responseText
  });

  if (!response.ok) {
    console.error('Delete request failed:', {
      status: response.status,
      statusText: response.statusText,
      responseText,
      imageId,
      url
    });
    throw new Error(responseText || `Failed to delete image: ${response.status} ${response.statusText}`);
  }

  try {
    const result = JSON.parse(responseText);
    console.log('Delete successful:', result);
  } catch (e) {
    console.warn('Could not parse delete response as JSON:', responseText);
  }
}

export async function downloadEncrypted(filename: string): Promise<Blob> {
  const token = localStorage.getItem('token');
  if (!token) {
    throw new Error('No authentication token found');
  }

  const baseName = filename.split('.')[0];
  const url = `${API_BASE}/api/encrypted/${baseName}_encrypted_preview`;
  
  console.log('Downloading encrypted file from:', url);
  const response = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  
  if (!response.ok) {
    const errorText = await response.text();
    console.error('Download failed:', { status: response.status, statusText: response.statusText, errorText });
    throw new Error(`Download failed: ${response.status} ${response.statusText}`);
  }

  const blob = await response.blob();
  if (blob.size === 0) {
    throw new Error('Downloaded file is empty');
  }
  return blob;
}

export async function downloadDecrypted(filename: string, key: string): Promise<Blob> {
  const baseName = filename.replace(/_preview$/, '').replace(/_encrypted$/, '');
  
  const formData = new FormData();
  formData.append('filename', baseName);
  formData.append('key', key);

  console.log('Sending decryption request for:', { baseName, key });

  const response = await fetch(`${API_BASE}/api/decrypt`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Decryption failed:', { status: response.status, statusText: response.statusText, errorText });
    throw new Error(errorText || `Decryption failed: ${response.status} ${response.statusText}`);
  }

  const blob = await response.blob();
  if (blob.size === 0) {
    throw new Error('Decrypted file is empty');
  }
  return blob;
} 