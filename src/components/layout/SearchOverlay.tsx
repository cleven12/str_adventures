'use client'

import { useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { ArrowRight, Search, X } from 'lucide-react'

export type SearchItem = { title: string; href: string; image?: string | null }
export type SearchGroup = { label: string; seeAllHref: string; items: SearchItem[] }

export function SearchOverlay({ groups, onClose }: { groups: SearchGroup[]; onClose: () => void }) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [query, setQuery] = useState('')

  useEffect(() => {
    inputRef.current?.focus()
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const filtered = groups
    .map((group) => ({
      ...group,
      items: group.items.filter((item) => item.title.toLowerCase().includes(query.toLowerCase())).slice(0, 4),
    }))
    .filter((group) => group.items.length > 0)

  return (
    <div className="search-overlay" role="dialog" aria-modal="true" aria-label="Search Structured Adventures">
      <div className="search-modal">
        <div className="search-modal-head">
          <span className="eyebrow">Search the collection</span>
          <button onClick={onClose} aria-label="Close search">
            <X />
          </button>
        </div>
        <div className="global-search">
          <Search />
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Try “Kilimanjaro” or “safari”"
          />
        </div>
        <div className="search-results">
          {filtered.length === 0 && query && <p className="muted">No results for &ldquo;{query}&rdquo;.</p>}
          {filtered.map((group) => (
            <section key={group.label}>
              <div className="search-group-head">
                <h3>{group.label}</h3>
                <Link href={group.seeAllHref} onClick={onClose}>
                  See all results <ArrowRight />
                </Link>
              </div>
              <div className="search-result-list">
                {group.items.map((item) => (
                  <Link href={item.href} key={item.href} onClick={onClose}>
                    <span style={item.image ? { backgroundImage: `url(${item.image})` } : undefined} />
                    <strong>{item.title}</strong>
                    <ArrowRight />
                  </Link>
                ))}
              </div>
            </section>
          ))}
        </div>
      </div>
    </div>
  )
}
