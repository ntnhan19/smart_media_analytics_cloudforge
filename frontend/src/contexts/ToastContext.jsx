import { createContext, useContext, useState, useCallback } from 'react';
import { Icon } from '@iconify/react';

const ToastContext = createContext(null);

export const ToastProvider = ({ children }) => {
  const [toasts, setToasts] = useState([]);

  const showToast = useCallback((message, type = 'success', duration = 4000) => {
    const id = Date.now().toString() + Math.random().toString(36).substring(2);
    setToasts((prev) => [...prev, { id, message, type }]);

    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, duration);
  }, []);

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      {/* Global Toast Container */}
      <div className="fixed top-6 right-6 z-[9999] flex flex-col gap-2 pointer-events-none">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`px-6 py-3 rounded-lg shadow-2xl text-white font-medium text-sm flex items-center space-x-2 animate-fade-in-down pointer-events-auto transition-all transform duration-300 ease-in-out ${
              toast.type === 'success'
                ? 'bg-gradient-to-r from-emerald-500 to-emerald-600'
                : toast.type === 'error'
                ? 'bg-gradient-to-r from-red-500 to-red-600'
                : 'bg-gradient-to-r from-[#7B5CF5] to-[#6044DD]'
            }`}
          >
            <Icon
              icon={
                toast.type === 'success'
                  ? 'lucide:check-circle'
                  : toast.type === 'error'
                  ? 'lucide:alert-circle'
                  : 'lucide:info'
              }
              width="18"
            />
            <span>{toast.message}</span>
            <button
              onClick={() => removeToast(toast.id)}
              className="ml-auto pl-4 opacity-70 hover:opacity-100 transition-opacity"
            >
              <Icon icon="lucide:x" width="16" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};
