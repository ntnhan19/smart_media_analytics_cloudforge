import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import AppShell from './components/layout/AppShell';
import Dashboard from './pages/Dashboard';
import Search from './pages/Search';
import AssetDetail from './pages/AssetDetail';
import Upload from './pages/Upload';
import Settings from './pages/Settings';
import UiKitDemo from './pages/UiKitDemo';

const queryClient = new QueryClient();

import { JobProvider } from './contexts/JobContext';

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <JobProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<AppShell />}>
              <Route index element={<Dashboard />} />
              <Route path="search" element={<Search />} />
              <Route path="assets/:id" element={<AssetDetail />} />
              <Route path="upload" element={<Upload />} />
              <Route path="settings" element={<Settings />} />
              <Route path="uikit" element={<UiKitDemo />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </JobProvider>
    </QueryClientProvider>
  );
}

export default App;
