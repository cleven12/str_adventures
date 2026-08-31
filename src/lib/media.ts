import type { Media } from '../payload-types'

/** Payload relationship fields resolve to either an id or the populated doc — normalize to a URL. */
export function mediaUrl(media?: (number | Media) | null): string | null {
  if (!media || typeof media === 'number') return null
  return media.url ?? null
}
