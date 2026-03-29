const KNOWN_CARC_CODES = new Set([
  '197','15','27','204','198','50','150','151','54','167','146',
  '11','22','109','24','119','5','4','16','97','18','45','6','7',
  '8','9','125','181','29','39','55','56','183','188','26','96',
  '1','2','3','31','32','33','170','186',
])

function validateDenialCodes(value) {
  if (!value.trim()) return null
  const tokens = value.split(/[,;]/).map((t) => t.trim()).filter(Boolean)
  const warnings = []

  for (const token of tokens) {
    // Try to extract numeric code from various formats
    const prefixMatch = token.match(/^(CO|PR|OA|PI)[-\s]?(\d{1,3})$/i)
    const carcMatch = token.match(/^CARC\s*(\d{1,3})$/i)
    const bareMatch = token.match(/^(\d{1,3})$/)

    const code = prefixMatch?.[2] ?? carcMatch?.[1] ?? bareMatch?.[1]

    if (!code) {
      warnings.push(`"${token}" doesn't look like a denial code (expected: CO-50, PR-96, or 50)`)
    } else if (!KNOWN_CARC_CODES.has(code)) {
      warnings.push(`Code ${code} not in our reference list — may still be valid`)
    }

    if (warnings.length >= 3) break
  }

  return warnings.length ? warnings.join('. ') : null
}

function validateCPTCodes(value) {
  if (!value.trim()) return null
  const tokens = value.split(/[,;]/).map((t) => t.trim()).filter(Boolean)
  const warnings = []

  for (const token of tokens) {
    const cleaned = token.replace(/^CPT[-\s]*/i, '').trim()
    // Allow optional description in parens: "27447 (total knee replacement)"
    const codeOnly = cleaned.replace(/\s*\(.*\)$/, '')
    if (!/^\d{5}$/.test(codeOnly)) {
      warnings.push(`"${token}" — CPT codes are 5 digits (e.g. 27447)`)
    }
    if (warnings.length >= 3) break
  }

  return warnings.length ? warnings.join('. ') : null
}

function validateICD10Codes(value) {
  if (!value.trim()) return null
  const tokens = value.split(/[,;]/).map((t) => t.trim()).filter(Boolean)
  const warnings = []

  for (const token of tokens) {
    // Strip optional description after dash or em-dash
    const codeOnly = token.replace(/\s*[—–-]\s+.*$/, '').trim()
    if (!/^[A-TV-Z]\d{2}(\.\d{1,4})?$/i.test(codeOnly)) {
      warnings.push(`"${token}" — expected ICD-10 format (e.g. M17.11, E11.9)`)
    }
    if (warnings.length >= 3) break
  }

  return warnings.length ? warnings.join('. ') : null
}

function validateDateOfService(value) {
  if (!value.trim()) return null

  let date = null
  // YYYY-MM-DD
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    date = new Date(value + 'T00:00:00')
  }
  // MM/DD/YYYY or MM-DD-YYYY
  const mdyMatch = value.match(/^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$/)
  if (mdyMatch) {
    date = new Date(`${mdyMatch[3]}-${mdyMatch[1].padStart(2, '0')}-${mdyMatch[2].padStart(2, '0')}T00:00:00`)
  }

  if (!date || isNaN(date.getTime())) {
    return 'Unrecognized date format (expected YYYY-MM-DD or MM/DD/YYYY)'
  }

  const today = new Date()
  today.setHours(23, 59, 59, 999)
  if (date > today) {
    return 'Date of service is in the future'
  }

  return null
}

function validateMemberID(value) {
  if (!value.trim()) return null
  if (value.trim().length < 2) return 'Member ID seems too short'
  if (value.trim().length > 30) return 'Member ID seems too long'
  return null
}

function validateInsurancePlan() {
  return null
}

export const FIELD_VALIDATORS = {
  'Denial Code(s)': validateDenialCodes,
  'Procedure / CPT Code': validateCPTCodes,
  'Diagnosis / ICD-10 Code': validateICD10Codes,
  'Date of Service': validateDateOfService,
  'Insurance Plan & Group Number': validateInsurancePlan,
  'Member ID': validateMemberID,
}
