import { useState, useRef, useEffect, useCallback } from 'react'
import { createPortal } from 'react-dom'

const APPEAL_PDF_URL = null
const CHAT_API_ENDPOINT = null
const INITIAL_SUMMARY_API = null

const PLACEHOLDER_SUMMARY =
  `Your appeal disputes the denial of **CPT 27447** (Total Knee Replacement) under code **CO-50**.\n\n` +
  `Key arguments: prior auth #PA-9988, ICD-10 M17.11, and Plan Section 5.2. You have **30 days** to file.\n\n` +
  `What would you like to strengthen?`

const HIGHLIGHT_COLORS = [
  { label: 'Yellow', bg: 'rgba(253,224,71,0.50)', swatch: '#fde047' },
  { label: 'Sage',   bg: 'rgba(134,239,172,0.45)', swatch: '#86efac' },
  { label: 'Rose',   bg: 'rgba(249,168,212,0.45)', swatch: '#f9a8d4' },
]

function MarkdownLine({ text }) {
  const parts = text.split(/(\*\*[^*]+\*\*)/)
  return (
    <>
      {parts.map((p, i) =>
        p.startsWith('**') && p.endsWith('**')
          ? <strong key={i} style={{ color: '#5C4033', fontWeight: 600 }}>{p.slice(2, -2)}</strong>
          : <span key={i}>{p}</span>
      )}
    </>
  )
}

