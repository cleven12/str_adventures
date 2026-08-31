import { getPayload } from '../../../lib/getPayload'
import { PageShell } from '../../../components/layout/PageShell'
import { Breadcrumbs } from '../../../components/Breadcrumbs'
import { BookingForm } from '../../../components/forms/BookingForm'
import { ExploreMesh } from '../../../components/ExploreMesh'

export const revalidate = 3600

async function getTours() {
  const payload = await getPayload()
  const tours = await payload.find({ collection: 'tours', where: { isActive: { equals: true } }, limit: 100 })
  return tours.docs.map((t) => ({ id: t.id, title: t.title }))
}

export default async function BookingPage() {
  const tours = await getTours()

  return (
    <PageShell>
      <main className="page booking">
        <Breadcrumbs items={['Plan your trip']} />
        <div className="booking-head">
          <span className="eyebrow">Start planning</span>
          <h1>Make it yours.</h1>
          <p>Tell us a little about the journey you&apos;re imagining.</p>
        </div>
        <BookingForm tours={tours} />
        <ExploreMesh />
      </main>
    </PageShell>
  )
}
