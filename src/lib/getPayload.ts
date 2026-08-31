import { getPayload as getPayloadInstance } from 'payload'
import config from '../payload.config'

let cached: ReturnType<typeof getPayloadInstance> | null = null

/** Cached Payload local API — avoids re-initializing per request in dev. */
export async function getPayload() {
  if (!cached) {
    cached = getPayloadInstance({ config })
  }
  return cached
}
