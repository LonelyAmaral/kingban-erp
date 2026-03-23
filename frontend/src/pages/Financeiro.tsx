import { useState, useEffect } from 'react'
import { Table, Tabs, Input, Space, Typography, Tag, Button, Modal, Form, Select, InputNumber, DatePicker, message } from 'antd'
import { SearchOutlined, PlusOutlined, DollarOutlined } from '@ant-design/icons'
import api from '../api/client'
import { formatCurrency } from '../utils/currency'
import dayjs from 'dayjs'

const { Title } = Typography

interface Conta {
  id: number
  tipo: string
  descricao: string | null
  pedido_id: number | null
  compra_id: number | null
  cliente_ou_fornecedor: string | null
  vencimento: string | null
  valor: number
  valor_pago: number
  status: string
  data_pagamento: string | null
  observacoes: string | null
  criado_em: string | null
}

const STATUS_COLORS: Record<string, string> = {
  PENDING: 'orange',
  PARTIAL: 'blue',
  PAID: 'green',
  OVERDUE: 'red',
}

const STATUS_LABELS: Record<string, string> = {
  PENDING: 'Pendente',
  PARTIAL: 'Parcial',
  PAID: 'Pago',
  OVERDUE: 'Vencido',
}

export default function Financeiro() {
  const [contas, setContas] = useState<Conta[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [pagina, setPagina] = useState(1)
  const [busca, setBusca] = useState('')
  const [tipoFilter, setTipoFilter] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<string | null>(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [pagamentoModal, setPagamentoModal] = useState<Conta | null>(null)
  const [form] = Form.useForm()
  const [formPag] = Form.useForm()

  const fetchContas = async () => {
    setLoading(true)
    try {
      const params: Record<string, any> = { pagina, por_pagina: 50 }
      if (busca) params.busca = busca
      if (tipoFilter) params.tipo = tipoFilter
      if (statusFilter) params.status = statusFilter
      const { data } = await api.get('/accounts', { params })
      setContas(data.itens)
      setTotal(data.total)
    } catch { message.error('Erro ao carregar contas') }
    finally { setLoading(false) }
  }

  useEffect(() => { fetchContas() }, [pagina, busca, tipoFilter, statusFilter])

  const criarConta = async () => {
    const v = await form.validateFields()
    try {
      await api.post('/accounts', {
        tipo: v.tipo,
        descricao: v.descricao,
        cliente_ou_fornecedor: v.cliente_ou_fornecedor || '',
        vencimento: v.vencimento?.format('YYYY-MM-DD'),
        valor: v.valor,
        observacoes: v.observacoes || '',
      })
      message.success('Conta criada!')
      setModalOpen(false)
      form.resetFields()
      fetchContas()
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Erro ao criar conta')
    }
  }

  const registrarPagamento = async () => {
    if (!pagamentoModal) return
    const v = await formPag.validateFields()
    try {
      await api.post(`/accounts/${pagamentoModal.id}/pagamento`, {
        valor_pago: v.valor_pago,
        data_pagamento: v.data_pagamento?.format('YYYY-MM-DD') || null,
      })
      message.success('Pagamento registrado!')
      setPagamentoModal(null)
      formPag.resetFields()
      fetchContas()
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Erro ao registrar pagamento')
    }
  }

  const columns = [
    {
      title: 'Tipo',
      dataIndex: 'tipo',
      key: 'tipo',
      width: 100,
      render: (v: string) => (
        <Tag color={v === 'RECEIVABLE' ? 'green' : 'red'}>
          {v === 'RECEIVABLE' ? 'Receber' : 'Pagar'}
        </Tag>
      ),
    },
    { title: 'Descricao', dataIndex: 'descricao', key: 'descricao' },
    { title: 'Cliente/Fornecedor', dataIndex: 'cliente_ou_fornecedor', key: 'cliente_ou_fornecedor', width: 180 },
    { title: 'Vencimento', dataIndex: 'vencimento', key: 'vencimento', width: 110 },
    { title: 'Valor', dataIndex: 'valor', key: 'valor', width: 120, render: (v: number) => formatCurrency(v) },
    { title: 'Pago', dataIndex: 'valor_pago', key: 'valor_pago', width: 120, render: (v: number) => formatCurrency(v) },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (v: string) => <Tag color={STATUS_COLORS[v]}>{STATUS_LABELS[v] || v}</Tag>,
    },
    {
      title: 'Acoes',
      key: 'acoes',
      width: 120,
      render: (_: any, record: Conta) =>
        record.status !== 'PAID' && (
          <Button
            type="link"
            icon={<DollarOutlined />}
            onClick={() => {
              setPagamentoModal(record)
              formPag.setFieldsValue({ valor_pago: record.valor - record.valor_pago })
            }}
          >
            Pagar
          </Button>
        ),
    },
  ]

  return (
    <div>
      <Title level={3}>Financeiro — Contas</Title>

      <Space style={{ marginBottom: 16 }} wrap>
        <Input
          placeholder="Buscar..."
          prefix={<SearchOutlined />}
          allowClear
          onChange={(e) => setBusca(e.target.value)}
          style={{ width: 220 }}
        />
        <Select
          placeholder="Tipo"
          allowClear
          style={{ width: 140 }}
          onChange={(v) => setTipoFilter(v || null)}
          options={[
            { value: 'RECEIVABLE', label: 'A Receber' },
            { value: 'PAYABLE', label: 'A Pagar' },
          ]}
        />
        <Select
          placeholder="Status"
          allowClear
          style={{ width: 140 }}
          onChange={(v) => setStatusFilter(v || null)}
          options={[
            { value: 'PENDING', label: 'Pendente' },
            { value: 'PARTIAL', label: 'Parcial' },
            { value: 'PAID', label: 'Pago' },
            { value: 'OVERDUE', label: 'Vencido' },
          ]}
        />
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
          Nova Conta
        </Button>
      </Space>

      <Table
        dataSource={contas}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={{
          current: pagina,
          pageSize: 50,
          total,
          showTotal: (t) => `Total: ${t} contas`,
          onChange: (p) => setPagina(p),
        }}
        size="middle"
        scroll={{ x: 1100 }}
      />

      {/* Modal Nova Conta */}
      <Modal title="Nova Conta" open={modalOpen} onOk={criarConta} onCancel={() => setModalOpen(false)} okText="Salvar" cancelText="Cancelar">
        <Form form={form} layout="vertical">
          <Form.Item name="tipo" label="Tipo" rules={[{ required: true }]}>
            <Select options={[
              { value: 'RECEIVABLE', label: 'A Receber' },
              { value: 'PAYABLE', label: 'A Pagar' },
            ]} />
          </Form.Item>
          <Form.Item name="descricao" label="Descricao" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="cliente_ou_fornecedor" label="Cliente/Fornecedor">
            <Input />
          </Form.Item>
          <Form.Item name="vencimento" label="Vencimento" rules={[{ required: true }]}>
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="valor" label="Valor (R$)" rules={[{ required: true }]}>
            <InputNumber style={{ width: '100%' }} min={0.01} step={0.01} />
          </Form.Item>
          <Form.Item name="observacoes" label="Observacoes">
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>

      {/* Modal Pagamento */}
      <Modal
        title={`Pagamento — ${pagamentoModal?.descricao || ''}`}
        open={!!pagamentoModal}
        onOk={registrarPagamento}
        onCancel={() => { setPagamentoModal(null); formPag.resetFields() }}
        okText="Registrar"
        cancelText="Cancelar"
      >
        <Form form={formPag} layout="vertical">
          <Form.Item name="valor_pago" label="Valor do Pagamento (R$)" rules={[{ required: true }]}>
            <InputNumber style={{ width: '100%' }} min={0.01} step={0.01} />
          </Form.Item>
          <Form.Item name="data_pagamento" label="Data do Pagamento">
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
