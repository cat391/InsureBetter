import { useState, useEffect, useRef } from 'react'
import LandingPage from './components/LandingPage.jsx'
import UploadDocumentsPage from './components/UploadDocumentsPage.jsx'
import ManualEntryPage from './components/ManualEntryPage.jsx'
import AppealResultPage from './components/AppealResultPage.jsx'

function Breadcrumb({ page }) {
  const steps = [
    { label: 'Get Started', active: true },
    { label: 'Enter Info', active: page === 'upload' || page === 'manual' || page === 'appeal' },
    { label: 'Your Appeal', active: page === 'appeal' },
  ]

  return (
    <div className="flex items-center gap-1.5 text-xs flex-shrink-0">
      {steps.map((step, i) => (
        <span key={step.label} className="flex items-center gap-1.5">
          {i > 0 && <span style={{ color: '#D8CCC4' }}>›</span>}
          <span style={{
            color: step.active ? '#5C4033' : '#C9B99A',
            fontWeight: step.active && i === steps.filter(s => s.active).length - 1 ? 600 : 400,
          }}>
            {step.label}
          </span>
        </span>
      ))}
    </div>
  )
}

function PageTransition({ pageKey, children }) {
  const [visible, setVisible] = useState(false)
  const [currentChildren, setCurrentChildren] = useState(children)
  const isFirstRender = useRef(true)

  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false
      setVisible(true)
      return
    }

    // Fade out current content
    setVisible(false)

    const t = setTimeout(() => {
      // Swap to new content, then fade in
      setCurrentChildren(children)
      requestAnimationFrame(() => setVisible(true))
    }, 300)

    return () => clearTimeout(t)
  }, [pageKey]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div
      style={{
        opacity: visible ? 1 : 0,
        transform: visible ? 'translateY(0)' : 'translateY(8px)',
        transition: 'opacity 0.30s cubic-bezier(0.4,0,0.2,1), transform 0.30s cubic-bezier(0.4,0,0.2,1)',
      }}
    >
      {currentChildren}
    </div>
  )
}

export default function App() {
  const [page, setPage] = useState('landing')
  const [formData, setFormData] = useState(null)

  const handleNext = (selection) => {
    if (selection === 'upload') setPage('upload')
    else if (selection === 'manual') setPage('manual')
  }

  const handleGenerate = (data) => {
    setFormData(data)
    setPage('appeal')
  }

  const handleBack = () => setPage('landing')
  const handleBackFromAppeal = () => setPage(formData?.source ?? 'landing')

  return (
    <>
      {/* Fixed full-width top bar — no bottom border */}
      <div
        className="fixed top-0 left-0 right-0 z-50 flex items-center px-6 gap-3"
        style={{ height: 48, background: '#FAF8F4' }}
      >
        {/* Logo + Name */}
        <div className="flex items-center gap-2.5 flex-shrink-0">
          <img src="/logo.png" alt="InsureBetter" className="flex-shrink-0 rounded-full" style={{ width: 36, height: 36 }} />
          <span
            className="font-playfair font-bold tracking-tight"
            style={{ fontSize: 18, lineHeight: 1 }}
          >
            <span style={{ color: '#5C3D1E' }}>Insure</span><span style={{ color: '#C87834' }}>Better</span>
          </span>
        </div>

        {/* Separator + Breadcrumb — always visible */}
        <div style={{ width: 1, height: 14, background: '#E8DDD5', flexShrink: 0 }} />
        <Breadcrumb page={page} />

        {/* Separator + Disclaimer — always visible */}
        <div style={{ width: 1, height: 14, background: '#E8DDD5', flexShrink: 0 }} />
        <span style={{ fontSize: 10, color: '#C9B99A' }}>
          Not legal advice — consult a healthcare advocate for complex disputes.
        </span>
      </div>

      {/* Pages */}
      <div className="relative z-10" style={{ paddingTop: 48 }}>
        <PageTransition pageKey={page}>
          {page === 'landing' && <LandingPage onNext={handleNext} />}
          {page === 'upload' && (
            <UploadDocumentsPage
              onBack={handleBack}
              onGenerate={(data) => handleGenerate({ ...data, source: 'upload' })}
            />
          )}
          {page === 'manual' && (
            <ManualEntryPage
              onBack={handleBack}
              onGenerate={(data) => handleGenerate({ ...data, source: 'manual' })}
            />
          )}
          {page === 'appeal' && (
            <AppealResultPage onBack={handleBackFromAppeal} formData={formData} />
          )}
        </PageTransition>
      </div>
    </>
  )
}
