/**
 * Login page — clean, premium design with gradient accents.
 */

import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useAuth } from '../hooks/useAuth';
import { Briefcase, Eye, EyeOff, ArrowRight, Loader2 } from 'lucide-react';

const loginSchema = z.object({
  email: z.string().email('Enter a valid email'),
  password: z.string().min(1, 'Password is required'),
});

type LoginForm = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginForm) => {
    try {
      setError('');
      const loggedInUser = await login(data);
      if (loggedInUser?.role === 'candidate') {
        navigate('/my-dashboard');
      } else if (loggedInUser?.role === 'interviewer') {
        navigate('/interviews');
      } else {
        navigate('/dashboard');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid credentials');
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left panel — branding */}
      <div className="hidden lg:flex lg:w-1/2 gradient-primary relative overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-20 left-20 w-72 h-72 bg-white rounded-full blur-3xl" />
          <div className="absolute bottom-20 right-20 w-96 h-96 bg-white rounded-full blur-3xl" />
        </div>
        <div className="relative z-10 flex flex-col justify-center px-16 text-white">
          <div className="flex items-center gap-3 mb-8">
            <div className="w-12 h-12 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center">
              <Briefcase className="w-6 h-6" />
            </div>
            <span className="text-2xl font-bold">RecruitFlow</span>
          </div>
          <h1 className="text-4xl font-bold leading-tight mb-4">
            Streamline Your<br />Hiring Process
          </h1>
          <p className="text-lg text-white/80 max-w-md">
            From job posting to offer letters — manage your entire recruitment pipeline in one powerful platform.
          </p>
          <div className="mt-12 space-y-4">
            {['Track candidates in real-time', 'Schedule interviews effortlessly', 'Data-driven hiring decisions'].map((item, i) => (
              <div key={i} className="flex items-center gap-3 text-white/90">
                <div className="w-6 h-6 bg-white/20 rounded-full flex items-center justify-center text-xs">✓</div>
                <span>{item}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right panel — form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-md animate-fade-in">
          <div className="lg:hidden flex items-center gap-2 mb-8">
            <div className="w-10 h-10 gradient-primary rounded-xl flex items-center justify-center">
              <Briefcase className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold gradient-text">RecruitFlow</span>
          </div>

          <h2 className="text-2xl font-bold text-surface-900 mb-1">Welcome back</h2>
          <p className="text-surface-500 mb-8">Sign in to continue to your dashboard</p>

          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700 animate-fade-in">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            <div>
              <label htmlFor="email" className="label-text">Email</label>
              <input
                id="email"
                type="email"
                placeholder="you@company.com"
                className="input-field"
                {...register('email')}
              />
              {errors.email && <p className="mt-1 text-xs text-danger">{errors.email.message}</p>}
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label htmlFor="password" className="label-text mb-0">Password</label>
                <Link to="/forgot-password" className="text-xs text-primary-600 hover:text-primary-700 font-medium">
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••"
                  className="input-field pr-10"
                  {...register('password')}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-surface-400 hover:text-surface-600"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {errors.password && <p className="mt-1 text-xs text-danger">{errors.password.message}</p>}
            </div>

            <button type="submit" disabled={isSubmitting} className="btn-primary w-full">
              {isSubmitting ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <>Sign In <ArrowRight className="w-4 h-4" /></>
              )}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-surface-500">
            Don't have an account?{' '}
            <Link to="/register" className="font-semibold text-primary-600 hover:text-primary-700">
              Create account
            </Link>
          </p>

          {/* Demo credentials hint */}
          <div className="mt-8 p-4 bg-surface-50 rounded-xl border border-surface-200">
            <p className="text-xs font-semibold text-surface-500 mb-2 uppercase tracking-wider">
              Quick Demo Accounts (1-Click Fill)
            </p>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => {
                  setValue('email', 'admin@recruitflow.dev');
                  setValue('password', 'Demo1234!');
                }}
                className="text-xs px-2.5 py-1 rounded-lg bg-surface-200 hover:bg-primary-50 hover:text-primary-700 text-surface-700 font-medium transition-colors"
              >
                Admin
              </button>
              <button
                type="button"
                onClick={() => {
                  setValue('email', 'recruiter@recruitflow.dev');
                  setValue('password', 'Demo1234!');
                }}
                className="text-xs px-2.5 py-1 rounded-lg bg-surface-200 hover:bg-primary-50 hover:text-primary-700 text-surface-700 font-medium transition-colors"
              >
                Recruiter
              </button>
              <button
                type="button"
                onClick={() => {
                  setValue('email', 'manager@recruitflow.dev');
                  setValue('password', 'Demo1234!');
                }}
                className="text-xs px-2.5 py-1 rounded-lg bg-surface-200 hover:bg-primary-50 hover:text-primary-700 text-surface-700 font-medium transition-colors"
              >
                Manager
              </button>
              <button
                type="button"
                onClick={() => {
                  setValue('email', 'interviewer@recruitflow.dev');
                  setValue('password', 'Demo1234!');
                }}
                className="text-xs px-2.5 py-1 rounded-lg bg-surface-200 hover:bg-primary-50 hover:text-primary-700 text-surface-700 font-medium transition-colors"
              >
                Interviewer
              </button>
              <button
                type="button"
                onClick={() => {
                  setValue('email', 'alex@example.com');
                  setValue('password', 'Demo1234!');
                }}
                className="text-xs px-2.5 py-1 rounded-lg bg-surface-200 hover:bg-primary-50 hover:text-primary-700 text-surface-700 font-medium transition-colors"
              >
                Candidate
              </button>
            </div>
            <p className="mt-2 text-[11px] text-surface-400">Password: Demo1234!</p>
          </div>
        </div>
      </div>
    </div>
  );
}
