import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import api from '../services/api';
import { BrainCircuit, Mail, User, Lock, Loader2, AlertCircle, CheckCircle } from 'lucide-react';

const registerSchema = z.object({
  fullName: z.string().max(100, { message: "Name must be less than 100 characters" }).optional(),
  email: z.string().email({ message: "Invalid email address format" }),
  password: z.string()
    .min(8, { message: "Password must be at least 8 characters long" })
    .regex(/[A-Z]/, { message: "Password must contain at least one uppercase letter" })
    .regex(/[a-z]/, { message: "Password must contain at least one lowercase letter" })
    .regex(/\d/, { message: "Password must contain at least one digit" })
    .regex(/[!@#$%^&*(),.?":{}|<>]/, { message: "Password must contain at least one special character" }),
});

type RegisterFormValues = z.infer<typeof registerSchema>;

const Register: React.FC = () => {
  const navigate = useNavigate();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: { fullName: '', email: '', password: '' },
  });

  const onSubmit = async (data: RegisterFormValues) => {
    setErrorMessage(null);
    setSuccessMessage(null);
    try {
      await api.post('/auth/register', {
        email: data.email,
        password: data.password,
        full_name: data.fullName || null
      });
      setSuccessMessage("Account created successfully! Redirecting to login...");
      setTimeout(() => navigate('/login'), 2000);
    } catch (err: any) {
      const detail = err.response?.data?.detail || "Registration failed. Email might already be taken.";
      setErrorMessage(detail);
    }
  };

  return (
    <div className="relative flex h-screen w-screen items-center justify-center bg-[#070b13] overflow-hidden">
      {/* Background blobs */}
      <div className="absolute top-1/4 left-1/4 h-96 w-96 rounded-full bg-primary/20 blur-[100px] animate-pulse-slow" />
      <div className="absolute bottom-1/4 right-1/4 h-96 w-96 rounded-full bg-violet-600/10 blur-[120px]" />

      <div className="z-10 w-full max-w-md rounded-2xl border border-white/5 bg-[#0d1527]/40 p-8 shadow-2xl backdrop-blur-xl">
        <div className="flex flex-col items-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary">
            <BrainCircuit className="h-8 w-8 text-primary animate-pulse-slow" />
          </div>
          <h2 className="mt-4 font-outfit text-2xl font-bold tracking-tight text-white">Create your account</h2>
          <p className="mt-1 text-sm text-slate-400">Start organizing and analyzing your documents</p>
        </div>

        {errorMessage && (
          <div className="mt-6 flex items-start space-x-2 rounded-xl bg-destructive/10 border border-destructive/20 p-3.5 text-xs text-rose-400 animate-fade-in">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {successMessage && (
          <div className="mt-6 flex items-start space-x-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20 p-3.5 text-xs text-emerald-400 animate-fade-in">
            <CheckCircle className="h-4 w-4 shrink-0" />
            <span>{successMessage}</span>
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300">Full Name</label>
            <div className="relative mt-1">
              <User className="absolute top-3 left-3 h-4.5 w-4.5 text-slate-500" />
              <input
                type="text"
                placeholder="John Doe"
                {...register('fullName')}
                className="w-full rounded-xl border border-white/5 bg-slate-950/40 py-2.5 pr-4 pl-10 text-sm text-white placeholder-slate-500 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary transition-all duration-200"
              />
            </div>
            {errors.fullName && <p className="mt-1.5 text-xs text-rose-400">{errors.fullName.message}</p>}
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300">Email Address</label>
            <div className="relative mt-1">
              <Mail className="absolute top-3 left-3 h-4.5 w-4.5 text-slate-500" />
              <input
                type="email"
                placeholder="you@example.com"
                {...register('email')}
                className="w-full rounded-xl border border-white/5 bg-slate-950/40 py-2.5 pr-4 pl-10 text-sm text-white placeholder-slate-500 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary transition-all duration-200"
              />
            </div>
            {errors.email && <p className="mt-1.5 text-xs text-rose-400">{errors.email.message}</p>}
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300">Password</label>
            <div className="relative mt-1">
              <Lock className="absolute top-3 left-3 h-4.5 w-4.5 text-slate-500" />
              <input
                type="password"
                placeholder="••••••••"
                {...register('password')}
                className="w-full rounded-xl border border-white/5 bg-slate-950/40 py-2.5 pr-4 pl-10 text-sm text-white placeholder-slate-500 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary transition-all duration-200"
              />
            </div>
            {errors.password && <p className="mt-1.5 text-xs text-rose-400">{errors.password.message}</p>}
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="flex w-full items-center justify-center rounded-xl bg-primary py-3 text-sm font-semibold text-white hover:bg-primary/95 transition-all shadow-lg shadow-primary/20 hover:scale-[1.01]"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Registering account...
              </>
            ) : (
              'Create Account'
            )}
          </button>
        </form>

        <p className="mt-8 text-center text-xs text-slate-400">
          Already have an account?{' '}
          <Link to="/login" className="text-primary hover:underline font-semibold">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
};

export default Register;
