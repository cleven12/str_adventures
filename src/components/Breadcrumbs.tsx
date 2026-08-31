import Link from 'next/link'
import { ChevronRight } from 'lucide-react'

export function Breadcrumbs({ items }: { items: string[] }) {
  return (
    <nav className="breadcrumbs" aria-label="Breadcrumb">
      <Link href="/">Home</Link>
      {items.map((item) => (
        <span key={item}>
          <ChevronRight />
          {item}
        </span>
      ))}
    </nav>
  )
}
