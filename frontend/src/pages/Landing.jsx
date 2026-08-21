import { Link } from 'react-router-dom';
import { Play, Search, Video, Mic, ChevronRight, Zap, Shield, Cpu, ArrowRight, BarChart3, Layers } from 'lucide-react';
import { useEffect, useState } from 'react';

export default function Landing() {
  const [scrolled, setScrolled] = useState(false);

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
            <div className="flex items-center gap-3 group cursor-pointer">
              <div className="relative">
                <div className="absolute inset-0 bg-sma-purple blur-md opacity-50 group-hover:opacity-100 transition-opacity"></div>
                <div className="bg-gradient-to-br from-[#16132A] to-[#2a244c] p-2 rounded-xl border border-sma-purple/30 relative z-10">
                  <Play className="text-sma-purple w-5 h-5" fill="currentColor" />
                </div>
              </div>
              <span className="font-extrabold text-xl tracking-tight text-gray-900 dark:text-white group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-sma-purple group-hover:to-sma-blue transition-all duration-300">
                SMA
              </span>
            </div>
            
            <nav className="hidden md:flex items-center gap-8">
              <a href="#features" className="text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-sma-purple transition-colors">Features</a>
              <a href="#how-it-works" className="text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-sma-purple transition-colors">How it works</a>
              <a href="#security" className="text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-sma-purple transition-colors">Security</a>
            </nav>

            <div className="flex items-center gap-4">
              <Link 
                to="/login" 
                className="text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors"
              >
                Log in
              </Link>
              <Link 
                to="/login" 
                className="text-sm font-medium px-5 py-2.5 rounded-xl text-white bg-white/10 hover:bg-white/20 border border-white/10 backdrop-blur-md shadow-lg transition-all hover:scale-105 active:scale-95 bg-gradient-to-r from-sma-purple to-sma-blue"
              >
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </header>

      <main className="flex-grow">
        {/* Hero Section */}
        <div className="relative pt-32 pb-20 md:pt-48 md:pb-32 overflow-hidden">
          {/* Animated Background */}
          <div className="absolute top-0 left-0 w-full h-full overflow-hidden z-0 pointer-events-none">
            <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-sma-purple opacity-20 rounded-full blur-[120px] animate-pulse"></div>
            <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-sma-blue opacity-20 rounded-full blur-[120px] animate-pulse" style={{ animationDelay: '2s' }}></div>
          </div>
          
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/5 border border-white/10 text-sm font-medium mb-8 shadow-sm backdrop-blur-md hover:bg-white/10 transition-colors cursor-pointer group">
              <span className="w-2 h-2 rounded-full bg-sma-purple group-hover:animate-ping"></span>
              <span className="text-gray-300">The next generation of Media Management</span>
              <ChevronRight className="w-4 h-4 text-gray-400 group-hover:translate-x-1 transition-transform" />
            </div>
            
            <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight mb-8 leading-[1.1]">
              Unlock the Intelligence <br className="hidden md:block" />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-sma-purple via-[#9b72ff] to-sma-blue">
                Hidden in Your Media
              </span>
            </h1>
            
            <p className="mt-4 text-xl text-gray-600 dark:text-gray-400 max-w-3xl mx-auto mb-10 leading-relaxed font-light">
              Transform hours of unstructured video and audio into searchable, actionable data. 
              Our AI-driven pipeline automatically transcribes, tags, and analyzes every frame.
            </p>
            
            <div className="flex flex-col sm:flex-row items-center justify-center gap-5">
              <Link 
                to="/login" 
                className="w-full sm:w-auto flex items-center justify-center gap-2 px-8 py-4 rounded-xl font-medium text-white bg-gradient-to-r from-sma-purple to-sma-blue hover:from-purple-500 hover:to-blue-500 shadow-lg shadow-purple-500/25 transition-all hover:shadow-purple-500/40 hover:-translate-y-1"
              >
                Access Dashboard <ArrowRight className="w-5 h-5" />
              </Link>
              <a 
                href="#how-it-works" 
                className="w-full sm:w-auto flex items-center justify-center gap-2 px-8 py-4 rounded-xl font-medium text-gray-700 dark:text-white bg-white/5 border border-gray-200 dark:border-white/10 hover:bg-gray-50 dark:hover:bg-white/10 transition-all backdrop-blur-sm hover:-translate-y-1"
              >
                Discover Features
              </a>
            </div>
          </div>
          
          {/* Dashboard Preview Image (Placeholder styling) */}
          <div className="mt-20 max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
            <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-md shadow-2xl p-2 relative overflow-hidden group">
              <div className="absolute inset-0 bg-gradient-to-t from-[#0a0a0f] via-transparent to-transparent z-10 opacity-60"></div>
              <div className="aspect-[16/9] w-full rounded-xl bg-[#16132A] flex items-center justify-center relative overflow-hidden">
                 <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=2070&auto=format&fit=crop')] bg-cover bg-center opacity-30 group-hover:opacity-40 transition-opacity duration-700"></div>
                 <div className="absolute inset-0 bg-gradient-to-r from-sma-purple/20 to-sma-blue/20 mix-blend-overlay"></div>
                 {/* Fake UI Elements for visual */}
                 <div className="absolute left-6 top-6 bottom-6 w-48 bg-[#0a0a0f]/80 backdrop-blur-md rounded-lg border border-white/5 hidden md:flex flex-col p-4 gap-3">
                   <div className="h-6 w-24 bg-white/10 rounded-md mb-4"></div>
                   <div className="h-4 w-full bg-sma-purple/40 rounded-md"></div>
                   <div className="h-4 w-3/4 bg-white/10 rounded-md"></div>
                   <div className="h-4 w-4/5 bg-white/10 rounded-md"></div>
                 </div>
                 <div className="absolute right-6 top-6 bottom-6 left-6 md:left-60 bg-[#0a0a0f]/80 backdrop-blur-md rounded-lg border border-white/5 p-6 flex flex-col">
                   <div className="h-8 w-64 bg-white/10 rounded-md mb-6"></div>
                   <div className="flex-1 grid grid-cols-3 gap-4">
                     <div className="col-span-2 bg-white/5 rounded-md border border-white/5"></div>
                     <div className="col-span-1 bg-white/5 rounded-md border border-white/5 flex flex-col gap-4 p-4">
                       <div className="h-4 w-full bg-white/10 rounded-md"></div>
                       <div className="h-4 w-3/4 bg-white/10 rounded-md"></div>
                     </div>
                   </div>
                 </div>
              </div>
            </div>
          </div>
        </div>

        {/* Features Section */}
        <div id="features" className="py-24 bg-[#0a0a0f] relative z-10">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-20">
              <h2 className="text-sm font-bold tracking-widest text-sma-purple uppercase mb-3">Enterprise Capabilities</h2>
              <h3 className="text-3xl md:text-5xl font-bold tracking-tight text-white mb-6">
                Purpose-built for Media Workflows
              </h3>
              <p className="max-w-2xl mx-auto text-lg text-gray-400 font-light">
                Our platform goes beyond basic storage. We apply advanced Machine Learning models to understand the content of your media files.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Feature 1 */}
              <div className="p-8 rounded-3xl bg-white/5 border border-white/10 hover:border-sma-purple/50 hover:bg-white/[0.07] transition-all duration-300 group">
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-sma-purple/20 to-transparent border border-sma-purple/30 flex items-center justify-center mb-8 group-hover:scale-110 transition-transform">
                  <Search className="w-7 h-7 text-sma-purple" />
                </div>
                <h4 className="text-xl font-bold text-white mb-3">Semantic Search</h4>
                <p className="text-gray-400 leading-relaxed font-light">
                  Find exact moments using natural language. Instead of searching for "IMG_102", search for "a red car driving on a bridge at sunset".
                </p>
              </div>

              {/* Feature 2 */}
              <div className="p-8 rounded-3xl bg-white/5 border border-white/10 hover:border-sma-blue/50 hover:bg-white/[0.07] transition-all duration-300 group">
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-sma-blue/20 to-transparent border border-sma-blue/30 flex items-center justify-center mb-8 group-hover:scale-110 transition-transform">
                  <Video className="w-7 h-7 text-sma-blue" />
                </div>
                <h4 className="text-xl font-bold text-white mb-3">Vision AI Analysis</h4>
                <p className="text-gray-400 leading-relaxed font-light">
                  Automated keyframe extraction and scene detection. We use advanced Vision Language Models to understand the visual context of your videos.
                </p>
              </div>

              {/* Feature 3 */}
              <div className="p-8 rounded-3xl bg-white/5 border border-white/10 hover:border-emerald-500/50 hover:bg-white/[0.07] transition-all duration-300 group">
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-emerald-500/20 to-transparent border border-emerald-500/30 flex items-center justify-center mb-8 group-hover:scale-110 transition-transform">
                  <Mic className="w-7 h-7 text-emerald-500" />
                </div>
                <h4 className="text-xl font-bold text-white mb-3">Audio Transcription</h4>
                <p className="text-gray-400 leading-relaxed font-light">
                  Highly accurate, multi-language speech-to-text powered by state-of-the-art ASR models. Search through spoken words instantly.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* How it Works / Tech Workflow */}
        <div id="how-it-works" className="py-24 bg-[#0d0c13] relative border-t border-white/5">
          <div className="absolute right-0 top-0 w-1/3 h-full bg-sma-blue/5 blur-[150px] pointer-events-none"></div>
          
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
              <div>
                <h2 className="text-3xl md:text-4xl font-bold text-white mb-6 leading-tight">
                  A seamless pipeline from <br/> upload to insights
                </h2>
                <p className="text-gray-400 text-lg font-light mb-10">
                  Every asset you upload goes through our proprietary AI processing pipeline, designed for speed and accuracy.
                </p>
                
                <div className="space-y-8">
                  <div className="flex gap-4">
                    <div className="shrink-0 mt-1">
                      <div className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center border border-white/20">
                        <span className="font-bold text-white">1</span>
                      </div>
                    </div>
                    <div>
                      <h4 className="text-xl font-bold text-white mb-2">Secure Upload & Storage</h4>
                      <p className="text-gray-400 font-light">Your media is encrypted and safely stored in high-performance cloud buckets, ready for processing.</p>
                    </div>
                  </div>
                  
                  <div className="flex gap-4">
                    <div className="shrink-0 mt-1">
                      <div className="w-10 h-10 rounded-full bg-sma-purple/20 flex items-center justify-center border border-sma-purple/40">
                        <span className="font-bold text-sma-purple">2</span>
                      </div>
                    </div>
                    <div>
                      <h4 className="text-xl font-bold text-white mb-2">Automated AI Processing</h4>
                      <p className="text-gray-400 font-light">Background workers automatically extract audio, detect scenes, transcribe speech, and generate embeddings.</p>
                    </div>
                  </div>

                  <div className="flex gap-4">
                    <div className="shrink-0 mt-1">
                      <div className="w-10 h-10 rounded-full bg-sma-blue/20 flex items-center justify-center border border-sma-blue/40">
                        <span className="font-bold text-sma-blue">3</span>
                      </div>
                    </div>
                    <div>
                      <h4 className="text-xl font-bold text-white mb-2">Instant Search & Discovery</h4>
                      <p className="text-gray-400 font-light">Data is indexed in a vector database, allowing you to instantly query your entire library using natural language.</p>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="relative">
                <div className="aspect-square rounded-full border border-white/10 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[120%] animate-[spin_60s_linear_infinite]"></div>
                <div className="aspect-square rounded-full border border-white/5 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[80%] animate-[spin_40s_linear_infinite_reverse]"></div>
                
                <div className="relative z-10 grid grid-cols-2 gap-4">
                  <div className="space-y-4 pt-12">
                    <div className="bg-white/5 backdrop-blur-xl border border-white/10 p-6 rounded-2xl shadow-2xl">
                      <Layers className="w-8 h-8 text-sma-purple mb-4" />
                      <h5 className="text-white font-bold mb-1">Scalable Architecture</h5>
                      <p className="text-xs text-gray-400">Microservices designed to handle massive media libraries.</p>
                    </div>
                    <div className="bg-white/5 backdrop-blur-xl border border-white/10 p-6 rounded-2xl shadow-2xl">
                      <BarChart3 className="w-8 h-8 text-sma-blue mb-4" />
                      <h5 className="text-white font-bold mb-1">Deep Analytics</h5>
                      <p className="text-xs text-gray-400">Extract metadata, tags, and sentiment from every frame.</p>
                    </div>
                  </div>
                  <div className="space-y-4">
                    <div className="bg-white/5 backdrop-blur-xl border border-white/10 p-6 rounded-2xl shadow-2xl">
                      <Cpu className="w-8 h-8 text-emerald-500 mb-4" />
                      <h5 className="text-white font-bold mb-1">Local Inference</h5>
                      <p className="text-xs text-gray-400">Powered by advanced LLMs and VLMs running securely.</p>
                    </div>
                    <div className="bg-white/5 backdrop-blur-xl border border-white/10 p-6 rounded-2xl shadow-2xl">
                      <Shield className="w-8 h-8 text-amber-500 mb-4" />
                      <h5 className="text-white font-bold mb-1">Enterprise Security</h5>
                      <p className="text-xs text-gray-400">Your data never leaves your controlled environment.</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* CTA Section */}
        <div className="relative py-24 overflow-hidden border-t border-white/10 bg-[#0a0a0f]">
          <div className="absolute inset-0 bg-gradient-to-b from-sma-purple/10 to-transparent"></div>
          <div className="max-w-4xl mx-auto px-4 relative z-10 text-center">
            <h2 className="text-4xl font-bold text-white mb-6">Ready to transform your media library?</h2>
            <p className="text-xl text-gray-400 mb-10 font-light">Join the future of media asset management. Intelligent, fast, and secure.</p>
            <Link 
              to="/login" 
              className="inline-flex items-center justify-center gap-2 px-10 py-4 rounded-xl font-bold text-white bg-white/10 border border-white/20 hover:bg-white/20 backdrop-blur-md shadow-2xl transition-all hover:scale-105"
            >
              Get Started Now
            </Link>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-[#050508] py-12 border-t border-white/5">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="flex items-center gap-3">
              <Play className="text-sma-purple w-5 h-5" fill="currentColor" />
              <span className="text-white font-bold text-lg tracking-tight">Smart Media Analytics</span>
            </div>
            
            <div className="flex gap-8">
              <a href="#" className="text-sm text-gray-500 hover:text-white transition-colors">Privacy Policy</a>
              <a href="#" className="text-sm text-gray-500 hover:text-white transition-colors">Terms of Service</a>
              <a href="#" className="text-sm text-gray-500 hover:text-white transition-colors">Contact Support</a>
            </div>
          </div>
          
          <div className="mt-8 pt-8 border-t border-white/5 text-center md:text-left text-sm text-gray-600">
            © {new Date().getFullYear()} Smart Media Analytics. All rights reserved. Proprietary and Confidential.
          </div>
        </div>
      </footer>
    </div>
  );
}
