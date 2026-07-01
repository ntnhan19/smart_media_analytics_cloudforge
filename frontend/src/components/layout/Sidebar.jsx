import React from 'react';
import PropTypes from 'prop-types';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Upload, Settings, Folder, Heart, Trash } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { getAssets } from '../../services/api';
import AIProcessingPanel from './AIProcessingPanel';

export default function Sidebar({ activeMenu, showLibraryCount = false }) {
  const { data: assets } = useQuery({
    queryKey: ['assets'],
    queryFn: ({ signal }) => getAssets(signal),
    enabled: showLibraryCount,
  });

  const [deletedCount, setDeletedCount] = React.useState(() => {
    return parseInt(localStorage.getItem('deletedAssetsCount') || '0', 10);
  });

  React.useEffect(() => {
    const handleAssetDeleted = () => {
      setDeletedCount(parseInt(localStorage.getItem('deletedAssetsCount') || '0', 10));
    };
    window.addEventListener('assetDeleted', handleAssetDeleted);
    return () => window.removeEventListener('assetDeleted', handleAssetDeleted);
  }, []);

  const libraryStats = {
    all: assets?.total || assets?.items?.length || 0,
    favourites: assets?.items?.filter(a => a.is_favorite).length || 0,
    trash: deletedCount,
  };

  const navItems = [
    { name: 'Dashboard', path: '/', id: 'dashboard', icon: LayoutDashboard },
    { name: 'Upload', path: '/upload', id: 'upload', icon: Upload },
    { name: 'Settings', path: '/settings', id: 'settings', icon: Settings },
  ];

  return (
    // Sửa h-screen thành h-full để Sidebar bám theo container cha
    // Sử dụng overflow-hidden để ngăn chặn thanh cuộn ngoài ý muốn
    <aside className="w-[310px] h-full bg-[#16132A] flex flex-col shrink-0 overflow-hidden">

      {/* Header - Cố định */}
      <div className="pt-3 pb-3 pl-[20px] shrink-0">
        <img src="/logo.png" alt="SMA Logo" className="w-[160px] h-auto object-contain" />
      </div>

      {/* Nav - Cố định */}
      <nav className="flex flex-col items-center space-y-4 w-full px-[31px] shrink-0 my-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeMenu === item.id;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={`relative w-[240px] h-[36px] flex items-center rounded-[6px] transition-colors ${isActive ? 'bg-[#7B5CF5]' : 'border border-[#4F8EF7]'}`}
            >
              <Icon className="absolute left-[12px] w-[20px] h-[20px] text-white" />
              <span className="w-full text-center font-bold text-[16px] text-white">{item.name}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Nội dung linh hoạt - Chỉ phần này mới được cuộn */}
      <div className="flex-1 min-h-0 flex flex-col overflow-y-auto scrollbar-hide">
        {showLibraryCount && (
          <div className="relative w-full px-[24px] py-3">
            <div className="relative flex items-center justify-center mb-4">
              <div className="absolute w-full h-px bg-[#D9D9D9]"></div>
              <span className="bg-[#16132A] px-2 relative z-10 text-[10px] text-white">LIBRARY</span>
            </div>
            <div className="flex flex-col space-y-3 px-[10px]">
              {[
                { label: 'All Assets', icon: Folder, count: libraryStats.all },
                { label: 'Favourites', icon: Heart, count: libraryStats.favourites },
                { label: 'Trash', icon: Trash, count: libraryStats.trash }
              ].map((item, idx) => (
                <div key={idx} className="flex items-center justify-between">
                  <div className="flex items-center gap-4 text-white">
                    <item.icon className="w-5 h-5" />
                    <span className="text-[12px]">{item.label}</span>
                  </div>
                  <div className="w-10 h-5 bg-[#4F8EF7] rounded-[5px] flex items-center justify-center text-[11px] text-white">
                    {item.count}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* AI Processing Panel - Tự căn lề */}
        <div className="flex justify-center w-full mt-auto py-4">
          <AIProcessingPanel />
        </div>
      </div>

      {/* Footer - Cố định */}
      <div className="pt-3 pb-4 flex justify-center shrink-0 border-t border-[#2D2844]">
        <button className="w-[250px] h-10 border border-[#4F8EF7] rounded-[8px] flex items-center justify-center text-white hover:bg-[#4F8EF7]/10 transition-colors text-[10px]">
          Login / Signup
        </button>
      </div>
    </aside>
  );
}