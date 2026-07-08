import PropTypes from 'prop-types';
import { Upload } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import SearchBar from '../search/SearchBar';

export default function TopBar({
  searchPlaceholder = "Search your media library...",
  showUploadBtn = true,
  showSearchBar = true
}) {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');

  const handleSearch = (query) => {
    if (query.trim()) {
      navigate(`/search?q=${encodeURIComponent(query.trim())}`);
    }
  };

  return (
    <header className={`py-4 px-6 flex items-center bg-sma-bg text-white ${showSearchBar ? 'justify-between' : 'justify-end'}`}>
      {showSearchBar && (
        <div className="flex-1 max-w-[800px]">
          {/* Sử dụng bản variant="large" bự chà bá */}
          <SearchBar 
            variant="large"
            value={searchQuery}
            onChange={setSearchQuery}
            onSearch={handleSearch}
            placeholder={searchPlaceholder}
          />
        </div>
      )}

      <div className="flex items-center gap-4 ml-8">
        {showUploadBtn && (
          <button
            onClick={() => navigate('/upload')}
            className="flex items-center gap-2 px-4 py-2.5 bg-[#7B5CF5] hover:bg-[#7B5CF5]/90 text-white rounded-lg text-sm font-bold transition-colors"
          >
            <Upload className="w-5 h-5" />
            Upload
          </button>
        )}

        <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-[#7B5CF5] to-[#4F8EF7] flex items-center justify-center font-bold text-sm">
          A
        </div>
      </div>
    </header>
  );
}

TopBar.propTypes = {
  searchPlaceholder: PropTypes.string,
  showUploadBtn: PropTypes.bool,
  showSearchBar: PropTypes.bool
};
