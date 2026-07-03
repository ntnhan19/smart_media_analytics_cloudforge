
export default function SearchSkeleton() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 py-6">
      {Array.from({ length: 8 }).map((_, i) => (
        <div key={i} className="flex flex-col bg-gray-900 border border-gray-800 rounded-xl overflow-hidden animate-pulse">
          {/* Thumbnail Skeleton */}
          <div className="relative aspect-video bg-gray-800">
            <div className="absolute top-2 right-2 w-16 h-6 bg-gray-700 rounded-md"></div>
            <div className="absolute bottom-2 right-2 w-12 h-6 bg-gray-700 rounded-md"></div>
          </div>
          
          {/* Content Skeleton */}
          <div className="p-4 flex flex-col flex-1 gap-3">
            <div className="h-4 bg-gray-800 rounded w-full"></div>
            <div className="h-4 bg-gray-800 rounded w-4/5"></div>
            
            <div className="mt-auto pt-3 border-t border-gray-800/50 flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <div className="h-3 bg-gray-800 rounded w-1/2"></div>
                <div className="h-4 bg-gray-800 rounded w-8"></div>
              </div>
              <div className="flex gap-2">
                <div className="h-4 bg-gray-800 rounded w-12"></div>
                <div className="h-4 bg-gray-800 rounded w-16"></div>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
