import { useState, useEffect } from 'react';
import api from '../../services/api';
import { Server, ServerOff, Loader2 } from 'lucide-react';

export default function HealthCheck() {
  const [status, setStatus] = useState('loading'); // loading, ok, error

  useEffect(() => {
    api.get('/health')
      .then(() => setStatus('ok'))
      .catch(() => setStatus('error'));
  }, []);

  if (status === 'loading') {
    return (
      <div className="flex items-center gap-2 text-gray-400">
        <Loader2 className="w-4 h-4 animate-spin" />
        <span className="text-sm">Checking backend...</span>
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="flex items-center gap-2 text-red-500">
        <ServerOff className="w-4 h-4" />
        <span className="text-sm font-medium">Backend: Offline ✗</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 text-green-500">
      <Server className="w-4 h-4" />
      <span className="text-sm font-medium">Backend: Connected ✓</span>
    </div>
  );
}
