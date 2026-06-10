import PropTypes from 'prop-types';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Upload, Settings, Folder, Film, Image, Heart, Trash } from 'lucide-react';
import AIProcessingPanel from './AIProcessingPanel';

export default function Sidebar({
  activeMenu,
  showLibraryCount = false,
  libraryStats = { all: 0, videos: 0, images: 0, favourites: 0 },
  jobId
}) {
  const navItems = [
    { name: 'DASHBOARD', path: '/', id: 'dashboard', icon: LayoutDashboard },
    { name: 'Ingest / Upload', path: '/upload', id: 'upload', icon: Upload },
    { name: 'SETTINGS', path: '/settings', id: 'settings', icon: Settings },
  ];

  return (
    <aside className="relative w-[310px] h-full bg-[#16132A] rounded-[6px] flex flex-col shrink-0 overflow-y-auto overflow-x-hidden">
      <div className="relative pt-[20px] pb-[20px] flex flex-col items-left z-10 shrink-0">
        <img src="/logo.png" alt="SMA Logo" className="w-[160px] h-auto object-contain" />
      </div>

      <nav className="flex flex-col items-center space-y-[16px] w-full px-[31px] relative z-10 shrink-0">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeMenu === item.id;

          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={`relative w-[240px] h-[36px] flex items-center rounded-[6px] transition-colors box-border ${isActive
                ? 'bg-[#7B5CF5]'
                : 'border border-[#4F8EF7]'
                }`}
            >
              <Icon className="absolute left-[12px] w-[22px] h-[22px] text-white" />
              <span className="w-full text-center font-inter font-bold text-[18px] leading-[22px] text-white">
                {item.name}
              </span>
            </NavLink>
          );
        })}
      </nav>

      {showLibraryCount && libraryStats && (
        <div className="mt-[20px] relative w-full px-[24px] shrink-0 mb-[16px]">
          <div className="relative flex items-center justify-center mb-[16px]">
            <div className="absolute w-[258px] h-px bg-[#D9D9D9]"></div>
            <span className="bg-[#16132A] px-2 relative z-10 font-inter font-medium text-[10px] leading-[12px] text-white">
              LIBRARY
            </span>
          </div>

          <div className="flex flex-col space-y-[16px] pl-[10px] pr-[10px]">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-[18px] text-white">
                <Folder className="w-[20px] h-[20px]" />
                <span className="font-inter font-normal text-[12px] leading-[15px]">ALL ASSETS</span>
              </div>
              <div className="w-[41px] h-[13px] bg-[#4F8EF7] rounded-[5px] flex items-center justify-center">
                <span className="font-inter font-normal text-[12px] leading-[15px] text-white">{libraryStats.all || 0}</span>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-[18px] text-white">
                <Film className="w-[20px] h-[20px]" />
                <span className="font-inter font-normal text-[12px] leading-[15px]">VIDEOS</span>
              </div>
              <div className="w-[41px] h-[13px] bg-[#4F8EF7] rounded-[5px] flex items-center justify-center">
                <span className="font-inter font-normal text-[12px] leading-[15px] text-white">{libraryStats.videos || 0}</span>
              </div>
            </div>



            <div className="flex items-center justify-between">
              <div className="flex items-center gap-[18px] text-white">
                <Heart className="w-[18px] h-[18px] ml-[1px]" />
                <span className="font-inter font-normal text-[12px] leading-[15px]">FAVOURITES</span>
              </div>
              <div className="w-[41px] h-[13px] bg-[#4F8EF7] rounded-[5px] flex items-center justify-center">
                <span className="font-inter font-normal text-[12px] leading-[15px] text-white">{libraryStats.favourites || 0}</span>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-[18px] text-white">
                <Trash className="w-[20px] h-[20px]" />
                <span className="font-inter font-normal text-[12px] leading-[15px]">TRASH</span>
              </div>
              <div className="w-[41px] h-[13px] bg-[#4F8EF7] rounded-[5px] flex items-center justify-center">
                <span className="font-inter font-normal text-[12px] leading-[15px] text-white">0</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* AI Processing Panel embedded in Sidebar */}
      <div className="flex justify-center w-full shrink-0">
        <AIProcessingPanel jobId={jobId} />
      </div>

      <div className="mt-auto pt-4 pb-[16px] flex justify-center shrink-0">
        <button className="w-[250px] h-[44px] box-border border border-[#4F8EF7] rounded-[8px] flex items-center justify-center text-white hover:bg-[#4F8EF7]/10 transition-colors">
          <span className="font-inter font-normal text-[10px] leading-[12px]">LOGIN & SIGN IN</span>
        </button>
      </div>

    </aside>
  );
}

Sidebar.propTypes = {
  activeMenu: PropTypes.string.isRequired,
  showLibraryCount: PropTypes.bool,
  libraryStats: PropTypes.shape({
    all: PropTypes.number,
    videos: PropTypes.number,
    images: PropTypes.number,
    favourites: PropTypes.number,
  }),
  jobId: PropTypes.string,
};

