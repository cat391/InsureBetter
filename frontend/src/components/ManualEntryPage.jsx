import { useState } from 'react'

const FIELD_HINTS = [
  { label: 'Denial Code(s)', placeholder: 'e.g. CO-4, PR-96, CARC 50…' },
  { label: 'Procedure / CPT Code', placeholder: 'e.g. CPT 27447 (total knee replacement)' },
  { label: 'Diagnosis / ICD-10 Code', placeholder: 'e.g. M17.11 — primary osteoarthritis, right knee' },
  { label: 'Date of Service', placeholder: 'e.g. 2024-11-15' },
  { label: 'Insurance Plan & Group Number', placeholder: 'e.g. BlueCross BlueShield PPO, Group #12345' },
  { label: 'Member ID', placeholder: 'e.g. XYZ123456789' },
]

export default function ManualEntryPage({ onBack, onGenerate }) {
  const [fields, setFields] = useState(
    Object.fromEntries(FIELD_HINTS.map((f) => [f.label, '']))
  )
  const [planDetails, setPlanDetails] = useState('')
  const [denialReason, setDenialReason] = useState('')

  const setField = (label, val) => setFields((prev) => ({ ...prev, [label]: val }))

  const canSubmit = planDetails.trim().length > 0 || denialReason.trim().length > 0

  return (
    <div className="min-h-screen flex flex-col">

      {/* Main */}
      <main className="flex-1 px-6 py-8">
        <div className="max-w-2xl mx-auto">
          <div className="mb-6">
            <h2 className="text-2xl font-bold mb-1" style={{ color: '#5C4033' }}>Enter Your Claim Information</h2>
            <p className="text-sm" style={{ color: '#7C6553' }}>
              Fill in as much detail as you have. The more specific you are, the stronger your appeal will be.
            </p>
          </div>

          {/* Code Fields Grid */}
          <div className="mb-5">
            <p className="field-label">Claim & Plan Details</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {FIELD_HINTS.map((f) => (
                <div key={f.label}>
                  <label className="block text-xs font-medium mb-1" style={{ color: '#7C6553' }}>{f.label}</label>
                  <input
                    type="text"
                    placeholder={f.placeholder}
                    value={fields[f.label]}
                    onChange={(e) => setField(f.label, e.target.value)}
                    className="input-field"
                  />
                </div>
              ))}
            </div>
          </div>

          {/* Denial Reason */}
          <div className="mb-5">
            <label className="field-label" htmlFor="denial-reason">
              Reason for Denial
              <span className="ml-1 font-normal text-xs" style={{ color: '#A08060' }}>(as stated by your insurer)</span>
            </label>
            <textarea
              id="denial-reason"
              className="textarea"
              rows={3}
              placeholder="e.g. Claim denied as not medically necessary. Reference code CO-50. Service not covered under current plan benefits..."
              value={denialReason}
              onChange={(e) => setDenialReason(e.target.value)}
            />
          </div>

          {/* Plan / Policy Details */}
          <div className="mb-7">
            <label className="field-label" htmlFor="plan-details">
              Plan & Policy Information
              <span className="ml-1 text-red-500">*</span>
            </label>
            <p className="text-xs mb-2" style={{ color: '#A08060' }}>
              Describe your health plan coverage, relevant policy language, prior authorizations, or physician notes that support your claim.
            </p>
            <textarea
              id="plan-details"
              className="textarea"
              rows={5}
              placeholder="e.g. My plan (BCBS PPO, Group #12345) covers medically necessary orthopedic procedures under Section 5.2. My physician, Dr. Smith, submitted a prior authorization on 10/01/2024 (auth #PA-9988) which was approved..."
              value={planDetails}
              onChange={(e) => setPlanDetails(e.target.value)}
            />
          </div>

          {/* Actions */}
          <div className="flex items-center justify-between">
            <button type="button" onClick={onBack} className="btn-secondary">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Back
            </button>
            <div className="flex items-center gap-3">
              {!canSubmit && (
                <span className="text-xs" style={{ color: '#C9B99A' }}>Add details above to continue</span>
              )}
              <button
                type="button"
                disabled={!canSubmit}
                onClick={() => onGenerate?.({ fields, planDetails, denialReason })}
                className="btn-primary"
              >
                Generate Appeal
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
