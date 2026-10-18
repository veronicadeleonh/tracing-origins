import { Suspense, lazy, useEffect, useState } from 'react'
import { Analytics } from '@vercel/analytics/react'
import App from './App.tsx'

// /#tokens: página de documentación de design tokens (carga aparte, solo si se pide).
const TokensPage = lazy(() => import('./components/TokensPage.tsx'))

export default function Root() {
  const [showTokens, setShowTokens] = useState(window.location.hash === '#tokens')
  useEffect(() => {
    const onHash = () => setShowTokens(window.location.hash === '#tokens')
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [])

  if (showTokens) {
    return (
      <Suspense fallback={null}>
        <TokensPage />
      </Suspense>
    )
  }
  return (
    <>
      <App />
      <Analytics />
    </>
  )
}
