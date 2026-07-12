import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Upload, Settings, Folder, Heart, Trash, User, PanelLeftClose, PanelLeftOpen, LogOut } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { useState, useEffect } from 'react';
import { useAuthenticator } from '@aws-amplify/ui-react';
import { getAssets } from '../../services/api';
import AIProcessingPanel from './AIProcessingPanel';

export default function Sidebar({ activeMenu, showLibraryCount = false, onClose, onOpen, isCollapsed = false }) {
  const { user, signOut } = useAuthenticator((context) => [context.user]);
  const { data: assets } = useQuery({
    queryKey: ['assets'],
    queryFn: ({ signal }) => getAssets(signal),
    enabled: showLibraryCount,
  });

  const [deletedCount, setDeletedCount] = useState(() => {
    return parseInt(localStorage.getItem('deletedAssetsCount') || '0', 10);
  });

  useEffect(() => {
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
    <aside className={`${isCollapsed ? 'w-[64px]' : 'w-[310px]'} h-full bg-white dark:bg-[#16132A] border-r border-gray-200 dark:border-transparent flex flex-col shrink-0 overflow-hidden transition-all duration-300`}>

      {/* Header - Cố định */}
      <div className={`pt-3 pb-3 shrink-0 flex items-center ${isCollapsed ? 'justify-center' : 'justify-between pl-[20px] pr-[16px]'}`}>
        {!isCollapsed && <img src="/logo.png" alt="SMA Logo" className="w-[160px] h-auto object-contain dark:invert-0 invert" />}
        {(onClose || onOpen) && (
          <button
            onClick={isCollapsed ? onOpen : onClose}
            className={`flex items-center justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-[#2D2844] transition-all text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white ${isCollapsed ? 'w-10 h-10' : 'w-8 h-8'}`}
            title={isCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
          >
            {isCollapsed ? <PanelLeftOpen className="w-5 h-5" /> : <PanelLeftClose className="w-5 h-5" />}
          </button>
        )}
      </div>

      {/* Nav - Cố định */}
      <nav className={`flex flex-col items-center space-y-4 w-full shrink-0 my-2 ${isCollapsed ? 'px-2' : 'px-[31px]'}`}>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeMenu === item.id;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              title={isCollapsed ? item.name : undefined}
              className={`flex items-center rounded-lg transition-colors ${isActive ? (isCollapsed ? 'bg-sma-purple/10 dark:bg-sma-purple/20 text-sma-purple' : 'bg-sma-purple text-white') : 'bg-transparent hover:bg-gray-100 dark:hover:bg-[#1A1630]'} ${isCollapsed ? 'w-10 h-10 justify-center' : 'w-[240px] h-10 px-3 gap-3'}`}
            >
              <Icon className={`w-5 h-5 shrink-0 ${isActive ? (isCollapsed ? 'text-sma-purple dark:text-[#9A7DFF]' : 'text-white') : 'text-gray-600 dark:text-gray-400'}`} />
              {!isCollapsed && (
                <span className={`font-medium text-[15px] ${isActive ? 'text-white' : 'text-gray-700 dark:text-gray-200'}`}>{item.name}</span>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Nội dung linh hoạt - Chỉ phần này mới được cuộn */}
      <div className="flex-1 min-h-0 flex flex-col overflow-y-auto scrollbar-hide">
        {!isCollapsed && showLibraryCount && (
          <div className="relative w-full px-[24px] py-3">
            <div className="relative flex items-center justify-center mb-4">
              <div className="absolute w-full h-px bg-gray-300 dark:bg-[#D9D9D9] transition-colors"></div>
              <span className="bg-white dark:bg-[#16132A] px-2 relative z-10 text-[10px] text-gray-500 dark:text-gray-300 transition-colors">LIBRARY</span>
            </div>
            <div className="flex flex-col space-y-3 px-[10px]">
              {[
                { label: 'All Assets', icon: Folder, count: libraryStats.all },
                { label: 'Favourites', icon: Heart, count: libraryStats.favourites },
                { label: 'Trash', icon: Trash, count: libraryStats.trash }
              ].map((item, idx) => (
                <div key={idx} className="flex items-center justify-between group cursor-pointer">
                  <div className="flex items-center gap-4 text-gray-700 dark:text-gray-200 group-hover:text-sma-purple transition-colors">
                    <item.icon className="w-5 h-5" />
                    <span className="text-[12px]">{item.label}</span>
                  </div>
                  <div className="w-10 h-5 bg-gray-200 dark:bg-sma-blue rounded-[5px] flex items-center justify-center text-[11px] text-gray-700 dark:text-white transition-colors">
                    {item.count}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {!isCollapsed && (
          <div className="flex justify-center w-full mt-auto py-4">
            <AIProcessingPanel />
          </div>
        )}
      </div>

      {/* Footer - Cố định */}
      <div className={`pt-3 pb-4 flex flex-col justify-center shrink-0 border-t border-gray-200 dark:border-[#2D2844] transition-colors ${isCollapsed ? 'px-2 items-center' : 'px-4'}`}>
        {!isCollapsed ? (
          <div className="flex items-center justify-between bg-gray-50 dark:bg-[#1A1630] rounded-lg p-2">
            <div className="flex items-center gap-3 overflow-hidden">
              <div className="w-8 h-8 rounded-full bg-sma-purple text-white flex items-center justify-center font-bold text-sm shrink-0">
                {(user?.attributes?.name || user?.username || 'U')[0].toUpperCase()}
              </div>
              <div className="flex flex-col truncate">
                <span className="text-sm font-semibold text-gray-700 dark:text-gray-200 truncate">
                  {user?.attributes?.name || user?.username || 'User'}
                </span>
                <span className="text-xs text-gray-500 dark:text-gray-400 truncate">
                  {user?.attributes?.email || ''}
                </span>
              </div>
            </div>
            <button
              onClick={signOut}
              title="Đăng xuất"
              className="p-2 text-gray-500 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 rounded-md transition-colors shrink-0"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <button
            onClick={signOut}
            title="Đăng xuất"
            className="w-10 h-10 rounded-lg flex items-center justify-center text-gray-500 hover:bg-red-50 hover:text-red-500 dark:text-gray-400 dark:hover:bg-red-500/10 dark:hover:text-red-400 transition-colors"
          >
            <LogOut className="w-5 h-5" />
          </button>
        )}
      </div>
    </aside>
  );
}