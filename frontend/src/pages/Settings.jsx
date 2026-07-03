import { useState, useEffect } from 'react';
import { Icon } from '@iconify/react';

// Switch Component Helper — defined outside to avoid re-creation during render
function ToggleSwitch({ checked, onChange }) {
  return (
    <button
      type="button"
      onClick={onChange}
      aria-label="Toggle setting"
      className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer items-center justify-center rounded-full focus:outline-none focus-visible:ring-2 focus-visible:ring-sma-purple focus-visible:ring-opacity-75 transition-colors ${checked ? 'bg-[#7B5CF5]' : 'bg-gray-300 dark:bg-[#2D2844]'}`}
    >
      <span className="sr-only">Toggle</span>
      <span
        aria-hidden="true"
        className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow-sm ring-0 transition duration-200 ease-in-out ${checked ? 'translate-x-2' : '-translate-x-2'}`}
      />
    </button>
  );
}

export default function Settings() {
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'dark');
  const [toast, setToast] = useState(null);

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

  const handleSave = (e) => {
    e.preventDefault();
    showToast('Settings saved successfully!');
  };

  return (
    <div className="max-w-[1200px] mx-auto h-full flex flex-col relative text-gray-900 dark:text-white transition-colors">
      {toast && (
        <div className={`fixed top-[20px] right-[20px] z-50 px-4 py-2 rounded shadow-lg text-white font-inter text-sm animate-fade-in-down ${toast.type === 'success' ? 'bg-green-600' : 'bg-red-600'}`}>
          {toast.message}
        </div>
      )}

      {/* Header */}
      <div className="mb-2 shrink-0 mt-0 px-2">
        <h1 className="text-[32px] leading-none font-bold font-inter text-gray-900 dark:text-white tracking-wide uppercase">Settings</h1>
        <p className="text-gray-500 dark:text-gray-400 text-[13px] mt-1 font-light">Manage preferences for your SMA experience and configure your workflow environment.</p>
      </div>

      <form onSubmit={handleSave} className="flex-1">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 h-full">
          
          {/* Card 1: General */}
          <div className="bg-white dark:bg-[#120F24] border border-gray-200 dark:border-[#2D2844] rounded-xl flex flex-col overflow-hidden shadow-sm dark:shadow-none transition-colors">
            <div className="px-4 py-3 flex items-start space-x-3 border-b border-gray-200 dark:border-[#2D2844] transition-colors">
              <Icon icon="lucide:settings" width="24" height="24" className="text-gray-700 dark:text-white mt-0.5" />
              <div>
                <h2 className="text-base font-bold leading-tight">General</h2>
                <p className="text-gray-500 dark:text-gray-400 text-[11px] mt-0.5">Basic preferences for your SMA experience.</p>
              </div>
            </div>
            <div className="px-4 py-3 space-y-3 flex-1">
              
              {/* Setting Item */}
              <div className="flex justify-between items-center">
                <div className="pr-4">
                  <h3 className="text-sm font-semibold tracking-wider text-gray-700 dark:text-gray-200 uppercase">Language</h3>
                  <p className="text-xs text-gray-500 mt-1">Choose your preferred language.</p>
                </div>
                <div className="relative shrink-0">
                  <select
                    className="appearance-none bg-gray-50 dark:bg-transparent border border-gray-300 dark:border-[#3f3b60] text-gray-700 dark:text-gray-300 text-sm rounded-full pl-10 pr-8 py-1.5 focus:outline-none focus:border-sma-purple cursor-pointer transition-colors"
                  >
                    <option value="en">ENGLISH</option>
                    <option value="vi">VIETNAMESE</option>
                  </select>
                  <Icon icon="lucide:globe" className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 dark:text-gray-400" width="16" />
                  <Icon icon="lucide:chevron-down" className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 dark:text-gray-400" width="16" />
                </div>
              </div>

              {/* Setting Item */}
              <div className="flex justify-between items-center">
                <div className="pr-4">
                  <h3 className="text-sm font-semibold tracking-wider text-gray-700 dark:text-gray-200 uppercase">Auto Save Search History</h3>
                  <p className="text-xs text-gray-500 mt-1">Automatically save your search history.</p>
                </div>
                <ToggleSwitch checked={true} onChange={() => {}} />
              </div>

            </div>
          </div>

          {/* Card 2: AI Preferences */}
          <div className="bg-white dark:bg-[#120F24] border border-gray-200 dark:border-[#2D2844] rounded-xl flex flex-col overflow-hidden shadow-sm dark:shadow-none transition-colors">
            <div className="px-4 py-3 flex items-start space-x-3 border-b border-gray-200 dark:border-[#2D2844] relative transition-colors">
              <Icon icon="lucide:bot" width="24" height="24" className="text-gray-700 dark:text-white mt-0.5" />
              <div>
                <h2 className="text-base font-bold leading-tight">AI Preferences</h2>
                <p className="text-gray-500 dark:text-gray-400 text-[11px] mt-0.5">Configures AI features for media analysis.</p>
              </div>
              <span className="absolute top-3 right-4 text-[9px] font-bold px-1.5 py-0.5 bg-yellow-100 dark:bg-yellow-500/20 text-yellow-700 dark:text-yellow-500 rounded border border-yellow-300 dark:border-yellow-500/50 uppercase">
                Placeholder UI
              </span>
            </div>
            <div className="px-4 py-3 space-y-3 flex-1">
              
              <div className="flex justify-between items-center">
                <div className="pr-4">
                  <h3 className="text-sm font-semibold tracking-wider text-gray-700 dark:text-gray-200 uppercase">AI Provider</h3>
                  <p className="text-xs text-gray-500 mt-1">Select the AI engine for semantic search.</p>
                </div>
                <div className="relative shrink-0">
                  <select
                    className="appearance-none bg-gray-50 dark:bg-transparent border border-gray-300 dark:border-[#3f3b60] text-gray-700 dark:text-gray-300 text-sm rounded-full pl-4 pr-8 py-1.5 focus:outline-none focus:border-sma-purple cursor-pointer transition-colors"
                  >
                    <option value="ollama">Ollama (Local)</option>
                    <option value="bedrock">AWS Bedrock</option>
                    <option value="openai">OpenAI</option>
                  </select>
                  <Icon icon="lucide:chevron-down" className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 dark:text-gray-400" width="16" />
                </div>
              </div>

              <div className="flex justify-between items-center">
                <div className="pr-4 w-full">
                  <h3 className="text-sm font-semibold tracking-wider text-gray-700 dark:text-gray-200 uppercase">API Key</h3>
                  <p className="text-xs text-gray-500 mt-1 mb-2">Required for Bedrock and OpenAI.</p>
                  <input
                    type="password"
                    placeholder="••••••••••••••••"
                    className="w-full bg-gray-50 dark:bg-[#1A1630] border border-gray-300 dark:border-[#2D2844] rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-sma-purple text-gray-900 dark:text-gray-300 transition-colors"
                  />
                </div>
              </div>

              <div className="flex justify-between items-center">
                <div className="pr-4 w-full">
                  <h3 className="text-sm font-semibold tracking-wider text-gray-700 dark:text-gray-200 uppercase">Local Model</h3>
                  <p className="text-xs text-gray-500 mt-1 mb-2">Model name for Ollama.</p>
                  <input
                    type="text"
                    defaultValue="llava:latest"
                    className="w-full bg-gray-50 dark:bg-[#1A1630] border border-gray-300 dark:border-[#2D2844] rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-sma-purple text-gray-900 dark:text-gray-300 transition-colors"
                  />
                </div>
              </div>

            </div>
          </div>

          {/* Card 3: Appearance */}
          <div className="bg-white dark:bg-[#120F24] border border-gray-200 dark:border-[#2D2844] rounded-xl flex flex-col overflow-hidden shadow-sm dark:shadow-none transition-colors">
            <div className="px-4 py-3 flex items-start space-x-3 border-b border-gray-200 dark:border-[#2D2844] transition-colors">
              <Icon icon="lucide:palette" width="24" height="24" className="text-gray-700 dark:text-white mt-0.5" />
              <div>
                <h2 className="text-base font-bold leading-tight">Appearance</h2>
                <p className="text-gray-500 dark:text-gray-400 text-[11px] mt-0.5">Customize the look and feel.</p>
              </div>
            </div>
            <div className="px-4 py-3 space-y-3 flex-1">
              
              <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div className="pr-4">
                  <h3 className="text-sm font-semibold tracking-wider text-gray-700 dark:text-gray-200 uppercase">Theme</h3>
                  <p className="text-xs text-gray-500 mt-1">Select the appearance of the application.</p>
                </div>
                
                <div className="flex border border-gray-300 dark:border-[#3f3b60] rounded-full overflow-hidden shrink-0 transition-colors">
                  <button
                    type="button"
                    onClick={() => setTheme('dark')}
                    className={`flex items-center space-x-2 px-4 py-1.5 text-xs font-medium uppercase transition-colors ${theme === 'dark' ? 'bg-gray-200 text-gray-900 dark:bg-[#3f3b60] dark:text-white' : 'bg-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'}`}
                  >
                    <Icon icon="lucide:moon" width="14" />
                    <span>Dark</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setTheme('light')}
                    className={`flex items-center space-x-2 px-4 py-1.5 text-xs font-medium uppercase transition-colors border-l border-r border-gray-300 dark:border-[#3f3b60] ${theme === 'light' ? 'bg-gray-200 text-gray-900 dark:bg-[#3f3b60] dark:text-white' : 'bg-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'}`}
                  >
                    <Icon icon="lucide:sun" width="14" />
                    <span>Light</span>
                  </button>
                  <button
                    type="button"
                    className="flex items-center space-x-2 px-4 py-1.5 text-xs font-medium uppercase bg-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
                  >
                    <Icon icon="lucide:monitor" width="14" />
                    <span>System</span>
                  </button>
                </div>
              </div>

            </div>
          </div>

          {/* Card 4: About */}
          <div className="bg-white dark:bg-[#120F24] border border-gray-200 dark:border-[#2D2844] rounded-xl flex flex-col overflow-hidden shadow-sm dark:shadow-none transition-colors">
            <div className="px-4 py-3 flex items-start space-x-3 border-b border-gray-200 dark:border-[#2D2844] transition-colors">
              <Icon icon="lucide:info" width="24" height="24" className="text-gray-700 dark:text-white mt-0.5" />
              <div>
                <h2 className="text-base font-bold leading-tight">About</h2>
                <p className="text-gray-500 dark:text-gray-400 text-[11px] mt-0.5">System information and resources.</p>
              </div>
            </div>
            <div className="px-4 py-3 space-y-3 flex-1">
              
              <div className="flex justify-between items-center">
                <div className="pr-4">
                  <h3 className="text-sm font-semibold tracking-wider text-gray-700 dark:text-gray-200 uppercase">Version</h3>
                  <p className="text-xs text-gray-500 mt-1">Current software version.</p>
                </div>
                <div className="text-sm text-gray-700 dark:text-gray-300 font-mono">v1.0.0-beta</div>
              </div>

              <div className="flex justify-between items-center">
                <div className="pr-4">
                  <h3 className="text-sm font-semibold tracking-wider text-gray-700 dark:text-gray-200 uppercase">License</h3>
                  <p className="text-xs text-gray-500 mt-1">Software license information.</p>
                </div>
                <div className="text-sm text-gray-700 dark:text-gray-300">MIT</div>
              </div>

              <div className="pt-2 border-t border-gray-200 dark:border-[#2D2844] flex flex-col gap-2 transition-colors">
                <a href="#" className="text-sma-purple hover:text-sma-purple/80 dark:hover:text-white transition-colors text-xs flex items-center gap-2">
                  <Icon icon="lucide:github" width="14" /> View on GitHub
                </a>
                <a href="#" className="text-sma-purple hover:text-sma-purple/80 dark:hover:text-white transition-colors text-xs flex items-center gap-2">
                  <Icon icon="lucide:file-text" width="14" /> Documentation & Help
                </a>
              </div>

            </div>
          </div>

        </div>

        {/* Action Bar */}
        <div className="mt-2 flex justify-end shrink-0">
          <button type="submit" className="bg-[#7B5CF5] hover:bg-[#684CDE] text-white px-8 py-2.5 rounded-lg font-bold text-sm uppercase tracking-wider transition-colors shadow-md">
            Save Changes
          </button>
        </div>

      </form>
    </div>
  );
}
