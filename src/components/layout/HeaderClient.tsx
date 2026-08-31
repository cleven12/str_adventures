'use client'

import { useState } from 'react'
import Link from 'next/link'
import { ArrowRight, ChevronDown, Menu, Search, Star, X } from 'lucide-react'
import { primaryNav, menuGroups } from './nav-data'
import { SearchOverlay, type SearchGroup } from './SearchOverlay'

export function HeaderClient({
  searchGroups,
  reviewSummary,
}: {
  searchGroups: SearchGroup[]
  reviewSummary: { count: number; average: number } | null
}) {
  const [open, setOpen] = useState(false)
  const [searchOpen, setSearchOpen] = useState(false)
  const [expanded, setExpanded] = useState<string | null>(null)
  const dropdowns = new Map(menuGroups.map((group) => [group.label, group.links]))

  return (
    <>
      <div className="topbar">
        <div className="topbar-left">
          <span>+255 754 465 025</span>
          <span>info@structuredadventures.com</span>
          <span className="top-location">Kilimanjaro, Tanzania</span>
        </div>
        <div className="topbar-right">
          {reviewSummary && (
            <Link className="topbar-rating" href="/reviews">
              <Star fill="#e7b18a" />
              {reviewSummary.average.toFixed(1)} · {reviewSummary.count} reviews
            </Link>
          )}
          <span className="topbar-pay">VISA · MC · M-PESA</span>
        </div>
      </div>
      <header className="header">
        <Link href="/" className="brand">
          <img
            src="https://structuredadventures.com/wp-content/uploads/2025/10/LOGO-STRUCTURED-ADVENTURES.png"
            alt="Structured Adventures"
            className="brand-logo"
          />
        </Link>
        <nav className="desktop-nav" aria-label="Primary navigation">
          {primaryNav.map(([label, href]) => (
            <div className="nav-item" key={`${label}-${href}`}>
              <Link href={href}>
                {label}
                {dropdowns.has(label) && <ChevronDown />}
              </Link>
              {dropdowns.has(label) && (
                <div className="nav-dropdown">
                  {dropdowns.get(label)?.map(([childLabel, childHref]) => (
                    <Link href={childHref} key={childLabel}>
                      {childLabel}
                      <ArrowRight />
                    </Link>
                  ))}
                </div>
              )}
            </div>
          ))}
        </nav>
        <div className="header-actions">
          <button className="search-trigger" onClick={() => setSearchOpen(true)} aria-label="Open search">
            <Search />
          </button>
          <Link className="button button-small" href="/booking">
            Plan my trip
          </Link>
        </div>
        <button className="mobile-menu" onClick={() => setOpen(!open)} aria-label="Toggle menu" aria-expanded={open}>
          {open ? <X /> : <Menu />}
        </button>
      </header>
      {open && (
        <nav className="mobile-nav">
          {menuGroups.map((group) => (
            <div key={group.label} className="mobile-group">
              <button
                onClick={() => setExpanded(expanded === group.label ? null : group.label)}
                aria-expanded={expanded === group.label}
              >
                {group.label}
                <ChevronDown />
              </button>
              {expanded === group.label && (
                <div className="mobile-subnav">
                  {group.links.map(([label, href]) => (
                    <Link key={label} href={href} onClick={() => setOpen(false)}>
                      {label}
                    </Link>
                  ))}
                </div>
              )}
            </div>
          ))}
          <Link href="/destinations" onClick={() => setOpen(false)}>
            Destinations
          </Link>
          <Link href="/about" onClick={() => setOpen(false)}>
            About us
          </Link>
          <Link className="button" href="/booking">
            Plan my trip
          </Link>
        </nav>
      )}
      {searchOpen && <SearchOverlay groups={searchGroups} onClose={() => setSearchOpen(false)} />}
    </>
  )
}
