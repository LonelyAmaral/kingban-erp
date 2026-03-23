import { useState } from 'react'
import { Table, Button, Input, Space, Modal, Form, Tag, Popconfirm, Typography } from 'antd'
import { PlusOutlined, SearchOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import { useCrud } from '../hooks/useCrud'

const { Title } = Typography

interface Fornecedor {
  id: number
  nome: string
  cnpj: string | null
  ie: string | null
  endereco: string | null
  cidade: string | null
  estado: string | null
  cep: string | null
  telefone: string | null
  email: string | null
  contato: string | null
  categoria: string | null
  observacoes: string | null
  ativo: boolean
}

export default function Fornecedores() {
  const [modalOpen, setModalOpen] = useState(false)
  const [editando, setEditando] = useState<Fornecedor | null>(null)
  const [form] = Form.useForm()

  const {
    data, loading, total, pagina, porPagina,
    setPagina, setPorPagina, setBusca,
    criar, atualizar, excluir,
  } = useCrud<Fornecedor>({ endpoint: '/suppliers' })

  const abrirModal = (fornecedor?: Fornecedor) => {
    if (fornecedor) {
      setEditando(fornecedor)
      form.setFieldsValue(fornecedor)
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
    { title: 'CNPJ', dataIndex: 'cnpj', key: 'cnpj', width: 160 },
    { title: 'Categoria', dataIndex: 'categoria', key: 'categoria', width: 140 },
    { title: 'Cidade', dataIndex: 'cidade', key: 'cidade', width: 140 },
    { title: 'UF', dataIndex: 'estado', key: 'estado', width: 60 },
    { title: 'Telefone', dataIndex: 'telefone', key: 'telefone', width: 140 },
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
      render: (_: any, record: Fornecedor) => (
        <Space>
          <Button type="text" icon={<EditOutlined />} onClick={() => abrirModal(record)} />
          <Popconfirm
            title="Desativar este fornecedor?"
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
        <Title level={3} style={{ margin: 0 }}>Fornecedores</Title>
        <Space>
          <Input
            placeholder="Buscar..."
            prefix={<SearchOutlined />}
            allowClear
            onChange={(e) => setBusca(e.target.value)}
            style={{ width: 250 }}
          />
          <Button type="primary" icon={<PlusOutlined />} onClick={() => abrirModal()}>
            Novo Fornecedor
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
          showTotal: (t) => `Total: ${t} fornecedores`,
          onChange: (p, s) => { setPagina(p); setPorPagina(s) },
        }}
        size="middle"
        scroll={{ x: 900 }}
      />

      <Modal
        title={editando ? 'Editar Fornecedor' : 'Novo Fornecedor'}
        open={modalOpen}
        onOk={salvar}
        onCancel={() => setModalOpen(false)}
        okText="Salvar"
        cancelText="Cancelar"
        width={700}
      >
        <Form form={form} layout="vertical" initialValues={{ ativo: true }}>
          <Form.Item name="nome" label="Nome" rules={[{ required: true, message: 'Informe o nome' }]}>
            <Input />
          </Form.Item>
          <Space style={{ width: '100%' }} size="middle">
            <Form.Item name="cnpj" label="CNPJ" style={{ flex: 1 }}>
              <Input />
            </Form.Item>
            <Form.Item name="ie" label="IE" style={{ flex: 1 }}>
              <Input />
            </Form.Item>
            <Form.Item name="categoria" label="Categoria" style={{ flex: 1 }}>
              <Input />
            </Form.Item>
          </Space>
          <Form.Item name="endereco" label="Endereco">
            <Input />
          </Form.Item>
          <Space style={{ width: '100%' }} size="middle">
            <Form.Item name="cidade" label="Cidade" style={{ flex: 2 }}>
              <Input />
            </Form.Item>
            <Form.Item name="estado" label="UF" style={{ flex: 1 }}>
              <Input maxLength={2} />
            </Form.Item>
            <Form.Item name="cep" label="CEP" style={{ flex: 1 }}>
              <Input />
            </Form.Item>
          </Space>
          <Space style={{ width: '100%' }} size="middle">
            <Form.Item name="telefone" label="Telefone" style={{ flex: 1 }}>
              <Input />
            </Form.Item>
            <Form.Item name="email" label="Email" style={{ flex: 1 }}>
              <Input type="email" />
            </Form.Item>
          </Space>
          <Form.Item name="contato" label="Contato">
            <Input />
          </Form.Item>
          <Form.Item name="observacoes" label="Observacoes">
            <Input.TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
