import { useState, useEffect } from 'react'
import { Table, Space, Typography, Tag, Button, Modal, Form, Select, Input, InputNumber, DatePicker, message, Popconfirm } from 'antd'
import { PlusOutlined, CheckOutlined, CloseOutlined, SearchOutlined } from '@ant-design/icons'
import api from '../api/client'
import { formatCurrency } from '../utils/currency'
import dayjs from 'dayjs'

const { Title } = Typography

interface Compra {
  id: number
  numero: number | null
  data: string
  fornecedor_id: number | null
  nome_fornecedor: string | null
  status: string
  subtotal: number
  frete: number
  desconto: number
  total: number
  forma_pagamento: string | null
  observacoes: string | null
  itens: Array<{
    id: number
    produto_id: number | null
    codigo_produto: string | null
    nome_produto: string
    quantidade: number
    preco_unitario: number
    total: number
  }>
}

const STATUS_COLORS: Record<string, string> = {
  PENDENTE: 'orange',
  RECEBIDA: 'green',
  CANCELADA: 'red',
}

export default function Compras() {
  const [compras, setCompras] = useState<Compra[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [pagina, setPagina] = useState(1)
  const [busca, setBusca] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [form] = Form.useForm()

  const fetchCompras = async () => {
    setLoading(true)
    try {
      const params: Record<string, any> = { pagina, por_pagina: 50 }
      if (busca) params.busca = busca
      const { data } = await api.get('/purchases', { params })
      setCompras(data.itens)
      setTotal(data.total)
    } catch { message.error('Erro ao carregar compras') }
    finally { setLoading(false) }
  }

  useEffect(() => { fetchCompras() }, [pagina, busca])

  const criarCompra = async () => {
    const v = await form.validateFields()
    if (!v.itens || v.itens.length === 0) {
      message.warning('Adicione pelo menos um item')
      return
    }
    try {
      await api.post('/purchases', {
        data: v.data?.format('YYYY-MM-DD'),
        nome_fornecedor: v.nome_fornecedor || '',
        frete: v.frete || 0,
        desconto: v.desconto || 0,
        forma_pagamento: v.forma_pagamento || '',
        observacoes: v.observacoes || '',
        itens: v.itens.map((i: any) => ({
          nome_produto: i.nome_produto,
          quantidade: i.quantidade || 1,
          preco_unitario: i.preco_unitario || 0,
        })),
      })
      message.success('Compra criada! Conta a pagar gerada automaticamente.')
      setModalOpen(false)
      form.resetFields()
      fetchCompras()
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Erro ao criar compra')
    }
  }

  const receberCompra = async (id: number) => {
    try {
      await api.post(`/purchases/${id}/receber`)
      message.success('Compra recebida! Estoque atualizado.')
      fetchCompras()
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Erro ao receber compra')
    }
  }

  const cancelarCompra = async (id: number) => {
    try {
      await api.post(`/purchases/${id}/cancelar`)
      message.success('Compra cancelada.')
      fetchCompras()
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Erro ao cancelar compra')
    }
  }

  const columns = [
    { title: '#', dataIndex: 'numero', key: 'numero', width: 60 },
    { title: 'Data', dataIndex: 'data', key: 'data', width: 100 },
    { title: 'Fornecedor', dataIndex: 'nome_fornecedor', key: 'nome_fornecedor' },
    { title: 'Total', dataIndex: 'total', key: 'total', width: 120, render: (v: number) => formatCurrency(v) },
    { title: 'Pagamento', dataIndex: 'forma_pagamento', key: 'forma_pagamento', width: 140 },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (v: string) => <Tag color={STATUS_COLORS[v]}>{v}</Tag>,
    },
    {
      title: 'Acoes',
      key: 'acoes',
      width: 160,
      render: (_: any, record: Compra) => (
        <Space>
          {record.status === 'PENDENTE' && (
            <>
              <Popconfirm title="Confirmar recebimento?" onConfirm={() => receberCompra(record.id)}>
                <Button type="link" icon={<CheckOutlined />} style={{ color: '#3f8600' }}>Receber</Button>
              </Popconfirm>
              <Popconfirm title="Cancelar compra?" onConfirm={() => cancelarCompra(record.id)}>
                <Button type="link" icon={<CloseOutlined />} danger>Cancelar</Button>
              </Popconfirm>
            </>
          )}
        </Space>
      ),
    },
  ]

  return (
    <div>
      <Title level={3}>Compras</Title>

      <Space style={{ marginBottom: 16 }}>
        <Input
          placeholder="Buscar fornecedor..."
          prefix={<SearchOutlined />}
          allowClear
          onChange={(e) => setBusca(e.target.value)}
          style={{ width: 250 }}
        />
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
          Nova Compra
        </Button>
      </Space>

      <Table
        dataSource={compras}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={{
          current: pagina,
          pageSize: 50,
          total,
          showTotal: (t) => `Total: ${t} compras`,
          onChange: (p) => setPagina(p),
        }}
        size="middle"
        scroll={{ x: 900 }}
        expandable={{
          expandedRowRender: (record) => (
            <Table
              dataSource={record.itens}
              rowKey="id"
              size="small"
              pagination={false}
              columns={[
                { title: 'Produto', dataIndex: 'nome_produto', key: 'nome_produto' },
                { title: 'Qtd', dataIndex: 'quantidade', key: 'quantidade', width: 60 },
                { title: 'Preco Uni', dataIndex: 'preco_unitario', key: 'preco_unitario', width: 100, render: (v: number) => formatCurrency(v) },
                { title: 'Total', dataIndex: 'total', key: 'total', width: 100, render: (v: number) => formatCurrency(v) },
              ]}
            />
          ),
        }}
      />

      <Modal
        title="Nova Compra"
        open={modalOpen}
        onOk={criarCompra}
        onCancel={() => setModalOpen(false)}
        okText="Salvar"
        cancelText="Cancelar"
        width={700}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="data" label="Data" rules={[{ required: true }]}>
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="nome_fornecedor" label="Fornecedor">
            <Input />
          </Form.Item>
          <Form.Item name="forma_pagamento" label="Forma de Pagamento">
            <Select allowClear options={[
              { value: 'PIX', label: 'PIX' },
              { value: 'BOLETO', label: 'Boleto' },
              { value: 'TRANSFERENCIA', label: 'Transferencia' },
              { value: 'CARTAO', label: 'Cartao' },
              { value: 'DINHEIRO', label: 'Dinheiro' },
            ]} />
          </Form.Item>
          <Form.Item name="frete" label="Frete (R$)">
            <InputNumber style={{ width: '100%' }} min={0} step={0.01} />
          </Form.Item>
          <Form.Item name="desconto" label="Desconto (R$)">
            <InputNumber style={{ width: '100%' }} min={0} step={0.01} />
          </Form.Item>

          <Typography.Text strong>Itens da Compra</Typography.Text>
          <Form.List name="itens">
            {(fields, { add, remove }) => (
              <>
                {fields.map(({ key, name, ...rest }) => (
                  <Space key={key} style={{ display: 'flex', marginBottom: 8, alignItems: 'center' }} align="baseline">
                    <Form.Item {...rest} name={[name, 'nome_produto']} rules={[{ required: true, message: 'Nome' }]}>
                      <Input placeholder="Produto" style={{ width: 200 }} />
                    </Form.Item>
                    <Form.Item {...rest} name={[name, 'quantidade']} initialValue={1}>
                      <InputNumber placeholder="Qtd" min={1} style={{ width: 70 }} />
                    </Form.Item>
                    <Form.Item {...rest} name={[name, 'preco_unitario']} initialValue={0}>
                      <InputNumber placeholder="Preco" min={0} step={0.01} style={{ width: 100 }} />
                    </Form.Item>
                    <Button type="link" danger onClick={() => remove(name)}>Remover</Button>
                  </Space>
                ))}
                <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>
                  Adicionar Item
                </Button>
              </>
            )}
          </Form.List>

          <Form.Item name="observacoes" label="Observacoes" style={{ marginTop: 16 }}>
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
