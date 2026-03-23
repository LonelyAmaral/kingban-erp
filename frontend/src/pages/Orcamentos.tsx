import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Table, Button, Input, Space, Tag, Typography, Select, message, Modal, Popconfirm, Tooltip } from 'antd'
import {
  PlusOutlined, SearchOutlined, EditOutlined, DeleteOutlined,
  FilePdfOutlined, CopyOutlined, SwapOutlined,
} from '@ant-design/icons'
import api from '../api/client'

const { Title } = Typography

interface Pedido {
  id: number
  numero: number
  tipo_documento: string
  status: string
  cliente_id: number | null
  nome_cliente: string | null
  nome_vendedor: string | null
  tipo_nf: string | null
  total: number
  criado_em: string | null
}

interface PaginacaoResponse {
  itens: Pedido[]
  total: number
  pagina: number
  paginas: number
}

const STATUS_COLORS: Record<string, string> = {
  'ORCAMENTO': 'blue',
  'CONFIRMADO': 'green',
  'RESERVAR ESTOQUE': 'purple',
  'PRODUCAO': 'orange',
  'EXPEDIDO': 'cyan',
  'ENTREGUE': 'gold',
  'CANCELADO': 'red',
}

const STATUS_OPTIONS = [
  'ORCAMENTO', 'CONFIRMADO', 'RESERVAR ESTOQUE',
  'PRODUCAO', 'EXPEDIDO', 'ENTREGUE', 'CANCELADO',
]

export default function Orcamentos() {
  const navigate = useNavigate()
  const [data, setData] = useState<Pedido[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [pagina, setPagina] = useState(1)
  const [porPagina, setPorPagina] = useState(50)
  const [busca, setBusca] = useState('')
  const [statusFilter, setStatusFilter] = useState<string | undefined>()
  const [statusModal, setStatusModal] = useState<{ open: boolean; pedido: Pedido | null }>({ open: false, pedido: null })
  const [novoStatus, setNovoStatus] = useState('')

  const fetchData = async () => {
    setLoading(true)
    try {
      const params: Record<string, any> = { pagina, por_pagina: porPagina }
      if (busca) params.busca = busca
      if (statusFilter) params.status = statusFilter
      const { data: res } = await api.get<PaginacaoResponse>('/orders', { params })
      setData(res.itens)
      setTotal(res.total)
    } catch {
      message.error('Erro ao carregar pedidos')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchData() }, [pagina, porPagina, busca, statusFilter])

  const mudarStatus = async () => {
    if (!statusModal.pedido || !novoStatus) return
    try {
      const { data: res } = await api.post(`/orders/${statusModal.pedido.id}/status`, { novo_status: novoStatus })
      message.success(res.mensagem)
      setStatusModal({ open: false, pedido: null })
      fetchData()
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Erro ao mudar status')
    }
  }

  const excluir = async (id: number) => {
    try {
      const { data: res } = await api.delete(`/orders/${id}`)
      message.success(res.mensagem)
      fetchData()
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Erro ao excluir')
    }
  }

  const duplicar = async (id: number) => {
    try {
      await api.post(`/orders/${id}/duplicar`)
      message.success('Pedido duplicado com sucesso!')
      fetchData()
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Erro ao duplicar')
    }
  }

  const downloadPdf = async (id: number, numero: number) => {
    try {
      const response = await api.get(`/orders/${id}/pdf`, { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `orcamento_${String(numero).padStart(5, '0')}.pdf`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err: any) {
      message.error('Erro ao gerar PDF')
    }
  }

  const formatCurrency = (v: number) => v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

  const columns = [
    { title: '#', dataIndex: 'numero', key: 'numero', width: 70, sorter: true },
    { title: 'Tipo', dataIndex: 'tipo_documento', key: 'tipo_documento', width: 100 },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 150,
      render: (s: string) => <Tag color={STATUS_COLORS[s] || 'default'}>{s}</Tag>,
    },
    { title: 'Cliente', dataIndex: 'nome_cliente', key: 'nome_cliente' },
    { title: 'Vendedor', dataIndex: 'nome_vendedor', key: 'nome_vendedor', width: 150 },
    { title: 'Tipo NF', dataIndex: 'tipo_nf', key: 'tipo_nf', width: 110 },
    {
      title: 'Total',
      dataIndex: 'total',
      key: 'total',
      width: 130,
      render: (v: number) => formatCurrency(v),
    },
    {
      title: 'Acoes',
      key: 'acoes',
      width: 200,
      render: (_: any, record: Pedido) => (
        <Space size="small">
          <Tooltip title="Editar">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => navigate(`/orcamentos/${record.id}/editar`)}
            />
          </Tooltip>
          <Tooltip title="Mudar Status">
            <Button
              type="text"
              icon={<SwapOutlined />}
              onClick={() => { setStatusModal({ open: true, pedido: record }); setNovoStatus('') }}
            />
          </Tooltip>
          <Tooltip title="Ver PDF">
            <Button
              type="text"
              icon={<FilePdfOutlined />}
              onClick={() => downloadPdf(record.id, record.numero)}
            />
          </Tooltip>
          <Tooltip title="Duplicar">
            <Popconfirm
              title="Duplicar este pedido?"
              onConfirm={() => duplicar(record.id)}
              okText="Sim"
              cancelText="Nao"
            >
              <Button type="text" icon={<CopyOutlined />} />
            </Popconfirm>
          </Tooltip>
          {record.status === 'ORCAMENTO' && (
            <Popconfirm title="Excluir este orcamento?" onConfirm={() => excluir(record.id)} okText="Sim" cancelText="Nao">
              <Button type="text" danger icon={<DeleteOutlined />} />
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16, flexWrap: 'wrap', gap: 8 }}>
        <Title level={3} style={{ margin: 0 }}>Orcamentos / Pedidos</Title>
        <Space wrap>
          <Select
            placeholder="Filtrar status"
            allowClear
            style={{ width: 180 }}
            onChange={(v) => setStatusFilter(v)}
            options={STATUS_OPTIONS.map(s => ({ value: s, label: s }))}
          />
          <Input
            placeholder="Buscar cliente..."
            prefix={<SearchOutlined />}
            allowClear
            onChange={(e) => setBusca(e.target.value)}
            style={{ width: 200 }}
          />
          <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/orcamentos/novo')}>
            Novo Orcamento
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
          showTotal: (t) => `Total: ${t} pedidos`,
          onChange: (p, s) => { setPagina(p); setPorPagina(s) },
        }}
        size="middle"
        scroll={{ x: 1100 }}
      />

      <Modal
        title={`Mudar Status — Pedido #${statusModal.pedido?.numero || ''}`}
        open={statusModal.open}
        onOk={mudarStatus}
        onCancel={() => setStatusModal({ open: false, pedido: null })}
        okText="Confirmar"
        cancelText="Cancelar"
        okButtonProps={{ disabled: !novoStatus }}
      >
        <p>Status atual: <Tag color={STATUS_COLORS[statusModal.pedido?.status || '']}>{statusModal.pedido?.status}</Tag></p>
        <Select
          placeholder="Selecionar novo status"
          style={{ width: '100%' }}
          value={novoStatus || undefined}
          onChange={setNovoStatus}
          options={STATUS_OPTIONS
            .filter(s => s !== statusModal.pedido?.status)
            .map(s => ({ value: s, label: s }))
          }
        />
      </Modal>
    </div>
  )
}
