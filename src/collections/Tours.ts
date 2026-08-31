import type { CollectionConfig } from 'payload'
import { lexicalEditor } from '@payloadcms/richtext-lexical'
import { slugField, seoFields } from '../lib/seoFields'

// CATALOG context. Deliberately no Commerce fields here — no price gateway,
// no booking state machine, no payment status. "Price from" is display-only
// copy; conversion happens via inquiry (WhatsApp / form), not checkout.
export const Tours: CollectionConfig = {
  slug: 'tours',
  labels: { singular: 'Tour', plural: 'Tours' },
  admin: {
    useAsTitle: 'title',
    defaultColumns: ['title', 'category', 'priceFrom', 'isActive', '_status'],
    description:
      'A single bookable trip — a Kilimanjaro route, a safari package, a beach stay. This is the main content type on the site; everything else (Guides, Articles, Reviews) links back to Tours.',
  },
  versions: {
    drafts: { autosave: { interval: 2000 } },
    maxPerDoc: 20,
  },
  access: { read: () => true },
  fields: [
    { name: 'title', type: 'text', required: true, admin: { description: 'The tour name, shown everywhere — cards, page title, browser tab.' } },
    slugField('title'),
    {
      name: 'category',
      type: 'relationship',
      relationTo: 'categories',
      required: true,
      admin: { description: 'The destination this tour belongs to (Kilimanjaro, Serengeti, Zanzibar, ...).' },
    },
    {
      name: 'durationDays',
      type: 'number',
      min: 1,
      admin: { description: 'How many days the trip lasts, e.g. 8. Shown next to the title and used for "X days" text throughout the site.' },
    },
    {
      name: 'priceFrom',
      type: 'number',
      admin: { description: 'Display-only "from" price. Not a transactable amount — no payment flow attached.' },
    },
    {
      name: 'groupSize',
      type: 'group',
      admin: { description: 'The min/max number of travelers for a single departure.' },
      fields: [
        { name: 'min', type: 'number', defaultValue: 1, admin: { description: 'Minimum travelers to run this tour.' } },
        { name: 'max', type: 'number', admin: { description: 'Maximum travelers per departure/group.' } },
      ],
    },
    {
      name: 'gallery',
      type: 'array',
      admin: { description: 'Photos shown in the tour\'s image gallery. Add as many as you like — the first one is used as the main hero image.' },
      fields: [{ name: 'image', type: 'upload', relationTo: 'media', required: true }],
    },
    {
      name: 'itinerary',
      type: 'array',
      admin: { description: 'The day-by-day plan. Add one entry per day, in order — this drives both the itinerary list and the route map on the tour page.' },
      fields: [
        { name: 'day', type: 'number', required: true, admin: { description: 'Day number, e.g. 1, 2, 3.' } },
        { name: 'title', type: 'text', required: true, admin: { description: 'Short heading for this day, e.g. "Moshi to Machame Camp".' } },
        { name: 'description', type: 'textarea', admin: { description: 'What happens on this day.' } },
        {
          name: 'location',
          type: 'group',
          fields: [
            { name: 'lat', type: 'number', admin: { description: 'Latitude of this day\'s location.' } },
            { name: 'lng', type: 'number', admin: { description: 'Longitude of this day\'s location.' } },
            { name: 'name', type: 'text', admin: { description: 'Place name shown as a label on the map pin.' } },
          ],
          admin: { description: 'Feeds the MapLibre route on the tour detail page. Leave blank if you don\'t have coordinates for this day — the map just skips it.' },
        },
        {
          name: 'activities',
          type: 'array',
          admin: { description: 'Bullet-point list of what happens this day (optional, in addition to the description above).' },
          fields: [{ name: 'activity', type: 'text', required: true }],
        },
        { name: 'accommodation', type: 'text', admin: { description: 'Where travelers sleep that night, e.g. "Camping" or a lodge name.' } },
        { name: 'meals', type: 'text', admin: { description: 'Meals included that day, e.g. "Breakfast, Lunch, Dinner".' } },
      ],
    },
    {
      name: 'faqs',
      type: 'array',
      fields: [
        { name: 'question', type: 'text', required: true },
        { name: 'answer', type: 'textarea', required: true },
      ],
      admin: { description: 'Common questions shown on the tour page. Rendered as FAQPage schema for Google too, so real questions people ask help SEO.' },
    },
    {
      type: 'collapsible',
      label: 'Promo & pricing',
      fields: [
        { name: 'promoSuperTitle', type: 'text', admin: { description: 'Small label above the promo title, e.g. a route name.' } },
        { name: 'promoTitle', type: 'text', admin: { description: 'Short marketing headline shown at the top of the tour page.' } },
        { name: 'promoSubtitle', type: 'textarea', admin: { description: 'One-line pitch shown below the promo title.' } },
        { name: 'oldPrice', type: 'number', admin: { description: 'Struck-through reference price, for discount display. Display-only, like priceFrom.' } },
        { name: 'discountTitle', type: 'text', admin: { description: 'e.g. "10% Deposit Secures Your Safari Date".' } },
        { name: 'departureLocation', type: 'text', admin: { description: 'Where the trip starts, e.g. "Moshi".' } },
        { name: 'returnLocation', type: 'text', admin: { description: 'Where the trip ends, e.g. "Moshi or Arusha".' } },
        { name: 'bookingLinkOverride', type: 'text', admin: { description: 'If set, the "Enquire now" CTA links here instead of /booking.' } },
      ],
    },
    {
      type: 'collapsible',
      label: 'Price includes / excludes',
      fields: [
        {
          name: 'priceIncludes',
          type: 'array',
          admin: { description: 'What\'s included in the price — one line per item, shown as a checklist.' },
          fields: [{ name: 'item', type: 'text', required: true }],
        },
        {
          name: 'priceExcludes',
          type: 'array',
          admin: { description: 'What\'s NOT included — flights, visas, tips, etc. Setting realistic expectations here reduces support questions later.' },
          fields: [{ name: 'item', type: 'text', required: true }],
        },
      ],
    },
    {
      type: 'collapsible',
      label: 'Start dates',
      fields: [
        { name: 'isEverydayTour', type: 'checkbox', defaultValue: false, admin: { description: 'Check this if the tour departs every day (like a day trip) instead of on fixed dates.' } },
        {
          name: 'everydayStartTime',
          type: 'text',
          admin: { description: 'e.g. "06:00". Overrides startDates when isEverydayTour is set.', condition: (_, siblingData) => Boolean(siblingData?.isEverydayTour) },
        },
        {
          name: 'startDates',
          type: 'array',
          admin: { description: 'Fixed departure dates, if this isn\'t an everyday tour.', condition: (_, siblingData) => !siblingData?.isEverydayTour },
          fields: [
            { name: 'date', type: 'date', required: true },
            { name: 'time', type: 'text', admin: { description: 'Departure time, e.g. "06:00".' } },
          ],
        },
      ],
    },
    {
      type: 'collapsible',
      label: 'Additional pricing & info',
      fields: [
        {
          name: 'additionalPrices',
          type: 'array',
          admin: { description: 'Optional add-ons with their own price, e.g. "Private airport transfer upgrade — $25".' },
          fields: [
            { name: 'title', type: 'text', required: true },
            { name: 'price', type: 'number', required: true },
          ],
        },
        {
          name: 'additionalInfoItems',
          type: 'array',
          admin: { description: 'Extra info blocks shown on the page, each with its own heading — e.g. "Best time to go".' },
          fields: [
            { name: 'title', type: 'text', required: true },
            { name: 'description', type: 'textarea' },
          ],
        },
        {
          name: 'complementaries',
          type: 'array',
          admin: { description: 'Small extras included free with the trip, e.g. "Welcome drink".' },
          fields: [
            { name: 'title', type: 'text', required: true },
            { name: 'description', type: 'textarea' },
          ],
        },
      ],
    },
    {
      type: 'collapsible',
      label: 'Map & custom tab',
      fields: [
        {
          name: 'mapEmbedUrl',
          type: 'text',
          admin: { description: 'Google Maps iframe src, as an alternative to the itinerary day coordinates.' },
        },
        { name: 'customTabTitle', type: 'text', admin: { description: 'Adds an extra tab to the tour detail page.' } },
        { name: 'customTabContent', type: 'richText', editor: lexicalEditor(), admin: { description: 'Content shown in that extra tab.' } },
      ],
    },
    { name: 'moreInfo', type: 'richText', editor: lexicalEditor(), admin: { description: 'Rendered in an "Additional info" section — trip logistics, what to bring, etc.' } },
    { name: 'content', type: 'richText', editor: lexicalEditor(), admin: { description: 'Optional longer-form write-up about the tour, if you want more than the itinerary/FAQs tell.' } },
    ...seoFields,
    {
      name: 'isActive',
      type: 'checkbox',
      defaultValue: true,
      admin: { position: 'sidebar', description: 'Uncheck to hide this tour from the live site without deleting it (e.g. a seasonal or retired trip).' },
    },
    { name: 'publishDate', type: 'date', admin: { position: 'sidebar', description: 'Shown as the publish date, if your page design displays one.' } },
  ],
}
