'use client';
import React, { useState, useEffect } from 'react';
import  FileCard  from './FileCard';
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

// export default function DriveView() {
//   const [files, setFiles] = useState([]);
//   const [uploading, setUploading] = useState(false);
//   const [uploadKey, setUploadKey] = useState("");

//   useEffect(() => {
//     fetchItems();
//   }, []);

//   const fetchItems = async () => {
//     const res = await axios.get("http://localhost:8000/api/items");
//     setFiles(res.data);
//   };

//   const handleUpload = async (e) => {
//     const file = e.target.files[0];
//     if (!file) return;

//     const formData = new FormData();
//     formData.append("file", file);
//     setUploading(true);

//     try {
//       const res = await axios.post("http://localhost:8000/api/encrypt", formData, {
//         headers: { "Content-Type": "multipart/form-data" },
//       });
//       setUploadKey(res.data.encryption_key);
//       alert("File uploaded and encrypted! Key: " + res.data.encryption_key);
//       fetchItems();
//     } catch (err) {
//       console.error(err);
//       alert("Encryption failed");
//     }

//     setUploading(false);
//   };

//   return (
//     <div className="p-4 space-y-4">
//       <h1 className="text-xl font-bold mb-4">Secure Drive</h1>
//       <input
//         type="file"
//         onChange={handleUpload}
//         disabled={uploading}
//         className="mb-2"
//       />
//       {uploadKey && (
//         <div className="bg-yellow-100 p-2 rounded text-sm">
//           Encryption Key: <span className="font-mono">{uploadKey}</span>
//         </div>
//       )}
//       <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
//         {files.map((file) => (
//           <FileCard
//             key={file.id}
//             filename={file.name + ".tiff"}
//             encryptionKey={uploadKey}
//           />
//         ))}
//       </div>
//     </div>
//   );
// }

export default function DriveView() {
  const [items, setItems] = useState([]);

  useEffect(() => {
    fetchItems();
  }, []);

  const fetchItems = async () => {
    try {
      const res = await axios.get("http://localhost:8000/api/items");
      setItems(res.data);
    } catch (err) {
      console.error("Failed to fetch items", err);
    }
  };

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    const formData = new FormData();
    formData.append("file", file);

    try {
      await axios.post("http://localhost:8000/api/encrypt", formData);
      fetchItems();
    } catch (err) {
      console.error("Upload failed", err);
      alert("Encryption/upload failed");
    }
  };

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Encrypted Drive</h1>
      <input type="file" onChange={handleUpload} className="mb-4" />
      <div className="grid grid-cols-3 gap-4">
        {items.map((item) => (
          <FileCard
            key={item.id}
            id={item.id}
            previewUrl={`http://localhost:8000${item.preview}`}
          />
        ))}
      </div>
    </div>
  );
}
