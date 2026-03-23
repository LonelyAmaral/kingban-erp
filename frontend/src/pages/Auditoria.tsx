import { useState, useEffect } from 'react'
import { Table, Space, Typography, Select, Input, Tag, message } from 'antd'
import { SearchOutlined } from '@ant-design/icons'
import api from '../api/client'

const { Title } = Typography

interface LogEntry {
  id: number
  usuario_id: number
  tabela: string
  registro_id: number
  acao: string
  valores_antigos: string | null
  valores_novos: string | null
  data_hora: string | null
}

const ACAO_COLORS: Record<string, string> = {
  CREATE: 'green',
  UPDATE: 'blue',
  DELETE: 'red',
  PAYMENT: 'gold',
  STATUS_CHANGE: 'purple',
  RECEIVE: 'cyan',
  CANCEL: 'volcano',
}

const ACAO_LABELS: Record<string, string> = {
  CREATE: 'Criacao',
  UPDATE: 'Alteracao',
  DELETE: 'Exclusao',
  PAYMENT: 'Pagamento',
  STATUS_CHANGE: 'Mudanca Status',
  RECEIVE: 'Recebimento',
  CANCEL: 'Cancelamento',
}

export default function Auditoria() {
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [pagina, setPagina] = useState(1)
  const [tabelas, setTabelas] = useState<string[]>([])
  const [acoes, setAcoes] = useState<string[]>([])
  const [tabelaFilter, setTabelaFilter] = useState<string | null>(null)
  const [acaoFilter, setAcaoFilter] = useState<string | null>(null)

  const fetchLogs = async () => {
    setLoading(true)
    try {
      const params: Record<string, any> = { pagina, por_pagina: 50 }
      if (tabelaFilter) params.tabela = tabelaFilter
      if (acaoFilter) params.acao = acaoFilter
      const { data } = await api.get('/audit', { params })
      setLogs(data.itens)
      setTotal(data.total)
    } catch { message.error('Erro ao carregar logs') }
    finally { setLoading(false) }
  }

  const fetchFilters = async () => {
    try {
      const [t, a] = await Promise.all([
        api.get('/audit/tabelas'),
        api.get('/audit/acoes'),
      ])
      setTabelas(t.data)
      setAcoes(a.data)
    } catch { /* silencioso */ }
  }

  useEffect(() => { fetchLogs() }, [pagina, tabelaFilter, acaoFilter])
  useEffect(() => { fetchFilters() }, [])

  const columns = [
    {
      title: 'Data/Hora',
      dataIndex: 'data_hora',
      key: 'data_hora',
      width: 170,
      render: (v: string | null) => v ? new Date(v).toLocaleString('pt-BR') : '-',
    },
    {
      title: 'Acao',
      dataIndex: 'acao',
      key: 'acao',
      width: 130,
      render: (v: string) => <Tag color={ACAO_COLORS[v] || 'default'}>{ACAO_LABELS[v] || v}</Tag>,
    },
    { title: 'Tabela', dataIndex: 'tabela', key: 'tabela', width: 140 },
    { title: 'Registro #', dataIndex: 'registro_id', key: 'registro_id', width: 90 },
    { title: 'Usuario #', dataIndex: 'usuario_id', key: 'usuario_id', width: 90 },
    {
      title: 'Detalhes',
      key: 'detalhes',
      ellipsis: true,
      render: (_: any, record: LogEntry) => {
        if (record.valores_novos) {
          try {
            const parsed = JSON.parse(record.valores_novos)
            return <span style={{ fontSize: 12, color: '#888' }}>{JSON.stringify(parsed)}</span>
          } catch { return record.valores_novos }
        }
        if (record.valores_antigos) {
          try {
            const parsed = JSON.parse(record.valores_antigos)
            return <span style={{ fontSize: 12, color: '#888' }}>{JSON.stringify(parsed)}</span>
          } catch { return record.valores_antigos }
        }
        return '-'
      },
    },
  ]

  return (
    <div>
      <Title level={3}>Auditoria — Log de Acoes</Title>

      <Space style={{ marginBottom: 16 }} wrap>
        <Select
          placeholder="Tabela"
          allowClear
          style={{ width: 180 }}
          onChange={(v) => { setTabelaFilter(v || null); setPagina(1) }}
          options={tabelas.map(t => ({ value: t, label: t }))}
        />
        <Select
          placeholder="Acao"
          allowClear
          style={{ width: 180 }}
          onChange={(v) => { setAcaoFilter(v || null); setPagina(1) }}
          options={acoes.map(a => ({ value: a, label: ACAO_LABELS[a] || a }))}
        />
      </Space>

      <Table
        dataSource={logs}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={{
          current: pagina,
          pageSize: 50,
          total,
          showTotal: (t) => `Total: ${t} registros`,
          onChange: (p) => setPagina(p),
        }}
        size="middle"
        scroll={{ x: 900 }}
      />
    </div>
  )
}
