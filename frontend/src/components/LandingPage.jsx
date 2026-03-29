import { useState } from 'react'

const OPTIONS = [
  {
    id: 'upload',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"
        style={{ color: '#A08060' }}>
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
      </svg>
    ),
    title: 'Upload EOB & Denial Letter',
  },
  {
    id: 'manual',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"
        style={{ color: '#A08060' }}>
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
      </svg>
    ),
    title: 'Enter Insurance Plan Information Manually',
  },
]

export default function LandingPage({ onNext }) {
  const [selected, setSelected] = useState(null)

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6 pb-12"
      style={{ background: '#FAF8F4' }}>
      <div className="w-full max-w-xl">

        {/* Hero */}
        <div className="mb-10 text-center">
          <h1
            className="font-playfair font-bold text-4xl leading-tight mb-4"
            style={{ color: '#5C4033' }}
          >
            Fight Your Claim Denial
          </h1>
          <p className="text-base leading-relaxed max-w-md mx-auto" style={{ color: '#A08060' }}>
            Build a compelling, evidence-based appeal for healthcare claim denials — in minutes.
          </p>
        </div>

        {/* Divider */}
        <div className="flex items-center gap-4 mb-6">
          <div className="flex-1 h-px" style={{ background: '#E8DDD5' }} />
          <span className="text-xs font-semibold uppercase tracking-widest whitespace-nowrap"
            style={{ color: '#C9B99A' }}>
            How would you like to get started?
          </span>
          <div className="flex-1 h-px" style={{ background: '#E8DDD5' }} />
        </div>

        {/* Option Cards */}
        <div className="flex flex-col gap-3 mb-8">
          {OPTIONS.map((opt) => {
            const isSelected = selected === opt.id
            return (
              <button
                key={opt.id}
                type="button"
                onClick={() => setSelected(opt.id)}
                className="relative flex items-center gap-4 p-5 rounded-xl border-2 cursor-pointer transition-all duration-200"
                style={{
                  background: isSelected ? 'rgba(92,64,51,0.04)' : '#FFFFFF',
                  borderColor: isSelected ? '#A08060' : '#E8DDD5',
                  boxShadow: isSelected ? '0 2px 8px rgba(92,64,51,0.08)' : 'none',
                }}
              >
                {/* Radio indicator */}
                <div
                  className="flex-shrink-0 rounded-full border-2 flex items-center justify-center transition-colors"
                  style={{
                    width: 18,
                    height: 18,
                    borderColor: isSelected ? '#7C6553' : '#C9B99A',
                    background: isSelected ? '#7C6553' : 'transparent',
                  }}
                >
                  {isSelected && <div className="w-2 h-2 rounded-full bg-white" />}
                </div>

                {/* Text — left aligned */}
                <div className="flex-1 flex items-center justify-start">
                  <p className="font-semibold text-sm" style={{ color: '#5C4033' }}>
                    {opt.title}
                  </p>
                </div>

                {/* Icon — pushed to far right */}
                <div
                  className="flex-shrink-0 w-9 h-9 rounded-lg flex items-center justify-center transition-colors"
                  style={{ background: isSelected ? 'rgba(92,64,51,0.08)' : '#F5F0EB' }}
                >
                  {opt.icon}
                </div>
              </button>
            )
          })}
        </div>

        {/* Next Button */}
        <div className="flex justify-end items-center gap-3">
          {!selected && (
            <p className="text-xs" style={{ color: '#C9B99A' }}>Select an option above to continue</p>
          )}
          <button
            type="button"
            disabled={!selected}
            onClick={() => onNext(selected)}
            className="inline-flex items-center justify-center gap-2 rounded-lg px-6 py-2.5 text-sm font-semibold transition-all duration-150 focus:outline-none disabled:cursor-not-allowed disabled:opacity-40"
            style={{
              background: selected ? '#5C4033' : '#C9B99A',
              color: '#FAF7F4',
              minWidth: 120,
            }}
          >
            Continue
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}
