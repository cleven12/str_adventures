'use client'

import { useState } from 'react'
import { ArrowRight, Check } from 'lucide-react'
import { useFormSubmit } from './useFormSubmit'

const steps = ['Trip details', 'Traveler info', 'Review & submit']

type Tour = { id: number; title: string }

export function BookingForm({ tours }: { tours: Tour[] }) {
  const [step, setStep] = useState(1)
  const { status, submit } = useFormSubmit()
  const [data, setData] = useState({
    tourId: tours[0] ? String(tours[0].id) : '',
    preferredDate: '',
    travelers: '',
    firstName: '',
    lastName: '',
    email: '',
    whatsapp: '',
    notes: '',
  })

  if (status === 'success') {
    return <p className="form-status success">Thanks — your trip request is in. We&apos;ll follow up within 24 hours.</p>
  }

  const selectedTour = tours.find((t) => String(t.id) === data.tourId)

  return (
    <>
      <div className="progress">
        {steps.map((label, i) => (
          <div className={step > i ? 'done' : ''} key={label}>
            <span>{String(i + 1).padStart(2, '0')}</span>
            {label}
          </div>
        ))}
      </div>
      <div className="booking-form">
        {step === 1 && (
          <>
            <h2>Trip details</h2>
            <p className="muted">What kind of adventure are you looking for?</p>
            <label>
              Selected tour
              <select value={data.tourId} onChange={(e) => setData({ ...data, tourId: e.target.value })}>
                {tours.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.title}
                  </option>
                ))}
              </select>
            </label>
            <div className="form-row">
              <label>
                Preferred date
                <input
                  type="date"
                  value={data.preferredDate}
                  onChange={(e) => setData({ ...data, preferredDate: e.target.value })}
                />
              </label>
              <label>
                Travelers
                <select value={data.travelers} onChange={(e) => setData({ ...data, travelers: e.target.value })}>
                  <option value="">Select</option>
                  <option>1 traveler</option>
                  <option>2 travelers</option>
                  <option>3 travelers</option>
                  <option>4+ travelers</option>
                </select>
              </label>
            </div>
            <label>
              Anything else we should know?
              <textarea
                rows={4}
                placeholder="Your interests, preferences, or questions..."
                value={data.notes}
                onChange={(e) => setData({ ...data, notes: e.target.value })}
              />
            </label>
          </>
        )}
        {step === 2 && (
          <>
            <h2>Traveler info</h2>
            <p className="muted">Who will be joining this adventure?</p>
            <div className="form-row">
              <label>
                First name
                <input value={data.firstName} onChange={(e) => setData({ ...data, firstName: e.target.value })} />
              </label>
              <label>
                Last name
                <input value={data.lastName} onChange={(e) => setData({ ...data, lastName: e.target.value })} />
              </label>
            </div>
            <label>
              Email address
              <input
                type="email"
                placeholder="you@example.com"
                value={data.email}
                onChange={(e) => setData({ ...data, email: e.target.value })}
              />
            </label>
            <label>
              WhatsApp number
              <input
                placeholder="+1 555 000 0000"
                value={data.whatsapp}
                onChange={(e) => setData({ ...data, whatsapp: e.target.value })}
              />
            </label>
          </>
        )}
        {step === 3 && (
          <>
            <h2>Review & submit</h2>
            <p className="muted">Take a look, then send your inquiry. We&apos;ll be in touch within 24 hours.</p>
            <div className="summary">
              <div>
                <span className="eyebrow">Selected adventure</span>
                <h3>{selectedTour?.title ?? 'No tour selected'}</h3>
                <p>
                  {data.travelers || 'Travelers TBD'} {data.preferredDate ? `· ${data.preferredDate}` : ''}
                </p>
              </div>
            </div>
            <div className="review-line">
              <Check /> Your dates are flexible until confirmed by our team.
            </div>
          </>
        )}
        <div className="form-actions">
          {step > 1 && (
            <button className="button button-outline" onClick={() => setStep(step - 1)} type="button">
              Back
            </button>
          )}
          {step < 3 ? (
            <button className="button" onClick={() => setStep(step + 1)} type="button">
              Continue <ArrowRight />
            </button>
          ) : (
            <button
              className="button"
              onClick={() =>
                submit({
                  source: 'booking',
                  name: `${data.firstName} ${data.lastName}`.trim(),
                  email: data.email,
                  whatsapp: data.whatsapp,
                  tour: data.tourId,
                  preferredDate: data.preferredDate,
                  travelers: data.travelers,
                  message: data.notes,
                })
              }
              disabled={status === 'submitting'}
              type="button"
            >
              {status === 'submitting' ? 'Sending…' : 'Send inquiry'} <ArrowRight />
            </button>
          )}
        </div>
        {status === 'error' && <p className="form-status error">Something went wrong — please try again.</p>}
      </div>
    </>
  )
}
