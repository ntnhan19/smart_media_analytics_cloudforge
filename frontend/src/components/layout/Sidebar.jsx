import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Folder, Heart, Trash, Upload, Settings, Home, LogOut, PanelLeftClose, PanelLeftOpen } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { getAssets } from '../../services/api';
import { projectsApi } from '../../api/projects';
import AIProcessingPanel from './AIProcessingPanel';
import CreateProjectModal from '../project/CreateProjectModal';
import { useToast } from '../../contexts/ToastContext';

export default function Sidebar({ activeMenu, showLibraryCount = false, onClose, onOpen, isCollapsed = false }) {
  const { user, logout: signOut } = useAuth();
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const { data: assets } = useQuery({
    queryKey: ['assets'],
    queryFn: ({ signal }) => getAssets(signal),
    enabled: showLibraryCount,
  });

  const { data: projectsData } = useQuery({
    queryKey: ['projects'],
    queryFn: projectsApi.list,
  });

  const createProjectMutation = useMutation({
    mutationFn: projectsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setIsCreateModalOpen(false);
      showToast('Project created successfully', 'success');
    },
    onError: (err) => {
      console.error(err);
      showToast('Failed to create project', 'error');
    }
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

  const mainNavItems = [
    { name: 'Dashboard', path: '/app', id: 'dashboard', icon: LayoutDashboard },
    { name: 'Assets', path: '/app/assets', id: 'assets', icon: Folder },
    { name: 'Favourites', path: '/app/favourites', id: 'favourites', icon: Heart },
    { name: 'Trash', path: '/app/trash', id: 'trash', icon: Trash },
  ];

  const bottomNavItems = [
    { name: 'Settings', path: '/app/settings', id: 'settings', icon: Settings },
  ];

  return (
    <aside className={`${isCollapsed ? 'w-[64px]' : 'w-[260px]'} h-full bg-white dark:bg-[#16132A] border-r border-gray-200 dark:border-transparent flex flex-col shrink-0 overflow-hidden transition-all duration-300 z-20`}>

      {/* Header */}
      <div className={`pt-5 pb-5 shrink-0 flex items-center ${isCollapsed ? 'justify-center' : 'justify-between pl-6 pr-4'}`}>
        {!isCollapsed && (
          <NavLink to="/" className="flex items-center">
            <img src="/logo.png" alt="SMA Logo" className="h-14 w-auto object-contain dark:invert-0 invert transition-transform hover:scale-105" />
          </NavLink>
        )}
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

      <div className="flex-1 min-h-0 flex flex-col overflow-y-auto scrollbar-hide">
        {/* Upload Button - Primary Action */}
        <div className={`shrink-0 mb-6 flex ${isCollapsed ? 'justify-center px-2' : 'px-4'}`}>
          <NavLink
            to="/app/upload"
            title={isCollapsed ? "Upload" : undefined}
            className={`flex items-center justify-center rounded-xl transition-all duration-200 bg-sma-purple hover:bg-sma-purple/90 text-white shadow-sm hover:shadow active:scale-[0.98] ${isCollapsed ? 'w-10 h-10' : 'w-full h-11 gap-2.5'}`}
          >
            <Upload className={`shrink-0 ${isCollapsed ? 'w-5 h-5' : 'w-4.5 h-4.5'}`} />
            {!isCollapsed && (
              <span className="font-semibold text-[14px]">Upload Media</span>
            )}
          </NavLink>
        </div>

        {/* Main Nav */}
        <nav className={`flex flex-col space-y-1 shrink-0 ${isCollapsed ? 'px-2 items-center' : 'px-3'}`}>
          {mainNavItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeMenu === item.id;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                title={isCollapsed ? item.name : undefined}
                className={`flex items-center rounded-lg transition-all duration-200 ${isActive ? 'bg-sma-purple/10 text-sma-purple dark:bg-sma-purple/20 dark:text-[#9A7DFF]' : 'bg-transparent text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-[#1A1630] hover:text-gray-900 dark:hover:text-gray-200'} ${isCollapsed ? 'w-10 h-10 justify-center' : 'w-full h-10 px-3 gap-3'}`}
              >
                <Icon className={`w-[18px] h-[18px] shrink-0`} />
                {!isCollapsed && (
                  <span className={`font-medium text-[14px]`}>{item.name}</span>
                )}
              </NavLink>
            );
          })}
        </nav>

        {/* Projects Section */}
        <div className={`mt-6 mb-2 shrink-0 ${isCollapsed ? 'px-2 flex justify-center' : 'px-6'}`}>
          {!isCollapsed && (
            <div className="flex items-center justify-between mb-2 group">
              <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider">Projects</h3>
              <button 
                onClick={() => setIsCreateModalOpen(true)}
                className="text-gray-400 hover:text-sma-purple opacity-0 group-hover:opacity-100 transition-opacity"
                title="Create Project"
              >
                <Icon icon="lucide:plus" width="16" />
              </button>
            </div>
          )}
          
          {projectsData && projectsData.length > 0 ? (
            <nav className={`flex flex-col space-y-1 ${isCollapsed ? 'items-center' : ''}`}>
              {projectsData.map(proj => (
                <NavLink
                  key={proj.id}
                  to={`/app/assets?project=${proj.id}`}
                  title={isCollapsed ? proj.name : undefined}
                  className={`flex items-center rounded-lg transition-all duration-200 ${activeMenu === proj.id ? 'bg-sma-purple/10 text-sma-purple dark:bg-sma-purple/20 dark:text-[#9A7DFF]' : 'bg-transparent text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-[#1A1630] hover:text-gray-900 dark:hover:text-gray-200'} ${isCollapsed ? 'w-10 h-10 justify-center' : 'w-full h-9 px-3 gap-3'}`}
                >
                  <div className="w-[18px] h-[18px] shrink-0 bg-sma-purple/20 rounded flex items-center justify-center">
                    <span className="text-[10px] font-bold text-sma-purple">{proj.name.charAt(0).toUpperCase()}</span>
                  </div>
                  {!isCollapsed && (
                    <span className="font-medium text-[13px] truncate">{proj.name}</span>
                  )}
                </NavLink>
              ))}
            </nav>
          ) : (
            !isCollapsed && (
              <div className="text-xs text-gray-400 text-center py-2 border border-dashed border-gray-200 dark:border-white/10 rounded-lg">
                No projects yet.
              </div>
            )
          )}
        </div>

        {/* Spacer to push bottom items down */}
        <div className="flex-1"></div>

        {/* Bottom Nav */}
        <nav className={`flex flex-col space-y-1 shrink-0 ${isCollapsed ? 'px-2 items-center' : 'px-3'}`}>
          {bottomNavItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeMenu === item.id;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                title={isCollapsed ? item.name : undefined}
                className={`flex items-center rounded-lg transition-all duration-200 ${isActive ? 'bg-sma-purple/10 text-sma-purple dark:bg-sma-purple/20 dark:text-[#9A7DFF]' : 'bg-transparent text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-[#1A1630] hover:text-gray-900 dark:hover:text-gray-200'} ${isCollapsed ? 'w-10 h-10 justify-center' : 'w-full h-10 px-3 gap-3'}`}
              >
                <Icon className={`w-[18px] h-[18px] shrink-0`} />
                {!isCollapsed && (
                  <span className={`font-medium text-[14px]`}>{item.name}</span>
                )}
              </NavLink>
            );
          })}
        </nav>

        {/* AI Processing Panel */}
        {!isCollapsed && (
          <div className="flex justify-center w-full py-4 px-4 shrink-0 mt-2">
            <AIProcessingPanel />
          </div>
        )}
      </div>

      {/* Footer */}
      <div className={`pt-3 pb-4 flex flex-col justify-center shrink-0 border-t border-gray-200 dark:border-[#2D2844] transition-colors ${isCollapsed ? 'px-2 items-center' : 'px-4'}`}>
        {!isCollapsed ? (
          <div className="flex items-center justify-between bg-gray-50 dark:bg-[#1A1630] rounded-xl p-2.5">
            <div className="flex items-center gap-3 overflow-hidden">
              <div className="w-8 h-8 rounded-full bg-sma-purple text-white flex items-center justify-center font-bold text-sm shrink-0 shadow-sm">
                {(user?.attributes?.name || user?.username || 'U')[0].toUpperCase()}
              </div>
              <div className="flex flex-col truncate pr-2">
                <span className="text-[13px] font-semibold text-gray-800 dark:text-gray-200 truncate leading-tight">
                  {user?.attributes?.name || user?.username || 'User'}
                </span>
                <span className="text-[11px] text-gray-500 dark:text-gray-400 truncate leading-tight mt-0.5">
                  {user?.email || ''}
                </span>
              </div>
            </div>
            <button
              onClick={signOut}
              title="Log Out"
              className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 rounded-lg transition-colors shrink-0"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <button
            onClick={signOut}
            title="Log Out"
            className="w-10 h-10 rounded-xl flex items-center justify-center text-gray-500 hover:bg-red-50 hover:text-red-500 dark:text-gray-400 dark:hover:bg-red-500/10 dark:hover:text-red-400 transition-colors"
          >
            <LogOut className="w-[18px] h-[18px]" />
          </button>
        )}
      </div>
      
      <CreateProjectModal 
        isOpen={isCreateModalOpen} 
        onClose={() => setIsCreateModalOpen(false)} 
        onSubmit={(data) => createProjectMutation.mutate(data)}
        isLoading={createProjectMutation.isLoading}
      />
    </aside>
  );
}