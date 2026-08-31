import { CalendarDays, Mail, MapPin, Phone } from 'lucide-react'
import { PageShell } from '../../../components/layout/PageShell'
import { Breadcrumbs } from '../../../components/Breadcrumbs'
import { ContactForm } from '../../../components/forms/ContactForm'
import { ExploreMesh } from '../../../components/ExploreMesh'

export const revalidate = 3600

const details = [
  [MapPin, 'Address', 'Arusha, Tanzania'],
  [Phone, 'Phone', '+255 754 465 025'],
  [Mail, 'Email', 'info@structuredadventures.com'],
  [CalendarDays, 'Hours', 'Mon–Sat · 7:00 AM – 8:00 PM'],
] as const

export default async function ContactPage() {
  return (
    <PageShell>
      <main className="page contact">
        <Breadcrumbs items={['Contact']} />
        <div className="contact-grid">
          <div>
            <span className="eyebrow">Say hello</span>
            <h1>Get in touch</h1>
            <p>We&apos;re here to help you plan the adventure you&apos;ve been waiting for.</p>
            <div className="contact-details">
              {details.map(([Icon, label, value]) => (
                <div key={label}>
                  <Icon />
                  <span>
                    <small>{label}</small>
                    <strong>{value}</strong>
                  </span>
                </div>
              ))}
            </div>
          </div>
          <ContactForm />
        </div>
        <div className="contact-map">
          <MapPin />
          <span>Arusha, Tanzania</span>
        </div>
        <ExploreMesh />
      </main>
    </PageShell>
  )
}
