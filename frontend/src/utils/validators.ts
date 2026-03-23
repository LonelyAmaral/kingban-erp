/**
 * Validadores de documentos brasileiros — CNPJ e CPF.
 */

function onlyDigits(value: string): string {
  return value.replace(/\D/g, '')
}

/**
 * Valida CPF brasileiro (11 digitos + 2 verificadores).
 */
export function validateCPF(cpf: string): boolean {
  const d = onlyDigits(cpf)
  if (d.length !== 11) return false
  if (/^(\d)\1{10}$/.test(d)) return false

  let sum = 0
  for (let i = 0; i < 9; i++) sum += parseInt(d[i]) * (10 - i)
  let rest = sum % 11
  const d1 = rest < 2 ? 0 : 11 - rest
  if (parseInt(d[9]) !== d1) return false

  sum = 0
  for (let i = 0; i < 10; i++) sum += parseInt(d[i]) * (11 - i)
  rest = sum % 11
  const d2 = rest < 2 ? 0 : 11 - rest
  if (parseInt(d[10]) !== d2) return false

  return true
}

/**
 * Valida CNPJ brasileiro (14 digitos + 2 verificadores).
 */
export function validateCNPJ(cnpj: string): boolean {
  const d = onlyDigits(cnpj)
  if (d.length !== 14) return false
  if (/^(\d)\1{13}$/.test(d)) return false

  const w1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
  let sum = 0
  for (let i = 0; i < 12; i++) sum += parseInt(d[i]) * w1[i]
  let rest = sum % 11
  const d1 = rest < 2 ? 0 : 11 - rest
  if (parseInt(d[12]) !== d1) return false

  const w2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
  sum = 0
  for (let i = 0; i < 13; i++) sum += parseInt(d[i]) * w2[i]
  rest = sum % 11
  const d2 = rest < 2 ? 0 : 11 - rest
  if (parseInt(d[13]) !== d2) return false

  return true
}

/**
 * Valida CPF ou CNPJ automaticamente.
 */
export function validateDocument(doc: string): { valid: boolean; type: 'CPF' | 'CNPJ' | 'INVALIDO' } {
  const d = onlyDigits(doc)
  if (d.length === 11) return { valid: validateCPF(d), type: 'CPF' }
  if (d.length === 14) return { valid: validateCNPJ(d), type: 'CNPJ' }
  return { valid: false, type: 'INVALIDO' }
}

/**
 * Formata CPF: 123.456.789-09
 */
export function formatCPF(cpf: string): string {
  const d = onlyDigits(cpf)
  if (d.length !== 11) return cpf
  return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6, 9)}-${d.slice(9)}`
}

/**
 * Formata CNPJ: 12.345.678/0001-90
 */
export function formatCNPJ(cnpj: string): string {
  const d = onlyDigits(cnpj)
  if (d.length !== 14) return cnpj
  return `${d.slice(0, 2)}.${d.slice(2, 5)}.${d.slice(5, 8)}/${d.slice(8, 12)}-${d.slice(12)}`
}

/**
 * Regra de validacao para Form.Item do Ant Design.
 */
export const cnpjCpfRule = {
  validator: (_: any, value: string) => {
    if (!value || value.trim() === '') return Promise.resolve()
    const { valid } = validateDocument(value)
    if (valid) return Promise.resolve()
    return Promise.reject(new Error('CPF ou CNPJ invalido'))
  },
}
