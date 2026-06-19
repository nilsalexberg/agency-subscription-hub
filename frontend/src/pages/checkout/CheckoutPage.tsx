import { type ReactNode, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { CreditCard, QrCode, ArrowRight, AlertCircle } from 'lucide-react'
import { Button, Spinner } from '@/components/ui'
import { HubLogo } from '@/components/auth/HubLogo'

type PaymentMethod = 'credit_card' | 'boleto_pix'

interface CheckoutData {
  client_name: string
  client_email: string
  client_document: string
  plan_name: string
  plan_description: string | null
  plan_price: number
  plan_billing_cycle: 'weekly' | 'monthly' | 'yearly'
}

const BILLING_CYCLE_LABEL: Record<string, string> = {
  weekly: 'semana',
  monthly: 'mês',
  yearly: 'ano',
}

async function fetchCheckoutData(token: string): Promise<CheckoutData> {
  const res = await fetch(`/api/checkout/${token}`)
  if (!res.ok) throw new Error('Checkout not found')
  return res.json() as Promise<CheckoutData>
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)
}

export function CheckoutPage() {
  const { token } = useParams<{ token: string }>()
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>('credit_card')

  const { data, isPending, isError } = useQuery({
    queryKey: ['checkout', token],
    queryFn: () => fetchCheckoutData(token!),
    enabled: !!token,
    retry: false,
  })

  return (
    <div className="min-h-screen bg-bg flex flex-col items-center justify-center p-6">
      <div className="flex items-center gap-2.5 mb-10">
        <div className="bg-primary w-8 h-8 rounded-lg flex items-center justify-center">
          <HubLogo size={16} />
        </div>
        <span className="font-semibold text-sm tracking-wide font-display text-fg">
          Subscription Hub
        </span>
      </div>

      <div className="w-full max-w-md">
        {isPending && (
          <div className="flex justify-center py-16">
            <Spinner />
          </div>
        )}

        {isError && (
          <div className="rounded-xl border border-danger/30 bg-danger-light px-6 py-10 text-center space-y-3">
            <AlertCircle size={32} className="text-danger mx-auto" />
            <p className="font-semibold text-fg">Link inválido</p>
            <p className="text-sm text-fg-secondary">
              Este link de checkout não existe ou expirou.
            </p>
          </div>
        )}

        {data && (
          <div className="rounded-xl border border-border bg-surface shadow-sm overflow-hidden">
            <div className="bg-fg px-6 py-6">
              <p className="text-[10px] font-semibold text-white/35 uppercase tracking-widest mb-2">
                Plano
              </p>
              <h1 className="text-xl font-semibold font-display text-white leading-tight">
                {data.plan_name}
              </h1>
              {data.plan_description && (
                <p className="text-sm text-white/45 mt-1.5 leading-relaxed">
                  {data.plan_description}
                </p>
              )}
              <div className="mt-5 flex items-baseline gap-1">
                <span className="text-3xl font-bold font-display text-white">
                  {formatCurrency(data.plan_price)}
                </span>
                <span className="text-sm text-white/35">
                  / {BILLING_CYCLE_LABEL[data.plan_billing_cycle]}
                </span>
              </div>
            </div>

            <div className="px-6 py-5 space-y-5">
              <div>
                <p className="text-sm font-medium text-fg">
                  Olá,{' '}
                  <span className="text-primary">{data.client_name}</span>
                </p>
                <p className="text-xs text-fg-muted mt-0.5">{data.client_email}</p>
              </div>

              <div className="border-t border-border" />

              <div className="space-y-2">
                <p className="text-[10px] font-semibold text-fg-muted uppercase tracking-widest">
                  Forma de pagamento
                </p>
                <PaymentMethodOption
                  id="credit_card"
                  label="Cartão de Crédito"
                  icon={<CreditCard size={16} />}
                  selected={paymentMethod === 'credit_card'}
                  onSelect={() => setPaymentMethod('credit_card')}
                />
                <PaymentMethodOption
                  id="boleto_pix"
                  label="Boleto / PIX"
                  icon={<QrCode size={16} />}
                  selected={paymentMethod === 'boleto_pix'}
                  onSelect={() => setPaymentMethod('boleto_pix')}
                />
              </div>

              <Button size="lg" className="w-full">
                Continuar
                <ArrowRight size={14} />
              </Button>
            </div>
          </div>
        )}
      </div>

      <p className="mt-8 text-xs text-fg-muted">Pagamento seguro · Subscription Hub</p>
    </div>
  )
}

interface PaymentMethodOptionProps {
  id: string
  label: string
  icon: ReactNode
  selected: boolean
  onSelect: () => void
}

function PaymentMethodOption({ id, label, icon, selected, onSelect }: PaymentMethodOptionProps) {
  return (
    <label
      htmlFor={id}
      className={[
        'flex items-center gap-3 px-4 py-3 rounded-lg border cursor-pointer transition-all duration-150',
        selected
          ? 'border-primary bg-primary/5 text-fg'
          : 'border-border bg-surface text-fg-secondary hover:border-border-strong hover:bg-surface-raised',
      ].join(' ')}
    >
      <input
        id={id}
        type="radio"
        name="payment_method"
        value={id}
        checked={selected}
        onChange={onSelect}
        className="sr-only"
      />
      <span className={selected ? 'text-primary' : 'text-fg-muted'}>{icon}</span>
      <span className="font-medium text-sm flex-1">{label}</span>
      <span
        className={[
          'w-4 h-4 rounded-full border-2 flex items-center justify-center transition-all',
          selected ? 'border-primary' : 'border-border-strong',
        ].join(' ')}
      >
        {selected && <span className="w-2 h-2 rounded-full bg-primary" />}
      </span>
    </label>
  )
}
