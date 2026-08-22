import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getAssets, getTags } from '../services/api';
import { Icon } from '@iconify/react';
import { useNavigate } from 'react-router-dom';
import MediaCard from '../components/media/MediaCard';
import { useAuth } from '../contexts/AuthContext';
import { getSearchHistory } from '../utils/history';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

export default function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const searchHistory = getSearchHistory();
  
  const { data: assetsData, isLoading } = useQuery({
    queryKey: ['assets'],
    queryFn: ({ signal }) => getAssets(signal, 50, 0),
    refetchOnWindowFocus: false,
  });

  const { data: tagsData } = useQuery({
    queryKey: ['tags'],
    queryFn: ({ signal }) => getTags(signal),
    refetchOnWindowFocus: false,
  });

  const assets = useMemo(() => {
    const rawAssets = assetsData?.items || [];
    try {
      const trashedIds = JSON.parse(localStorage.getItem('trashedIds') || '[]');
      return rawAssets.filter(a => !trashedIds.includes(a.asset_id));
    } catch {
      return rawAssets;
    }
  }, [assetsData]);

  const totalAssets = assets.length;
  
  // Calculate mock processing jobs
  const processingJobs = assets.filter(a => a.status === 'processing' || a.status === 'queued').length;
  
  // Get Favourites
  const getFavouriteIds = () => {
    try { return JSON.parse(localStorage.getItem('favouriteIds') || '[]'); } 
    catch { return []; }
  };
  const favouritesCount = assets.filter(a => getFavouriteIds().includes(a.asset_id)).length;

  // Chart Data: Media Types Breakdown
  const chartData = useMemo(() => {
    const types = {};
    assets.forEach(a => {
      const t = a.media_type || 'unknown';
      types[t] = (types[t] || 0) + 1;
    });
    return Object.keys(types).map(key => ({ name: key.toUpperCase(), value: types[key] }));
  }, [assets]);

  // Recent Uploads
  const recentAssets = useMemo(() => {
    return [...assets].sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0)).slice(0, 4);
  }, [assets]);

  return (
    <div className="max-w-7xl mx-auto space-y-6 relative min-h-full flex flex-col p-2 pb-12">
      
      {/* 1. Welcome Banner */}
      <div className="bg-[#1a1b26] rounded-2xl p-8 relative overflow-hidden text-white flex flex-col md:flex-row items-center justify-between shadow-sm">
        <div className="relative z-10 flex-1">
          <h1 className="text-3xl font-bold mb-2">Welcome back, {user?.attributes?.name || user?.username || 'User'}! 👋</h1>
          <p className="text-gray-400 text-sm max-w-xl">
            You currently have <strong className="text-white">{totalAssets}</strong> assets in your library. 
            {processingJobs > 0 && <span> <strong className="text-sma-purple">{processingJobs}</strong> videos are being analyzed by Gemini AI.</span>}
          </p>
          <div className="flex gap-4 mt-6">
            <button 
              onClick={() => navigate('/app/upload')}
              className="bg-sma-purple hover:bg-[#6b4ce6] text-white px-5 py-2.5 rounded-lg font-medium transition-all shadow-sm flex items-center gap-2"
            >
              <Icon icon="lucide:upload-cloud" width="18" /> Upload Media
            </button>
            <button 
              onClick={() => navigate('/app/assets')}
              className="bg-white/10 hover:bg-white/20 text-white px-5 py-2.5 rounded-lg font-medium transition-all flex items-center gap-2"
            >
              <Icon icon="lucide:layout-grid" width="18" /> View Library
            </button>
          </div>
        </div>
        <div className="hidden md:block absolute -right-10 -bottom-10 opacity-30 pointer-events-none">
          <Icon icon="lucide:activity" width="300" height="300" className="text-sma-purple" />
        </div>
      </div>

      {/* 2. Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Total Assets', value: totalAssets, icon: 'database', color: 'text-sma-purple', bg: 'bg-sma-purple/10' },
          { label: 'AI Processing', value: processingJobs, icon: 'cpu', color: 'text-blue-500', bg: 'bg-blue-500/10' },
          { label: 'Favourites', value: favouritesCount, icon: 'heart', color: 'text-red-500', bg: 'bg-red-500/10' },
          { label: 'Storage Used', value: `${(totalAssets * 12.5).toFixed(1)} MB`, icon: 'hard-drive', color: 'text-emerald-500', bg: 'bg-emerald-500/10' }
        ].map((stat, idx) => (
          <div key={idx} className="bg-white dark:bg-[#1a1b26] p-5 rounded-2xl border border-gray-100 dark:border-white/5 flex items-center justify-between shadow-sm hover:shadow-md transition-shadow">
            <div>
              <p className="text-gray-500 dark:text-gray-400 text-xs font-bold uppercase tracking-wider mb-1">{stat.label}</p>
              <h3 className="text-2xl font-black text-gray-900 dark:text-white">{stat.value}</h3>
            </div>
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${stat.bg}`}>
              <Icon icon={`lucide:${stat.icon}`} width="24" className={stat.color} />
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* 3. Main Chart & Uploads */}
        <div className="lg:col-span-2 space-y-6">
          
          <div className="bg-white dark:bg-[#1a1b26] p-6 rounded-2xl border border-gray-100 dark:border-white/5 shadow-sm">
            <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-6 flex items-center gap-2">
              <Icon icon="lucide:bar-chart-2" className="text-sma-purple" />
              Media Format Distribution
            </h3>
            <div className="h-[250px] w-full">
              {chartData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <XAxis dataKey="name" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                    <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                    <Tooltip cursor={{fill: 'transparent'}} contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                    <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                      {chartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={index === 0 ? '#7b5cf5' : '#3b82f6'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="w-full h-full flex flex-col items-center justify-center text-gray-400">
                  <Icon icon="lucide:inbox" width="32" className="mb-2 opacity-50" />
                  <p className="text-sm">Not enough data to display chart</p>
                </div>
              )}
            </div>
          </div>

          <div className="bg-white dark:bg-[#1a1b26] p-6 rounded-2xl border border-gray-100 dark:border-white/5 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
                <Icon icon="lucide:clock" className="text-sma-purple" />
                Recent Uploads
              </h3>
              <button 
                onClick={() => navigate('/app/assets')}
                className="text-sm font-medium text-sma-purple hover:text-[#6b4ce6] transition-colors"
              >
                View all
              </button>
            </div>
            
            {isLoading ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                 {[1, 2].map(n => <div key={n} className="animate-pulse bg-gray-200 dark:bg-white/5 h-[200px] rounded-xl" />)}
              </div>
            ) : recentAssets.length === 0 ? (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400 border border-dashed border-gray-200 dark:border-white/10 rounded-xl">
                No recent uploads found.
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 opacity-90">
                {recentAssets.map(asset => (
                  <MediaCard key={asset.asset_id} {...asset} />
                ))}
              </div>
            )}
          </div>
        </div>

        {/* 4. Side Widget (Tags & Searches) */}
        <div className="space-y-6">
          <div className="bg-white dark:bg-[#1a1b26] p-6 rounded-2xl border border-gray-100 dark:border-white/5 shadow-sm">
            <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
              <Icon icon="lucide:tag" className="text-sma-purple" />
              Popular Tags
            </h3>
            {tagsData?.items?.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {tagsData.items.slice(0, 15).map((tag, idx) => (
                  <button 
                    key={idx}
                    onClick={() => navigate('/app/assets')}
                    className="px-3 py-1.5 bg-gray-100 dark:bg-white/5 hover:bg-sma-purple/10 dark:hover:bg-sma-purple/20 text-gray-600 dark:text-gray-300 hover:text-sma-purple rounded-lg text-xs font-medium transition-colors"
                  >
                    {tag.name || tag}
                  </button>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500 dark:text-gray-400">No tags available yet.</p>
            )}
          </div>

          <div className="bg-white dark:bg-[#1a1b26] p-6 rounded-2xl border border-gray-100 dark:border-white/5 shadow-sm">
            <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
              <Icon icon="lucide:search" className="text-sma-purple" />
              Recent Searches
            </h3>
            {searchHistory.length > 0 ? (
              <div className="flex flex-col space-y-2">
                {searchHistory.slice(0, 5).map((term, idx) => (
                  <div key={idx} className="flex items-center gap-3 p-3 rounded-xl bg-gray-50 dark:bg-white/5 text-gray-700 dark:text-gray-300">
                    <Icon icon="lucide:history" className="text-gray-400 shrink-0" width="16" />
                    <span className="text-sm font-medium truncate">{term}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500 dark:text-gray-400">No recent searches.</p>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
