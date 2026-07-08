import { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import { Menu, X } from 'lucide-react';

export default function AppShell() {
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const getActiveMenu = () => {
    if (location.pathname.startsWith('/upload')) return 'upload';
    if (location.pathname.startsWith('/settings')) return 'settings';
    return 'dashboard';
  };

  return (
    <div className="flex h-screen overflow-hidden bg-[#F8F9FA] dark:bg-sma-bg text-gray-900 dark:text-white transition-colors">

      {/* Sidebar */}
      <div
        className="shrink-0 overflow-hidden transition-all duration-300 ease-in-out"
        style={{ width: sidebarOpen ? '310px' : '64px' }}
      >
        <div style={{ width: '310px', height: '100%' }}>
          <Sidebar 
            activeMenu={getActiveMenu()} 
            showLibraryCount={true} 
            onClose={() => setSidebarOpen(false)} 
            onOpen={() => setSidebarOpen(true)}
            isCollapsed={!sidebarOpen} 
          />
        </div>
      </div>

      <main className="flex-1 min-w-0 flex flex-col overflow-hidden relative">
        {/* Content */}
        <div className="flex-1 min-h-0 overflow-hidden pl-4 pr-3 pt-2 pb-2">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
