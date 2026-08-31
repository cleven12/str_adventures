import { ChevronDown } from 'lucide-react'

export function FaqList({ items }: { items: { id?: string | number | null; question: string; answer: string }[] }) {
  if (items.length === 0) return null
  return (
    <div className="itinerary faq-list">
      {items.map((faq, i) => (
        <details key={faq.id ?? faq.question} open={i === 0}>
          <summary>
            <span>Q</span>
            {faq.question}
            <ChevronDown />
          </summary>
          <p>{faq.answer}</p>
        </details>
      ))}
    </div>
  )
}
