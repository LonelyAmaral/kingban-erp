/**
 * Formata valor para moeda brasileira: R$ 1.234,56
 */
export function formatCurrency(value: number | null | undefined): string {
  if (value == null) return 'R$ 0,00'
  return value.toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  })
}

/**
 * Formata percentual: 15,00%
 */
export function formatPercent(value: number | null | undefined): string {
  if (value == null) return '0,00%'
  return (value * 100).toLocaleString('pt-BR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }) + '%'
}
