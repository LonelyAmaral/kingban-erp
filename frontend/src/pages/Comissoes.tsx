import { useState, useEffect } from 'react'
import { Table, Space, Typography, Button, Form, Select, DatePicker, InputNumber, Card, Row, Col, Statistic, Divider, message } from 'antd'
import { CalculatorOutlined } from '@ant-design/icons'
import api from '../api/client'
import { formatCurrency, formatPercent } from '../utils/currency'

const { Title, Text } = Typography
const { RangePicker } = DatePicker

interface Vendedor {
  id: number
  nome: string
}

interface LinhaComissao {
  venda_id: number
  data: string
  codigo_produto: string
  nome_produto: string
  quantidade: number
  preco_unitario: number
  total_venda: number
  valor_nf_unitario: number
  total_nf: number
  nome_cliente: string
  origem_envio: string
  custo_total_unitario: number
  liquido_unitario: number
  liquido_total: number
  taxa_comissao: number
  valor_comissao: number
}

interface Relatorio {
  vendedor_id: number
  nome_vendedor: string
  data_inicio: string
  data_fim: string
  total_vendas: number
  total_nf: number
  total_liquido: number
  total_comissao: number
  outras_comissoes: number
  salario_fixo: number
  gratificacao: number
  adiantamentos: number
  bruto_total: number
  saldo: number
  itens: LinhaComissao[]
}

