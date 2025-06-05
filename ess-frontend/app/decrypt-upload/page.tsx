'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { API_BASE } from '@/lib/api';

export default function DecryptUploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [key, setKey] = useState('');
  const [decryptedUrl, setDecryptedUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    } else {
      setFile(null);
    }
    setDecryptedUrl(null);
    setError(null);
  };

  const handleKeyChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setKey(e.target.value);
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setDecryptedUrl(null);
    if (!file || !key.trim()) {
      setError('Please select a file and enter a key.');
      setIsLoading(false);
      return;
    }
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('key', key);
      const response = await fetch(`${API_BASE}/api/decrypt-upload`, {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || 'Failed to decrypt image');
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      setDecryptedUrl(url);
    } catch (err: any) {
      setError(err.message || 'Failed to decrypt image');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownload = () => {
    if (decryptedUrl && file) {
      const a = document.createElement('a');
      a.href = decryptedUrl;
      a.download = file.name.replace(/\.[^.]+$/, '') + '_decrypted.tiff';
      document.body.appendChild(a);
      a.click();
      a.remove();
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 p-4">
      <div className="bg-white rounded-lg shadow p-8 w-full max-w-md">
        <button
          onClick={() => router.push('/')}
          className="mb-4 px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
        >
          ← Back to Home
        </button>
        <h2 className="text-2xl font-bold mb-4 text-center">Decrypt Uploaded Encrypted Image</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block mb-1 font-medium">Encrypted Image File</label>
            <input
              type="file"
              accept="image/*,.tiff,.tif,.npy"
              onChange={handleFileChange}
              className="w-full border rounded px-3 py-2"
              disabled={isLoading}
            />
          </div>
          <div>
            <label className="block mb-1 font-medium">Decryption Key</label>
            <input
              type="text"
              value={key}
              onChange={handleKeyChange}
              placeholder="e.g. 1.23, 4.56, 7.89, 0.12, 3.45"
              className="w-full border rounded px-3 py-2"
              disabled={isLoading}
            />
          </div>
          {error && <div className="text-red-600 text-sm">{error}</div>}
          <button
            type="submit"
            className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:opacity-50"
            disabled={isLoading}
          >
            {isLoading ? 'Decrypting...' : 'Decrypt & Preview'}
          </button>
        </form>
        {decryptedUrl && (
          <div className="mt-6 text-center">
            <h3 className="font-medium mb-2">Decrypted Image Preview</h3>
            <img
              src={decryptedUrl}
              alt="Decrypted Preview"
              className="mx-auto max-w-full max-h-64 border rounded mb-2"
              style={{ objectFit: 'contain' }}
              onError={(e) => {
                (e.target as HTMLImageElement).style.display = 'none';
              }}
            />
            <button
              onClick={handleDownload}
              className="mt-2 bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
            >
              Download Decrypted Image
            </button>
          </div>
        )}
      </div>
    </div>
  );
} 