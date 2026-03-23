import { useState, useEffect } from 'react'
import { Table, Input, Space, Typography, DatePicker, Card, Row, Col, Statistic, message } from 'antd'
import { SearchOutlined, DollarOutlined, PercentageOutlined } from '@ant-design/icons'
import api from '../api/client'
import { formatCurrency } from '../utils/currency'
import dayjs from 'dayjs'

const { Title } = Typography
const { RangePicker } = DatePicker

interface Venda {
  id: number
  data: string
  numero_pedido: number | null
  nome_cliente: string | null
  codigo_produto: string | null
  nome_produto: string | null
  quantidade: number
  preco_unitario: number
  valor_total: number
  custo_total: number
  imposto: number
  lucro_total: number
  forma_pagamento: string | null
}

interface Resumo {
  total_vendas: number
  total_custos: number
  total_impostos: number
  total_lucro: number
  quantidade_vendas: number
}

export default function Vendas() {
  const [data, setData] = useState<Venda[]>([])
  const [resumo, setResumo] = useState<Resumo | null>(null)
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [pagina, setPagina] = useState(1)
  const [porPagina, setPorPagina] = useState(50)
  const [busca, setBusca] = useState('')
  const [dateRange, setDateRange] = useState<[string, string] | null>(null)

  const fetchData = async () => {
    setLoading(true)
    try {
      const params: Record<string, any> = { pagina, por_pagina: porPagina }
      if (busca) params.busca = busca
      if (dateRange) {
        params.data_inicio = dateRange[0]
        params.data_fim = dateRange[1]
      }

      const [listRes, resumoRes] = await Promise.all([
        api.get('/sales', { params }),
        api.get('/sales/resumo', { params: dateRange ? { data_inicio: dateRange[0], data_fim: dateRange[1] } : {} }),
      ])
      setData(listRes.data.itens)
      setTotal(listRes.data.total)
      setResumo(resumoRes.data)
    } catch {
      message.error('Erro ao carregar vendas')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchData() }, [pagina, porPagina, busca, dateRange])

  const columns = [
    { title: 'Data', dataIndex: 'data', key: 'data', width: 100 },
    { title: 'Pedido', dataIndex: 'numero_pedido', key: 'numero_pedido', width: 80, render: (v: number | null) => v ? `#${v}` : '-' },
    { title: 'Cliente', dataIndex: 'nome_cliente', key: 'nome_cliente' },
    { title: 'Produto', dataIndex: 'nome_produto', key: 'nome_produto' },
    { title: 'Qtd', dataIndex: 'quantidade', key: 'quantidade', width: 60 },
    { title: 'Valor', dataIndex: 'valor_total', key: 'valor_total', width: 120, render: (v: number) => formatCurrency(v) },
    { title: 'Custo', dataIndex: 'custo_total', key: 'custo_total', width: 110, render: (v: number) => formatCurrency(v) },
    { title: 'Imposto', dataIndex: 'imposto', key: 'imposto', width: 100, render: (v: number) => formatCurrency(v) },
    { title: 'Lucro', dataIndex: 'lucro_total', key: 'lucro_total', width: 110, render: (v: number) => formatCurrency(v) },
    { title: 'Pagamento', dataIndex: 'forma_pagamento', key: 'forma_pagamento', width: 140 },
  ]

  return (
    <div>
      <Title level={3}>Vendas</Title>

      {resumo && (
        <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
          <Col xs={24} sm={12} lg={6}>
            <Card><Statistic title="Total Vendas" value={resumo.total_vendas} prefix="R$" precision={2} /></Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card><Statistic title="Total Custos" value={resumo.total_custos} prefix="R$" precision={2} /></Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card><Statistic title="Total Impostos" value={resumo.total_impostos} prefix="R$" precision={2} /></Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Lucro Total"
                value={resumo.total_lucro}
                prefix="R$"
                precision={2}
                valueStyle={{ color: resumo.total_lucro >= 0 ? '#3f8600' : '#cf1322' }}
              />
            </Card>
          </Col>
        </Row>
      )}

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
        <Input
          placeholder="Buscar cliente ou produto..."
          prefix={<SearchOutlined />}
          allowClear
          onChange={(e) => setBusca(e.target.value)}
          style={{ width: 250 }}
        />
      </Space>

      <Table
        dataSource={data}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={{
          current: pagina,
          pageSize: porPagina,
          total,
          showSizeChanger: true,
          showTotal: (t) => `Total: ${t} vendas`,
          onChange: (p, s) => { setPagina(p); setPorPagina(s) },
        }}
        size="middle"
        scroll={{ x: 1100 }}
      />
    </div>
  )
}
