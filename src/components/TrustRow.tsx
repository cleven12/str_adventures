import { Check, Leaf, Phone, ShieldCheck } from 'lucide-react'

const items = [
  [ShieldCheck, 'Locally Owned'],
  [Check, 'Best Price Guarantee'],
  [Phone, '24/7 Support'],
  [Leaf, 'Responsible Tourism'],
] as const

export function TrustRow() {
  return (
    <div className="trust-row">
      {items.map(([Icon, label]) => (
        <div key={label}>
          <Icon />
          <span>{label}</span>
        </div>
      ))}
    </div>
  )
}
