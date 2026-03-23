import { useState, useEffect } from 'react'
import { Table, Space, Typography, Button, Form, Select, InputNumber, Card, Row, Col, Statistic, Divider, message } from 'antd'
import { CalculatorOutlined } from '@ant-design/icons'
import api from '../api/client'
import { formatCurrency, formatPercent } from '../utils/currency'

const { Title, Text } = Typography

interface Estado {
  uf: string
  nome: string
  ncm: string
  aliq_interna: number
  aliq_inter: number
  fcp: number
  formula_especial: string | null
}

interface ResultadoDifal {
  estado: string
  valor_produto: number
  ncm: string
  aliq_interna: number
  aliq_inter: number
  fcp: number
  valor_difal: number
  valor_fcp: number
  valor_total: number
  formula_usada: string
}

const NCM_OPTIONS = [
  { value: '94037000', label: '94037000 — Banheiro Quimico' },
  { value: '94069090', label: '94069090 — Outros' },
]

export default function Difal() {
  const [estados, setEstados] = useState<Estado[]>([])
  const [resultado, setResultado] = useState<ResultadoDifal | null>(null)
  const [loading, setLoading] = useState(false)
  const [ncmFilter, setNcmFilter] = useState('94037000')
  const [form] = Form.useForm()

  const fetchEstados = async () => {
    try {
      const { data } = await api.get('/difal/estados', { params: { ncm: ncmFilter } })
      setEstados(data)
    } catch { message.error('Erro ao carregar estados') }
  }

  useEffect(() => { fetchEstados() }, [ncmFilter])

  const calcular = async () => {
    const v = await form.validateFields()
    setLoading(true)
    try {
      const { data } = await api.post('/difal/calcular', {
        estado_destino: v.estado,
        valor: v.valor,
        ncm: v.ncm || '94037000',
      })
      setResultado(data)
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Erro ao calcular DIFAL')
    } finally {
      setLoading(false)
    }
  }

  const estadoColumns = [
    { title: 'UF', dataIndex: 'uf', key: 'uf', width: 60 },
    { title: 'Estado', dataIndex: 'nome', key: 'nome' },
    { title: 'NCM', dataIndex: 'ncm', key: 'ncm', width: 100 },
    { title: 'Aliq. Interna', dataIndex: 'aliq_interna', key: 'aliq_interna', width: 110, render: (v: number) => formatPercent(v * 100) },
    { title: 'Aliq. Inter', dataIndex: 'aliq_inter', key: 'aliq_inter', width: 100, render: (v: number) => formatPercent(v * 100) },
    { title: 'FCP', dataIndex: 'fcp', key: 'fcp', width: 80, render: (v: number) => v > 0 ? formatPercent(v * 100) : '-' },
    { title: 'Formula', dataIndex: 'formula_especial', key: 'formula_especial', width: 80, render: (v: string | null) => v || 'Padrao' },
  ]

  return (
    <div>
      <Title level={3}>DIFAL — Calculadora</Title>

      <Card style={{ marginBottom: 16 }}>
        <Form form={form} layout="inline" style={{ flexWrap: 'wrap', gap: 8 }}>
          <Form.Item name="estado" label="Estado Destino" rules={[{ required: true }]}>
            <Select
              style={{ width: 200 }}
              placeholder="Selecione o estado..."
              showSearch
              optionFilterProp="label"
              options={estados.map(e => ({ value: e.uf, label: `${e.uf} — ${e.nome}` }))}
            />
          </Form.Item>
          <Form.Item name="valor" label="Valor do Produto (R$)" rules={[{ required: true }]}>
            <InputNumber style={{ width: 180 }} min={0.01} step={10} />
          </Form.Item>
          <Form.Item name="ncm" label="NCM" initialValue="94037000">
            <Select style={{ width: 280 }} options={NCM_OPTIONS} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" icon={<CalculatorOutlined />} onClick={calcular} loading={loading}>
              Calcular
            </Button>
          </Form.Item>
        </Form>
      </Card>

      {resultado && (
        <Card title={`Resultado — ${resultado.estado}`} style={{ marginBottom: 16 }}>
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={8}>
              <Statistic title="Valor Produto" value={resultado.valor_produto} prefix="R$" precision={2} />
            </Col>
            <Col xs={24} sm={8}>
              <Statistic
                title="DIFAL"
                value={resultado.valor_difal}
                prefix="R$"
                precision={2}
                valueStyle={{ color: '#cf1322' }}
              />
            </Col>
            <Col xs={24} sm={8}>
              <Statistic
                title="FCP"
                value={resultado.valor_fcp}
                prefix="R$"
                precision={2}
                valueStyle={{ color: resultado.valor_fcp > 0 ? '#cf1322' : undefined }}
              />
            </Col>
            <Col xs={24} sm={8}>
              <Statistic
                title="Total DIFAL + FCP"
                value={resultado.valor_total}
                prefix="R$"
                precision={2}
                valueStyle={{ color: '#cf1322', fontWeight: 'bold', fontSize: 24 }}
              />
            </Col>
            <Col xs={24} sm={8}>
              <Statistic title="Aliq. Interna" value={resultado.aliq_interna * 100} suffix="%" precision={1} />
            </Col>
            <Col xs={24} sm={8}>
              <Text>Formula: <Text strong>{resultado.formula_usada === 'MG' ? 'Especial MG (1/3)' : 'Padrao'}</Text></Text>
            </Col>
          </Row>
        </Card>
      )}

      <Divider>Aliquotas por Estado</Divider>

      <Space style={{ marginBottom: 16 }}>
        <Select
          value={ncmFilter}
          onChange={setNcmFilter}
          style={{ width: 280 }}
          options={NCM_OPTIONS}
        />
      </Space>

      <Table
        dataSource={estados}
        columns={estadoColumns}
        rowKey={(r) => `${r.uf}-${r.ncm}`}
        size="small"
        pagination={false}
        scroll={{ x: 600 }}
      />
    </div>
  )
}
