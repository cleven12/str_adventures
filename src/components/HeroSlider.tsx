'use client'

import { useEffect, useState } from 'react'

/** Crossfading background image slider — mirrors the fade-slider hero pattern used by Altezza Travel. */
export function HeroSlider({ images, intervalMs = 5000 }: { images: string[]; intervalMs?: number }) {
  const [index, setIndex] = useState(0)

  useEffect(() => {
    if (images.length <= 1) return
    const id = setInterval(() => setIndex((i) => (i + 1) % images.length), intervalMs)
    return () => clearInterval(id)
  }, [images.length, intervalMs])

  return (
    <div className="hero-slider" aria-hidden="true">
      {images.map((src, i) => (
        <div
          key={src}
          className={`hero-slide ${i === index ? 'is-active' : ''}`}
          style={{ backgroundImage: `url(${src})` }}
        />
      ))}
    </div>
  )
}
