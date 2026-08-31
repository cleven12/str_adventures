export const primaryNav: [string, string][] = [
  ['About us', '/about'],
  ['Kilimanjaro', '/climbing-kilimanjaro'],
  ['Safaris', '/tanzania-safari'],
  ['Day trips', '/day-trips'],
  ['Destinations', '/destinations'],
  ['Travel info', '/blog'],
  ['Contact', '/contact'],
]

export const menuGroups: { label: string; links: [string, string][] }[] = [
  {
    label: 'Kilimanjaro',
    links: [
      ['Climbing Kilimanjaro', '/climbing-kilimanjaro'],
      ['All climbs & safaris', '/tours'],
      ['Guides', '/guides'],
    ],
  },
  {
    label: 'Safaris',
    links: [
      ['Tanzania safari', '/tanzania-safari'],
      ['Day trips', '/day-trips'],
      ['Destinations', '/destinations'],
    ],
  },
  {
    label: 'Travel info',
    links: [
      ['Guides & stories', '/blog'],
      ['Traveler reviews', '/reviews'],
      ['About us', '/about'],
      ['Contact', '/contact'],
    ],
  },
]
