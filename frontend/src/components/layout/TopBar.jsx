import PropTypes from 'prop-types';
import { Search, Upload, Bot } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Icon } from "@iconify/react";
// Custom Vector icon from Figma
const Vector = ({ className }) => (
  <svg className={className} width="40" height="37" viewBox="0 0 40 37" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M15.9708 13.2701L17.7207 7.60812C18.3765 5.48876 21.6235 5.48876 22.2793 7.60812L24.0273 13.2701C24.1379 13.6282 24.3454 13.9544 24.6302 14.2178C24.9149 14.4812 25.2676 14.6732 25.6547 14.7756L31.7756 16.3925C34.0668 16.9991 34.0668 20.0027 31.7756 20.6093L25.6547 22.2262C25.2676 22.3286 24.9149 22.5205 24.6302 22.7839C24.3454 23.0473 24.1379 23.3735 24.0273 23.7317L22.2793 29.3936C21.6235 31.513 18.3765 31.513 17.7207 29.3936L15.9727 23.7317C15.8621 23.3735 15.6546 23.0473 15.3698 22.7839C15.0851 22.5205 14.7324 22.3286 14.3452 22.2262L8.22437 20.6093C5.93324 20.0027 5.93324 16.9991 8.22437 16.3925L14.3452 14.7756C14.7324 14.6732 15.0851 14.4812 15.3698 14.2178C15.6546 13.9544 15.8621 13.6282 15.9727 13.2701M32.0561 26.7353C32.6269 25.1951 35.0267 25.1933 35.5955 26.7353L35.6469 26.8942L36.2315 29.0648L38.5779 29.6074C40.474 30.0459 40.474 32.5343 38.5779 32.9728L36.2315 33.5154L35.6469 35.6859C35.1728 37.438 32.4807 37.438 32.0067 35.6859L31.4201 33.5154L29.0737 32.9728C27.1776 32.5343 27.1776 30.044 29.0737 29.6074L31.4201 29.0648L32.0067 26.8942L32.0561 26.7353ZM33.8258 30.9192C33.7121 31.06 33.5771 31.1849 33.4248 31.2901C33.5771 31.3952 33.7121 31.5201 33.8258 31.661C33.9395 31.5201 34.0745 31.3952 34.2267 31.2901C34.0744 31.1844 33.9393 31.0588 33.8258 30.9174M4.4045 1.15505C4.99309 -0.436293 7.53506 -0.383309 7.99526 1.314L8.57989 3.48451L10.9263 4.02714C12.8224 4.46563 12.8224 6.95404 10.9263 7.39253L8.57989 7.93516L7.99526 10.1057C7.52123 11.8578 4.82915 11.8578 4.35512 10.1057L3.76852 7.93516L1.42208 7.39253C-0.474027 6.95404 -0.474027 4.4638 1.42208 4.02714L3.76852 3.48451L4.35512 1.314L4.4045 1.15505ZM6.1742 5.34077C6.06039 5.48095 5.92536 5.60525 5.77326 5.70983C5.92563 5.81554 6.06068 5.94108 6.1742 6.08255C6.28773 5.94108 6.42278 5.81554 6.57515 5.70983C6.42291 5.60469 6.28787 5.4816 6.1742 5.34077Z" fill="currentColor"/>
  </svg>
);

export default function TopBar({
  searchPlaceholder = "Search with SMA...",
  showUploadBtn = true,
  showAIIcon = true
}) {
  const navigate = useNavigate();

  return (
    <header className="h-[51px] px-6 flex items-center justify-between bg-[#16132A] text-white">
      <div className="flex-1 max-w-[800px]">
        <div className="relative flex items-center">
          <Vector className="absolute left-3 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder={searchPlaceholder}
            className="w-full pl-10 pr-[76px] py-1.5 bg-[#0E0B1F] border border-[#4F8EF7]/30 rounded-[6px] focus:outline-none focus:border-[#4F8EF7] text-sm transition-colors text-white placeholder-gray-500"
          />
          <Search className="absolute right-3 w-4 h-4 text-gray-400 pointer-events-none" />
          
          {showAIIcon && (
            <div
              className="absolute right-[32px] w-[26px] h-[26px] bg-[#7B5CF5] opacity-80 hover:opacity-100 rounded-[4px] flex items-center justify-center cursor-pointer transition-opacity"
            >
              <Icon
                icon="tabler:ai"
                width="18"
                height="18"
                className="text-white"
              />
            </div>
          )}
        </div>
      </div>

      <div className="flex items-center gap-4 ml-4">

        {showUploadBtn && (
          <button
            onClick={() => navigate('/upload')}
            className="flex items-center gap-2 px-3 py-1.5 bg-[#7B5CF5] hover:bg-[#7B5CF5]/90 text-white rounded-[6px] text-sm font-medium transition-colors"
          >
            <Upload className="w-4 h-4" />
            Upload
          </button>
        )}

        <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-[#7B5CF5] to-[#4F8EF7] flex items-center justify-center font-bold text-xs">
          a
        </div>
      </div>
    </header>
  );
}

TopBar.propTypes = {
  searchPlaceholder: PropTypes.string,
  showUploadBtn: PropTypes.bool,
  showAIIcon: PropTypes.bool,
};

