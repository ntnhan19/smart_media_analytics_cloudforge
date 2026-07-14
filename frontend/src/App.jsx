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
import { Authenticator, View } from '@aws-amplify/ui-react';
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

const components = {
  Header() {
    return (
      <View textAlign="center" padding="2.5rem 0 1.5rem 0" className="flex flex-col items-center">
        <div className="relative animate-float mb-6">
           <div className="absolute inset-0 bg-sma-purple blur-xl opacity-40 rounded-full"></div>
           <div className="relative bg-[#16132A] p-4 rounded-2xl border border-white/10 shadow-xl flex items-center justify-center">
             <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-sma-purple">
               <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
               <polyline points="17 8 12 3 7 8"></polyline>
               <line x1="12" y1="3" x2="12" y2="15"></line>
             </svg>
           </div>
        </div>
        <h1 className="text-3xl font-extrabold bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent font-inter tracking-tight">
          Smart Media Analytics
        </h1>
        <p className="text-gray-400 mt-2 font-inter text-sm">Sign in to access your AI library</p>
      </View>
    );
  }
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
    <Authenticator loginMechanisms={['email']} formFields={formFields} components={components}>
      {() => (
        <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', width: '100%' }}>

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