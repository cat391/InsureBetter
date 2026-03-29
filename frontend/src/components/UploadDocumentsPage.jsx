import { useState, useRef } from 'react'

const ACCEPTED_TYPES = '.pdf,.png,.jpg,.jpeg,.tiff,.tif'

function FileChip({ file, onRemove }) {
  const ext = file.name.split('.').pop().toUpperCase()
  return (
    <div className="flex items-center gap-2 rounded-lg border px-3 py-2 text-sm"
      style={{ background: '#FFFFFF', borderColor: '#E8DDD5' }}>
      <span className="rounded px-1.5 py-0.5 text-xs font-bold"
        style={{ background: 'rgba(92,64,51,0.10)', color: '#5C4033' }}>{ext}</span>
      <span style={{ color: '#7C6553' }} className="truncate max-w-[200px]">{file.name}</span>
      <button
        type="button"
        onClick={() => onRemove(file.name)}
        className="ml-auto transition-opacity hover:opacity-50"
        style={{ color: '#A08060' }}
        aria-label="Remove file"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  )
}

export default function UploadDocumentsPage({ onBack, onGenerate }) {
  const [files, setFiles] = useState([])
  const [isDragging, setIsDragging] = useState(false)
  const [additionalContext, setAdditionalContext] = useState('')
  const fileInputRef = useRef(null)

  const addFiles = (newFiles) => {
    const list = Array.from(newFiles)
    setFiles((prev) => {
      const existing = new Set(prev.map((f) => f.name))
      return [...prev, ...list.filter((f) => !existing.has(f.name))]
    })
  }

  const removeFile = (name) => setFiles((prev) => prev.filter((f) => f.name !== name))

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragging(false)
    addFiles(e.dataTransfer.files)
  }

  const handleDragOver = (e) => { e.preventDefault(); setIsDragging(true) }
  const handleDragLeave = () => setIsDragging(false)

  const canSubmit = files.length > 0

  return (
    <div className="min-h-screen flex flex-col">

      {/* Main */}
      <main className="flex-1 px-6 py-8">
        <div className="max-w-2xl mx-auto">
          <div className="mb-6">
            <h2 className="text-2xl font-bold mb-1" style={{ color: '#5C4033' }}>Upload Your Documents</h2>
            <p className="text-sm" style={{ color: '#7C6553' }}>
              Upload your EOB and/or denial letter. We'll read them and pull out the relevant details for your appeal.
            </p>
          </div>

          {/* File Upload Zone */}
          <div className="mb-5">
            <label className="field-label">
              EOB & Denial Letter
              <span className="ml-1 text-red-500">*</span>
            </label>
            <div
              className={`upload-zone cursor-pointer ${isDragging ? 'drag-over' : ''}`}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onClick={() => fileInputRef.current?.click()}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && fileInputRef.current?.click()}
            >
              <div className="w-14 h-14 rounded-2xl flex items-center justify-center transition-colors"
                style={{ background: isDragging ? 'rgba(92,64,51,0.10)' : '#F5F0EB' }}>
                <svg className="w-7 h-7 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                  style={{ color: isDragging ? '#7C6553' : '#C9B99A' }}>
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                    d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-medium" style={{ color: '#5C4033' }}>
                  Drag & drop files here, or{' '}
                  <span className="underline underline-offset-2 cursor-pointer" style={{ color: '#7C6553' }}>browse</span>
                </p>
                <p className="text-xs mt-1" style={{ color: '#A08060' }}>PDF, PNG, JPG, TIFF — up to 25 MB each</p>
              </div>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept={ACCEPTED_TYPES}
                className="hidden"
                onChange={(e) => addFiles(e.target.files)}
              />
            </div>

            {files.length > 0 && (
              <div className="mt-3 flex flex-col gap-2">
                {files.map((f) => (
                  <FileChip key={f.name} file={f} onRemove={removeFile} />
                ))}
              </div>
            )}
          </div>

          {/* Additional Context */}
          <div className="mb-7">
            <label className="field-label" htmlFor="context">
              Additional Claim Context
              <span className="ml-2 text-slate-400 font-normal text-xs">(optional)</span>
            </label>
            <p className="text-xs mb-2" style={{ color: '#A08060' }}>
              Prior authorizations, dates of service, physician notes, or anything else not captured in your documents.
            </p>
            <textarea
              id="context"
              className="textarea"
              rows={4}
              placeholder="e.g. My doctor confirmed this procedure was medically necessary due to a prior diagnosis of..."
              value={additionalContext}
              onChange={(e) => setAdditionalContext(e.target.value)}
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
                <span className="text-xs" style={{ color: '#C9B99A' }}>Upload at least one document to continue</span>
              )}
              <button
                type="button"
                disabled={!canSubmit}
                onClick={() => onGenerate?.({ files, additionalContext })}
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
