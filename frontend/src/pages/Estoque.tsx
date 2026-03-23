import { useState, useEffect } from 'react'
import { Table, Tabs, Input, Space, Typography, Tag, Button, Modal, Form, Select, InputNumber, DatePicker, message } from 'antd'
import { SearchOutlined, PlusOutlined, WarningOutlined } from '@ant-design/icons'
import api from '../api/client'
import { formatCurrency } from '../utils/currency'
import dayjs from 'dayjs'

const { Title } = Typography

interface EstoqueAtual {
  codigo: string
  nome: string
  categoria: string | null
  quantidade_atual: number
  preco_unitario: number
  valor_total: number
  quantidade_minima: number
  ultima_entrada: string | null
  ultima_saida: string | null
}

interface Entrada {
  id: number
  data: string
  codigo_produto: string
  nome_produto: string
  quantidade: number
  tipo_entrada: string
  observacoes: string | null
}

interface Saida {
  id: number
  data: string
  codigo_produto: string
  nome_produto: string
  quantidade: number
  nome_cliente: string | null
  tipo_saida: string
  observacoes: string | null
}

const ENTRY_TYPES = ['Compra', 'Item Montagem', 'Devolucao', 'Ajuste', 'Cancelamento Reserva']
const EXIT_TYPES = ['BAIXA DE VENDA', 'Reserva de Pedido', 'Ajuste', 'Perda', 'Devolucao Fornecedor']

