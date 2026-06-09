import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation } from '@tanstack/react-query'
import { ArrowRight } from 'lucide-react'
import { loginUser, type ApiError } from '@/api/auth'
import { useAuthStore } from '@/store/authStore'
import { Alert, Button, FormField, Input, PasswordInput, Spinner } from '@/components/ui'
import { AuthLayout } from '@/components/auth/AuthLayout'

const schema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(1, 'Password is required'),
})
type FormData = z.infer<typeof schema>

const PANEL = {
  headline: (
    <>
      Manage
      <br />
      subscriptions
      <br />
      <span className="text-white/35">with precision.</span>
    </>
  ),
  tagline: "One hub for all your agency’s client plans, payments, and billing splits.",
  accentGradient: 'radial-gradient(ellipse at 15% 85%, rgba(37,99,235,0.18) 0%, transparent 55%)',
}

export function LoginPage() {
  const navigate = useNavigate()
  const login = useAuthStore((s) => s.login)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) })

  const { mutate, isPending, error } = useMutation({
    mutationFn: ({ email, password }: FormData) => loginUser(email, password),
    onSuccess: ({ token, user }) => {
      login(user, token.access_token)
      navigate('/dashboard', { replace: true })
    },
  })

  const apiError = error
    ? ((error as ApiError).response?.data?.detail ?? 'Sign in failed. Try again.')
    : null

  return (
    <AuthLayout panel={PANEL}>
      <div className="mb-8">
        <h1 className="text-[2rem] font-semibold font-display text-fg mb-1.5 leading-tight">
          Sign in
        </h1>
        <p className="text-sm text-fg-muted">Enter your credentials to continue.</p>
      </div>

      {apiError && (
        <Alert variant="danger" className="mb-5">
          {apiError}
        </Alert>
      )}

      <form onSubmit={handleSubmit((data) => mutate(data))} className="space-y-4" noValidate>
        <FormField label="Email address" htmlFor="email" error={errors.email?.message}>
          <Input
            id="email"
            {...register('email')}
            type="email"
            autoComplete="email"
            placeholder="you@agency.com"
            error={!!errors.email}
          />
        </FormField>

        <FormField label="Password" htmlFor="password" error={errors.password?.message}>
          <PasswordInput
            id="password"
            {...register('password')}
            autoComplete="current-password"
            placeholder="••••••••"
            error={!!errors.password}
          />
        </FormField>

        <Button type="submit" disabled={isPending} size="lg" className="w-full mt-2">
          {isPending ? (
            <>
              <Spinner size="sm" className="text-primary-fg" />
              Signing in…
            </>
          ) : (
            <>
              Sign in
              <ArrowRight size={14} />
            </>
          )}
        </Button>
      </form>

      <p className="mt-6 text-xs text-center text-fg-muted">
        First time?{' '}
        <Link to="/register" className="font-medium text-primary hover:underline">
          Set up admin account →
        </Link>
      </p>
    </AuthLayout>
  )
}
