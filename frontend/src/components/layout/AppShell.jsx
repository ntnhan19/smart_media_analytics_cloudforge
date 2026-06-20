import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import TopBar from './TopBar';

export default function AppShell() {
  const location = useLocation();
  
  const getActiveMenu = () => {
    if (location.pathname.startsWith('/upload')) return 'upload';
    if (location.pathname.startsWith('/settings')) return 'settings';
    return 'dashboard';
  };

  // Mock state: User has uploaded a video
  const hasUploadedVideo = true;
  const isDashboard = location.pathname === '/';

  return (
    <div className="flex h-screen bg-sma-bg text-white overflow-hidden">
      <Sidebar 
        activeMenu={getActiveMenu()} 
        showLibraryCount={true} 
      />
      
      <main className="flex-1 flex flex-col overflow-hidden relative">
        {isDashboard && hasUploadedVideo && (
          <TopBar />
        )}
        
        <div className="flex-1 overflow-y-auto">
          <div className="flex h-full">
            <div className="flex-1 overflow-y-auto p-6">
              <Outlet />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
