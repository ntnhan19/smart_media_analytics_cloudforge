import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import AppShell from './components/layout/AppShell';
import Dashboard from './pages/Dashboard';
import Assets from './pages/Assets';
import Search from './pages/Search';
import AssetDetail from './pages/AssetDetail';
import Upload from './pages/Upload';
import Settings from './pages/Settings';
import UiKitDemo from './pages/UiKitDemo';
import Favourites from './pages/Favourites';
import Trash from './pages/Trash';

import Landing from './pages/Landing';
import Login from './pages/Login';
import RequireAuth from './components/auth/RequireAuth';

import { JobProvider } from './contexts/JobContext';
import { AuthProvider } from './contexts/AuthContext';
import { useEffect } from 'react';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: false,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

function App() {
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') || 'light';
    if (savedTheme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', width: '100%' }}>
      <div style={{ flex: 1 }}>
        <QueryClientProvider client={queryClient}>
          <AuthProvider>
            <JobProvider>
              <BrowserRouter>
                <Routes>
                  {/* Public Routes */}
                  <Route path="/" element={<Landing />} />
                  <Route path="/login" element={<Login />} />

                  {/* Private App Routes */}
                  <Route path="/app" element={
                    <RequireAuth>
                      <AppShell />
                    </RequireAuth>
                  }>
                    <Route index element={<Dashboard />} />
                    <Route path="assets" element={<Assets />} />
                    <Route path="search" element={<Search />} />
                    <Route path="favourites" element={<Favourites />} />
                    <Route path="trash" element={<Trash />} />
                    <Route path="assets/:id" element={<AssetDetail />} />
                    <Route path="upload" element={<Upload />} />
                    <Route path="settings" element={<Settings />} />
                    <Route path="uikit" element={<UiKitDemo />} />
                  </Route>
                </Routes>
              </BrowserRouter>
            </JobProvider>
          </AuthProvider>
        </QueryClientProvider>
      </div>
    </div>
  );
}

export default App;