import { useParams } from 'react-router-dom';
import EmptyState from '../components/ui/EmptyState';
import { Film } from 'lucide-react';

export default function AssetDetail() {
  const { id } = useParams();

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div className="flex items-center gap-4">
        <div className="p-3 bg-gray-900 rounded-lg border border-gray-800">
          <Film className="w-6 h-6 text-blue-500" />
        </div>
        <div>
          <h1 className="text-2xl font-bold">Asset Detail</h1>
          <p className="text-gray-500 text-sm mt-1">ID: {id}</p>
        </div>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          <div className="aspect-video bg-gray-900 rounded-xl border border-gray-800 flex items-center justify-center">
            <span className="text-gray-500">Video Player Placeholder</span>
          </div>
        </div>
        
        <div className="space-y-6">
          <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
            <h3 className="font-medium mb-4">Metadata</h3>
            <EmptyState message="No metadata available" />
          </div>
        </div>
      </div>
    </div>
  );
}
