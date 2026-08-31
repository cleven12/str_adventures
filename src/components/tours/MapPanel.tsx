'use client'

import { useEffect, useRef } from 'react'
import { MapPin } from 'lucide-react'
import 'maplibre-gl/dist/maplibre-gl.css'

export type ItineraryPoint = { day: number; lat: number; lng: number; name?: string | null }

export function MapPanel({ points }: { points: ItineraryPoint[] }) {
  const ref = useRef<HTMLDivElement>(null)
  const mapRef = useRef<import('maplibre-gl').Map | null>(null)

  useEffect(() => {
    if (!ref.current || mapRef.current || points.length === 0) return
    let active = true
    import('maplibre-gl').then((maplibregl) => {
      if (!active || !ref.current) return
      const map = new maplibregl.Map({
        container: ref.current,
        style: 'https://tiles.openfreemap.org/styles/liberty',
        center: [points[0].lng, points[0].lat],
        zoom: 9,
        attributionControl: false,
      })
      map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right')
      map.on('load', () => {
        const coordinates: [number, number][] = points.map((p) => [p.lng, p.lat])
        map.addSource('route', {
          type: 'geojson',
          data: { type: 'Feature', properties: {}, geometry: { type: 'LineString', coordinates } },
        })
        map.addLayer({
          id: 'route-line',
          type: 'line',
          source: 'route',
          paint: { 'line-color': '#bd4c14', 'line-width': 4 },
        })
        points.forEach((point, i) => {
          const el = document.createElement('button')
          el.className = 'map-pin'
          el.textContent = String(point.day ?? i + 1)
          el.setAttribute('aria-label', `Fly to day ${point.day ?? i + 1}`)
          el.onclick = () => map.flyTo({ center: [point.lng, point.lat], zoom: 11 })
          new maplibregl.Marker({ element: el }).setLngLat([point.lng, point.lat]).addTo(map)
        })
      })
      mapRef.current = map
    })
    return () => {
      active = false
      mapRef.current?.remove()
      mapRef.current = null
    }
  }, [points])

  if (points.length === 0) return null

  return (
    <div className="map-wrap">
      <div ref={ref} id="route-map" className="route-map" />
      <div className="map-caption">
        <span>
          <MapPin /> Route rendered from itinerary data
        </span>
        <span className="map-legend">
          1 — {points.length} day markers
        </span>
      </div>
    </div>
  )
}
