import { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import TopBar from './TopBar';
import { Menu, X } from 'lucide-react';

export default function AppShell() {
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const getActiveMenu = () => {
    if (location.pathname.startsWith('/upload')) return 'upload';
    if (location.pathname.startsWith('/settings')) return 'settings';
    return 'dashboard';
  };

  const isDashboard = location.pathname === '/';

  return (
    <div className="flex h-screen overflow-hidden bg-sma-bg text-white">

      {/* Sidebar */}
      <div
        className="shrink-0 overflow-hidden transition-all duration-300 ease-in-out"
        style={{ width: sidebarOpen ? '310px' : '0' }}
      >
        <div style={{ width: '310px', height: '100%' }}>
          <Sidebar activeMenu={getActiveMenu()} showLibraryCount={true} />
        </div>
      </div>

      {/* Main */}
      <main className="flex-1 min-w-0 flex flex-col overflow-hidden relative">
        {/* Toggle Sidebar Button */}
        <button
          onClick={() => setSidebarOpen(p => !p)}
          className="absolute top-3 left-3 z-50 w-7 h-7 flex items-center justify-center rounded bg-[#16132A] border border-white/10 hover:border-[#7B5CF5] hover:bg-[#7B5CF5]/20 transition-all"
        >
          {sidebarOpen ? <X className="w-3.5 h-3.5 text-white" /> : <Menu className="w-3.5 h-3.5 text-white" />}
        </button>

        {/* Content: zero vertical padding để nội dung lấp đầy h-screen */}
        <div className="flex-1 min-h-0 overflow-hidden pl-11 pr-3 pt-2 pb-2">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
