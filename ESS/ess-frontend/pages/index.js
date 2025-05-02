// pages/index.js
import DriveView from '@/components/DriveView';

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-50">
      <h1 className="text-2xl font-bold p-4">Encrypted Drive</h1>
      <DriveView />
    </main>
  );
}
