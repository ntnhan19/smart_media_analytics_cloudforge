import { Search as SearchIcon } from 'lucide-react';
import EmptyState from '../components/ui/EmptyState';

export default function Search() {
  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <h1 className="text-3xl font-bold">Semantic Search</h1>
      
      <div className="relative max-w-2xl mx-auto">
        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
          <SearchIcon className="h-5 w-5 text-gray-500" />
        </div>
        <input
          type="text"
          className="block w-full pl-11 pr-4 py-4 bg-gray-900 border border-gray-700 rounded-xl text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-shadow"
          placeholder="Search media by natural language (e.g. 'sunset over the ocean')"
        />
      </div>

      <div className="pt-8">
        <EmptyState message="Start typing to search your media library" />
      </div>
    </div>
  );
}
