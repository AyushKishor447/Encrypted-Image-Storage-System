# Encrypted Image Storage System (ESS) - Project Notes

## Project Overview
This project is a secure, user-specific image storage system with:
- **Frontend:** Next.js (React)
- **Backend:** FastAPI (Python)
- **Authentication:** JWT (JSON Web Token)
- **Storage:** Migrated from local JSON files to MongoDB Atlas
- **Features:**
  - User authentication (signup/login)
  - Per-user folders and images
  - Image encryption/decryption
  - Starred and recent images
  - Image/folder CRUD

---

## Major Steps & Changes (Chronological)

### 1. **Initial Setup & Local Storage**
- The backend used local JSON files (`users.json`, `metadata.json`, `image_folders.json`) for all data.
- The frontend handled authentication, image/folder CRUD, and encryption key dialogs.
- Issues included missing dependencies, SSR/CSR token handling, and double-fetches.

### 2. **Authentication Flow**
- JWT tokens are stored in both localStorage and cookies for compatibility.
- All protected API endpoints require the `Authorization: Bearer <token>` header.
- The frontend only fetches data after the token is available client-side.
- Defensive coding was added to handle missing `user_id` fields in legacy data.

### 3. **Per-User Data Handling**
- All images and folders are tagged with `user_id`.
- Backend endpoints were patched to filter by `user_id` for all CRUD and listing operations.
- Starred and recent endpoints were updated to only show items for the current user.

### 4. **Frontend Improvements**
- All API requests (fetch/axios) were updated to include the JWT token.
- The upload dialog was improved to show one encryption key at a time for multiple uploads.
- Error handling was improved for all user actions.

### 5. **Migration to MongoDB**
- **Step 1:** User authentication (signup, login, user info) was migrated to MongoDB (`users` collection).
- **Step 2a:** Folder creation and listing were migrated to MongoDB (`folders` collection).
- **Step 2b:** All image metadata and image-related endpoints were migrated to MongoDB (`images` collection). Starred and recent logic now use MongoDB queries.
- All file-based metadata logic was removed.

### 6. **Delete Endpoint Fixes**
- The delete endpoint was updated to:
  - Look up the image document in MongoDB by `id` and user.
  - Delete the correct files using the paths from the document.
  - Remove the image document from MongoDB.
  - Require authentication (JWT).
- The frontend was updated to include the `Authorization` header for DELETE requests.

---

## Troubleshooting & Error Corrections
- **Starred/Recent showing all images:** Fixed by using dedicated endpoints and MongoDB queries filtered by `user_id` and `starred`.
- **Upload dialog for multiple images:** Now shows one popup per image/key, not all at once.
- **Folder creation error:** Fixed by removing the MongoDB `_id` field before returning the folder object.
- **Delete not authenticated:** Fixed by adding the `Authorization` header to frontend DELETE requests.
- **Delete file not found:** Fixed by using MongoDB to look up the correct file paths.

---

## Codebase Structure (Key Files)
- `backend.py` — FastAPI backend, all endpoints, MongoDB integration
- `ess-frontend/app/page.tsx` — Main Next.js page, image/folder listing, view switching
- `ess-frontend/components/UploadButton.tsx` — Handles image upload and encryption key dialogs
- `ess-frontend/components/ImageCard.tsx` — Image card UI, move/star/delete actions
- `ess-frontend/components/Sidebar.tsx` — Folder navigation and creation
- `ess-frontend/lib/api.ts` — Frontend API helpers (fetch, upload, delete, download)
- `.env` — Contains `MONGO_URI` for MongoDB Atlas

---

## MongoDB Collections
- `users` — User authentication info
- `folders` — Folder metadata (id, name, parent_folder, user_id, etc.)
- `images` — Image metadata (id, name, starred, parent_folder, user_id, etc.)

---

## Testing Instructions (for future devs)
- **Signup/Login:** Should create/find user in MongoDB and return JWT.
- **Create Folder:** Should create a folder in MongoDB and return it (without `_id`).
- **Upload Image:** Should create a new image document in MongoDB and store files on disk.
- **List Images/Folders:** Should only show items for the current user.
- **Star/Unstar/Move:** Should update the image document in MongoDB.
- **Delete Image:** Should delete files from disk and remove the document from MongoDB.
- **Recent/Starred:** Should show only the correct images for the user.

---

## Suggestions for Future Improvements
- Add async MongoDB support (e.g., with `motor`)
- Add image preview caching/CDN
- Add user roles/admin panel
- Add more robust error handling/logging
- Add tests for all endpoints

---

## Summary
This project has been fully migrated from local file storage to MongoDB, with all authentication, folder, and image operations now using the database. All endpoints are user-specific and require authentication. The frontend and backend are now robust, scalable, and ready for further development. 