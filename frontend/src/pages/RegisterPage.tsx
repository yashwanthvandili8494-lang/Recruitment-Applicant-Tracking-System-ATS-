/**
 * Registration page for candidates.
 */

import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useAuth } from '../hooks/useAuth';
import { Briefcase, Eye, EyeOff, ArrowRight, Loader2 } from 'lucide-react';

const registerSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  email: z.string().email('Enter a valid email'),
  password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Must contain an uppercase letter')
    .regex(/[a-z]/, 'Must contain a lowercase letter')
    .regex(/\d/, 'Must contain a digit'),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: 'Passwords do not match',
  path: ['confirmPassword'],
});

type RegisterForm = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const { register: authRegister } = useAuth();
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = async (data: RegisterForm) => {
    try {
      setError('');
      await authRegister({
        name: data.name,
        email: data.email,
        password: data.password,
      });
      setSuccess(true);
      setTimeout(() => navigate('/login'), 2000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-8 bg-surface-50">
      <div className="w-full max-w-md animate-fade-in">
        <div className="flex items-center gap-2 mb-8 justify-center">
          <div className="w-10 h-10 gradient-primary rounded-xl flex items-center justify-center">
            <Briefcase className="w-5 h-5 text-white" />
          </div>
          <span className="text-xl font-bold gradient-text">RecruitFlow</span>
        </div>

        <div className="card p-8">
          <h2 className="text-2xl font-bold text-surface-900 mb-1 text-center">Create your account</h2>
          <p className="text-surface-500 mb-6 text-center">Start your job search journey</p>

          {success ? (
            <div className="p-4 bg-green-50 border border-green-200 rounded-xl text-sm text-green-700 text-center animate-fade-in">
              ✓ Account created! Redirecting to login...
            </div>
          ) : (
            <>
              {error && (
                <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700 animate-fade-in">
                  {error}
                </div>
              )}

              <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                <div>
                  <label htmlFor="name" className="label-text">Full Name</label>
                  <input id="name" type="text" placeholder="John Doe" className="input-field" {...register('name')} />
                  {errors.name && <p className="mt-1 text-xs text-danger">{errors.name.message}</p>}
                </div>

                <div>
                  <label htmlFor="reg-email" className="label-text">Email</label>
                  <input id="reg-email" type="email" placeholder="you@example.com" className="input-field" {...register('email')} />
                  {errors.email && <p className="mt-1 text-xs text-danger">{errors.email.message}</p>}
                </div>

                <div>
                  <label htmlFor="reg-password" className="label-text">Password</label>
                  <div className="relative">
                    <input
                      id="reg-password"
                      type={showPassword ? 'text' : 'password'}
                      placeholder="Min 8 chars, uppercase, lowercase, digit"
                      className="input-field pr-10"
                      {...register('password')}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-surface-400"
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  {errors.password && <p className="mt-1 text-xs text-danger">{errors.password.message}</p>}
                </div>

                <div>
                  <label htmlFor="confirm-password" className="label-text">Confirm Password</label>
                  <input
                    id="confirm-password"
                    type="password"
                    placeholder="••••••••"
                    className="input-field"
                    {...register('confirmPassword')}
                  />
                  {errors.confirmPassword && <p className="mt-1 text-xs text-danger">{errors.confirmPassword.message}</p>}
                </div>

                <button type="submit" disabled={isSubmitting} className="btn-primary w-full">
                  {isSubmitting ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <>Create Account <ArrowRight className="w-4 h-4" /></>
                  )}
                </button>
              </form>
            </>
          )}

          <p className="mt-6 text-center text-sm text-surface-500">
            Already have an account?{' '}
            <Link to="/login" className="font-semibold text-primary-600 hover:text-primary-700">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
