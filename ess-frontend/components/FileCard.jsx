// FileCard.jsx
'use client';
import React, { useState } from "react";
import axios from "axios";
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { API_BASE } from '@/lib/api'; // Import API_BASE

export default function FileCard({ id, previewUrl }) {
  const [keyInput, setKeyInput] = useState("");

  // const handleDownload = async () => {
  //   if (!keyInput) {
  //     alert("Please enter the decryption key.");
  //     return;
  //   }
  //   try {
  //     const formData = new FormData();
  //     formData.append("filename", `${id}`);
  //     formData.append("key", keyInput);

  //     const decResp = await axios.post(
  //       "http://localhost:8000/api/decrypt",
  //       formData,
  //       { responseType: "blob" }
  //     );

  //     const blob = new Blob([decResp.data], { type: "image/tiff" });
  //     const url = window.URL.createObjectURL(blob);
  //     const link = document.createElement("a");
  //     link.href = url;
  //     link.setAttribute("download", `${id}_decrypted.tiff`);
  //     document.body.appendChild(link);
  //     link.click();
  //     link.remove();
  //   } catch (error) {
  //     console.error("Decryption failed:", error);
  //     alert("Decryption failed. Please check the key or file.");
  //   }
  // };

  const handleDownload = async () => {
    if (!keyInput) return alert("Please enter the decryption key.");
  
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/api/decrypt`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ id: id }),
      });

      // Get base name by stripping "_encrypted" from the ID
      const baseFilename = id.replace("_encrypted_preview", "");
  
      const formData = new FormData();
      formData.append("filename", baseFilename); // only "lena256"
      formData.append("key", keyInput);
  
      const decResp = await axios.post(
        `${API_BASE}:8000/api/decrypt`,
        formData,
        { responseType: "blob" }
      );
  
      const blob = new Blob([decResp.data], { type: "image/tiff" });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${baseFilename}_decrypted.tiff`;
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error("Decryption failed:", err.response || err);
      alert(`Decryption failed: ${err.response?.statusText || err.message}`);
    }
  };
  
  return (
    <div className="border rounded p-2 shadow-md">
      <img
        src={previewUrl}
        alt={id}
        className="w-full h-48 object-cover mb-2"
      />
      <div className="text-sm font-medium truncate mb-2">{id}</div>
      <input
        type="text"
        placeholder="Enter decryption key"
        value={keyInput}
        onChange={(e) => setKeyInput(e.target.value)}
        className="border px-2 py-1 mb-2 w-full"
      />
      <button
        onClick={handleDownload}
        className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded w-full"
      >
        Download Decrypted
      </button>
    </div>
  );
}

