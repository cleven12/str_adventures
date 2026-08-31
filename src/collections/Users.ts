import type { CollectionConfig } from 'payload'

export const Users: CollectionConfig = {
  slug: 'users',
  auth: true,
  admin: {
    useAsTitle: 'email',
    description: 'Staff accounts for this admin panel — not customers. Only existing admins can create new accounts.',
  },
  access: {
    read: ({ req }) => Boolean(req.user),
    create: ({ req }) => req.user?.role === 'admin',
    update: ({ req }) => {
      if (!req.user) return false
      if (req.user.role === 'admin') return true
      // Editors can update their own account (e.g. change their password) but not others.
      return { id: { equals: req.user.id } }
    },
    delete: ({ req }) => req.user?.role === 'admin',
  },
  fields: [
    {
      name: 'role',
      type: 'select',
      options: ['admin', 'editor'],
      defaultValue: 'editor',
      required: true,
      admin: {
        description:
          '"Editor" can manage Tours/Guides/Articles/etc. — everyday content work. "Admin" can additionally create/remove staff accounts and change site Settings. Most staff should be Editor.',
      },
    },
  ],
}
