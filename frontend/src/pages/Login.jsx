import { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Play } from 'lucide-react';

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, signup } = useAuth();
  
  const [isSignUp, setIsSignUp] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const from = location.state?.from?.pathname || "/app";

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please fill in all fields');
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      let result;
      if (isSignUp) {
        result = await signup(email, password);
      } else {
        result = await login(email, password);
      }
      
      if (result.success) {
        navigate(from, { replace: true });
      }
    } catch (err) {
      setError(isSignUp ? 'Failed to create account. Email might be in use or password too weak.' : 'Failed to log in. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#F8F9FA] dark:bg-sma-bg relative overflow-hidden transition-colors">
      {/* Background decorations */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden z-0 pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-sma-purple opacity-10 rounded-full blur-[100px]"></div>
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-sma-blue opacity-10 rounded-full blur-[100px]"></div>
      </div>

      <div className="w-full max-w-md p-8 relative z-10">
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center justify-center mb-6 relative group">
             <div className="absolute inset-0 bg-sma-purple blur-lg opacity-40 rounded-full group-hover:opacity-60 transition-opacity"></div>
             <div className="relative bg-[#16132A] p-4 rounded-2xl border border-white/10 shadow-xl flex items-center justify-center">
               <Play className="text-sma-purple w-8 h-8" fill="currentColor" />
             </div>
          </Link>
          <h1 className="text-3xl font-extrabold tracking-tight text-gray-900 dark:text-white mb-2">
            {isSignUp ? 'Create an account' : 'Welcome back'}
          </h1>
          <p className="text-gray-500 dark:text-gray-400">
            {isSignUp ? 'Sign up to start analyzing your media' : 'Sign in to access your media analytics'}
          </p>
        </div>

        <div className="bg-white dark:bg-[#1A162B] rounded-2xl shadow-xl border border-gray-100 dark:border-white/10 p-8">
          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="p-3 rounded-lg bg-red-50 text-red-600 text-sm border border-red-100 dark:bg-red-900/20 dark:border-red-900/50 dark:text-red-400">
                {error}
              </div>
            )}
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Email address
              </label>
              <input 
                type="email" 
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-2.5 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-black/20 text-gray-900 dark:text-white focus:ring-2 focus:ring-sma-purple focus:border-transparent transition-all outline-none"
                placeholder="you@example.com"
                autoComplete="email"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Password
              </label>
              <input 
                type="password" 
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-2.5 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-black/20 text-gray-900 dark:text-white focus:ring-2 focus:ring-sma-purple focus:border-transparent transition-all outline-none"
                placeholder="••••••••"
                autoComplete="current-password"
              />
            </div>

            {!isSignUp && (
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <input
                    id="remember-me"
                    name="remember-me"
                    type="checkbox"
                    className="h-4 w-4 rounded border-gray-300 text-sma-purple focus:ring-sma-purple"
                  />
                  <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-500 dark:text-gray-400">
                    Remember me
                  </label>
                </div>

                <div className="text-sm">
                  <a href="#" className="font-medium text-sma-purple hover:text-sma-blue transition-colors">
                    Forgot password?
                  </a>
                </div>
              </div>
            )}

            <button 
              type="submit" 
              disabled={loading}
              className="w-full py-2.5 px-4 rounded-lg font-medium text-white bg-gradient-to-r from-sma-purple to-sma-blue hover:from-purple-500 hover:to-blue-500 shadow-lg shadow-purple-500/20 disabled:opacity-70 disabled:cursor-not-allowed transition-all"
            >
              {loading ? (
                <div className="flex items-center justify-center">
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                </div>
              ) : (
                isSignUp ? 'Sign up' : 'Sign in'
              )}
            </button>
            
            <p className="text-center text-sm text-gray-500 dark:text-gray-400 pt-2">
              {isSignUp ? 'Already have an account?' : "Don't have an account?"}{' '}
              <button type="button" onClick={() => setIsSignUp(!isSignUp)} className="font-medium text-sma-purple hover:text-sma-blue transition-colors">
                {isSignUp ? 'Sign in' : 'Sign up'}
              </button>
            </p>
          </form>
        </div>
      </div>
    </div>
  );
}
