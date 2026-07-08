import PropTypes from 'prop-types';
import { History } from 'lucide-react';

export default function SearchHistory({ history, onSelectHistory, onClearHistory }) {
  if (!history || history.length === 0) return null;

  return (
    <div className="flex flex-col gap-3 py-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm font-medium text-gray-500 dark:text-gray-400">
          <History className="w-4 h-4" />
          <span>Recent Searches</span>
        </div>
        <button 
          onClick={onClearHistory}
          className="text-xs text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300 transition-colors"
        >
          Clear
        </button>
      </div>
      <div className="flex flex-wrap gap-2">
        {history.map((term, index) => (
          <button
            key={`${term}-${index}`}
            onClick={() => onSelectHistory(term)}
            className="group flex items-center gap-2 px-3 py-1.5 bg-gray-100 hover:bg-gray-200 dark:bg-gray-800/80 dark:hover:bg-gray-700 rounded-lg text-sm text-gray-700 dark:text-gray-300 transition-colors border border-gray-200 hover:border-gray-300 dark:border-gray-700 dark:hover:border-gray-600"
          >
            {term}
          </button>
        ))}
      </div>
    </div>
  );
}

SearchHistory.propTypes = {
  history: PropTypes.arrayOf(PropTypes.string).isRequired,
  onSelectHistory: PropTypes.func.isRequired,
  onClearHistory: PropTypes.func.isRequired,
};
