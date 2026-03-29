import { useState, useRef, useEffect, useCallback } from 'react'
import { createPortal } from 'react-dom'

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
          ? { background: '#FFFFFF', color: '#5C4033', border: '1px solid rgba(92,64,51,0.25)', borderRadius: '12px 12px 4px 12px', padding: '10px 14px' }
          : { background: '#FFFFFF', color: '#7C6553', border: '1px solid rgba(92,64,51,0.12)', borderRadius: '12px 12px 12px 4px', padding: '10px 14px' }
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
        <span key={delay} className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: '#C9B99A', animationDelay: `${delay}ms` }} />
      ))}
    </div>
  )
}

function ContextChip({ context, onDismiss }) {
  if (!context) return null
  return (
    <div className="px-3 pb-1.5 flex-shrink-0">
      <div className="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 max-w-full" style={{ background: '#FFFFFF', border: '1px solid rgba(92,64,51,0.18)' }}>
        <svg className="w-3 h-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" style={{ color: '#A08060' }}>
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
        </svg>
        <span className="text-xs italic truncate" style={{ color: '#7C6553', maxWidth: 160 }}>"{context.truncated}"</span>
        <button onClick={onDismiss} className="flex-shrink-0 hover:opacity-60 transition-opacity ml-0.5" style={{ color: '#A08060' }}>
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
    <div data-selection-toolbar style={{
      position: 'fixed', left: popup.x, top: popup.y, transform: 'translate(-50%, calc(-100% - 10px))', zIndex: 1000,
      background: '#2C1A12', borderRadius: 10, boxShadow: '0 8px 24px rgba(0,0,0,0.20)',
      display: 'flex', alignItems: 'center', gap: 6, padding: '6px 10px', whiteSpace: 'nowrap',
    }}>
      <div style={{ position: 'absolute', bottom: -5, left: '50%', transform: 'translateX(-50%)', width: 0, height: 0, borderLeft: '5px solid transparent', borderRight: '5px solid transparent', borderTop: '5px solid #2C1A12' }} />
      <span style={{ fontSize: 10, color: '#A08060', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase' }}>Highlight</span>
      {HIGHLIGHT_COLORS.map(({ label, bg, swatch }) => (
        <button key={label} title={label} onMouseDown={(e) => { e.preventDefault(); onHighlight(bg) }}
          style={{ width: 16, height: 16, borderRadius: 4, background: swatch, border: '2px solid rgba(255,255,255,0.20)', cursor: 'pointer', flexShrink: 0, outline: 'none' }} />
      ))}
      <div style={{ width: 1, background: 'rgba(255,255,255,0.12)', height: 14, margin: '0 2px' }} />
      <button onMouseDown={(e) => { e.preventDefault(); onAskAbout() }}
        style={{ fontSize: 11, fontWeight: 600, color: '#FAF7F4', background: 'rgba(160,128,96,0.50)', border: '1px solid rgba(160,128,96,0.40)', borderRadius: 6, padding: '2px 8px', cursor: 'pointer', outline: 'none' }}>
        Ask about this
      </button>
    </div>,
    document.body
  )
}

/* ── Section type → style mapping ── */
const SECTION_STYLES = {
  sender:          { color: '#5C4033', fontWeight: 600 },
  date:            { color: '#7C6553' },
  recipient:       { color: '#5C4033', fontWeight: 600 },
  subject:         { color: '#5C4033', fontWeight: 700 },
  greeting:        { color: '#7C6553' },
  body:            { color: '#7C6553' },
  evidence_header: { color: '#5C4033', fontWeight: 600 },
  evidence_item:   { color: '#7C6553', paddingLeft: 16 },
  closing:         { color: '#7C6553' },
  signature:       { color: '#5C4033', fontWeight: 600 },
  disclaimer:      { color: '#A08060', fontSize: 11, fontStyle: 'italic' },
}

/* ── Render a single editable section ── */
function SectionRenderer({ section, onEdit }) {
  const ref = useRef(null)
  const style = SECTION_STYLES[section.type] || { color: '#7C6553' }
  const isDisclaimer = section.type === 'disclaimer'

  return (
    <div
      ref={ref}
      contentEditable={!isDisclaimer}
      suppressContentEditableWarning
      onBlur={() => {
        if (ref.current && onEdit) {
          onEdit(ref.current.innerText)
        }
      }}
      className={`outline-none ${isDisclaimer ? '' : 'hover:bg-[rgba(92,64,51,0.03)] rounded transition-colors'}`}
      style={{ ...style, whiteSpace: 'pre-wrap', cursor: isDisclaimer ? 'default' : 'text', padding: '2px 0' }}
    >
      {section.text}
    </div>
  )
}

/* ── Section-based letter view ── */
function LetterView({ sections, onSectionEdit }) {
  if (!sections || sections.length === 0) {
    return (
      <div className="px-10 py-16 text-center">
        <div className="flex flex-col items-center gap-3">
          <div className="flex items-center gap-1.5">
            {[0, 150, 300].map((delay) => (
              <span key={delay} className="w-2 h-2 rounded-full animate-bounce" style={{ background: '#C9B99A', animationDelay: `${delay}ms` }} />
            ))}
          </div>
          <p className="text-sm" style={{ color: '#A08060' }}>Analyzing your document and generating appeal...</p>
        </div>
      </div>
    )
  }
  return (
    <div className="px-10 py-8 text-sm leading-relaxed space-y-4">
      {sections.map((section, i) => (
        <SectionRenderer
          key={`${i}-${section.type}`}
          section={section}
          onEdit={(newText) => onSectionEdit(i, newText)}
        />
      ))}
    </div>
  )
}

/* ── Section-based diff view ── */
function SectionDiffView({ oldSections, newSections }) {
  const maxLen = Math.max(oldSections.length, newSections.length)
  const rows = []

  for (let i = 0; i < maxLen; i++) {
    const oldS = oldSections[i]
    const newS = newSections[i]

    if (oldS && newS && oldS.type === newS.type && oldS.text === newS.text) {
      // Unchanged
      const style = SECTION_STYLES[oldS.type] || { color: '#7C6553' }
      rows.push(<div key={i} style={{ ...style, whiteSpace: 'pre-wrap', padding: '2px 0' }}>{oldS.text}</div>)
    } else {
      // Changed, removed, or added
      if (oldS) {
        const style = SECTION_STYLES[oldS.type] || { color: '#7C6553' }
        rows.push(
          <div key={`${i}-old`} style={{ ...style, whiteSpace: 'pre-wrap', background: 'rgba(239,68,68,0.12)', textDecoration: 'line-through', opacity: 0.7, padding: '2px 4px', borderRadius: 3 }}>
            {oldS.text}
          </div>
        )
      }
      if (newS) {
        const style = SECTION_STYLES[newS.type] || { color: '#7C6553' }
        rows.push(
          <div key={`${i}-new`} style={{ ...style, whiteSpace: 'pre-wrap', background: 'rgba(34,197,94,0.12)', padding: '2px 4px', borderRadius: 3 }}>
            {newS.text}
          </div>
        )
      }
    }
  }

  return <div className="px-10 py-8 text-sm leading-relaxed space-y-4">{rows}</div>
}

/* ── Approval card ── */
function ApprovalCard({ onAccept, onReject }) {
  return (
    <div className="mx-0 my-1 p-3 rounded-xl" style={{ background: '#FFFFFF', border: '1px solid rgba(92,64,51,0.15)' }}>
      <p className="text-xs font-medium mb-2" style={{ color: '#5C4033' }}>
        Proposed changes are shown on the letter. Review the highlighted differences.
      </p>
      <div className="flex gap-2">
        <button onClick={onAccept} className="inline-flex items-center gap-1 rounded-lg px-3 py-1.5 text-xs font-medium transition-opacity hover:opacity-80" style={{ background: '#5C4033', color: '#FFFFFF' }}>
          Accept Changes
        </button>
        <button onClick={onReject} className="inline-flex items-center gap-1 rounded-lg px-3 py-1.5 text-xs font-medium transition-opacity hover:opacity-70" style={{ background: '#FFFFFF', color: '#7C6553', border: '1px solid rgba(92,64,51,0.20)' }}>
          Reject
        </button>
      </div>
    </div>
  )
}

/* ── Helper: sections → plain text for download ── */
function sectionsToText(sections) {
  return sections.map(s => s.type === 'evidence_item' ? `  - ${s.text}` : s.text).join('\n\n')
}


export default function AppealResultPage({ onBack, formData }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isSending, setIsSending] = useState(false)
  const [selectionPopup, setSelectionPopup] = useState(null)
  const [askContext, setAskContext] = useState(null)
  const [docsExpanded, setDocsExpanded] = useState(false)
  const [pipelineData, setPipelineData] = useState(null)
  const [letterSections, setLetterSections] = useState([])
  const [pendingEdit, setPendingEdit] = useState(null)
  const bottomRef = useRef(null)
  const documentRef = useRef(null)
  const inputRef = useRef(null)

  // ── Initial load: call backend pipeline ──
  useEffect(() => {
    async function loadAppeal() {
      try {
        let res
        if (formData?.source === 'upload' && formData.files?.length > 0) {
          const fd = new FormData()
          fd.append('file', formData.files[0])
          res = await fetch('/api/appeal/upload', { method: 'POST', body: fd })
        } else if (formData?.source === 'manual') {
          res = await fetch('/api/appeal/manual', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              denial_codes: formData.fields?.['Denial Code(s)'] || '',
              cpt_codes: formData.fields?.['Procedure / CPT Code'] || '',
              icd10_codes: formData.fields?.['Diagnosis / ICD-10 Code'] || '',
              date_of_service: formData.fields?.['Date of Service'] || '',
              plan_info: formData.fields?.['Insurance Plan & Group Number'] || '',
              member_id: formData.fields?.['Member ID'] || '',
              denial_reason: formData.denialReason || '',
              plan_details: formData.planDetails || '',
            }),
          })
        }

        if (res && res.ok) {
          const data = await res.json()
          setPipelineData(data)
          setLetterSections(data.appeal_letter.letter_sections || [])
          const ext = data.extraction
          const codes = ext.denied_cpt_codes?.join(', ') || 'unknown'
          const carc = ext.carc_code || 'unknown'
          const dtype = ext.denial_type?.replace(/_/g, ' ') || 'unknown'
          const deadline = ext.appeal_deadline || 'check your denial letter'
          const summary =
            `Your appeal disputes the denial of **${codes}** under code **${carc}**.\n\n` +
            `Denial type: **${dtype}**. Appeal deadline: **${deadline}**.\n\n` +
            `What would you like to change or strengthen?`
          setMessages([{ role: 'assistant', content: summary }])
        } else {
          const errText = res ? await res.text() : 'No response'
          console.error('Pipeline error:', errText)
          setMessages([{ role: 'assistant', content: 'There was an error processing your document. Please try again.' }])
        }
      } catch (err) {
        console.error('Failed to load appeal:', err)
        setMessages([{ role: 'assistant', content: 'Failed to connect to the server. Make sure the backend is running.' }])
      }
      setIsLoading(false)
    }
    loadAppeal()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading, isSending])

  // ── Text selection handling ──
  useEffect(() => {
    const handleMouseUp = () => {
      setTimeout(() => {
        const selection = window.getSelection()
        if (!selection || selection.isCollapsed || !selection.toString().trim()) { setSelectionPopup(null); return }
        const range = selection.getRangeAt(0)
        if (!documentRef.current?.contains(range.commonAncestorContainer)) { setSelectionPopup(null); return }
        const rect = range.getBoundingClientRect()
        setSelectionPopup({ x: rect.left + rect.width / 2, y: rect.top, text: selection.toString().trim() })
      }, 10)
    }
    const handleMouseDown = (e) => { if (!e.target.closest('[data-selection-toolbar]')) setSelectionPopup(null) }
    document.addEventListener('mouseup', handleMouseUp)
    document.addEventListener('mousedown', handleMouseDown)
    return () => { document.removeEventListener('mouseup', handleMouseUp); document.removeEventListener('mousedown', handleMouseDown) }
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
      try { range.surroundContents(span) } catch { const fragment = range.extractContents(); span.appendChild(fragment); range.insertNode(span) }
      selection.removeAllRanges()
    } catch (err) { console.error('Highlight error:', err) }
    setSelectionPopup(null)
  }, [])

  const handleAskAbout = useCallback(() => {
    if (!selectionPopup?.text) return
    const text = selectionPopup.text
    const truncated = text.length > 70 ? text.slice(0, 70) + '\u2026' : text
    setAskContext({ text, truncated })
    setSelectionPopup(null)
    window.getSelection()?.removeAllRanges()
    setTimeout(() => inputRef.current?.focus(), 80)
  }, [selectionPopup])

  // ── Section edit (user typing directly) ──
  const handleSectionEdit = useCallback((index, newText) => {
    setLetterSections(prev => {
      const updated = [...prev]
      updated[index] = { ...updated[index], text: newText }
      return updated
    })
  }, [])

  // ── Chat send with intent-aware handling ──
  const handleSend = async () => {
    if (isSending || !pipelineData) return
    const text = input.trim()
    if (!text && !askContext) return

    let messageContent = text
    if (askContext) {
      messageContent = `About this passage: "${askContext.text}"\n\n${text || 'Can you explain this?'}`
    }

    setInput('')
    setAskContext(null)
    setMessages((prev) => [...prev, { role: 'user', content: messageContent }])
    setIsSending(true)

    try {
      const res = await fetch('/api/appeal/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_message: messageContent,
          current_letter_sections: letterSections,
          extraction: pipelineData.extraction,
          lookup: pipelineData.lookup,
          conversation_history: messages.map(m => ({ role: m.role, content: m.content })),
          additional_context: pipelineData.additional_context || '',
        }),
      })
      const data = await res.json()
      setMessages((prev) => [...prev, { role: 'assistant', content: data.assistant_message }])

      if ((data.intent === 'edit' || data.intent === 'both') && data.proposed_letter) {
        setPendingEdit({
          proposedSections: data.proposed_letter.letter_sections || [],
          proposedExtraction: data.proposed_extraction,
          additionalContext: data.additional_context,
        })
      }
    } catch (err) {
      console.error('Chat API error:', err)
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' }])
    }
    setIsSending(false)
  }

  const handleAcceptEdit = () => {
    if (!pendingEdit) return
    setLetterSections(pendingEdit.proposedSections)
    setPipelineData((prev) => ({
      ...prev,
      extraction: pendingEdit.proposedExtraction || prev.extraction,
      additional_context: pendingEdit.additionalContext,
    }))
    setPendingEdit(null)
  }

  const handleRejectEdit = () => { setPendingEdit(null) }

  const handleKeyDown = (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() } }

  const handleDownload = useCallback(() => {
    const content = sectionsToText(letterSections) || 'No letter generated yet.'
    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'Appeal_Letter.txt'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }, [letterSections])

  const canSend = (input.trim() || askContext) && !isSending && pipelineData
  const requiredEvidence = pipelineData?.lookup?.required_evidence ?? []

  return (
    <div style={{ display: 'flex', minHeight: 'calc(100vh - 48px)', background: '#FAF8F4' }}>

      {/* ── Left: Appeal Letter ── */}
      <div style={{ flex: '1 1 65%', padding: '32px 24px 64px' }}>
        <div className="mb-6">
          <button type="button" onClick={onBack} className="inline-flex items-center gap-1.5 text-xs transition-opacity hover:opacity-60" style={{ color: '#A08060' }}>
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back
          </button>
        </div>

        <div ref={documentRef} className="max-w-[640px] mx-auto rounded-xl shadow-sm overflow-hidden select-text relative" style={{ background: '#FFFFFF', border: '1px solid rgba(92,64,51,0.10)' }}>
          {/* Letter header chrome */}
          <div className="px-10 py-6 relative" style={{ borderBottom: '1px solid #F5EDE6' }}>
            <p className="text-xs font-semibold uppercase tracking-widest mb-1" style={{ color: '#C9B99A' }}>Appeal Letter — Draft</p>
            <p className="text-xs" style={{ color: '#C9B99A' }}>
              Generated {new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
            </p>
            <button type="button" onClick={handleDownload} disabled={letterSections.length === 0}
              className="absolute top-4 right-4 inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-opacity hover:opacity-70 disabled:opacity-30"
              style={{ background: '#FFFFFF', color: '#7C6553', border: '1px solid rgba(92,64,51,0.14)' }}>
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Download
            </button>
          </div>

          {/* Letter body — sections or diff */}
          {pendingEdit ? (
            <SectionDiffView oldSections={letterSections} newSections={pendingEdit.proposedSections} />
          ) : (
            <LetterView sections={letterSections} onSectionEdit={handleSectionEdit} />
          )}

          {/* Supporting documents */}
          {requiredEvidence.length > 0 && (
            <div className="px-10 pb-8">
              <div style={{ borderTop: '1px solid #F0E8E0', paddingTop: 16 }}>
                <button type="button" onClick={() => setDocsExpanded((x) => !x)}
                  className="flex items-center gap-1.5 transition-opacity hover:opacity-70" style={{ color: '#A08060', fontSize: 12, fontWeight: 600 }}>
                  <svg className="w-3.5 h-3.5 transition-transform" style={{ transform: docsExpanded ? 'rotate(90deg)' : 'rotate(0deg)' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  Supporting Documentation ({docsExpanded ? 'collapse' : `${requiredEvidence.length} items`})
                </button>
                {docsExpanded && (
                  <ul className="mt-3 space-y-1.5 pl-5" style={{ color: '#A08060', fontSize: 13 }}>
                    {requiredEvidence.map((item, i) => <li key={i}>{item}</li>)}
                  </ul>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── Right: Chat ── */}
      <div style={{ flex: '0 0 35%', position: 'sticky', top: 48, height: 'calc(100vh - 48px)', display: 'flex', flexDirection: 'column', background: '#FAF8F4', overflow: 'hidden', borderLeft: '1px solid rgba(92,64,51,0.08)' }}>
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3.5">
          {isLoading ? <TypingIndicator /> : (
            <>
              {messages.map((msg, i) => <ChatMessage key={i} message={msg} />)}
              {pendingEdit && <ApprovalCard onAccept={handleAcceptEdit} onReject={handleRejectEdit} />}
            </>
          )}
          {isSending && <TypingIndicator />}
          <div ref={bottomRef} />
        </div>

        {messages.length === 1 && !isSending && (
          <div className="px-4 pb-2 flex flex-col gap-1 flex-shrink-0">
            {['How strong is my appeal?', 'What documents should I attach?', 'Strengthen the medical necessity section'].map((prompt) => (
              <button key={prompt} type="button" onClick={() => { setInput(prompt); inputRef.current?.focus() }}
                className="text-left text-xs px-1 py-1 transition-opacity hover:opacity-60 underline underline-offset-2" style={{ color: '#A08060', textDecorationColor: '#E8DDD5' }}>
                {prompt}
              </button>
            ))}
          </div>
        )}

        <ContextChip context={askContext} onDismiss={() => setAskContext(null)} />

        <div className="flex-shrink-0 px-3 py-3">
          <div className="flex items-end gap-2">
            <textarea ref={inputRef}
              className="flex-1 rounded-xl px-3.5 py-2.5 text-sm resize-none focus:outline-none transition"
              style={{ background: '#FFFFFF', border: '1.5px solid rgba(92,64,51,0.20)', color: '#5C4033', minHeight: 40, maxHeight: 100, lineHeight: '1.5', boxShadow: '0 1px 4px rgba(92,64,51,0.06)' }}
              rows={1} placeholder={askContext ? 'Ask about the selected passage\u2026' : 'Ask about your appeal\u2026'}
              value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={handleKeyDown} />
            <button type="button" onClick={handleSend} disabled={!canSend}
              className="flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center transition-all disabled:opacity-35 disabled:cursor-not-allowed" style={{ background: '#5C4033' }}>
              <svg className="w-3.5 h-3.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </button>
          </div>
          <p className="mt-1.5 text-center" style={{ fontSize: 10, color: '#C9B99A' }}>Enter to send · Shift+Enter for new line</p>
        </div>
      </div>

      <SelectionToolbar popup={selectionPopup} onHighlight={applyHighlight} onAskAbout={handleAskAbout} />
    </div>
  )
}
