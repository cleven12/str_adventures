'use client'

import { ArrowRight } from 'lucide-react'
import { useFormSubmit } from './useFormSubmit'

export function ContactForm() {
  const { status, submit } = useFormSubmit()

  if (status === 'success') {
    return <p className="form-status success">Thanks — we&apos;ll be in touch within 24 hours.</p>
  }

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        const fd = new FormData(e.currentTarget)
        submit({
          source: 'contact',
          name: String(fd.get('name') ?? ''),
          email: String(fd.get('email') ?? ''),
          whatsapp: String(fd.get('whatsapp') ?? ''),
          message: String(fd.get('message') ?? ''),
        })
      }}
    >
      <div className="form-row">
        <input name="name" aria-label="Your name" placeholder="Your name" required />
        <input name="email" aria-label="Email address" placeholder="Email address" type="email" required />
      </div>
      <input name="whatsapp" aria-label="WhatsApp number" placeholder="WhatsApp number" />
      <textarea name="message" aria-label="Your message" placeholder="Tell us about your trip" rows={5} required />
      <button className="button" type="submit" disabled={status === 'submitting'}>
        {status === 'submitting' ? 'Sending…' : 'Send inquiry'} <ArrowRight />
      </button>
      {status === 'error' && <p className="form-status error">Something went wrong — please try again.</p>}
    </form>
  )
}
