import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation } from '@tanstack/react-query'
import { ArrowRight, ShieldCheck } from 'lucide-react'
import { registerUser, type ApiError } from '@/api/auth'
import { Alert, Button, FormField, PasswordInput, Input, Spinner } from '@/components/ui'
import { AuthLayout } from '@/components/auth/AuthLayout'

const schema = z
  .object({
    email: z.string().email('Invalid email address'),
    password: z.string().min(8, 'Password must be at least 8 characters'),
    confirmPassword: z.string().min(1, 'Please confirm your password'),
  })
  .refine((d) => d.password === d.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  })
type FormData = z.infer<typeof schema>

const PANEL = {
  headline: (
    <>
      Your workspace
      <br />
      starts
      <br />
      <span className="text-white/35">right here.</span>
    </>
  ),
  tagline:
    'Create the first administrator account to unlock the full platform. This can only be done once.',
  badge: (
    <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium bg-success/15 text-green-300/90 border border-success/25">
      <ShieldCheck size={12} />
      One-time admin setup
    </div>
  ),
  accentGradient: 'radial-gradient(ellipse at 80% 20%, rgba(22,163,74,0.14) 0%, transparent 55%)',
}

export function RegisterPage() {
  const navigate = useNavigate()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) })

  const { mutate, isPending, error, isSuccess } = useMutation({
    mutationFn: ({ email, password }: FormData) => registerUser(email, password),
    onSuccess: () => {
      setTimeout(() => navigate('/login', { replace: true }), 1800)
    },
  })

  const apiError = error
    ? ((error as ApiError).response?.data?.detail ?? 'Registration failed. Try again.')
    : null

  return (
    <AuthLayout panel={PANEL}>
      {isSuccess ? (
        <div className="text-center space-y-4">
          <div className="w-14 h-14 rounded-full bg-success-light flex items-center justify-center mx-auto">
            <ShieldCheck size={26} className="text-success" />
          </div>
          <div>
            <h2 className="text-xl font-semibold font-display text-fg mb-1">
              Admin account created
            </h2>
            <p className="text-sm text-fg-muted">Redirecting you to sign in…</p>
          </div>
        </div>
      ) : (
        <>
          <div className="mb-6">
            <h1 className="text-[2rem] font-semibold font-display text-fg mb-1.5 leading-tight">
              First time setup
            </h1>
            <p className="text-sm text-fg-muted">Create the initial admin account.</p>
          </div>

          <Alert variant="info" className="mb-5 text-xs">
            This endpoint is only accessible before any user exists. Once created, further
            registrations must go through the admin panel.
          </Alert>

          {apiError && (
            <Alert variant="danger" className="mb-5">
              {apiError}
            </Alert>
          )}

          <form
            onSubmit={handleSubmit((data) => mutate(data))}
            className="space-y-4"
            noValidate
          >
            <FormField label="Email address" htmlFor="email" error={errors.email?.message}>
              <Input
                id="email"
                {...register('email')}
                type="email"
                autoComplete="email"
                placeholder="admin@agency.com"
                error={!!errors.email}
              />
            </FormField>

            <FormField label="Password" htmlFor="password" error={errors.password?.message}>
              <PasswordInput
                id="password"
                {...register('password')}
                autoComplete="new-password"
                placeholder="Min. 8 characters"
                error={!!errors.password}
              />
            </FormField>

            <FormField
              label="Confirm password"
              htmlFor="confirmPassword"
              error={errors.confirmPassword?.message}
            >
              <PasswordInput
                id="confirmPassword"
                {...register('confirmPassword')}
                autoComplete="new-password"
                placeholder="••••••••"
                error={!!errors.confirmPassword}
              />
            </FormField>

            <Button type="submit" disabled={isPending} size="lg" className="w-full mt-2">
              {isPending ? (
                <>
                  <Spinner size="sm" className="text-primary-fg" />
                  Creating account…
                </>
              ) : (
                <>
                  Create admin account
                  <ArrowRight size={14} />
                </>
              )}
            </Button>
          </form>

          <p className="mt-6 text-xs text-center text-fg-muted">
            Already have an account?{' '}
            <Link to="/login" className="font-medium text-primary hover:underline">
              Sign in →
            </Link>
          </p>
        </>
      )}
    </AuthLayout>
  )
}
