import { Header } from './Header'
import { Footer } from './Footer'

export function PageShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="sa-root">
      <Header />
      {children}
      <Footer />
    </div>
  )
}
