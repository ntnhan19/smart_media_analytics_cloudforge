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
              <img src="/logo.png" alt="SMA Logo" className="h-10 md:h-14 w-auto object-contain dark:invert-0 invert" />
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
              Unlock the Intelligence <br className="hidden md:block" />
              <span className="text-sma-purple">
                Hidden in Your Media
              </span>
            </h1>

            <p className="mt-4 text-xl text-gray-600 dark:text-gray-400 max-w-3xl mx-auto mb-10 leading-relaxed font-light">
              Transform hours of unstructured video and audio into searchable, actionable data.
              Our AI-driven pipeline automatically transcribes, tags, and analyzes every frame.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-5 mb-16">
              <Link
                to={isAuthenticated ? "/app" : "/login"}
                className="w-full sm:w-auto flex items-center justify-center gap-2 px-8 py-4 rounded-xl font-bold text-white bg-sma-purple hover:bg-[#6b4ce6] shadow-[0_8px_20px_rgb(123,92,245,0.3)] transition-all hover:-translate-y-1"
              >
                Get Started Free <ArrowRight className="w-5 h-5" />
              </Link>
              <a
                href="#how-it-works"
                className="w-full sm:w-auto flex items-center justify-center gap-2 px-8 py-4 rounded-xl font-medium text-gray-700 dark:text-white bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 hover:bg-gray-50 dark:hover:bg-white/10 transition-all backdrop-blur-sm hover:-translate-y-1"
              >
                Discover Features
              </a>
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
                    <div className="h-6 w-24 bg-gray-200 dark:bg-white/10 rounded-md mb-4"></div>
                    <div className="h-4 w-full bg-sma-purple/20 rounded-md"></div>
                    <div className="h-4 w-3/4 bg-gray-100 dark:bg-white/5 rounded-md"></div>
                    <div className="h-4 w-5/6 bg-gray-100 dark:bg-white/5 rounded-md"></div>
                    <div className="h-4 w-4/5 bg-gray-100 dark:bg-white/5 rounded-md"></div>
                  </div>

                  {/* Main Area */}
                  <div className="flex-1 flex flex-col p-4 md:p-8">
                    {/* Header */}
                    <div className="flex justify-between items-center mb-8">
                      <div className="h-10 w-full max-w-sm bg-gray-50 dark:bg-[#16132A] rounded-lg border border-gray-200 dark:border-white/5 flex items-center px-3 gap-2">
                        <Search className="w-4 h-4 text-gray-400" />
                        <div className="h-2 w-24 bg-gray-200 dark:bg-white/10 rounded-full"></div>
                      </div>
                      <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-sma-purple to-sma-blue ml-4 shrink-0"></div>
                    </div>

                    {/* Stats Row */}
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-6">
                      <div className="h-24 rounded-xl bg-gray-50 dark:bg-[#16132A] border border-gray-100 dark:border-white/5 p-4 flex flex-col justify-between">
                        <div className="h-3 w-20 bg-gray-200 dark:bg-white/10 rounded-full"></div>
                        <div className="h-6 w-12 bg-gray-300 dark:bg-white/20 rounded-md"></div>
                      </div>
                      <div className="h-24 rounded-xl bg-gray-50 dark:bg-[#16132A] border border-gray-100 dark:border-white/5 p-4 flex flex-col justify-between">
                        <div className="h-3 w-16 bg-gray-200 dark:bg-white/10 rounded-full"></div>
                        <div className="h-6 w-16 bg-gray-300 dark:bg-white/20 rounded-md"></div>
                      </div>
                      <div className="h-24 rounded-xl bg-gray-50 dark:bg-[#16132A] border border-gray-100 dark:border-white/5 p-4 flex-col justify-between hidden sm:flex">
                        <div className="h-3 w-24 bg-gray-200 dark:bg-white/10 rounded-full"></div>
                        <div className="h-6 w-10 bg-gray-300 dark:bg-white/20 rounded-md"></div>
                      </div>
                    </div>

                    {/* Fake Video Player & Tags */}
                    <div className="flex-1 rounded-xl bg-gray-50 dark:bg-[#16132A] border border-gray-100 dark:border-white/5 relative overflow-hidden flex flex-col">
                      {/* Fake Video Image Area */}
                      <div className="flex-1 bg-gray-200/50 dark:bg-black/20 flex items-center justify-center relative">
                        <div className="w-16 h-16 rounded-full bg-white/50 dark:bg-white/10 backdrop-blur-sm flex items-center justify-center text-gray-500 dark:text-white/50 border border-white/20 shadow-sm">
                          <Play className="w-6 h-6 ml-1" fill="currentColor" />
                        </div>
                        {/* Overlay Bounding Boxes (AI vision simulation) */}
                        <div className="absolute top-1/4 left-1/4 w-32 h-32 border border-sma-purple/50 rounded-lg bg-sma-purple/5 flex items-end p-1">
                          <span className="text-[10px] bg-sma-purple text-white px-1.5 py-0.5 rounded shadow-sm font-medium">Person 98%</span>
                        </div>
                        <div className="absolute bottom-1/4 right-1/3 w-48 h-24 border border-emerald-500/50 rounded-lg bg-emerald-500/5 flex items-end p-1">
                          <span className="text-[10px] bg-emerald-500 text-white px-1.5 py-0.5 rounded shadow-sm font-medium">Car 94%</span>
                        </div>
                      </div>
                      {/* Fake Timeline & Tags */}
                      <div className="h-16 border-t border-gray-100 dark:border-white/5 p-4 flex items-center gap-3">
                        <div className="px-3 py-1 bg-sma-purple/10 text-sma-purple text-xs rounded-full font-medium">Outdoors</div>
                        <div className="px-3 py-1 bg-sma-blue/10 text-sma-blue text-xs rounded-full font-medium hidden sm:block">Daylight</div>
                        <div className="px-3 py-1 bg-emerald-500/10 text-emerald-500 text-xs rounded-full font-medium">Vehicle</div>
                        <div className="flex-1"></div>
                        <div className="w-24 md:w-48 h-1.5 bg-gray-200 dark:bg-white/10 rounded-full overflow-hidden">
                          <div className="w-1/3 h-full bg-sma-purple animate-pulse"></div>
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
              <h2 className="text-3xl md:text-4xl font-bold tracking-tight mb-4">BUILT TO SCALE</h2>
              <p className="text-gray-500 dark:text-gray-400">Enterprise-grade architecture ready for your largest datasets.</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white dark:bg-[#16132A] border border-gray-100 dark:border-white/5 rounded-3xl p-8 flex flex-col items-center text-center shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-none hover:shadow-[0_20px_40px_rgb(0,0,0,0.08)] hover:-translate-y-1 transition-all">
                <Database className="w-10 h-10 text-sma-purple mb-5" />
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Unlimited Media Library</h3>
                <p className="text-gray-500 dark:text-gray-400 text-sm leading-relaxed">Scales from hundreds to millions of assets without performance loss.</p>
              </div>

              <div className="bg-white dark:bg-[#16132A] border border-gray-100 dark:border-white/5 rounded-3xl p-8 flex flex-col items-center text-center shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-none hover:shadow-[0_20px_40px_rgb(0,0,0,0.08)] hover:-translate-y-1 transition-all">
                <Activity className="w-10 h-10 text-sma-blue mb-5" />
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Real-Time Processing</h3>
                <p className="text-gray-500 dark:text-gray-400 text-sm leading-relaxed">Every upload is transcribed, tagged, and indexed automatically — no manual work.</p>
              </div>

              <div className="bg-white dark:bg-[#16132A] border border-gray-100 dark:border-white/5 rounded-3xl p-8 flex flex-col items-center text-center shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-none hover:shadow-[0_20px_40px_rgb(0,0,0,0.08)] hover:-translate-y-1 transition-all">
                <Tag className="w-10 h-10 text-emerald-500 mb-5" />
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Deep AI Understanding</h3>
                <p className="text-gray-500 dark:text-gray-400 text-sm leading-relaxed">Every frame and word is analyzed for searchable, actionable metadata.</p>
              </div>
            </div>
          </div>
        </div>

        {/* Features Section */}
        <div id="features" className="py-24 relative z-10 border-t border-gray-200 dark:border-white/5">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-20">
              <h2 className="text-sm font-bold tracking-widest text-sma-purple uppercase mb-3">Enterprise Capabilities</h2>
              <h3 className="text-3xl md:text-5xl font-bold tracking-tight text-gray-900 dark:text-white mb-6">
                Purpose-built for Media Workflows
              </h3>
              <p className="max-w-2xl mx-auto text-lg text-gray-400 font-light">
                Our platform goes beyond basic storage. We apply advanced Machine Learning models to understand the content of your media files.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Feature 1 */}
              <div className="p-8 rounded-3xl bg-white dark:bg-[#16132A] border border-gray-100 dark:border-white/5 hover:border-sma-purple/50 transition-all duration-300 group shadow-[0_4px_20px_rgb(0,0,0,0.03)] dark:shadow-sm">
                <div className="w-14 h-14 rounded-2xl bg-sma-purple/10 flex items-center justify-center mb-8 group-hover:scale-110 transition-transform">
                  <Search className="w-7 h-7 text-sma-purple" />
                </div>
                <h4 className="text-xl font-bold text-gray-900 dark:text-white mb-3">Semantic Search</h4>
                <p className="text-gray-500 dark:text-gray-400 leading-relaxed font-light">
                  Find exact moments using natural language. Instead of searching for "IMG_102", search for "a red car driving on a bridge at sunset".
                </p>
              </div>

              {/* Feature 2 */}
              <div className="p-8 rounded-3xl bg-white dark:bg-[#16132A] border border-gray-100 dark:border-white/5 hover:border-sma-blue/50 transition-all duration-300 group shadow-[0_4px_20px_rgb(0,0,0,0.03)] dark:shadow-sm">
                <div className="w-14 h-14 rounded-2xl bg-sma-blue/10 flex items-center justify-center mb-8 group-hover:scale-110 transition-transform">
                  <Video className="w-7 h-7 text-sma-blue" />
                </div>
                <h4 className="text-xl font-bold text-gray-900 dark:text-white mb-3">Vision AI Analysis</h4>
                <p className="text-gray-500 dark:text-gray-400 leading-relaxed font-light">
                  Automated keyframe extraction and scene detection. We use advanced Vision Language Models to understand the visual context of your videos.
                </p>
              </div>

              {/* Feature 3 */}
              <div className="p-8 rounded-3xl bg-white dark:bg-[#16132A] border border-gray-100 dark:border-white/5 hover:border-emerald-500/50 transition-all duration-300 group shadow-[0_4px_20px_rgb(0,0,0,0.03)] dark:shadow-sm">
                <div className="w-14 h-14 rounded-2xl bg-emerald-500/10 flex items-center justify-center mb-8 group-hover:scale-110 transition-transform">
                  <Mic className="w-7 h-7 text-emerald-500" />
                </div>
                <h4 className="text-xl font-bold text-gray-900 dark:text-white mb-3">Audio Transcription</h4>
                <p className="text-gray-500 dark:text-gray-400 leading-relaxed font-light">
                  Highly accurate, multi-language speech-to-text powered by state-of-the-art ASR models. Search through spoken words instantly.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* How it Works / Tech Workflow */}
        <div id="how-it-works" className="py-24 relative border-t border-gray-200 dark:border-white/5">
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

        {/* Trusted By / Social Proof Section */}
        <div className="py-20 border-t border-gray-200 dark:border-white/5 relative z-10">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            {/* 
              TODO: Thêm dải logo khách hàng hoặc case studies thật tại đây.
              Vui lòng KHÔNG dùng logo giả mạo hoặc tên công ty giả theo đúng Action Item 7.2.
            */}
          </div>
        </div>

        {/* CTA Section */}
        <div className="relative py-24 overflow-hidden border-t border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5">
          <div className="max-w-4xl mx-auto px-4 relative z-10 text-center">
            <h2 className="text-4xl font-bold text-gray-900 dark:text-white mb-6">Ready to transform your media library?</h2>
            <p className="text-xl text-gray-600 dark:text-gray-400 mb-10 font-light">Join the future of media asset management. Intelligent, fast, and secure.</p>
            <Link
              to="/login"
              className="inline-flex items-center justify-center gap-2 px-12 py-5 rounded-2xl font-bold text-white bg-sma-purple hover:bg-[#6b4ce6] shadow-[0_8px_30px_rgb(123,92,245,0.4)] transition-all hover:scale-105 active:scale-95"
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
              <Play className="text-sma-purple w-5 h-5" fill="currentColor" />
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
