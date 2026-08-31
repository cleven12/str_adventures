'use client'

import { useRef } from 'react'
import { motion, useInView } from 'framer-motion'

const marks = ['TATO', 'TANZANIA TOURISM BOARD', 'TRAVELIFE', 'KILIMANJARO PARKS']

export function Certifications() {
  const ref = useRef(null)
  const inView = useInView(ref, { once: true, amount: 0.35 })
  return (
    <section className="certifications" ref={ref}>
      <div>
        <span className="eyebrow">Travel with confidence</span>
        <h2>Trusted by people who care about place.</h2>
      </div>
      <motion.div
        className="certification-row"
        initial={{ opacity: 0, y: 16 }}
        animate={inView ? { opacity: 1, y: 0 } : {}}
        transition={{ duration: 0.7 }}
      >
        {marks.map((mark) => (
          <span key={mark}>{mark}</span>
        ))}
      </motion.div>
    </section>
  )
}
