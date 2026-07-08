
export default function SearchSkeleton() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 py-6">
      {Array.from({ length: 8 }).map((_, i) => (
        <div key={i} className="flex flex-col bg-gray-100 dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl overflow-hidden animate-pulse transition-colors">
          {/* Thumbnail Skeleton */}
          <div className="relative aspect-video bg-gray-200 dark:bg-gray-800 transition-colors">
            <div className="absolute top-2 right-2 w-16 h-6 bg-gray-300 dark:bg-gray-700 rounded-md transition-colors"></div>
            <div className="absolute bottom-2 right-2 w-12 h-6 bg-gray-300 dark:bg-gray-700 rounded-md transition-colors"></div>
          </div>
          
          {/* Content Skeleton */}
          <div className="p-4 flex flex-col flex-1 gap-3">
            <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded w-full transition-colors"></div>
            <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded w-4/5 transition-colors"></div>
            
            <div className="mt-auto pt-3 border-t border-gray-200 dark:border-gray-800/50 flex flex-col gap-2 transition-colors">
              <div className="flex items-center justify-between">
                <div className="h-3 bg-gray-200 dark:bg-gray-800 rounded w-1/2 transition-colors"></div>
                <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded w-8 transition-colors"></div>
              </div>
              <div className="flex gap-2">
                <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded w-12 transition-colors"></div>
                <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded w-16 transition-colors"></div>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