export default function Estoque() {
  const [saldo, setSaldo] = useState<EstoqueAtual[]>([])
  const [entradas, setEntradas] = useState<Entrada[]>([])
  const [saidas, setSaidas] = useState<Saida[]>([])
  const [loading, setLoading] = useState(false)
  const [busca, setBusca] = useState('')
  const [entradaModal, setEntradaModal] = useState(false)
  const [saidaModal, setSaidaModal] = useState(false)
  const [formEntrada] = Form.useForm()
  const [formSaida] = Form.useForm()

  const fetchSaldo = async () => {
    setLoading(true)
    try {
      const params: Record<string, any> = {}
      if (busca) params.busca = busca
      const { data } = await api.get('/inventory/saldo', { params })
      setSaldo(data)
    } catch { message.error('Erro ao carregar saldo') }
    finally { setLoading(false) }
  }

  const fetchEntradas = async () => {
    try {
      const { data } = await api.get('/inventory/entradas', { params: { por_pagina: 100 } })
      setEntradas(data.itens)
    } catch { message.error('Erro ao carregar entradas') }
  }

  const fetchSaidas = async () => {
    try {
      const { data } = await api.get('/inventory/saidas', { params: { por_pagina: 100 } })
      setSaidas(data.itens)
    } catch { message.error('Erro ao carregar saidas') }
  }

  useEffect(() => { fetchSaldo() }, [busca])

  const criarEntrada = async () => {
    const v = await formEntrada.validateFields()
    try {
      await api.post('/inventory/entradas', {
        produto_id: v.produto_id,
        quantidade: v.quantidade,
        tipo_entrada: v.tipo_entrada,
        data: v.data?.format('YYYY-MM-DD') || null,
        observacoes: v.observacoes || '',
      })
      message.success('Entrada registrada!')
      setEntradaModal(false)
      formEntrada.resetFields()
      fetchSaldo()
      fetchEntradas()
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Erro ao criar entrada')
    }
  }

  const criarSaida = async () => {
    const v = await formSaida.validateFields()
    try {
      await api.post('/inventory/saidas', {
        produto_id: v.produto_id,
        quantidade: v.quantidade,
        tipo_saida: v.tipo_saida,
        nome_cliente: v.nome_cliente || '',
        data: v.data?.format('YYYY-MM-DD') || null,
        observacoes: v.observacoes || '',
      })
      message.success('Saida registrada!')
      setSaidaModal(false)
      formSaida.resetFields()
      fetchSaldo()
      fetchSaidas()
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Erro ao criar saida')
    }
  }

  const saldoCols = [
    { title: 'Codigo', dataIndex: 'codigo', key: 'codigo', width: 90 },
    { title: 'Produto', dataIndex: 'nome', key: 'nome' },
    { title: 'Categoria', dataIndex: 'categoria', key: 'categoria', width: 130 },
    {
      title: 'Qtd Atual',
      dataIndex: 'quantidade_atual',
      key: 'quantidade_atual',
      width: 90,
      render: (v: number, r: EstoqueAtual) => (
        <span style={{ color: v <= r.quantidade_minima ? '#cf1322' : undefined, fontWeight: v <= r.quantidade_minima ? 'bold' : undefined }}>
          {v} {v <= r.quantidade_minima && <WarningOutlined />}
        </span>
      ),
    },
    { title: 'Preco', dataIndex: 'preco_unitario', key: 'preco_unitario', width: 110, render: (v: number) => formatCurrency(v) },
    { title: 'Valor Total', dataIndex: 'valor_total', key: 'valor_total', width: 120, render: (v: number) => formatCurrency(v) },
    { title: 'Ult. Entrada', dataIndex: 'ultima_entrada', key: 'ultima_entrada', width: 110 },
    { title: 'Ult. Saida', dataIndex: 'ultima_saida', key: 'ultima_saida', width: 110 },
  ]

  const entradaCols = [
    { title: 'Data', dataIndex: 'data', key: 'data', width: 100 },
    { title: 'Codigo', dataIndex: 'codigo_produto', key: 'codigo_produto', width: 90 },
    { title: 'Produto', dataIndex: 'nome_produto', key: 'nome_produto' },
    { title: 'Qtd', dataIndex: 'quantidade', key: 'quantidade', width: 70 },
    { title: 'Tipo', dataIndex: 'tipo_entrada', key: 'tipo_entrada', width: 150 },
    { title: 'Obs', dataIndex: 'observacoes', key: 'observacoes', width: 200 },
  ]

  const saidaCols = [
    { title: 'Data', dataIndex: 'data', key: 'data', width: 100 },
    { title: 'Codigo', dataIndex: 'codigo_produto', key: 'codigo_produto', width: 90 },
    { title: 'Produto', dataIndex: 'nome_produto', key: 'nome_produto' },
    { title: 'Qtd', dataIndex: 'quantidade', key: 'quantidade', width: 70 },
    { title: 'Cliente', dataIndex: 'nome_cliente', key: 'nome_cliente', width: 150 },
    { title: 'Tipo', dataIndex: 'tipo_saida', key: 'tipo_saida', width: 150 },
  ]

  return (
    <div>
      <Title level={3}>Estoque</Title>

      <Tabs
        items={[
          {
            key: 'saldo',
            label: 'Saldo Atual',
            children: (
              <>
                <Space style={{ marginBottom: 16 }}>
                  <Input placeholder="Buscar..." prefix={<SearchOutlined />} allowClear onChange={(e) => setBusca(e.target.value)} style={{ width: 250 }} />
                </Space>
                <Table dataSource={saldo} columns={saldoCols} rowKey="codigo" loading={loading} size="middle" scroll={{ x: 900 }} pagination={{ pageSize: 100 }} />
              </>
            ),
          },
          {
            key: 'entradas',
            label: 'Entradas',
            children: (
              <>
                <Button type="primary" icon={<PlusOutlined />} onClick={() => setEntradaModal(true)} style={{ marginBottom: 16 }}>
                  Nova Entrada
                </Button>
                <Table dataSource={entradas} columns={entradaCols} rowKey="id" size="middle" scroll={{ x: 700 }} pagination={{ pageSize: 50 }}
                  onchange={() => fetchEntradas()} />
              </>
            ),
          },
          {
            key: 'saidas',
            label: 'Saidas',
            children: (
              <>
                <Button type="primary" icon={<PlusOutlined />} onClick={() => setSaidaModal(true)} style={{ marginBottom: 16 }}>
                  Nova Saida
                </Button>
                <Table dataSource={saidas} columns={saidaCols} rowKey="id" size="middle" scroll={{ x: 700 }} pagination={{ pageSize: 50 }} />
              </>
            ),
          },
        ]}
        onChange={(key) => {
          if (key === 'entradas') fetchEntradas()
          if (key === 'saidas') fetchSaidas()
        }}
      />

      <Modal title="Nova Entrada" open={entradaModal} onOk={criarEntrada} onCancel={() => setEntradaModal(false)} okText="Salvar" cancelText="Cancelar">
        <Form form={formEntrada} layout="vertical">
          <Form.Item name="produto_id" label="ID do Produto" rules={[{ required: true }]}>
            <InputNumber style={{ width: '100%' }} min={1} />
          </Form.Item>
          <Form.Item name="quantidade" label="Quantidade" rules={[{ required: true }]}>
            <InputNumber style={{ width: '100%' }} min={1} />
          </Form.Item>
          <Form.Item name="tipo_entrada" label="Tipo" rules={[{ required: true }]}>
            <Select options={ENTRY_TYPES.map(t => ({ value: t, label: t }))} />
          </Form.Item>
          <Form.Item name="data" label="Data">
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="observacoes" label="Observacoes">
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal title="Nova Saida" open={saidaModal} onOk={criarSaida} onCancel={() => setSaidaModal(false)} okText="Salvar" cancelText="Cancelar">
        <Form form={formSaida} layout="vertical">
          <Form.Item name="produto_id" label="ID do Produto" rules={[{ required: true }]}>
            <InputNumber style={{ width: '100%' }} min={1} />
          </Form.Item>
          <Form.Item name="quantidade" label="Quantidade" rules={[{ required: true }]}>
            <InputNumber style={{ width: '100%' }} min={1} />
          </Form.Item>
          <Form.Item name="tipo_saida" label="Tipo" rules={[{ required: true }]}>
            <Select options={EXIT_TYPES.map(t => ({ value: t, label: t }))} />
          </Form.Item>
          <Form.Item name="nome_cliente" label="Cliente">
            <Input />
          </Form.Item>
          <Form.Item name="data" label="Data">
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="observacoes" label="Observacoes">
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
