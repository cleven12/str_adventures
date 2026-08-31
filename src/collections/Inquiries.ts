import type { CollectionConfig } from 'payload'

// TRUST/CONVERSION context. Every "Send inquiry" submission from the
// hardcoded /contact and /booking pages lands here — there is no
// CMS-configurable form builder; those two pages have a fixed field set
// baked into the frontend, and this collection just stores what visitors
// send. No payment fields: this build has no checkout, conversion happens
// via WhatsApp/email follow-up after an inquiry comes in.
export const Inquiries: CollectionConfig = {
  slug: 'inquiries',
  labels: { singular: 'Inquiry', plural: 'Inquiries' },
  admin: {
    useAsTitle: 'name',
    defaultColumns: ['name', 'email', 'source', 'tour', 'status', 'createdAt'],
    description:
      'Every submission from the Contact and Booking pages on the live site. Nothing to configure here — just follow up and update Status as you work through them.',
  },
  access: {
    // The public Contact/Booking forms POST here without logging in.
    create: () => true,
    // Only staff can see submitted contact details (name, email, message).
    read: ({ req }) => Boolean(req.user),
  },
  fields: [
    {
      name: 'source',
      type: 'select',
      required: true,
      options: [
        { label: 'Contact form', value: 'contact' },
        { label: 'Booking request', value: 'booking' },
      ],
      admin: { description: 'Which page this came from — set automatically, not editable by the visitor.' },
    },
    { name: 'name', type: 'text', required: true, admin: { description: "The visitor's full name." } },
    { name: 'email', type: 'email', required: true, admin: { description: 'Reply-to address for following up.' } },
    { name: 'whatsapp', type: 'text', admin: { description: 'Optional WhatsApp/phone number, if they gave one.' } },
    {
      name: 'tour',
      type: 'relationship',
      relationTo: 'tours',
      admin: {
        description: 'Which tour they were asking about — only set on Booking requests, blank for general Contact messages.',
        condition: (data) => data?.source === 'booking',
      },
    },
    { name: 'preferredDate', type: 'text', admin: { description: 'Their preferred travel date, as typed — not a validated calendar date.', condition: (data) => data?.source === 'booking' } },
    { name: 'travelers', type: 'text', admin: { description: 'Party size, as selected on the Booking form.', condition: (data) => data?.source === 'booking' } },
    { name: 'message', type: 'textarea', admin: { description: 'Their message or any extra notes they added.' } },
    {
      name: 'status',
      type: 'select',
      defaultValue: 'new',
      options: [
        { label: 'New', value: 'new' },
        { label: 'Contacted', value: 'contacted' },
        { label: 'Closed', value: 'closed' },
      ],
      admin: {
        position: 'sidebar',
        description: 'For your own tracking only — the visitor never sees this. Update it as you follow up.',
      },
    },
  ],
}
