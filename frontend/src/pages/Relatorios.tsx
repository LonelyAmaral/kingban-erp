import { useState } from 'react'
import { Typography, Card, Row, Col, Statistic, DatePicker, Button, Space, Divider, message } from 'antd'
import { BarChartOutlined, ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons'
import api from '../api/client'
import { formatCurrency, formatPercent } from '../utils/currency'

const { Title, Text } = Typography
const { RangePicker } = DatePicker

interface DRE {
  periodo: { inicio: string | null; fim: string | null }
  receita_bruta: number
  impostos: number
  custo_produtos: number
  lucro_bruto: number
  despesas_operacionais: number
  lucro_liquido: number
  quantidade_vendas: number
  margem_bruta: number
  margem_liquida: number
}

export default function Relatorios() {
  const [dre, setDre] = useState<DRE | null>(null)
  const [loading, setLoading] = useState(false)
  const [dateRange, setDateRange] = useState<[string, string] | null>(null)

  const gerarDRE = async () => {
    setLoading(true)
    try {
      const params: Record<string, any> = {}
      if (dateRange) {
        params.data_inicio = dateRange[0]
        params.data_fim = dateRange[1]
      }
      const { data } = await api.get('/reports/dre', { params })
      setDre(data)
    } catch {
      message.error('Erro ao gerar DRE')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <Title level={3}>Relatorios — DRE Simplificado</Title>

      <Space style={{ marginBottom: 16 }}>
        <RangePicker
          onChange={(dates) => {
            if (dates && dates[0] && dates[1]) {
              setDateRange([dates[0].format('YYYY-MM-DD'), dates[1].format('YYYY-MM-DD')])
            } else {
              setDateRange(null)
            }
          }}
        />
        <Button type="primary" icon={<BarChartOutlined />} onClick={gerarDRE} loading={loading}>
          Gerar DRE
        </Button>
      </Space>

      {dre && (
        <>
          <Card style={{ marginBottom: 16 }}>
            <Text type="secondary">
              Periodo: {dre.periodo.inicio || 'Inicio'} a {dre.periodo.fim || 'Hoje'} — {dre.quantidade_vendas} vendas
            </Text>
          </Card>

          {/* Linha principal */}
          <Card title="Demonstracao do Resultado do Exercicio" style={{ marginBottom: 16 }}>
            <div style={{ maxWidth: 600 }}>
              <Row justify="space-between" style={{ padding: '8px 0', borderBottom: '1px solid #f0f0f0' }}>
                <Col><Text strong>Receita Bruta</Text></Col>
                <Col><Text strong style={{ color: '#3f8600', fontSize: 18 }}>{formatCurrency(dre.receita_bruta)}</Text></Col>
              </Row>

              <Row justify="space-between" style={{ padding: '8px 0', borderBottom: '1px solid #f0f0f0', paddingLeft: 24 }}>
                <Col><Text type="danger">(-) Impostos (NF 8,5%)</Text></Col>
                <Col><Text type="danger">{formatCurrency(dre.impostos)}</Text></Col>
              </Row>

              <Row justify="space-between" style={{ padding: '8px 0', borderBottom: '1px solid #f0f0f0', paddingLeft: 24 }}>
                <Col><Text type="danger">(-) Custo dos Produtos</Text></Col>
                <Col><Text type="danger">{formatCurrency(dre.custo_produtos)}</Text></Col>
              </Row>

              <Row justify="space-between" style={{ padding: '12px 0', borderBottom: '2px solid #1677ff', background: '#f0f5ff', paddingLeft: 8, paddingRight: 8 }}>
                <Col><Text strong style={{ fontSize: 16 }}>(=) Lucro Bruto</Text></Col>
                <Col>
                  <Text strong style={{ fontSize: 16, color: dre.lucro_bruto >= 0 ? '#3f8600' : '#cf1322' }}>
                    {formatCurrency(dre.lucro_bruto)}
                  </Text>
                </Col>
              </Row>

              <Row justify="space-between" style={{ padding: '8px 0', borderBottom: '1px solid #f0f0f0', paddingLeft: 24 }}>
                <Col><Text type="danger">(-) Despesas Operacionais</Text></Col>
                <Col><Text type="danger">{formatCurrency(dre.despesas_operacionais)}</Text></Col>
              </Row>

              <Row justify="space-between" style={{ padding: '12px 0', borderBottom: '3px solid #52c41a', background: '#f6ffed', paddingLeft: 8, paddingRight: 8 }}>
                <Col><Text strong style={{ fontSize: 18 }}>(=) LUCRO LIQUIDO</Text></Col>
                <Col>
                  <Text strong style={{ fontSize: 18, color: dre.lucro_liquido >= 0 ? '#3f8600' : '#cf1322' }}>
                    {formatCurrency(dre.lucro_liquido)}
                  </Text>
                </Col>
              </Row>
            </div>
          </Card>

          {/* Margens */}
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={8}>
              <Card>
                <Statistic
                  title="Margem Bruta"
                  value={dre.margem_bruta}
                  suffix="%"
                  precision={1}
                  valueStyle={{ color: dre.margem_bruta >= 30 ? '#3f8600' : '#faad14' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={8}>
              <Card>
                <Statistic
                  title="Margem Liquida"
                  value={dre.margem_liquida}
                  suffix="%"
                  precision={1}
                  valueStyle={{ color: dre.margem_liquida >= 15 ? '#3f8600' : dre.margem_liquida >= 0 ? '#faad14' : '#cf1322' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={8}>
              <Card>
                <Statistic
                  title="Quantidade de Vendas"
                  value={dre.quantidade_vendas}
                />
              </Card>
            </Col>
          </Row>
        </>
      )}
    </div>
  )
}