function ChatMessage({ message }) {
  const isUser = message.role === 'user'
  return (
    <div className={`flex gap-2 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      <div
        className="max-w-[90%] text-sm leading-relaxed"
        style={isUser
          ? {
              background: '#FFFFFF',
              color: '#5C4033',
              border: '1px solid rgba(92,64,51,0.25)',
              borderRadius: '12px 12px 4px 12px',
              padding: '10px 14px',
            }
          : {
              background: '#FFFFFF',
              color: '#7C6553',
              border: '1px solid rgba(92,64,51,0.12)',
              borderRadius: '12px 12px 12px 4px',
              padding: '10px 14px',
            }
        }
      >
        {message.content.split('\n').map((line, i) => (
          <p key={i} className={line === '' ? 'mt-2' : line.startsWith('•') ? 'ml-2 my-0.5' : ''}>
            <MarkdownLine text={line} />
          </p>
        ))}
      </div>
    </div>
  )
}

function TypingIndicator() {
  return (
    <div className="flex items-center gap-1.5 px-1 py-2">
      {[0, 150, 300].map((delay) => (
        <span
          key={delay}
          className="w-1.5 h-1.5 rounded-full animate-bounce"
          style={{ background: '#C9B99A', animationDelay: `${delay}ms` }}
        />
      ))}
    </div>
  )
}

function ContextChip({ context, onDismiss }) {
  if (!context) return null
  return (
    <div className="px-3 pb-1.5 flex-shrink-0">
      <div
        className="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 max-w-full"
        style={{ background: '#FFFFFF', border: '1px solid rgba(92,64,51,0.18)' }}
      >
        <svg className="w-3 h-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"
          style={{ color: '#A08060' }}>
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
        </svg>
        <span className="text-xs italic truncate" style={{ color: '#7C6553', maxWidth: 160 }}>
          "{context.truncated}"
        </span>
        <button
          onClick={onDismiss}
          className="flex-shrink-0 hover:opacity-60 transition-opacity ml-0.5"
          style={{ color: '#A08060' }}
        >
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  )
}

function SelectionToolbar({ popup, onHighlight, onAskAbout }) {
  if (!popup) return null
  return createPortal(
    <div
      data-selection-toolbar
      style={{
        position: 'fixed',
        left: popup.x,
        top: popup.y,
        transform: 'translate(-50%, calc(-100% - 10px))',
        zIndex: 1000,
        background: '#2C1A12',
        borderRadius: 10,
        boxShadow: '0 8px 24px rgba(0,0,0,0.20)',
        display: 'flex',
        alignItems: 'center',
        gap: 6,
        padding: '6px 10px',
        whiteSpace: 'nowrap',
      }}
    >
      <div style={{
        position: 'absolute',
        bottom: -5,
        left: '50%',
        transform: 'translateX(-50%)',
        width: 0, height: 0,
        borderLeft: '5px solid transparent',
        borderRight: '5px solid transparent',
        borderTop: '5px solid #2C1A12',
      }} />

      <span style={{ fontSize: 10, color: '#A08060', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase' }}>
        Highlight
      </span>

      {HIGHLIGHT_COLORS.map(({ label, bg, swatch }) => (
        <button
          key={label}
          title={label}
          onMouseDown={(e) => { e.preventDefault(); onHighlight(bg) }}
          style={{
            width: 16, height: 16,
            borderRadius: 4,
            background: swatch,
            border: '2px solid rgba(255,255,255,0.20)',
            cursor: 'pointer',
            flexShrink: 0,
            outline: 'none',
          }}
        />
      ))}

      <div style={{ width: 1, background: 'rgba(255,255,255,0.12)', height: 14, margin: '0 2px' }} />

      <button
        onMouseDown={(e) => { e.preventDefault(); onAskAbout() }}
        style={{
          fontSize: 11,
          fontWeight: 600,
          color: '#FAF7F4',
          background: 'rgba(160,128,96,0.50)',
          border: '1px solid rgba(160,128,96,0.40)',
          borderRadius: 6,
          padding: '2px 8px',
          cursor: 'pointer',
          outline: 'none',
        }}
      >
        Ask about this
      </button>
    </div>,
    document.body
  )
}

export default function AppealResultPage({ onBack, formData }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isSending, setIsSending] = useState(false)
  const [selectionPopup, setSelectionPopup] = useState(null)
  const [askContext, setAskContext] = useState(null)
  const [docsExpanded, setDocsExpanded] = useState(false)
  const bottomRef = useRef(null)
  const documentRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    async function loadSummary() {
      let summary = PLACEHOLDER_SUMMARY
      if (INITIAL_SUMMARY_API) {
        try {
          const res = await fetch(INITIAL_SUMMARY_API, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ formData }),
          })
          const data = await res.json()
          summary = data.summary ?? PLACEHOLDER_SUMMARY
        } catch (err) {
          console.error('Failed to fetch summary:', err)
        }
      }
      setMessages([{ role: 'assistant', content: summary }])
      setIsLoading(false)
    }
    loadSummary()
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading, isSending])

  useEffect(() => {
    const handleMouseUp = () => {
      setTimeout(() => {
        const selection = window.getSelection()
        if (!selection || selection.isCollapsed || !selection.toString().trim()) {
          setSelectionPopup(null)
          return
        }
        const range = selection.getRangeAt(0)
        if (!documentRef.current?.contains(range.commonAncestorContainer)) {
          setSelectionPopup(null)
          return
        }
        const rect = range.getBoundingClientRect()
        setSelectionPopup({
          x: rect.left + rect.width / 2,
          y: rect.top,
          text: selection.toString().trim(),
        })
      }, 10)
    }

    const handleMouseDown = (e) => {
      if (!e.target.closest('[data-selection-toolbar]')) {
        setSelectionPopup(null)
      }
    }

    document.addEventListener('mouseup', handleMouseUp)
    document.addEventListener('mousedown', handleMouseDown)
    return () => {
      document.removeEventListener('mouseup', handleMouseUp)
      document.removeEventListener('mousedown', handleMouseDown)
    }
  }, [])

  const applyHighlight = useCallback((color) => {
    const selection = window.getSelection()
    if (!selection || selection.isCollapsed) return
    try {
      const range = selection.getRangeAt(0)
      const span = document.createElement('span')
      span.style.backgroundColor = color
      span.style.borderRadius = '2px'
      span.style.padding = '1px 0'
      try {
        range.surroundContents(span)
      } catch {
        const fragment = range.extractContents()
        span.appendChild(fragment)
        range.insertNode(span)
      }
      selection.removeAllRanges()
    } catch (err) {
      console.error('Highlight error:', err)
    }
    setSelectionPopup(null)
  }, [])

  const handleAskAbout = useCallback(() => {
    if (!selectionPopup?.text) return
    const text = selectionPopup.text
    const truncated = text.length > 70 ? text.slice(0, 70) + '…' : text
    setAskContext({ text, truncated })
    setSelectionPopup(null)
    window.getSelection()?.removeAllRanges()
    setTimeout(() => inputRef.current?.focus(), 80)
  }, [selectionPopup])

  const handleSend = async () => {
    if (isSending) return
    const text = input.trim()
    if (!text && !askContext) return

    let messageContent = text
    if (askContext) {
      messageContent = `About this passage: "${askContext.text}"\n\n${text || 'Can you explain this?'}`
    }

    setInput('')
    setAskContext(null)

    const userMessage = { role: 'user', content: messageContent }
    const nextMessages = [...messages, userMessage]
    setMessages(nextMessages)
    setIsSending(true)

    if (CHAT_API_ENDPOINT) {
      try {
        const res = await fetch(CHAT_API_ENDPOINT, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ messages: nextMessages }),
        })
        const data = await res.json()
        setMessages((prev) => [...prev, { role: 'assistant', content: data.reply }])
      } catch (err) {
        console.error('Chat API error:', err)
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' },
        ])
      }
    } else {
      await new Promise((r) => setTimeout(r, 900))
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content:
            "(Chat API not yet configured.) Once connected, I'll answer questions about your appeal and help strengthen your argument.",
        },
      ])
    }
    setIsSending(false)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleDownload = useCallback(() => {
    const date = new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
    const content = `APPEAL LETTER — DRAFT\nGenerated ${date}\n\nJane Smith\n123 Main Street, Springfield, IL 62701\nMember ID: XYZ123456789\n\nBlueCross BlueShield\nAppeals Department\nPO Box 99999, Chicago, IL 60601\n\nRe: Appeal of Claim Denial — CPT 27447 / DOS: November 15, 2024\n\nDear Appeals Department,\n\nI am writing to formally appeal the denial of my claim for a Total Knee Replacement (CPT 27447), performed on November 15, 2024 by Dr. John Smith at Springfield General Hospital. The claim was denied under code CO-50 ("not medically necessary"), a determination I respectfully dispute.\n\nBASIS FOR APPEAL\n\nMy physician, Dr. John Smith (NPI: 1234567890), submitted a prior authorization on October 1, 2024 (Auth #PA-9988), which your plan approved. The procedure addresses a diagnosis of primary osteoarthritis of the right knee (ICD-10: M17.11), documented through clinical imaging and functional assessments conducted over the past 18 months.\n\nPer my plan's Summary Plan Description (Group #12345, Section 5.2), medically necessary orthopedic surgical procedures are covered benefits. I have exhausted all conservative treatment options including physical therapy, corticosteroid injections, and oral NSAIDs without adequate relief.\n\nI respectfully request that you overturn the denial and process my claim for reimbursement under my plan benefits. If additional information is required, please contact me at (555) 123-4567 or jane.smith@email.com.\n\nSincerely,\nJane Smith\n\n---\nSUPPORTING DOCUMENTATION\n1. Prior Authorization #PA-9988 (approved Oct 1, 2024)\n2. Physician letter of medical necessity from Dr. Smith\n3. MRI report dated September 3, 2024\n4. AAOS Clinical Practice Guidelines on Knee OA Management\n5. Explanation of Benefits (EOB) dated December 2, 2024`
    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'Appeal_Letter.txt'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }, [])

  const canSend = (input.trim() || askContext) && !isSending

  return (
    <div style={{ display: 'flex', minHeight: 'calc(100vh - 48px)', background: '#FAF8F4' }}>

      {/* ── Left: Appeal Letter — scrolls with the page ── */}
      <div style={{ flex: '1 1 65%', padding: '32px 24px 64px' }}>

        {/* Back button */}
        <div className="mb-6">
          <button
            type="button"
            onClick={onBack}
            className="inline-flex items-center gap-1.5 text-xs transition-opacity hover:opacity-60"
            style={{ color: '#A08060' }}
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back
          </button>
        </div>

        {APPEAL_PDF_URL ? (
          <iframe
            src={APPEAL_PDF_URL}
            title="Appeal Letter"
            className="w-full rounded-xl"
            style={{ minHeight: 800, border: 'none' }}
          />
        ) : (
          <div
            ref={documentRef}
            className="max-w-[640px] mx-auto rounded-xl shadow-sm overflow-hidden select-text relative"
            style={{ background: '#FFFFFF', border: '1px solid rgba(92,64,51,0.10)' }}
          >
            {/* Letter header */}
            <div className="px-10 py-6 relative" style={{ borderBottom: '1px solid #F5EDE6' }}>
              <p className="text-xs font-semibold uppercase tracking-widest mb-1" style={{ color: '#C9B99A' }}>
                Appeal Letter — Draft
              </p>
              <p className="text-xs" style={{ color: '#C9B99A' }}>
                Generated {new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
              </p>

              <button
                type="button"
                onClick={handleDownload}
                className="absolute top-4 right-4 inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-opacity hover:opacity-70"
                style={{
                  background: '#FFFFFF',
                  color: '#7C6553',
                  border: '1px solid rgba(92,64,51,0.14)',
                }}
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Download
              </button>
            </div>

            {/* Letter body */}
            <div className="px-10 py-8 text-sm leading-relaxed space-y-5" style={{ color: '#7C6553' }}>
              <div className="space-y-0.5">
                <p style={{ color: '#5C4033', fontWeight: 600 }}>Jane Smith</p>
                <p>123 Main Street, Springfield, IL 62701</p>
                <p>Member ID: XYZ123456789</p>
              </div>

              <div className="space-y-0.5">
                <p style={{ color: '#5C4033', fontWeight: 600 }}>BlueCross BlueShield</p>
                <p>Appeals Department</p>
                <p>PO Box 99999, Chicago, IL 60601</p>
              </div>

              <p style={{ color: '#A08060' }}>
                Re: Appeal of Claim Denial — CPT 27447 / DOS: November 15, 2024
              </p>

              <p>Dear Appeals Department,</p>

              <p>
                I am writing to formally appeal the denial of my claim for a Total Knee Replacement
                (CPT 27447), performed on November 15, 2024 by Dr. John Smith at Springfield General
                Hospital. The claim was denied under code{' '}
                <span style={{ color: '#7C6553', fontWeight: 600 }}>CO-50</span>{' '}
                ("not medically necessary"), a determination I respectfully dispute.
              </p>

              <div>
                <p style={{ color: '#5C4033', fontWeight: 600 }} className="mb-2">Basis for Appeal</p>
                <p>
                  My physician, Dr. John Smith (NPI: 1234567890), submitted a prior authorization on
                  October 1, 2024 (Auth #PA-9988), which your plan approved. The procedure addresses a
                  diagnosis of primary osteoarthritis of the right knee (ICD-10: M17.11), documented
                  through clinical imaging and functional assessments conducted over the past 18 months.
                </p>
              </div>

              <p>
                Per my plan's Summary Plan Description (Group #12345, Section 5.2), medically necessary
                orthopedic surgical procedures are covered benefits. I have exhausted all conservative
                treatment options including physical therapy, corticosteroid injections, and oral
                NSAIDs without adequate relief.
              </p>

              <p>
                I respectfully request that you overturn the denial and process my claim for reimbursement
                under my plan benefits. If additional information is required, please contact me at
                (555) 123-4567 or jane.smith@email.com.
              </p>

              {/* Supporting documents */}
              <div style={{ borderTop: '1px solid #F0E8E0', paddingTop: 16 }}>
                <button
                  type="button"
                  onClick={() => setDocsExpanded((x) => !x)}
                  className="flex items-center gap-1.5 transition-opacity hover:opacity-70"
                  style={{ color: '#A08060', fontSize: 12, fontWeight: 600 }}
                >
                  <svg
                    className="w-3.5 h-3.5 transition-transform"
                    style={{ transform: docsExpanded ? 'rotate(90deg)' : 'rotate(0deg)' }}
                    fill="none" stroke="currentColor" viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  Supporting Documentation ({docsExpanded ? 'collapse' : '5 items'})
                </button>
                {docsExpanded && (
                  <ul className="mt-3 space-y-1.5 pl-5" style={{ color: '#A08060', fontSize: 13 }}>
                    <li>• Prior Authorization #PA-9988 (approved Oct 1, 2024)</li>
                    <li>• Physician letter of medical necessity from Dr. Smith</li>
                    <li>• MRI report dated September 3, 2024</li>
                    <li>• AAOS Clinical Practice Guidelines on Knee OA Management</li>
                    <li>• Explanation of Benefits (EOB) dated December 2, 2024</li>
                  </ul>
                )}
              </div>

              <div style={{ paddingTop: 8 }}>
                <p>Sincerely,</p>
                <p style={{ color: '#5C4033', fontWeight: 600, marginTop: 4 }}>Jane Smith</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ── Right: Chat assistant — sticky, stays pinned while letter scrolls ── */}
      <div
        style={{
          flex: '0 0 35%',
          position: 'sticky',
          top: 48,
          height: 'calc(100vh - 48px)',
          display: 'flex',
          flexDirection: 'column',
          background: '#FAF8F4',
          overflow: 'hidden',
          borderLeft: '1px solid rgba(92,64,51,0.08)',
        }}
      >
        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3.5">
          {isLoading ? (
            <TypingIndicator />
          ) : (
            messages.map((msg, i) => <ChatMessage key={i} message={msg} />)
          )}
          {isSending && <TypingIndicator />}
          <div ref={bottomRef} />
        </div>

        {/* Suggested prompts */}
        {messages.length === 1 && !isSending && (
          <div className="px-4 pb-2 flex flex-col gap-1 flex-shrink-0">
            {[
              'How strong is my appeal?',
              'What documents should I attach?',
              'Strengthen the medical necessity section',
            ].map((prompt) => (
              <button
                key={prompt}
                type="button"
                onClick={() => { setInput(prompt); inputRef.current?.focus() }}
                className="text-left text-xs px-1 py-1 transition-opacity hover:opacity-60 underline underline-offset-2"
                style={{ color: '#A08060', textDecorationColor: '#E8DDD5' }}
              >
                {prompt}
              </button>
            ))}
          </div>
        )}

        {/* Context chip */}
        <ContextChip context={askContext} onDismiss={() => setAskContext(null)} />

        {/* Input bar */}
        <div className="flex-shrink-0 px-3 py-3">
          <div className="flex items-end gap-2">
            <textarea
              ref={inputRef}
              className="flex-1 rounded-xl px-3.5 py-2.5 text-sm resize-none focus:outline-none transition"
              style={{
                background: '#FFFFFF',
                border: '1.5px solid rgba(92,64,51,0.20)',
                color: '#5C4033',
                minHeight: 40,
                maxHeight: 100,
                lineHeight: '1.5',
                boxShadow: '0 1px 4px rgba(92,64,51,0.06)',
              }}
              rows={1}
              placeholder={askContext ? 'Ask about the selected passage…' : 'Ask about your appeal…'}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
            />
            <button
              type="button"
              onClick={handleSend}
              disabled={!canSend}
              className="flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center transition-all disabled:opacity-35 disabled:cursor-not-allowed"
              style={{ background: '#5C4033' }}
            >
              <svg className="w-3.5 h-3.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </button>
          </div>
          <p className="mt-1.5 text-center" style={{ fontSize: 10, color: '#C9B99A' }}>
            Enter to send · Shift+Enter for new line
          </p>
        </div>
      </div>

      {/* Floating selection toolbar */}
      <SelectionToolbar
        popup={selectionPopup}
        onHighlight={applyHighlight}
        onAskAbout={handleAskAbout}
      />
    </div>
  )
}
