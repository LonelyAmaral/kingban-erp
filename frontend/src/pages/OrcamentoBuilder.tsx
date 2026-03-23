import { useState, useEffect, useCallback } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  Form, Input, InputNumber, Select, Button, Table, Space, Typography, Card,
  DatePicker, message, Row, Col, Divider, Popconfirm, TextArea, Table as AntTable,
} from 'antd'
import {
  PlusOutlined, DeleteOutlined, SaveOutlined, ArrowLeftOutlined, SearchOutlined,
  PrinterOutlined, FileTextOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import api from '../api/client'

const { Title, Text } = Typography

interface Produto {
  id: number
  codigo: string
  nome: string
  categoria: string
  unidade: string
  custo: number
  preco_nf_integral: number
  preco_nf_baixa_1_3: number
  preco_nf_baixa_4: number
  preco_nf_cheia_4: number
  preco_nf_integral_10: number
  preco_nf_baixa_10: number
  preco_fabrica_10: number
  taxa_comissao: number
  frete: number
}

interface ItemPedido {
  key: string
  ordem: number
  produto_id: number | null
  codigo_produto: string
  nome_produto: string
  quantidade: number
  unidade: string
  preco_unitario: number
  desconto: number
  total: number
  custo_unitario: number
  custo_total: number
  valor_nf_unitario: number
}

interface Cliente {
  id: number
  nome: string
  cnpj_cpf?: string
  cidade?: string
  estado?: string
}

interface Vendedor {
  id: number
  nome: string
}

const NF_TYPES = [
  { value: 'NF INTEGRAL', label: 'NF Integral' },
  { value: 'NF BAIXA 1-3', label: 'NF Baixa (1-3 un)' },
  { value: 'NF BAIXA 4+', label: 'NF Baixa (4+ un)' },
  { value: 'NF CHEIA 4+', label: 'NF Cheia (4+ un)' },
  { value: 'NF INTEGRAL 10+', label: 'NF Integral (10+ un)' },
  { value: 'NF BAIXA 10+', label: 'NF Baixa (10+ un)' },
  { value: 'FABRICA 10+', label: 'Fabrica (10+ un)' },
]

const SHIPPING_ORIGINS = [
  { value: 'FABRICA', label: 'Fabrica' },
  { value: 'DEPOSITO', label: 'Deposito' },
]

const PAYMENT_METHODS = [
  { value: 'PIX OU DEPOSITO BANCARIO', label: 'PIX / Deposito' },
  { value: 'BOLETO', label: 'Boleto' },
  { value: 'CARTAO', label: 'Cartao' },
  { value: 'OUTROS', label: 'Outros' },
]

const formatCurrency = (v: number) =>
  v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

let itemCounter = 0
const newItem = (): ItemPedido => ({
  key: `item-${++itemCounter}`,
  ordem: 0,
  produto_id: null,
  codigo_produto: '',
  nome_produto: '',
  quantidade: 1,
  unidade: 'UN',
  preco_unitario: 0,
  desconto: 0,
  total: 0,
  custo_unitario: 0,
  custo_total: 0,
  valor_nf_unitario: 0,
})

export default function OrcamentoBuilder() {
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  const isEditing = !!id

  const [form] = Form.useForm()
  const [itens, setItens] = useState<ItemPedido[]>([newItem()])
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [vendedores, setVendedores] = useState<Vendedor[]>([])
  const [produtos, setProdutos] = useState<Produto[]>([])
  const [proximoNumero, setProximoNumero] = useState(1)
  const [saving, setSaving] = useState(false)
  const [buscaProduto, setBuscaProduto] = useState('')

  // Load data on mount
  useEffect(() => {
    loadInitialData()
  }, [])

  useEffect(() => {
    if (isEditing) loadOrder()
  }, [id])

  const loadInitialData = async () => {
    try {
      const [clientesRes, vendedoresRes, produtosRes, numRes] = await Promise.all([
        api.get('/clients', { params: { por_pagina: 500 } }),
        api.get('/salespeople', { params: { por_pagina: 100 } }),
        api.get('/products', { params: { por_pagina: 500 } }),
        api.get('/orders/proximo-numero'),
      ])
      setClientes(clientesRes.data.itens || clientesRes.data)
      setVendedores(vendedoresRes.data.itens || vendedoresRes.data)
      setProdutos(produtosRes.data.itens || produtosRes.data)
      setProximoNumero(numRes.data.proximo_numero)
      if (!isEditing) {
        form.setFieldsValue({ numero: numRes.data.proximo_numero })
      }
    } catch {
      message.error('Erro ao carregar dados')
    }
  }

  const loadOrder = async () => {
    try {
      const { data } = await api.get(`/orders/${id}`)
      form.setFieldsValue({
        numero: data.numero,
        tipo_documento: data.tipo_documento,
        cliente_id: data.cliente_id,
        vendedor_id: data.vendedor_id,
        tipo_nf: data.tipo_nf,
        origem_frete: data.origem_frete,
        forma_pagamento: data.forma_pagamento,
        condicao_pagamento: data.condicao_pagamento,
        disponibilidade: data.disponibilidade,
        observacoes: data.observacoes,
        valor_frete: data.valor_frete,
      })
      if (data.itens && data.itens.length > 0) {
        setItens(data.itens.map((it: any, idx: number) => ({
          key: `item-${++itemCounter}`,
          ordem: idx,
          produto_id: it.produto_id,
          codigo_produto: it.codigo_produto || '',
          nome_produto: it.nome_produto || '',
          quantidade: it.quantidade || 1,
          unidade: it.unidade || 'UN',
          preco_unitario: it.preco_unitario || 0,
          desconto: it.desconto || 0,
          total: it.total || 0,
          custo_unitario: it.custo_unitario || 0,
          custo_total: it.custo_total || 0,
          valor_nf_unitario: it.valor_nf_unitario || 0,
        })))
      }
    } catch {
      message.error('Erro ao carregar pedido')
      navigate('/orcamentos')
    }
  }

  const getPriceForNfType = (produto: Produto, nfType: string): number => {
    switch (nfType) {
      case 'NF INTEGRAL': return produto.preco_nf_integral
      case 'NF BAIXA 1-3': return produto.preco_nf_baixa_1_3
      case 'NF BAIXA 4+': return produto.preco_nf_baixa_4
      case 'NF CHEIA 4+': return produto.preco_nf_cheia_4
      case 'NF INTEGRAL 10+': return produto.preco_nf_integral_10
      case 'NF BAIXA 10+': return produto.preco_nf_baixa_10
      case 'FABRICA 10+': return produto.preco_fabrica_10
      default: return produto.preco_nf_integral
    }
  }

  const handleProdutoSelect = (key: string, produtoId: number) => {
    const produto = produtos.find(p => p.id === produtoId)
    if (!produto) return

    const nfType = form.getFieldValue('tipo_nf') || 'NF INTEGRAL'
    const preco = getPriceForNfType(produto, nfType)

    setItens(prev => prev.map(item => {
      if (item.key !== key) return item
      const total = preco * item.quantidade
      return {
        ...item,
        produto_id: produto.id,
        codigo_produto: produto.codigo,
        nome_produto: produto.nome,
        unidade: produto.unidade,
        preco_unitario: preco,
        total,
        custo_unitario: produto.custo,
        custo_total: produto.custo * item.quantidade,
        valor_nf_unitario: preco,
      }
    }))
  }

  const handleQtdChange = (key: string, qty: number) => {
    setItens(prev => prev.map(item => {
      if (item.key !== key) return item
      const total = item.preco_unitario * qty - item.desconto
      return {
        ...item,
        quantidade: qty,
        total: Math.max(total, 0),
        custo_total: item.custo_unitario * qty,
      }
    }))
  }

  const handlePrecoChange = (key: string, preco: number) => {
    setItens(prev => prev.map(item => {
      if (item.key !== key) return item
      const total = preco * item.quantidade - item.desconto
      return { ...item, preco_unitario: preco, total: Math.max(total, 0) }
    }))
  }

  const addItem = () => setItens(prev => [...prev, newItem()])

  const removeItem = (key: string) => {
    if (itens.length <= 1) return
    setItens(prev => prev.filter(i => i.key !== key))
  }

  const calcTotals = useCallback(() => {
    const subtotal = itens.reduce((sum, i) => sum + i.total, 0)
    const custoTotal = itens.reduce((sum, i) => sum + i.custo_total, 0)
    const frete = form.getFieldValue('valor_frete') || 0
    const total = subtotal + frete
    const valorNf = itens.reduce((sum, i) => sum + (i.valor_nf_unitario * i.quantidade), 0)
    return { subtotal, custoTotal, frete, total, valorNf, lucro: total - custoTotal }
  }, [itens, form])

  const handleSave = async () => {
    try {
      await form.validateFields()
    } catch {
      return
    }

    const values = form.getFieldsValue()
    const totals = calcTotals()

    const payload = {
      numero: values.numero || proximoNumero,
      tipo_documento: values.tipo_documento || 'ORCAMENTO',
      status: 'ORCAMENTO',
      cliente_id: values.cliente_id || null,
      vendedor_id: values.vendedor_id || null,
      tipo_nf: values.tipo_nf || null,
      origem_frete: values.origem_frete || null,
      forma_pagamento: values.forma_pagamento || null,
      condicao_pagamento: values.condicao_pagamento || null,
      disponibilidade: values.disponibilidade || null,
      observacoes: values.observacoes || null,
      subtotal: totals.subtotal,
      valor_frete: totals.frete,
      desconto_total: 0,
      total: totals.total,
      custo_total: totals.custoTotal,
      valor_nf: totals.valorNf,
      valor_difal: 0,
      lucro: totals.lucro,
      itens: itens.filter(i => i.produto_id).map((i, idx) => ({
        ordem: idx,
        produto_id: i.produto_id,
        codigo_produto: i.codigo_produto,
        nome_produto: i.nome_produto,
        quantidade: i.quantidade,
        unidade: i.unidade,
        preco_unitario: i.preco_unitario,
        desconto: i.desconto,
        total: i.total,
        custo_unitario: i.custo_unitario,
        custo_total: i.custo_total,
        valor_nf_unitario: i.valor_nf_unitario,
      })),
    }

    setSaving(true)
    try {
      if (isEditing) {
        await api.put(`/orders/${id}`, payload)
        message.success('Pedido atualizado!')
      } else {
        await api.post('/orders', payload)
        message.success('Orcamento criado!')
      }
      navigate('/orcamentos')
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Erro ao salvar')
    } finally {
      setSaving(false)
    }
  }

  const totals = calcTotals()

  const produtosFiltrados = buscaProduto
    ? produtos.filter(p =>
        p.codigo.toLowerCase().includes(buscaProduto.toLowerCase()) ||
        p.nome.toLowerCase().includes(buscaProduto.toLowerCase())
      )
    : produtos

  const itemColumns = [
    {
      title: 'Produto',
      key: 'produto',
      width: 350,
      render: (_: any, record: ItemPedido) => (
        <Select
          showSearch
          placeholder="Buscar produto..."
          value={record.produto_id || undefined}
          onChange={(v: number) => handleProdutoSelect(record.key, v)}
          filterOption={(input, option) =>
            (option?.label as string || '').toLowerCase().includes(input.toLowerCase())
          }
          options={produtosFiltrados.map(p => ({
            value: p.id,
            label: `${p.codigo} — ${p.nome}`,
          }))}
          style={{ width: '100%' }}
        />
      ),
    },
    {
      title: 'Qtd',
      key: 'quantidade',
      width: 80,
      render: (_: any, record: ItemPedido) => (
        <InputNumber
          min={1}
          value={record.quantidade}
          onChange={(v) => handleQtdChange(record.key, v || 1)}
          style={{ width: '100%' }}
        />
      ),
    },
    {
      title: 'Valor Unit.',
      key: 'preco_unitario',
      width: 130,
      render: (_: any, record: ItemPedido) => (
        <InputNumber
          min={0}
          value={record.preco_unitario}
          onChange={(v) => handlePrecoChange(record.key, v || 0)}
          formatter={(v) => `R$ ${v}`.replace(/\B(?=(\d{3})+(?!\d))/g, '.')}
          style={{ width: '100%' }}
        />
      ),
    },
    {
      title: 'Total',
      key: 'total',
      width: 120,
      render: (_: any, record: ItemPedido) => (
        <Text strong>{formatCurrency(record.total)}</Text>
      ),
    },
    {
      title: '',
      key: 'acoes',
      width: 50,
      render: (_: any, record: ItemPedido) => (
        itens.length > 1 ? (
          <Button
            type="text"
            danger
            icon={<DeleteOutlined />}
            onClick={() => removeItem(record.key)}
          />
        ) : null
      ),
    },
  ]

  return (
    <div style={{ padding: '0 12px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/orcamentos')}>
            Voltar
          </Button>
          <Title level={2} style={{ margin: 0 }}>
            Orcamento / Pedido
          </Title>
        </Space>
      </div>

      <Form form={form} layout="vertical" initialValues={{ tipo_documento: 'ORCAMENTO' }}>

        {/* SEÇÃO: DADOS DO PEDIDO */}
        <Card title="Dados do Pedido" size="small" style={{ marginBottom: 16 }}>
          <Row gutter={[16, 16]}>
            {/* Row 1: Numero, Data, Cliente, Vendedor */}
            <Col xs={24} sm={12} md={4}>
              <Form.Item label="Numero" name="numero">
                <InputNumber style={{ width: '100%' }} disabled={isEditing} />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={4}>
              <Form.Item label="Data" name="data_pedido">
                <DatePicker style={{ width: '100%' }} format="DD/MM/YYYY" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <Form.Item label="Cliente" name="cliente_id">
                <Select
                  showSearch
                  allowClear
                  placeholder="Selecionar cliente..."
                  filterOption={(input, option) =>
                    (option?.label as string || '').toLowerCase().includes(input.toLowerCase())
                  }
                  options={clientes.map(c => ({
                    value: c.id,
                    label: `${c.id?.toString().padStart(5, '0')} - ${c.nome}`,
                  }))}
                />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={4}>
              <Button type="default" block>
                Pesquisar
              </Button>
            </Col>
            <Col xs={24} sm={12} md={4}>
              <Form.Item label="Vendedor" name="vendedor_id" noStyle>
                <Select
                  allowClear
                  placeholder="Vendedor"
                  options={vendedores.map(v => ({ value: v.id, label: v.nome }))}
                />
              </Form.Item>
            </Col>

            {/* Row 2: Tipo Doc, Tipo NF, Saida */}
            <Col xs={24} sm={12} md={4}>
              <Form.Item label="Tipo Doc" name="tipo_documento">
                <Select options={[
                  { value: 'ORCAMENTO', label: 'Orcamento' },
                  { value: 'PEDIDO', label: 'Pedido' },
                ]} />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={4}>
              <Form.Item label="Tipo NF" name="tipo_nf">
                <Select allowClear placeholder="Tipo NF" options={NF_TYPES} />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={4}>
              <Form.Item label="Saida" name="origem_frete">
                <Select allowClear placeholder="Origem" options={SHIPPING_ORIGINS} />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={12} />
          </Row>
        </Card>

        {/* SEÇÃO: ITENS DO PEDIDO */}
        <Card
          title="Itens do Pedido"
          size="small"
          style={{ marginBottom: 16 }}
          extra={
            <Space>
              <Button type="dashed" icon={<PlusOutlined />} onClick={addItem} size="small">
                Adicionar Item
              </Button>
              <Button danger icon={<DeleteOutlined />} size="small">
                Remover Item
              </Button>
              <Button icon={<SearchOutlined />} size="small">
                Pesquisar Produto
              </Button>
            </Space>
          }
        >
          <Table
            dataSource={itens}
            columns={itemColumns}
            rowKey="key"
            pagination={false}
            size="small"
            scroll={{ x: 'max-content' }}
          />
        </Card>

        {/* SEÇÃO: RESUMO */}
        <Card title="Resumo" size="small" style={{ marginBottom: 16 }}>
          <Row gutter={[24, 16]}>
            <Col xs={12} sm={8} md={6}>
              <Text type="secondary" style={{ fontSize: 12 }}>Subtotal</Text>
              <div><Text strong style={{ fontSize: 14 }}>{formatCurrency(totals.subtotal)}</Text></div>
            </Col>
            <Col xs={12} sm={8} md={6}>
              <Text type="secondary" style={{ fontSize: 12 }}>Desconto Total</Text>
              <div><Text strong style={{ fontSize: 14 }}>R$ 0,00</Text></div>
            </Col>
            <Col xs={12} sm={8} md={6}>
              <Text type="secondary" style={{ fontSize: 12 }}>Frete</Text>
              <div>
                <Form.Item name="valor_frete" noStyle>
                  <InputNumber min={0} size="small" style={{ width: 100 }} />
                </Form.Item>
              </div>
            </Col>
            <Col xs={12} sm={8} md={6}>
              <Text type="secondary" style={{ fontSize: 12 }}>Total</Text>
              <div><Text strong style={{ fontSize: 16, color: '#1B5E20' }}>{formatCurrency(totals.total)}</Text></div>
            </Col>

            <Col xs={12} sm={8} md={6}>
              <Text type="secondary" style={{ fontSize: 12 }}>Valor NF</Text>
              <div><Text strong>{formatCurrency(totals.total)}</Text></div>
            </Col>
            <Col xs={12} sm={8} md={6}>
              <Text type="secondary" style={{ fontSize: 12 }}>DIFAL</Text>
              <div><Text strong>R$ 0,00</Text></div>
            </Col>
            <Col xs={12} sm={8} md={6}>
              <Text type="secondary" style={{ fontSize: 12 }}>Custo Total</Text>
              <div><Text>{formatCurrency(totals.custoTotal)}</Text></div>
            </Col>
            <Col xs={12} sm={8} md={6}>
              <Text type="secondary" style={{ fontSize: 12 }}>Lucro</Text>
              <div><Text strong style={{ fontSize: 14, color: totals.lucro >= 0 ? '#1B5E20' : '#EF5350' }}>
                {formatCurrency(totals.lucro)}
              </Text></div>
            </Col>
          </Row>
        </Card>

        {/* SEÇÃO: CONDICOES */}
        <Card title="Condicoes" size="small" style={{ marginBottom: 16 }}>
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12} md={6}>
              <Form.Item label="Pagamento" name="forma_pagamento">
                <Select allowClear placeholder="Pagamento" options={PAYMENT_METHODS} />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Form.Item label="Condicoes" name="condicao_pagamento">
                <Input placeholder="Ex: 30/60/90" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Form.Item label="Disponibilidade" name="disponibilidade">
                <Input placeholder="A PRONTA ENTREGA" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Form.Item label="Observacoes" name="observacoes" style={{ marginBottom: 0 }}>
                <Input.TextArea rows={2} placeholder="Observacoes..." />
              </Form.Item>
            </Col>
          </Row>
        </Card>

        {/* BOTÕES DE AÇÃO */}
        <Space style={{ marginBottom: 20 }} wrap>
          <Button
            type="primary"
            icon={<SaveOutlined />}
            onClick={handleSave}
            loading={saving}
            style={{ backgroundColor: '#1e8449', borderColor: '#1e8449', minWidth: 100 }}
          >
            Salvar
          </Button>
          <Button
            icon={<FileTextOutlined />}
            style={{ backgroundColor: '#1a6ea8', color: 'white', borderColor: '#1a6ea8', minWidth: 100 }}
          >
            Gerar PDF
          </Button>
          <Button
            onClick={() => navigate('/orcamentos')}
            style={{ backgroundColor: '#7f8c8d', color: 'white', borderColor: '#7f8c8d', minWidth: 100 }}
          >
            Cancelar
          </Button>
        </Space>
      </Form>
    </div>
  )
}
