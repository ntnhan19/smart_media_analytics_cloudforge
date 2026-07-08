import { useState, useEffect } from 'react';
import { Icon } from '@iconify/react';
import { useTranslation } from 'react-i18next';

// Modern Switch Component
function ToggleSwitch({ checked, onChange }) {
  return (
    <button
      type="button"
      onClick={onChange}
      aria-label="Toggle setting"
      className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center justify-center rounded-full focus:outline-none focus-visible:ring-2 focus-visible:ring-sma-purple focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900 transition-all duration-300 ${checked ? 'bg-[#7B5CF5] shadow-[0_0_12px_rgba(123,92,245,0.4)]' : 'bg-gray-200 dark:bg-[#2D2844]'}`}
    >
      <span className="sr-only">Toggle</span>
      <span
        aria-hidden="true"
        className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-sm ring-0 transition duration-300 ease-in-out ${checked ? 'translate-x-2.5' : '-translate-x-2.5'}`}
      />
    </button>
  );
}

export default function Settings() {
  const { t, i18n } = useTranslation();
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'light');
  const [toast, setToast] = useState(null);
  const [activeTab, setActiveTab] = useState('general');
  const [isAnimating, setIsAnimating] = useState(false);

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    localStorage.setItem('theme', theme);
  }, [theme]);

  const handleTabChange = (tabId) => {
    if (tabId === activeTab) return;
    setIsAnimating(true);
    setTimeout(() => {
      setActiveTab(tabId);
      setIsAnimating(false);
    }, 150);
  };

  const handleSave = (e) => {
    e.preventDefault();
    showToast(t('settings.toastSuccess'));
  };

  const tabs = [
    { id: 'general', label: t('settings.general'), icon: 'lucide:settings' },
    { id: 'ai', label: t('settings.aiPrefs'), icon: 'lucide:bot' },
    { id: 'appearance', label: t('settings.appearance'), icon: 'lucide:palette' },
    { id: 'about', label: t('settings.about'), icon: 'lucide:info' }
  ];

  return (
    <div className="max-w-[1000px] mx-auto h-full flex flex-col relative text-gray-900 dark:text-gray-100 transition-colors pt-4 px-4">
      {/* Background glow effects for premium feel */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-[#7B5CF5] rounded-full blur-[120px] opacity-10 pointer-events-none"></div>
      <div className="absolute bottom-[-10%] right-[-10%] w-[30%] h-[30%] bg-[#4C3B8E] rounded-full blur-[100px] opacity-10 pointer-events-none"></div>

      {toast && (
        <div className={`fixed top-6 right-6 z-50 px-6 py-3 rounded-lg shadow-2xl text-white font-medium text-sm flex items-center space-x-2 animate-fade-in-down ${toast.type === 'success' ? 'bg-gradient-to-r from-emerald-500 to-emerald-600' : 'bg-gradient-to-r from-red-500 to-red-600'}`}>
          <Icon icon={toast.type === 'success' ? "lucide:check-circle" : "lucide:alert-circle"} width="18" />
          <span>{toast.message}</span>
        </div>
      )}

      {/* Header */}
      <div className="mb-8 shrink-0 relative z-10">
        <h1 className="text-3xl font-extrabold font-inter text-gray-900 dark:text-white tracking-tight">{t('settings.title')}</h1>
        <p className="text-gray-500 dark:text-gray-400 text-sm mt-2 font-medium">{t('settings.subtitle')}</p>
      </div>

      <form onSubmit={handleSave} className="flex-1 flex flex-col min-h-0 relative z-10">
        <div className="flex flex-col md:flex-row gap-8 h-full min-h-0">

          {/* Sidebar / Tabs Navigation */}
          <div className="w-full md:w-60 shrink-0 flex flex-row md:flex-col gap-2 overflow-x-auto md:overflow-visible pb-4 md:pb-0">
            {tabs.map(tab => {
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => handleTabChange(tab.id)}
                  className={`relative flex items-center space-x-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all duration-300 whitespace-nowrap group overflow-hidden ${isActive
                    ? 'text-[#7B5CF5] dark:text-white shadow-sm'
                    : 'text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 hover:bg-gray-50/50 dark:hover:bg-white/5'
                    }`}
                >
                  {/* Active Background highlight */}
                  {isActive && (
                    <div className="absolute inset-0 bg-white dark:bg-[#1A1630] border border-gray-200 dark:border-[#3f3b60]/40 rounded-xl -z-10 transition-all duration-300 shadow-[0_4px_12px_-2px_rgba(0,0,0,0.06)] dark:shadow-[0_2px_10px_rgba(0,0,0,0.2)]"></div>
                  )}
                  {isActive && (
                    <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-[#7B5CF5] rounded-r-full"></div>
                  )}

                  <Icon icon={tab.icon} width="20" height="20" className={`transition-transform duration-300 ${isActive ? 'scale-110 text-[#7B5CF5]' : 'group-hover:scale-110'}`} />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>

          {/* Content Area */}
          <div className="flex-1 min-w-0 flex flex-col overflow-hidden">
            <div className={`flex-1 overflow-y-auto pr-4 transition-all duration-300 ${isAnimating ? 'opacity-0 translate-y-4' : 'opacity-100 translate-y-0'}`}>

              {activeTab === 'general' && (
                <div className="space-y-8 pb-8">
                  <div>
                    <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-1">{t('settings.general')}</h2>
                    <p className="text-gray-500 dark:text-gray-400 text-sm">{t('settings.generalDesc')}</p>
                  </div>

                  <div className="bg-white dark:bg-[#16132A]/60 backdrop-blur-xl border border-gray-200 dark:border-white/5 rounded-2xl p-6 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.08)] dark:shadow-sm">
                    <div className="space-y-6">
                      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
                        <div className="pr-4">
                          <h3 className="text-sm font-semibold text-gray-900 dark:text-white">{t('settings.language')}</h3>
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{t('settings.languageDesc')}</p>
                        </div>
                        <div className="relative shrink-0 w-full sm:w-48">
                          <select 
                            className="w-full appearance-none bg-gray-50 dark:bg-[#0D0A1A] border border-gray-200 dark:border-[#3f3b60]/50 text-gray-900 dark:text-white text-sm rounded-xl pl-10 pr-8 py-2.5 focus:outline-none focus:ring-2 focus:ring-sma-purple/50 focus:border-sma-purple transition-all duration-200 cursor-pointer shadow-sm"
                            value={i18n.resolvedLanguage}
                            onChange={(e) => i18n.changeLanguage(e.target.value)}
                          >
                            <option value="en">English</option>
                            <option value="vi">Tiếng Việt</option>
                          </select>
                          <Icon icon="lucide:globe" className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" width="16" />
                          <Icon icon="lucide:chevron-down" className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400" width="16" />
                        </div>
                      </div>

                      <div className="h-px bg-gray-200 dark:bg-white/5 w-full"></div>

                      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
                        <div className="pr-4">
                          <h3 className="text-sm font-semibold text-gray-900 dark:text-white">{t('settings.autoSave')}</h3>
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{t('settings.autoSaveDesc')}</p>
                        </div>
                        <ToggleSwitch checked={true} onChange={() => { }} />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'ai' && (
                <div className="space-y-8 pb-8">
                  <div className="flex justify-between items-end">
                    <div>
                      <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-1">{t('settings.aiPrefs')}</h2>
                      <p className="text-gray-500 dark:text-gray-400 text-sm">{t('settings.aiPrefsDesc')}</p>
                    </div>
                    <span className="text-[10px] font-bold px-2.5 py-1 bg-sma-purple/10 text-sma-purple dark:bg-sma-purple/20 dark:text-[#A78BFA] rounded-md uppercase tracking-wider border border-sma-purple/20">
                      Placeholder UI Only
                    </span>
                  </div>

                  <div className="bg-white dark:bg-[#16132A]/60 backdrop-blur-xl border border-gray-200 dark:border-white/5 rounded-2xl p-6 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.08)] dark:shadow-sm">
                    <div className="space-y-6">
                      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-4">
                        <div className="pr-4 sm:w-1/2">
                          <h3 className="text-sm font-semibold text-gray-900 dark:text-white">{t('settings.aiProvider')}</h3>
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{t('settings.aiProviderDesc')}</p>
                        </div>
                        <div className="relative shrink-0 w-full sm:w-1/2">
                          <select className="w-full appearance-none bg-gray-50 dark:bg-[#0D0A1A] border border-gray-200 dark:border-[#3f3b60]/50 text-gray-900 dark:text-white text-sm rounded-xl pl-4 pr-10 py-2.5 focus:outline-none focus:ring-2 focus:ring-sma-purple/50 focus:border-sma-purple transition-all duration-200 cursor-pointer shadow-sm">
                            <option value="ollama">Ollama (Local, Private)</option>
                            <option value="bedrock">AWS Bedrock</option>
                            <option value="openai">OpenAI</option>
                          </select>
                          <Icon icon="lucide:chevron-down" className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400" width="16" />
                        </div>
                      </div>

                      <div className="h-px bg-gray-200 dark:bg-white/5 w-full"></div>

                      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-4">
                        <div className="pr-4 sm:w-1/2">
                          <h3 className="text-sm font-semibold text-gray-900 dark:text-white">{t('settings.apiKey')}</h3>
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{t('settings.apiKeyDesc')}</p>
                        </div>
                        <div className="w-full sm:w-1/2 relative">
                          <Icon icon="lucide:key" className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" width="16" />
                          <input
                            type="password"
                            placeholder="••••••••••••••••"
                            className="w-full bg-gray-50 dark:bg-[#0D0A1A] border border-gray-200 dark:border-[#3f3b60]/50 rounded-xl pl-10 pr-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-sma-purple/50 focus:border-sma-purple text-gray-900 dark:text-white transition-all duration-200 shadow-sm"
                          />
                        </div>
                      </div>

                      <div className="h-px bg-gray-200 dark:bg-white/5 w-full"></div>

                      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-4">
                        <div className="pr-4 sm:w-1/2">
                          <h3 className="text-sm font-semibold text-gray-900 dark:text-white">{t('settings.localModel')}</h3>
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{t('settings.localModelDesc')}</p>
                        </div>
                        <div className="w-full sm:w-1/2 relative">
                          <Icon icon="lucide:box" className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" width="16" />
                          <input
                            type="text"
                            defaultValue="llava:latest"
                            className="w-full bg-gray-50 dark:bg-[#0D0A1A] border border-gray-200 dark:border-[#3f3b60]/50 rounded-xl pl-10 pr-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-sma-purple/50 focus:border-sma-purple text-gray-900 dark:text-white transition-all duration-200 shadow-sm"
                          />
                        </div>
                      </div>

                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'appearance' && (
                <div className="space-y-8 pb-8">
                  <div>
                    <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-1">{t('settings.appearance')}</h2>
                    <p className="text-gray-500 dark:text-gray-400 text-sm">{t('settings.appearanceDesc')}</p>
                  </div>

                  <div className="bg-white dark:bg-[#16132A]/60 backdrop-blur-xl border border-gray-200 dark:border-white/5 rounded-2xl p-6 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.08)] dark:shadow-sm">
                    <div className="flex flex-col lg:flex-row lg:justify-between lg:items-center gap-6">
                      <div className="pr-4 max-w-sm">
                        <h3 className="text-sm font-semibold text-gray-900 dark:text-white">{t('settings.theme')}</h3>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{t('settings.themeDesc')}</p>
                      </div>

                      <div className="flex bg-gray-100 dark:bg-[#0D0A1A] border border-gray-200 dark:border-white/5 rounded-xl p-1 shrink-0">
                        <button
                          type="button"
                          aria-label="Enable Dark Theme"
                          onClick={() => setTheme('dark')}
                          className={`flex items-center justify-center space-x-2 px-5 py-2.5 rounded-lg text-sm font-semibold transition-all duration-300 ${theme === 'dark' ? 'bg-[#1A1630] text-white shadow-md' : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'}`}
                        >
                          <Icon icon="lucide:moon" width="16" />
                          <span>Dark</span>
                        </button>
                        <button
                          type="button"
                          aria-label="Enable Light Theme"
                          onClick={() => setTheme('light')}
                          className={`flex items-center justify-center space-x-2 px-5 py-2.5 rounded-lg text-sm font-semibold transition-all duration-300 ${theme === 'light' ? 'bg-white text-gray-900 shadow-md' : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'}`}
                        >
                          <Icon icon="lucide:sun" width="16" />
                          <span>Light</span>
                        </button>
                        <button
                          type="button"
                          aria-label="Enable System Theme"
                          className="flex items-center justify-center space-x-2 px-5 py-2.5 rounded-lg text-sm font-semibold transition-all duration-300 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                        >
                          <Icon icon="lucide:monitor" width="16" />
                          <span>System</span>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'about' && (
                <div className="space-y-8 pb-8">
                  <div>
                    <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-1">{t('settings.about')}</h2>
                    <p className="text-gray-500 dark:text-gray-400 text-sm">{t('settings.aboutDesc')}</p>
                  </div>

                  <div className="bg-white dark:bg-[#16132A]/60 backdrop-blur-xl border border-gray-200 dark:border-white/5 rounded-2xl p-6 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.08)] dark:shadow-sm">
                    <div className="flex flex-col items-center justify-center text-center py-2 mb-2">
                      <img src="/logo.png" alt="Smart Media Analytics" className="w-48 h-auto object-contain invert dark:invert-0 opacity-90 dark:opacity-100 transition-all duration-300" />
                      <h3 className="text-xl font-bold text-gray-900 dark:text-white mt-4">Smart Media Analytics</h3>
                      <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">AI-powered media management platform.</p>
                    </div>

                    <div className="space-y-4">
                      <div className="flex justify-between items-center py-2 border-t border-gray-100 dark:border-white/5">
                        <span className="text-sm text-gray-600 dark:text-gray-400">Version</span>
                        <span className="text-sm font-mono font-medium text-gray-900 dark:text-white bg-gray-100 dark:bg-white/10 px-2 py-0.5 rounded">v1.0.0-beta</span>
                      </div>
                      <div className="flex justify-between items-center py-2 border-t border-gray-100 dark:border-white/5">
                        <span className="text-sm text-gray-600 dark:text-gray-400">License</span>
                        <span className="text-sm font-medium text-gray-900 dark:text-white">MIT</span>
                      </div>
                    </div>

                    <div className="mt-8 grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <a href="https://github.com/ntnhan19/smart_media_analytics_cloudforge" target="_blank" rel="noopener noreferrer" className="flex items-center justify-center space-x-2 p-3 rounded-xl bg-gray-50 dark:bg-[#0D0A1A] hover:bg-gray-100 dark:hover:bg-[#1A1630] text-gray-700 dark:text-gray-300 transition-colors border border-gray-200 dark:border-white/5">
                        <Icon icon="lucide:github" width="18" />
                        <span className="text-sm font-semibold">GitHub Repository</span>
                      </a>
                      <a href="https://github.com/ntnhan19/smart_media_analytics_cloudforge#readme" target="_blank" rel="noopener noreferrer" className="flex items-center justify-center space-x-2 p-3 rounded-xl bg-gray-50 dark:bg-[#0D0A1A] hover:bg-gray-100 dark:hover:bg-[#1A1630] text-gray-700 dark:text-gray-300 transition-colors border border-gray-200 dark:border-white/5">
                        <Icon icon="lucide:book-open" width="18" />
                        <span className="text-sm font-semibold">Documentation</span>
                      </a>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Floating Action Bar at bottom */}
        <div className="mt-auto pt-4 pb-6 flex justify-end shrink-0 border-t border-gray-200 dark:border-white/10 relative z-20">
          <button type="submit" className="bg-[#7B5CF5] hover:bg-[#684CDE] text-white px-8 py-3 rounded-xl font-bold text-sm tracking-wide transition-all duration-300 shadow-[0_4px_14px_0_rgba(123,92,245,0.39)] hover:shadow-[0_6px_20px_rgba(123,92,245,0.23)] hover:-translate-y-0.5 flex items-center space-x-2">
            <Icon icon="lucide:save" width="18" />
            <span>{t('settings.save')}</span>
          </button>
        </div>

      </form>
    </div>
  );
}
