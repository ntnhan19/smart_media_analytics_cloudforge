import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import AppShell from './components/layout/AppShell';
import Dashboard from './pages/Dashboard';
import Search from './pages/Search';
import AssetDetail from './pages/AssetDetail';
import Upload from './pages/Upload';
import Settings from './pages/Settings';
import UiKitDemo from './pages/UiKitDemo';

import { JobProvider } from './contexts/JobContext';
import { useEffect } from 'react';

import { Amplify } from 'aws-amplify';
import { Authenticator } from '@aws-amplify/ui-react';
import '@aws-amplify/ui-react/styles.css';

Amplify.configure({
  Auth: {
    Cognito: {
      userPoolId: import.meta.env.VITE_COGNITO_USER_POOL_ID,
      userPoolClientId: import.meta.env.VITE_COGNITO_USER_POOL_CLIENT_ID,
    }
  }
});

const formFields = {
  signUp: {
    name: {
      order: 1,
      placeholder: 'Nhập họ và tên của bạn',
      label: 'Họ và tên *',
      isRequired: true,
    },
    email: {
      order: 2,
      placeholder: 'Nhập địa chỉ email',
      label: 'Email *',
      isRequired: true,
    },
    password: {
      order: 3,
      placeholder: 'Nhập mật khẩu',
      label: 'Mật khẩu *',
      isRequired: true,
    },
    confirm_password: {
      order: 4,
      placeholder: 'Nhập lại mật khẩu',
      label: 'Xác nhận mật khẩu *',
      isRequired: true,
    },
  },
  signIn: {
    username: {
      placeholder: 'Nhập địa chỉ email',
      label: 'Email *',
      isRequired: true,
    },
    password: {
      placeholder: 'Nhập mật khẩu',
      label: 'Mật khẩu *',
      isRequired: true,
    },
  },
};

const queryClient = new QueryClient();

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
    <Authenticator loginMechanisms={['email']} formFields={formFields}>
      {({ signOut, user }) => (
        <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
          <div style={{ padding: '8px 20px', display: 'flex', justifyContent: 'flex-end', alignItems: 'center', backgroundColor: '#111827', color: 'white', fontSize: '14px', zIndex: 9999 }}>
            <span style={{ marginRight: '16px' }}>Xin chào, <b style={{ color: '#60a5fa' }}>{user?.attributes?.name || user?.username}</b>!</span>
            <button
              onClick={signOut}
              style={{ padding: '4px 12px', cursor: 'pointer', backgroundColor: '#ef4444', color: 'white', border: 'none', borderRadius: '4px', fontWeight: 'bold' }}
            >
              Đăng xuất
            </button>
          </div>

          <div style={{ flex: 1 }}>
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
          </div>

        </div>
      )}
    </Authenticator>
  );
}

export default App;