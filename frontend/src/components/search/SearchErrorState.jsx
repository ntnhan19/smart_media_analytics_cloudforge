import PropTypes from 'prop-types';
import { AlertTriangle, RefreshCcw } from 'lucide-react';

export default function SearchErrorState({ error, onRetry }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 px-4 text-center">
      <div className="w-16 h-16 bg-red-500/10 rounded-full flex items-center justify-center mb-4 border border-red-500/20">
        <AlertTriangle className="w-8 h-8 text-red-500" />
      </div>
      <h3 className="text-xl font-bold text-gray-900 mb-2">Something went wrong</h3>
      <p className="text-gray-500 max-w-md mb-6 font-medium">
        {error || "An error occurred while fetching your search results. Please try again."}
      </p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="flex items-center gap-2 px-6 py-2.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg font-medium transition-colors border border-gray-200"
        >
          <RefreshCcw className="w-4 h-4" />
          Try Again
        </button>
      )}
    </div>
  );
}

SearchErrorState.propTypes = {
  error: PropTypes.string,
  onRetry: PropTypes.func,
};
