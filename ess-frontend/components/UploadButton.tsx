import { useState, useRef } from 'react';
import { API_BASE } from '@/lib/api';

interface UploadedKey {
  filename: string;
  key: string;
}

interface UploadButtonProps {
  onUploadComplete: () => void;
  currentFolder?: string | null;
}

export function UploadButton({ onUploadComplete, currentFolder }: UploadButtonProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [showKeyDialog, setShowKeyDialog] = useState(false);
  const [uploadedKeys, setUploadedKeys] = useState<UploadedKey[]>([]);
  const [currentKeyIndex, setCurrentKeyIndex] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    setIsUploading(true);
    const newKeys: UploadedKey[] = [];
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('No authentication token found');
      }

      for (const file of files) {
        const formData = new FormData();
        formData.append('file', file);
        
        // Upload and encrypt the file
        const response = await fetch(`${API_BASE}/api/encrypt`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
          body: formData,
        });

        if (!response.ok) {
          const errorText = await response.text();
          console.error('Upload failed:', errorText);
          throw new Error(errorText || 'Upload failed');
        }

        const result = await response.json();
        newKeys.push({ filename: file.name, key: result.encryption_key });

        // If we have a current folder, move the image to it
        if (currentFolder) {
          const moveFormData = new FormData();
          moveFormData.append('folder_id', currentFolder);

          const moveResponse = await fetch(
            `${API_BASE}/api/items/${result.preview_id}/move`,
            {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${token}`,
              },
              body: moveFormData,
            }
          );

          if (!moveResponse.ok) {
            throw new Error('Failed to move image to folder');
          }
        }
      }
      setUploadedKeys(newKeys);
      setCurrentKeyIndex(0);
      setShowKeyDialog(true);
      onUploadComplete();
    } catch (error) {
      console.error('Upload failed:', error);
      alert(error instanceof Error ? error.message : 'Failed to upload image');
    } finally {
      setIsUploading(false);
      // Reset the file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleCopy = (key: string) => {
    navigator.clipboard.writeText(key);
  };

  return (
    <>
      <div className="fixed bottom-8 right-8">
        <input
          type="file"
          id="file-upload"
          className="hidden"
          onChange={handleUpload}
          accept="image/*"
          multiple
          disabled={isUploading}
        />
        <label
          htmlFor="file-upload"
          className={`flex items-center justify-center w-14 h-14 bg-blue-600 text-white rounded-full shadow-lg cursor-pointer hover:bg-blue-700 transition-colors ${
            isUploading ? 'opacity-50 cursor-not-allowed' : ''
          }`}
        >
          {isUploading ? (
            <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 4v16m8-8H4"
              />
            </svg>
          )}
        </label>
      </div>

      {showKeyDialog && uploadedKeys.length > 0 && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-[99999]">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-medium mb-4">Save Your Encryption Key</h3>
            <p className="text-gray-600 mb-4">
              Please save this encryption key. You will need it to decrypt the image later:
            </p>
            <div className="space-y-4 mb-4 max-h-60 overflow-y-auto">
              <div className="bg-gray-100 p-3 rounded flex flex-col gap-1">
                <span className="font-semibold text-gray-700 text-sm">{uploadedKeys[currentKeyIndex].filename}</span>
                <div className="flex items-center gap-2">
                  <span className="break-all font-mono text-xs">{uploadedKeys[currentKeyIndex].key}</span>
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => handleCopy(uploadedKeys[currentKeyIndex]?.key || '')}
                className="px-4 py-2 bg-white text-black border border-gray-300 rounded hover:bg-gray-100"
                title="Copy key to clipboard"
              >
                Copy Key
              </button>
              <button
                onClick={() => {
                  if (currentKeyIndex < uploadedKeys.length - 1) {
                    setCurrentKeyIndex(currentKeyIndex + 1);
                  } else {
                    setShowKeyDialog(false);
                    setUploadedKeys([]);
                  }
                }}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                I&apos;ve Saved the Key
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
} 