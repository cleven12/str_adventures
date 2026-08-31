/** Renders one or more JSON-LD `<script>` tags. Falsy entries are dropped. */
export function JsonLd({ data }: { data: object | null | (object | null)[] }) {
  const items = (Array.isArray(data) ? data : [data]).filter((item): item is object => Boolean(item))
  if (items.length === 0) return null

  return (
    <>
      {items.map((item, i) => (
        <script key={i} type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(item) }} />
      ))}
    </>
  )
}