export default function Comissoes() {
  const [vendedores, setVendedores] = useState<Vendedor[]>([])
  const [relatorio, setRelatorio] = useState<Relatorio | null>(null)
  const [loading, setLoading] = useState(false)
  const [form] = Form.useForm()

  useEffect(() => {
    api.get('/commissions/vendedores')
      .then(({ data }) => setVendedores(data))
      .catch(() => message.error('Erro ao carregar vendedores'))
  }, [])

  const gerarRelatorio = async () => {
    const v = await form.validateFields()
    if (!v.periodo || !v.periodo[0] || !v.periodo[1]) {
      message.warning('Selecione o periodo')
      return
    }
    setLoading(true)
    try {
      const { data } = await api.post('/commissions/relatorio', {
        vendedor_id: v.vendedor_id,
        data_inicio: v.periodo[0].format('YYYY-MM-DD'),
        data_fim: v.periodo[1].format('YYYY-MM-DD'),
        gratificacao: v.gratificacao || 0,
        adiantamentos: v.adiantamentos || 0,
        outras_comissoes: v.outras_comissoes || 0,
      })
      setRelatorio(data)
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Erro ao gerar relatorio')
    } finally {
      setLoading(false)
    }
  }

  const columns = [
    { title: 'Data', dataIndex: 'data', key: 'data', width: 90 },
    { title: 'Codigo', dataIndex: 'codigo_produto', key: 'codigo_produto', width: 80 },
    { title: 'Produto', dataIndex: 'nome_produto', key: 'nome_produto', ellipsis: true },
    { title: 'Qtd', dataIndex: 'quantidade', key: 'quantidade', width: 50 },
    { title: 'Preco Uni', dataIndex: 'preco_unitario', key: 'preco_unitario', width: 100, render: (v: number) => formatCurrency(v) },
    { title: 'Total Venda', dataIndex: 'total_venda', key: 'total_venda', width: 110, render: (v: number) => formatCurrency(v) },
    { title: 'NF Uni', dataIndex: 'valor_nf_unitario', key: 'valor_nf_unitario', width: 90, render: (v: number) => formatCurrency(v) },
    { title: 'Cliente', dataIndex: 'nome_cliente', key: 'nome_cliente', width: 130, ellipsis: true },
    { title: 'Origem', dataIndex: 'origem_envio', key: 'origem_envio', width: 80 },
    { title: 'Custo Uni', dataIndex: 'custo_total_unitario', key: 'custo_total_unitario', width: 90, render: (v: number) => formatCurrency(v) },
    { title: 'Liquido', dataIndex: 'liquido_total', key: 'liquido_total', width: 100, render: (v: number) => formatCurrency(v) },
    { title: 'Taxa', dataIndex: 'taxa_comissao', key: 'taxa_comissao', width: 60, render: (v: number) => formatPercent(v * 100) },
    {
      title: 'Comissao',
      dataIndex: 'valor_comissao',
      key: 'valor_comissao',
      width: 100,
      render: (v: number) => <span style={{ fontWeight: 'bold', color: v >= 0 ? '#3f8600' : '#cf1322' }}>{formatCurrency(v)}</span>,
    },
  ]

  return (
    <div>
      <Title level={3}>Comissoes</Title>

      <Card style={{ marginBottom: 16 }}>
        <Form form={form} layout="inline" style={{ flexWrap: 'wrap', gap: 8 }}>
          <Form.Item name="vendedor_id" label="Vendedor" rules={[{ required: true }]}>
            <Select style={{ width: 200 }} placeholder="Selecione..." options={vendedores.map(v => ({ value: v.id, label: v.nome }))} />
          </Form.Item>
          <Form.Item name="periodo" label="Periodo" rules={[{ required: true }]}>
            <RangePicker />
          </Form.Item>
          <Form.Item name="gratificacao" label="Gratificacao">
            <InputNumber min={0} step={0.01} style={{ width: 120 }} />
          </Form.Item>
          <Form.Item name="adiantamentos" label="Adiantamentos">
            <InputNumber min={0} step={0.01} style={{ width: 120 }} />
          </Form.Item>
          <Form.Item name="outras_comissoes" label="Outras Comissoes">
            <InputNumber min={0} step={0.01} style={{ width: 120 }} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" icon={<CalculatorOutlined />} onClick={gerarRelatorio} loading={loading}>
              Gerar Relatorio
            </Button>
          </Form.Item>
        </Form>
      </Card>

      {relatorio && (
        <>
          <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
            <Col xs={24} sm={12} lg={4}>
              <Card><Statistic title="Total Vendas" value={relatorio.total_vendas} prefix="R$" precision={2} /></Card>
            </Col>
            <Col xs={24} sm={12} lg={4}>
              <Card><Statistic title="Total Liquido" value={relatorio.total_liquido} prefix="R$" precision={2} /></Card>
            </Col>
            <Col xs={24} sm={12} lg={4}>
              <Card><Statistic title="Comissao" value={relatorio.total_comissao} prefix="R$" precision={2} valueStyle={{ color: '#3f8600' }} /></Card>
            </Col>
            <Col xs={24} sm={12} lg={4}>
              <Card><Statistic title="Salario Fixo" value={relatorio.salario_fixo} prefix="R$" precision={2} /></Card>
            </Col>
            <Col xs={24} sm={12} lg={4}>
              <Card><Statistic title="Bruto Total" value={relatorio.bruto_total} prefix="R$" precision={2} /></Card>
            </Col>
            <Col xs={24} sm={12} lg={4}>
              <Card>
                <Statistic
                  title="Saldo"
                  value={relatorio.saldo}
                  prefix="R$"
                  precision={2}
                  valueStyle={{ color: relatorio.saldo >= 0 ? '#3f8600' : '#cf1322', fontWeight: 'bold' }}
                />
              </Card>
            </Col>
          </Row>

          <Table
            dataSource={relatorio.itens}
            columns={columns}
            rowKey="venda_id"
            size="small"
            scroll={{ x: 1400 }}
            pagination={{ pageSize: 100 }}
            summary={() => (
              <Table.Summary.Row>
                <Table.Summary.Cell index={0} colSpan={5}><Text strong>TOTAIS</Text></Table.Summary.Cell>
                <Table.Summary.Cell index={5}><Text strong>{formatCurrency(relatorio.total_vendas)}</Text></Table.Summary.Cell>
                <Table.Summary.Cell index={6} colSpan={4}></Table.Summary.Cell>
                <Table.Summary.Cell index={10}><Text strong>{formatCurrency(relatorio.total_liquido)}</Text></Table.Summary.Cell>
                <Table.Summary.Cell index={11}></Table.Summary.Cell>
                <Table.Summary.Cell index={12}><Text strong style={{ color: '#3f8600' }}>{formatCurrency(relatorio.total_comissao)}</Text></Table.Summary.Cell>
              </Table.Summary.Row>
            )}
          />
        </>
      )}
    </div>
  )
}
