import PropTypes from 'prop-types';
import { SearchX } from 'lucide-react';

export default function SearchEmptyState({ message }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 px-4 text-center">
      <div className="w-16 h-16 bg-sma-purple/10 rounded-full flex items-center justify-center mb-4">
        <SearchX className="w-8 h-8 text-sma-purple" />
      </div>
      <h3 className="text-xl font-bold text-gray-900 mb-2">No results found</h3>
      <p className="text-gray-500 max-w-md font-medium">
        {message || "We couldn't find any media matching your search. Try adjusting your keywords or filters."}
      </p>
    </div>
  );
}

SearchEmptyState.propTypes = {
  message: PropTypes.string,
};
