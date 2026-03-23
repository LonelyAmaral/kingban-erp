import { useState } from 'react'
import { Table, Button, Input, Space, Modal, Form, Tag, Popconfirm, Typography, InputNumber } from 'antd'
import { PlusOutlined, SearchOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import { useCrud } from '../hooks/useCrud'
import { formatCurrency } from '../utils/currency'

const { Title } = Typography

interface Vendedor {
  id: number
  nome: string
  telefone: string | null
  email: string | null
  salario_fixo: number
  ativo: boolean
}

export default function Vendedores() {
  const [modalOpen, setModalOpen] = useState(false)
  const [editando, setEditando] = useState<Vendedor | null>(null)
  const [form] = Form.useForm()

  const {
    data, loading, total, pagina, porPagina,
    setPagina, setPorPagina, setBusca,
    criar, atualizar, excluir,
  } = useCrud<Vendedor>({ endpoint: '/salespeople' })

  const abrirModal = (vendedor?: Vendedor) => {
    if (vendedor) {
      setEditando(vendedor)
      form.setFieldsValue(vendedor)
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
    { title: 'Nome', dataIndex: 'nome', key: 'nome', sorter: true },
    { title: 'Telefone', dataIndex: 'telefone', key: 'telefone', width: 150 },
    { title: 'Email', dataIndex: 'email', key: 'email', width: 220 },
    {
      title: 'Salario Fixo',
      dataIndex: 'salario_fixo',
      key: 'salario_fixo',
      width: 130,
      render: (v: number) => formatCurrency(v),
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
      render: (_: any, record: Vendedor) => (
        <Space>
          <Button type="text" icon={<EditOutlined />} onClick={() => abrirModal(record)} />
          <Popconfirm
            title="Desativar este vendedor?"
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

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0 }}>Vendedores</Title>
        <Space>
          <Input
            placeholder="Buscar..."
            prefix={<SearchOutlined />}
            allowClear
            onChange={(e) => setBusca(e.target.value)}
            style={{ width: 250 }}
          />
          <Button type="primary" icon={<PlusOutlined />} onClick={() => abrirModal()}>
            Novo Vendedor
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
          showTotal: (t) => `Total: ${t} vendedores`,
          onChange: (p, s) => { setPagina(p); setPorPagina(s) },
        }}
        size="middle"
      />

      <Modal
        title={editando ? 'Editar Vendedor' : 'Novo Vendedor'}
        open={modalOpen}
        onOk={salvar}
        onCancel={() => setModalOpen(false)}
        okText="Salvar"
        cancelText="Cancelar"
        width={500}
      >
        <Form form={form} layout="vertical" initialValues={{ salario_fixo: 1500, ativo: true }}>
          <Form.Item name="nome" label="Nome" rules={[{ required: true, message: 'Informe o nome' }]}>
            <Input />
          </Form.Item>
          <Space style={{ width: '100%' }} size="middle">
            <Form.Item name="telefone" label="Telefone" style={{ flex: 1 }}>
              <Input />
            </Form.Item>
            <Form.Item name="email" label="Email" style={{ flex: 1 }}>
              <Input type="email" />
            </Form.Item>
          </Space>
          <Form.Item name="salario_fixo" label="Salario Fixo">
            <InputNumber style={{ width: '100%' }} min={0} precision={2} prefix="R$" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
