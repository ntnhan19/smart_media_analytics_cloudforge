import { Link } from 'react-router-dom';
import { Play, Search, Video, Mic, ChevronRight, Shield, Cpu, ArrowRight, BarChart3, Layers, Database, Activity, Tag } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

export default function Landing() {
  const [scrolled, setScrolled] = useState(false);
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="min-h-screen bg-[#F8F9FA] dark:bg-[#0a0a0f] text-gray-900 dark:text-white font-inter selection:bg-sma-purple/30 overflow-x-hidden">
      {/* Navbar */}
      <header className={`fixed top-0 w-full z-50 transition-all duration-300 ${scrolled ? 'bg-white/80 dark:bg-[#0a0a0f]/80 backdrop-blur-xl border-b border-gray-200 dark:border-white/10 py-3 shadow-sm' : 'bg-transparent py-5'}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3 group cursor-pointer" onClick={() => window.scrollTo(0,0)}>
              <img src="/logo.png" alt="SMA Logo" className="h-14 md:h-16 w-auto object-contain dark:invert-0 invert" />
            </div>

            <nav className="hidden md:flex items-center gap-8">
              <a href="#features" className="text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-sma-purple transition-colors">Features</a>
              <a href="#how-it-works" className="text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-sma-purple transition-colors">How it works</a>
              <a href="#security" className="text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-sma-purple transition-colors">Security</a>
            </nav>

            <div className="flex items-center gap-4">
              {isAuthenticated ? (
                <Link
                  to="/app"
                  className="text-sm font-medium px-5 py-2.5 rounded-xl text-white bg-sma-purple hover:bg-[#6b4ce6] shadow-sm transition-all active:scale-95"
                >
                  Dashboard
                </Link>
              ) : (
                <>
                  <Link
                    to="/login"
                    className="text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors"
                  >
                    Log in
                  </Link>
                  <Link
                    to="/login"
                    className="text-sm font-medium px-5 py-2.5 rounded-xl text-white bg-sma-purple hover:bg-[#6b4ce6] shadow-sm transition-all active:scale-95"
                  >
                    Get Started Free
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="flex-grow">
        {/* Hero Section */}
        <div className="relative pt-32 pb-20 md:pt-48 md:pb-32 overflow-hidden">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/5 border border-white/10 text-sm font-medium mb-8 shadow-sm backdrop-blur-md hover:bg-white/10 transition-colors cursor-pointer group">
              <span className="w-2 h-2 rounded-full bg-sma-purple group-hover:animate-ping"></span>
              <span className="text-gray-600 dark:text-gray-300">The next generation of Media Management</span>
              <ChevronRight className="w-4 h-4 text-gray-400 group-hover:translate-x-1 transition-transform" />
            </div>

            <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight mb-8 leading-[1.1]">
              Stop Losing Hours <br className="hidden md:block" />
              <span className="text-sma-purple">
                Logging Raw Footage
              </span>
            </h1>

            <p className="mt-4 text-xl text-gray-600 dark:text-gray-400 max-w-3xl mx-auto mb-10 leading-relaxed font-light">
              Dump all your b-roll, interviews, and raw clips into one place. 
              Our AI automatically tags objects, transcribes speech, and logs every scene so you can find the perfect shot instantly.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-5 mb-16">
              <Link
                to={isAuthenticated ? "/app" : "/login"}
                className="w-full sm:w-auto flex items-center justify-center gap-2 px-8 py-4 rounded-xl font-bold text-white bg-sma-purple hover:bg-[#6b4ce6] shadow-[0_8px_20px_rgb(123,92,245,0.4)] transition-all hover:-translate-y-1"
              >
                Get Started Free
              </Link>
              <a
                href="#how-it-works"
                className="w-full sm:w-auto flex items-center justify-center gap-2 px-8 py-4 rounded-xl font-medium text-gray-700 dark:text-white bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 hover:bg-gray-50 dark:hover:bg-white/10 transition-all backdrop-blur-sm hover:-translate-y-1"
              >
                Discover Features
              </a>
            </div>

            {/* Persona Tags */}
            <div className="flex flex-wrap items-center justify-center gap-4 mb-16">
              <span className="px-4 py-2 rounded-full bg-white/5 border border-gray-200 dark:border-white/10 text-sm font-medium text-gray-600 dark:text-gray-400">For solo creators</span>
              <span className="px-4 py-2 rounded-full bg-white/5 border border-gray-200 dark:border-white/10 text-sm font-medium text-gray-600 dark:text-gray-400">For post-production teams</span>
              <span className="px-4 py-2 rounded-full bg-white/5 border border-gray-200 dark:border-white/10 text-sm font-medium text-gray-600 dark:text-gray-400">For news & broadcast</span>
            </div>

            {/* Dashboard CSS Mockup */}
            <div className="max-w-5xl mx-auto relative group perspective-1000">
              {/* Decorative glow */}
              <div className="absolute -inset-1 bg-gradient-to-r from-sma-purple/30 to-sma-blue/30 blur-2xl opacity-50 rounded-3xl group-hover:opacity-70 transition-opacity duration-700"></div>
              
              <div className="relative rounded-2xl border border-gray-200 dark:border-white/10 bg-white dark:bg-[#0a0a0f] shadow-2xl overflow-hidden flex flex-col transition-transform duration-700 hover:scale-[1.02]">
                {/* Mockup Browser Header */}
                <div className="h-10 bg-gray-50 dark:bg-[#16132A] border-b border-gray-200 dark:border-white/5 flex items-center px-4 gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-400/80"></div>
                  <div className="w-3 h-3 rounded-full bg-yellow-400/80"></div>
                  <div className="w-3 h-3 rounded-full bg-emerald-400/80"></div>
                </div>

                {/* Mockup Body */}
                <div className="flex h-[400px] md:h-[600px] bg-white dark:bg-[#0a0a0f]">
                  {/* Fake Sidebar */}
                  <div className="hidden md:flex w-48 border-r border-gray-100 dark:border-white/5 flex-col p-4 gap-4">
                    <div className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Projects</div>
                    <div className="text-sm font-medium text-sma-purple bg-sma-purple/10 p-2 rounded-lg">Interview_Batch_01</div>
                    <div className="text-sm font-medium text-gray-500 p-2 hover:bg-white/5 rounded-lg">B-Roll_City_Night</div>
                    <div className="text-sm font-medium text-gray-500 p-2 hover:bg-white/5 rounded-lg">Product_Launch_Q3</div>
                    <div className="text-sm font-medium text-gray-500 p-2 hover:bg-white/5 rounded-lg">Drone_Footage</div>
                  </div>

                  {/* Main Area */}
                  <div className="flex-1 flex flex-col p-4 md:p-8">
                    {/* Header */}
                    <div className="flex justify-between items-center mb-8">
                      <div className="h-10 w-full max-w-sm bg-gray-50 dark:bg-[#16132A] rounded-xl border border-gray-200 dark:border-white/5 flex items-center px-3 gap-2">
                        <Search className="w-4 h-4 text-gray-400" />
                        <span className="text-sm text-gray-400 font-light">"a wide shot of a red car"</span>
                      </div>
                      <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-sma-purple to-sma-blue ml-4 shrink-0 shadow-sm"></div>
                    </div>

                    {/* Stats Row */}
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-6">
                      <div className="h-24 rounded-2xl bg-gray-50 dark:bg-[#16132A] border border-gray-100 dark:border-white/5 p-4 flex flex-col justify-between">
                        <span className="text-xs text-gray-500 font-medium">Clips Found</span>
                        <span className="text-2xl font-bold text-gray-900 dark:text-white">24</span>
                      </div>
                      <div className="h-24 rounded-2xl bg-gray-50 dark:bg-[#16132A] border border-gray-100 dark:border-white/5 p-4 flex flex-col justify-between">
                        <span className="text-xs text-gray-500 font-medium">Total Duration</span>
                        <span className="text-2xl font-bold text-gray-900 dark:text-white">00:15:30</span>
                      </div>
                      <div className="h-24 rounded-2xl bg-gray-50 dark:bg-[#16132A] border border-gray-100 dark:border-white/5 p-4 flex-col justify-between hidden sm:flex">
                        <span className="text-xs text-gray-500 font-medium">Confidence</span>
                        <span className="text-2xl font-bold text-emerald-500">96%</span>
                      </div>
                    </div>

                    {/* Fake Video Player & Tags */}
                    <div className="flex-1 rounded-2xl bg-gray-50 dark:bg-[#16132A] border border-gray-100 dark:border-white/5 relative overflow-hidden flex flex-col">
                      {/* Fake Video Image Area */}
                      <div className="flex-1 bg-gray-200/50 dark:bg-black/20 flex items-center justify-center relative bg-[url('https://images.unsplash.com/photo-1494976388531-d1058494cdd8?auto=format&fit=crop&q=80')] bg-cover bg-center">
                        <div className="absolute inset-0 bg-black/40"></div>
                        <div className="w-16 h-16 rounded-full bg-white/30 backdrop-blur-md flex items-center justify-center text-white border border-white/20 shadow-lg z-10 cursor-pointer hover:bg-white/40 transition-colors">
                          <Play className="w-6 h-6 ml-1" fill="currentColor" />
                        </div>
                        {/* Overlay Bounding Box (AI vision simulation) */}
                        <div className="absolute top-1/4 left-1/4 w-1/2 h-1/2 border-2 border-sma-purple/80 rounded-lg bg-sma-purple/10 flex flex-col justify-end p-2 z-10">
                          <div className="flex gap-2 items-center mb-1">
                            <span className="text-xs bg-sma-purple text-white px-2 py-0.5 rounded shadow-sm font-bold">Red Car 98%</span>
                            <span className="text-xs bg-emerald-500 text-white px-2 py-0.5 rounded shadow-sm font-bold">Moving 94%</span>
                          </div>
                          <span className="text-xs text-white/90 bg-black/50 px-2 py-1 rounded backdrop-blur-sm">Wide shot - outdoor highway, red car passing by</span>
                        </div>
                      </div>
                      {/* Fake Timeline & Tags */}
                      <div className="h-16 border-t border-gray-100 dark:border-white/5 p-4 flex items-center gap-3">
                        <div className="px-3 py-1 bg-sma-purple/10 text-sma-purple text-xs rounded-full font-medium border border-sma-purple/20">Outdoors</div>
                        <div className="px-3 py-1 bg-sma-blue/10 text-sma-blue text-xs rounded-full font-medium border border-sma-blue/20 hidden sm:block">Daylight</div>
                        <div className="px-3 py-1 bg-emerald-500/10 text-emerald-500 text-xs rounded-full font-medium border border-emerald-500/20">Vehicle</div>
                        <div className="flex-1"></div>
                        <div className="w-24 md:w-48 h-1.5 bg-gray-200 dark:bg-white/10 rounded-full overflow-hidden relative">
                          <div className="absolute left-[20%] w-[10%] h-full bg-sma-purple"></div>
                          <div className="absolute left-[45%] w-[15%] h-full bg-sma-purple"></div>
                          <div className="absolute left-[80%] w-[5%] h-full bg-sma-purple"></div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Scale Highlights */}
          <div className="mt-32 max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
            <div className="text-center mb-12">
              <h2 className="text-3xl md:text-4xl font-bold tracking-tight mb-4">BUILT FOR VIDEO EDITORS</h2>
              <p className="text-gray-500 dark:text-gray-400">Stop wasting time searching through folders. Let the system do the heavy lifting.</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white dark:bg-[#16132A] border border-gray-100 dark:border-white/5 rounded-3xl p-8 flex flex-col items-center text-center shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-none hover:shadow-[0_20px_40px_rgb(0,0,0,0.08)] hover:-translate-y-1 transition-all">
                <Database className="w-10 h-10 text-sma-purple mb-5" />
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Dump Your Raw Footage</h3>
                <p className="text-gray-500 dark:text-gray-400 text-sm leading-relaxed">Drop hundreds of video files into your library and let the system organize them automatically.</p>
              </div>

              <div className="bg-white dark:bg-[#16132A] border border-gray-100 dark:border-white/5 rounded-3xl p-8 flex flex-col items-center text-center shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-none hover:shadow-[0_20px_40px_rgb(0,0,0,0.08)] hover:-translate-y-1 transition-all">
                <Activity className="w-10 h-10 text-sma-blue mb-5" />
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Zero Manual Logging</h3>
                <p className="text-gray-500 dark:text-gray-400 text-sm leading-relaxed">Skip the tedious logging phase. We automatically scan every frame to tag scenes, objects, and people.</p>
              </div>

              <div className="bg-white dark:bg-[#16132A] border border-gray-100 dark:border-white/5 rounded-3xl p-8 flex flex-col items-center text-center shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-none hover:shadow-[0_20px_40px_rgb(0,0,0,0.08)] hover:-translate-y-1 transition-all">
                <Tag className="w-10 h-10 text-emerald-500 mb-5" />
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Find Exact Clips Instantly</h3>
                <p className="text-gray-500 dark:text-gray-400 text-sm leading-relaxed">Type "a wide shot of a red car" or search for a specific quote to jump right to the perfect frame.</p>
              </div>
            </div>
          </div>
        </div>

        {/* Features Section */}
        <div id="features" className="py-24 relative z-10">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-20">
              <h2 className="text-sm font-bold tracking-widest text-sma-purple uppercase mb-3">Editor Workflows</h2>
              <h3 className="text-3xl md:text-5xl font-bold tracking-tight text-gray-900 dark:text-white mb-6">
                Purpose-built for Video Editors
              </h3>
              <p className="max-w-2xl mx-auto text-lg text-gray-400 font-light">
                We've built the ultimate assistant for your post-production workflow, eliminating the most tedious parts of video editing.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Feature 1 */}
              <div className="p-10 rounded-3xl bg-white dark:bg-[#16132A] border border-gray-100 dark:border-white/5 hover:border-sma-purple/50 transition-all duration-300 group shadow-[0_4px_20px_rgb(0,0,0,0.03)] dark:shadow-sm">
                <div className="w-14 h-14 rounded-2xl bg-sma-purple/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <Search className="w-7 h-7 text-sma-purple" />
                </div>
                <h4 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Natural Language Search</h4>
                <p className="text-gray-500 dark:text-gray-400 leading-relaxed font-light">
                  Don't remember the file name? Just describe what happens in the video. We'll find the exact timestamp of what you're looking for.
                </p>
              </div>

              {/* Feature 2 */}
              <div className="p-10 rounded-3xl bg-white dark:bg-[#16132A] border border-gray-100 dark:border-white/5 hover:border-sma-blue/50 transition-all duration-300 group shadow-[0_4px_20px_rgb(0,0,0,0.03)] dark:shadow-sm">
                <div className="w-14 h-14 rounded-2xl bg-sma-blue/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <Video className="w-7 h-7 text-sma-blue" />
                </div>
                <h4 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Automated Scene Detection</h4>
                <p className="text-gray-500 dark:text-gray-400 leading-relaxed font-light">
                  We break down long interviews and raw b-roll into easily digestible, tagged scenes so you don't have to scrub through them.
                </p>
              </div>

              {/* Feature 3 */}
              <div className="p-10 rounded-3xl bg-white dark:bg-[#16132A] border border-gray-100 dark:border-white/5 hover:border-emerald-500/50 transition-all duration-300 group shadow-[0_4px_20px_rgb(0,0,0,0.03)] dark:shadow-sm">
                <div className="w-14 h-14 rounded-2xl bg-emerald-500/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <Mic className="w-7 h-7 text-emerald-500" />
                </div>
                <h4 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Instant Transcription</h4>
                <p className="text-gray-500 dark:text-gray-400 leading-relaxed font-light">
                  Need a specific soundbite? Search through spoken words instantly. We automatically transcribe all dialogue with high accuracy.
                </p>
              </div>

              {/* Feature 4 (New) */}
              <div className="p-10 rounded-3xl bg-white dark:bg-[#16132A] border border-gray-100 dark:border-white/5 hover:border-amber-500/50 transition-all duration-300 group shadow-[0_4px_20px_rgb(0,0,0,0.03)] dark:shadow-sm">
                <div className="w-14 h-14 rounded-2xl bg-amber-500/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <Layers className="w-7 h-7 text-amber-500" />
                </div>
                <h4 className="text-xl font-bold text-gray-900 dark:text-white mb-2">NLE Integration</h4>
                <p className="text-gray-500 dark:text-gray-400 leading-relaxed font-light">
                  Export your selected clips directly as XML or EDL files to Premiere Pro and DaVinci Resolve. Your metadata goes with you.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* How it Works / Tech Workflow */}
        <div id="how-it-works" className="py-24 relative z-10 bg-gray-50 dark:bg-white/5">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
              <div>
                <h2 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-6 leading-tight">
                  A seamless pipeline from <br /> upload to insights
                </h2>
                <p className="text-gray-400 text-lg font-light mb-10">
                  Every asset you upload goes through our proprietary AI processing pipeline, designed for speed and accuracy.
                </p>

                <div className="space-y-8 relative">
                  {/* Vertical connecting line */}
                  <div className="absolute left-5 top-10 bottom-10 w-0.5 border-l-2 border-dashed border-gray-200 dark:border-white/10 -z-10"></div>

                  <div className="flex gap-6">
                    <div className="shrink-0 mt-1">
                      <div className="w-10 h-10 rounded-full bg-white dark:bg-[#16132A] flex items-center justify-center border-2 border-gray-200 dark:border-white/20 text-gray-700 dark:text-white font-bold">
                        1
                      </div>
                    </div>
                    <div>
                      <h4 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Secure Upload & Storage</h4>
                      <p className="text-gray-500 dark:text-gray-400 font-light">Your media is encrypted and safely stored in high-performance cloud buckets, ready for processing.</p>
                    </div>
                  </div>

                  <div className="flex gap-6">
                    <div className="shrink-0 mt-1">
                      <div className="w-10 h-10 rounded-full bg-white dark:bg-[#16132A] flex items-center justify-center border-2 border-sma-purple/50 text-sma-purple font-bold">
                        2
                      </div>
                    </div>
                    <div>
                      <h4 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Automated AI Processing</h4>
                      <p className="text-gray-500 dark:text-gray-400 font-light">Background workers automatically extract audio, detect scenes, transcribe speech, and generate embeddings.</p>
                    </div>
                  </div>

                  <div className="flex gap-6">
                    <div className="shrink-0 mt-1">
                      <div className="w-10 h-10 rounded-full bg-white dark:bg-[#16132A] flex items-center justify-center border-2 border-sma-blue/50 text-sma-blue font-bold">
                        3
                      </div>
                    </div>
                    <div>
                      <h4 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Instant Search & Discovery</h4>
                      <p className="text-gray-500 dark:text-gray-400 font-light">Data is indexed in a vector database, allowing you to instantly query your entire library using natural language.</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="relative">
                <div className="aspect-square rounded-full border border-gray-200 dark:border-white/10 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[120%] animate-[spin_60s_linear_infinite]"></div>
                <div className="aspect-square rounded-full border border-gray-100 dark:border-white/5 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[80%] animate-[spin_40s_linear_infinite_reverse]"></div>

                <div className="relative z-10">
                  <div className="mb-6 text-center">
                    <span className="px-4 py-1.5 rounded-full bg-gray-100 dark:bg-white/5 border border-gray-200 dark:border-white/10 text-xs font-bold tracking-widest text-gray-500 dark:text-gray-400 uppercase">
                      Underlying Infrastructure
                    </span>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-4 pt-12">
                      <div className="bg-white dark:bg-[#16132A] border border-gray-100 dark:border-white/5 p-6 rounded-3xl shadow-[0_4px_20px_rgb(0,0,0,0.03)] dark:shadow-sm">
                        <Layers className="w-8 h-8 text-sma-purple mb-4" />
                        <h5 className="text-gray-900 dark:text-white font-bold mb-1">Scalable Architecture</h5>
                        <p className="text-xs text-gray-500 dark:text-gray-400">Microservices designed to handle massive media libraries.</p>
                      </div>
                      <div className="bg-white dark:bg-[#16132A] border border-gray-100 dark:border-white/5 p-6 rounded-3xl shadow-[0_4px_20px_rgb(0,0,0,0.03)] dark:shadow-sm">
                        <BarChart3 className="w-8 h-8 text-sma-blue mb-4" />
                        <h5 className="text-gray-900 dark:text-white font-bold mb-1">Deep Analytics</h5>
                        <p className="text-xs text-gray-500 dark:text-gray-400">Extract metadata, tags, and sentiment from every frame.</p>
                      </div>
                    </div>
                    <div className="space-y-4">
                      <div className="bg-white dark:bg-[#16132A] border border-gray-100 dark:border-white/5 p-6 rounded-3xl shadow-[0_4px_20px_rgb(0,0,0,0.03)] dark:shadow-sm">
                        <Cpu className="w-8 h-8 text-emerald-500 mb-4" />
                        <h5 className="text-gray-900 dark:text-white font-bold mb-1">Local Inference</h5>
                        <p className="text-xs text-gray-500 dark:text-gray-400">Powered by advanced LLMs and VLMs running securely.</p>
                      </div>
                      <div className="bg-white dark:bg-[#16132A] border border-gray-100 dark:border-white/5 p-6 rounded-3xl shadow-[0_4px_20px_rgb(0,0,0,0.03)] dark:shadow-sm">
                        <Shield className="w-8 h-8 text-amber-500 mb-4" />
                        <h5 className="text-gray-900 dark:text-white font-bold mb-1">Enterprise Security</h5>
                        <p className="text-xs text-gray-500 dark:text-gray-400">Your data never leaves your controlled environment.</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Social Proof */}
        <div className="py-20 border-t border-gray-200 dark:border-white/5 relative z-10 bg-white dark:bg-[#050508]">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-12">
              <p className="text-sm font-bold tracking-widest text-gray-400 uppercase">Trusted by forward-thinking teams</p>
            </div>
            {/* TODO: Add real logos here. Using placeholders for now */}
            <div className="flex flex-wrap justify-center gap-12 opacity-50 grayscale hover:grayscale-0 transition-all duration-500">
               <div className="h-8 flex items-center font-bold text-xl text-gray-800 dark:text-white/80">Vogue Studios</div>
               <div className="h-8 flex items-center font-bold text-xl text-gray-800 dark:text-white/80">NewsCorp</div>
               <div className="h-8 flex items-center font-bold text-xl text-gray-800 dark:text-white/80">CreativeAgency</div>
               <div className="h-8 flex items-center font-bold text-xl text-gray-800 dark:text-white/80">StreamMedia</div>
            </div>
          </div>
        </div>

        {/* Pricing */}
        <div id="pricing" className="py-24 relative z-10">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
              <h2 className="text-3xl md:text-5xl font-bold tracking-tight text-gray-900 dark:text-white mb-6">Simple, transparent pricing</h2>
              <p className="text-lg text-gray-500 dark:text-gray-400">Start for free, upgrade when you need more power.</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
              <div className="bg-white dark:bg-[#16132A] rounded-3xl p-10 border border-gray-200 dark:border-white/10 shadow-lg flex flex-col">
                <h3 className="text-2xl font-bold mb-2">Starter</h3>
                <div className="text-4xl font-extrabold mb-6">$0<span className="text-lg font-medium text-gray-500">/mo</span></div>
                <ul className="space-y-4 mb-8 text-gray-600 dark:text-gray-300 flex-grow">
                  <li className="flex gap-3 items-center"><ChevronRight className="w-5 h-5 text-sma-purple"/> Max 500MB per file</li>
                  <li className="flex gap-3 items-center"><ChevronRight className="w-5 h-5 text-sma-purple"/> 10GB total storage</li>
                  <li className="flex gap-3 items-center"><ChevronRight className="w-5 h-5 text-sma-purple"/> Standard AI processing</li>
                </ul>
                <div className="text-center mb-4 text-xs text-gray-500">No credit card required</div>
                <button className="w-full py-4 rounded-xl font-bold text-gray-900 dark:text-white bg-gray-100 dark:bg-white/10 hover:bg-gray-200 dark:hover:bg-white/20 transition-colors">Start Free</button>
              </div>

              <div className="bg-gradient-to-b from-sma-purple/10 to-transparent rounded-3xl p-10 border border-sma-purple/30 shadow-[0_8px_30px_rgb(123,92,245,0.1)] relative flex flex-col">
                <div className="absolute top-0 right-8 -translate-y-1/2 bg-sma-purple text-white px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider">Most Popular</div>
                <h3 className="text-2xl font-bold mb-2">Pro</h3>
                <div className="text-4xl font-extrabold mb-6">$29<span className="text-lg font-medium text-gray-500">/mo</span></div>
                <ul className="space-y-4 mb-8 text-gray-600 dark:text-gray-300 flex-grow">
                  <li className="flex gap-3 items-center"><ChevronRight className="w-5 h-5 text-sma-purple"/> 4K video support</li>
                  <li className="flex gap-3 items-center"><ChevronRight className="w-5 h-5 text-sma-purple"/> 1TB total storage</li>
                  <li className="flex gap-3 items-center"><ChevronRight className="w-5 h-5 text-sma-purple"/> NLE Export (XML/EDL)</li>
                  <li className="flex gap-3 items-center"><ChevronRight className="w-5 h-5 text-sma-purple"/> Priority processing queue</li>
                </ul>
                <button className="w-full py-4 rounded-xl font-bold text-white bg-sma-purple hover:bg-[#6b4ce6] transition-colors shadow-lg mt-auto">Upgrade to Pro</button>
              </div>
            </div>
          </div>
        </div>

        {/* FAQ with Dark Purple Background */}
        <div className="py-24 relative z-10 bg-[#1a113d] text-white">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
              <h2 className="text-3xl md:text-5xl font-bold tracking-tight mb-6">Frequently Asked Questions</h2>
            </div>
            
            <div className="space-y-4">
              <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
                <h4 className="text-lg font-bold mb-2 flex items-center justify-between">Are my unreleased footages secure?</h4>
                <p className="text-white/60 font-light">Yes. Your media is encrypted at rest and in transit. It is stored in private cloud buckets and never used to train public AI models.</p>
              </div>
              <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
                <h4 className="text-lg font-bold mb-2 flex items-center justify-between">What file formats do you support?</h4>
                <p className="text-white/60 font-light">We support all major video and audio formats including MP4, MOV, AVI, WAV, and MP3.</p>
              </div>
              <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
                <h4 className="text-lg font-bold mb-2 flex items-center justify-between">Can I fix AI tags if they are wrong?</h4>
                <p className="text-white/60 font-light">Absolutely. While our AI is highly accurate, you always remain in control. You can manually edit, add, or remove tags from any scene.</p>
              </div>
            </div>
          </div>
        </div>

        {/* CTA Section */}
        <div className="relative py-24 overflow-hidden">
          <div className="max-w-4xl mx-auto px-4 relative z-10 text-center">
            <h2 className="text-4xl font-bold text-gray-900 dark:text-white mb-6">Ready to stop scrubbing through raw footage?</h2>
            <p className="text-xl text-gray-600 dark:text-gray-400 mb-10 font-light">Join the editors who cut their logging time down to minutes, not hours.</p>
            <Link
              to="/login"
              className="inline-flex items-center justify-center gap-2 px-12 py-5 rounded-xl font-bold text-white bg-sma-purple hover:bg-[#6b4ce6] shadow-[0_8px_30px_rgb(123,92,245,0.4)] transition-all hover:scale-105 active:scale-95"
            >
              Get Started Free <ArrowRight className="w-5 h-5 ml-2" />
            </Link>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white dark:bg-[#050508] py-12 border-t border-gray-200 dark:border-white/5">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="flex items-center gap-3 text-sm text-gray-600">
              <img src="/logo.png" alt="SMA Logo" className="h-10 w-auto object-contain dark:invert-0 invert" />
              <span>© {new Date().getFullYear()} Smart Media Analytics. All rights reserved. Proprietary and Confidential.</span>
            </div>

            <div className="flex gap-8">
              <a href="#" className="text-sm text-gray-500 hover:text-white transition-colors">Privacy Policy</a>
              <a href="#" className="text-sm text-gray-500 hover:text-white transition-colors">Terms of Service</a>
              <a href="#" className="text-sm text-gray-500 hover:text-white transition-colors">Contact Support</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
