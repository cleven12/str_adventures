import { redirect } from 'next/navigation'

// Superseded by /terms-and-conditions, which reads from the LegalPages
// collection instead of hardcoded copy. Kept as a redirect for old links.
export default function TermsRedirect() {
  redirect('/terms-and-conditions')
}
