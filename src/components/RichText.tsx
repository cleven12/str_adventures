import { RichText as LexicalRichText } from '@payloadcms/richtext-lexical/react'

export function RichText({ data }: { data: unknown }) {
  if (!data) return null
  return <LexicalRichText data={data as never} />
}
