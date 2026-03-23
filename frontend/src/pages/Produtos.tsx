import { useState } from 'react'
import { Table, Button, Input, Space, Modal, Form, Tag, Popconfirm, Typography, InputNumber, Tabs } from 'antd'
import { PlusOutlined, SearchOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import { useCrud } from '../hooks/useCrud'
import { formatCurrency, formatPercent } from '../utils/currency'

const { Title } = Typography

interface Produto {
  id: number
  codigo: string
  nome: string
  categoria: string | null
  unidade: string
  ncm: string | null
  custo: number
  frete: number
  preco_nf_integral: number
  preco_nf_baixa_1_3: number
  desconto_nf_baixa_1_3: number
  preco_nf_baixa_4: number
  desconto_nf_baixa_4: number
  preco_nf_cheia_4: number
  desconto_nf_cheia_4: number
  preco_nf_integral_10: number
  preco_nf_baixa_10: number
  desconto_nf_baixa_10: number
  preco_fabrica_10: number
  desconto_fabrica_10: number
  taxa_comissao: number
  ativo: boolean
}

export default function Produtos() {
  const [modalOpen, setModalOpen] = useState(false)
  const [editando, setEditando] = useState<Produto | null>(null)
  const [form] = Form.useForm()

  const {
    data, loading, total, pagina, porPagina,
    setPagina, setPorPagina, setBusca,
    criar, atualizar, excluir,
  } = useCrud<Produto>({ endpoint: '/products' })

  const abrirModal = (produto?: Produto) => {
    if (produto) {
      setEditando(produto)
      form.setFieldsValue(produto)
    } else {
      setEditando(null)
      form.resetFields()
    }
    setModalOpen(true)
  }

  const salvar = async () => {
    const valores = await form.validateFields()
    if (editando) {
      await atualizar(editando.id, valores)
    } else {
      await criar(valores)
    }
    setModalOpen(false)
  }

  const columns = [
    { title: 'Codigo', dataIndex: 'codigo', key: 'codigo', width: 100, sorter: true },
    { title: 'Nome', dataIndex: 'nome', key: 'nome', sorter: true },
    { title: 'Categoria', dataIndex: 'categoria', key: 'categoria', width: 120 },
    { title: 'UN', dataIndex: 'unidade', key: 'unidade', width: 60 },
    {
      title: 'Custo',
      dataIndex: 'custo',
      key: 'custo',
      width: 110,
      render: (v: number) => formatCurrency(v),
    },
    {
      title: 'NF Integral',
      dataIndex: 'preco_nf_integral',
      key: 'preco_nf_integral',
      width: 120,
      render: (v: number) => formatCurrency(v),
    },
    {
      title: 'Comissao',
      dataIndex: 'taxa_comissao',
      key: 'taxa_comissao',
      width: 90,
      render: (v: number) => formatPercent(v),
    },
    {
      title: 'Status',
      dataIndex: 'ativo',
      key: 'ativo',
      width: 80,
      render: (ativo: boolean) => (
        <Tag color={ativo ? 'green' : 'red'}>{ativo ? 'Ativo' : 'Inativo'}</Tag>
      ),
    },
    {
      title: 'Acoes',
      key: 'acoes',
      width: 100,
      render: (_: any, record: Produto) => (
        <Space>
          <Button type="text" icon={<EditOutlined />} onClick={() => abrirModal(record)} />
          <Popconfirm
            title="Desativar este produto?"
            onConfirm={() => excluir(record.id)}
            okText="Sim"
            cancelText="Nao"
          >
            <Button type="text" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const campoPreco = (name: string, label: string) => (
    <Form.Item name={name} label={label} style={{ flex: 1 }}>
      <InputNumber style={{ width: '100%' }} min={0} precision={2} prefix="R$" />
    </Form.Item>
  )

  const campoDesconto = (name: string, label: string) => (
    <Form.Item name={name} label={label} style={{ flex: 1 }}>
      <InputNumber style={{ width: '100%' }} min={0} max={100} precision={2} suffix="%" />
    </Form.Item>
  )

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0 }}>Produtos</Title>
        <Space>
          <Input
            placeholder="Buscar..."
            prefix={<SearchOutlined />}
            allowClear
            onChange={(e) => setBusca(e.target.value)}
            style={{ width: 250 }}
          />
          <Button type="primary" icon={<PlusOutlined />} onClick={() => abrirModal()}>
            Novo Produto
          </Button>
        </Space>
      </div>

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
          showTotal: (t) => `Total: ${t} produtos`,
          onChange: (p, s) => { setPagina(p); setPorPagina(s) },
        }}
        size="middle"
        scroll={{ x: 900 }}
      />

      <Modal
        title={editando ? 'Editar Produto' : 'Novo Produto'}
        open={modalOpen}
        onOk={salvar}
        onCancel={() => setModalOpen(false)}
        okText="Salvar"
        cancelText="Cancelar"
        width={800}
      >
        <Form form={form} layout="vertical" initialValues={{ unidade: 'UN', taxa_comissao: 0.15, ativo: true }}>
          <Tabs
            items={[
              {
                key: 'geral',
                label: 'Geral',
                children: (
                  <>
                    <Space style={{ width: '100%' }} size="middle">
                      <Form.Item name="codigo" label="Codigo" rules={[{ required: true }]} style={{ flex: 1 }}>
                        <Input />
                      </Form.Item>
                      <Form.Item name="nome" label="Nome" rules={[{ required: true }]} style={{ flex: 3 }}>
                        <Input />
                      </Form.Item>
                    </Space>
                    <Space style={{ width: '100%' }} size="middle">
                      <Form.Item name="categoria" label="Categoria" style={{ flex: 2 }}>
                        <Input />
                      </Form.Item>
                      <Form.Item name="unidade" label="Unidade" style={{ flex: 1 }}>
                        <Input />
                      </Form.Item>
                      <Form.Item name="ncm" label="NCM" style={{ flex: 1 }}>
                        <Input />
                      </Form.Item>
                    </Space>
                    <Space style={{ width: '100%' }} size="middle">
                      {campoPreco('custo', 'Custo')}
                      {campoPreco('frete', 'Frete')}
                      <Form.Item name="taxa_comissao" label="Taxa Comissao" style={{ flex: 1 }}>
                        <InputNumber style={{ width: '100%' }} min={0} max={1} step={0.01} precision={2} />
                      </Form.Item>
                    </Space>
                  </>
                ),
              },
              {
                key: 'precos',
                label: 'Faixas de Preco',
                children: (
                  <>
                    <Space style={{ width: '100%' }} size="middle">
                      {campoPreco('preco_nf_integral', 'NF Integral')}
                    </Space>
                    <Space style={{ width: '100%' }} size="middle">
                      {campoPreco('preco_nf_baixa_1_3', 'NF Baixa 1-3')}
                      {campoDesconto('desconto_nf_baixa_1_3', 'Desconto NF Baixa 1-3')}
                    </Space>
                    <Space style={{ width: '100%' }} size="middle">
                      {campoPreco('preco_nf_baixa_4', 'NF Baixa 4+')}
                      {campoDesconto('desconto_nf_baixa_4', 'Desconto NF Baixa 4+')}
                    </Space>
                    <Space style={{ width: '100%' }} size="middle">
                      {campoPreco('preco_nf_cheia_4', 'NF Cheia 4+')}
                      {campoDesconto('desconto_nf_cheia_4', 'Desconto NF Cheia 4+')}
                    </Space>
                    <Space style={{ width: '100%' }} size="middle">
                      {campoPreco('preco_nf_integral_10', 'NF Integral 10+')}
                    </Space>
                    <Space style={{ width: '100%' }} size="middle">
                      {campoPreco('preco_nf_baixa_10', 'NF Baixa 10+')}
                      {campoDesconto('desconto_nf_baixa_10', 'Desconto NF Baixa 10+')}
                    </Space>
                    <Space style={{ width: '100%' }} size="middle">
                      {campoPreco('preco_fabrica_10', 'Fabrica 10+')}
                      {campoDesconto('desconto_fabrica_10', 'Desconto Fabrica 10+')}
                    </Space>
                  </>
                ),
              },
            ]}
          />
        </Form>
      </Modal>
    </div>
  )
}
