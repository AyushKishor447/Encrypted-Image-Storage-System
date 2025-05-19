export interface ImageItem {
  id: string;
  name: string;
  type: string;
  preview: string;
  path: string;
  starred: boolean;
  last_modified: string;
  parent_folder: string | null;
}

export interface EncryptionResponse {
  message: string;
  encryption_key: string;
  preview_id: string;
  encrypted_id: string;
  preview_image_path: string;
}

export interface DecryptionRequest {
  filename: string;
  key: string;
} 