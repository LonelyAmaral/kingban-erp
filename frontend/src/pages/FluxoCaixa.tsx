import { useState, useEffect } from 'react'
import { Table, Input, Space, Typography, Tag, Button, Modal, Form, Select, InputNumber, DatePicker, Card, Row, Col, Statistic, message } from 'antd'
import { PlusOutlined, ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons'
import api from '../api/client'
import { formatCurrency } from '../utils/currency'
import dayjs from 'dayjs'

const { Title } = Typography
const { RangePicker } = DatePicker

interface Lancamento {
  id: number
  data: string
  tipo: string
  categoria: string
  descricao: string | null
  valor: number
  auto_gerado: string
  observacoes: string | null
}

interface Resumo {
  total_entradas: number
  total_saidas: number
  saldo_periodo: number
  saldo_acumulado: number
  quantidade_lancamentos: number
}

export default function FluxoCaixa() {
  const [lancamentos, setLancamentos] = useState<Lancamento[]>([])
  const [resumo, setResumo] = useState<Resumo | null>(null)
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [pagina, setPagina] = useState(1)
  const [dateRange, setDateRange] = useState<[string, string] | null>(null)
  const [tipoFilter, setTipoFilter] = useState<string | null>(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [categorias, setCategorias] = useState<{ entrada: string[]; saida: string[] }>({ entrada: [], saida: [] })
  const [form] = Form.useForm()
  const tipoSelecionado = Form.useWatch('tipo', form)

  const fetchData = async () => {
    setLoading(true)
    try {
      const params: Record<string, any> = { pagina, por_pagina: 50 }
      if (tipoFilter) params.tipo = tipoFilter
      if (dateRange) {
        params.data_inicio = dateRange[0]
        params.data_fim = dateRange[1]
      }

      const [listRes, resumoRes] = await Promise.all([
        api.get('/cashflow', { params }),
        api.get('/cashflow/resumo', {
          params: dateRange ? { data_inicio: dateRange[0], data_fim: dateRange[1] } : {},
        }),
      ])
      setLancamentos(listRes.data.itens)
      setTotal(listRes.data.total)
      setResumo(resumoRes.data)
    } catch { message.error('Erro ao carregar fluxo de caixa') }
    finally { setLoading(false) }
  }

  const fetchCategorias = async () => {
    try {
      const { data } = await api.get('/cashflow/categorias')
      setCategorias(data)
    } catch { /* usa padrao */ }
  }

  useEffect(() => { fetchData() }, [pagina, tipoFilter, dateRange])
  useEffect(() => { fetchCategorias() }, [])

  const criarLancamento = async () => {
    const v = await form.validateFields()
    try {
      await api.post('/cashflow', {
        data: v.data?.format('YYYY-MM-DD'),
        tipo: v.tipo,
        categoria: v.categoria,
        descricao: v.descricao || '',
        valor: v.valor,
        observacoes: v.observacoes || '',
      })
      message.success('Lancamento criado!')
      setModalOpen(false)
      form.resetFields()
      fetchData()
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Erro ao criar lancamento')
    }
  }

  const columns = [
    { title: 'Data', dataIndex: 'data', key: 'data', width: 100 },
    {
      title: 'Tipo',
      dataIndex: 'tipo',
      key: 'tipo',
      width: 90,
      render: (v: string) => (
        <Tag color={v === 'ENTRADA' ? 'green' : 'red'}>
          {v === 'ENTRADA' ? 'Entrada' : 'Saida'}
        </Tag>
      ),
    },
    { title: 'Categoria', dataIndex: 'categoria', key: 'categoria', width: 120 },
    { title: 'Descricao', dataIndex: 'descricao', key: 'descricao' },
    {
      title: 'Valor',
      dataIndex: 'valor',
      key: 'valor',
      width: 130,
      render: (v: number, r: Lancamento) => (
        <span style={{ color: r.tipo === 'ENTRADA' ? '#3f8600' : '#cf1322', fontWeight: 'bold' }}>
          {r.tipo === 'ENTRADA' ? '+' : '-'} {formatCurrency(v)}
        </span>
      ),
    },
    {
      title: 'Auto',
      dataIndex: 'auto_gerado',
      key: 'auto_gerado',
      width: 70,
      render: (v: string) => v === 'SIM' ? <Tag color="blue">Auto</Tag> : null,
    },
    { title: 'Obs', dataIndex: 'observacoes', key: 'observacoes', width: 150, ellipsis: true },
  ]

  return (
    <div>
      <Title level={3}>Fluxo de Caixa</Title>

      {resumo && (
        <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Entradas"
                value={resumo.total_entradas}
                prefix={<ArrowUpOutlined />}
                precision={2}
                valueStyle={{ color: '#3f8600' }}
                suffix="R$"
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Saidas"
                value={resumo.total_saidas}
                prefix={<ArrowDownOutlined />}
                precision={2}
                valueStyle={{ color: '#cf1322' }}
                suffix="R$"
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Saldo Periodo"
                value={resumo.saldo_periodo}
                prefix="R$"
                precision={2}
                valueStyle={{ color: resumo.saldo_periodo >= 0 ? '#3f8600' : '#cf1322' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Saldo Acumulado"
                value={resumo.saldo_acumulado}
                prefix="R$"
                precision={2}
                valueStyle={{ color: resumo.saldo_acumulado >= 0 ? '#3f8600' : '#cf1322' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      <Space style={{ marginBottom: 16 }} wrap>
        <RangePicker
          onChange={(dates) => {
            if (dates && dates[0] && dates[1]) {
              setDateRange([dates[0].format('YYYY-MM-DD'), dates[1].format('YYYY-MM-DD')])
            } else {
              setDateRange(null)
            }
          }}
        />
        <Select
          placeholder="Tipo"
          allowClear
          style={{ width: 140 }}
          onChange={(v) => setTipoFilter(v || null)}
          options={[
            { value: 'ENTRADA', label: 'Entradas' },
            { value: 'SAIDA', label: 'Saidas' },
          ]}
        />
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
          Novo Lancamento
        </Button>
      </Space>

      <Table
        dataSource={lancamentos}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={{
          current: pagina,
          pageSize: 50,
          total,
          showTotal: (t) => `Total: ${t} lancamentos`,
          onChange: (p) => setPagina(p),
        }}
        size="middle"
        scroll={{ x: 900 }}
      />

      <Modal title="Novo Lancamento" open={modalOpen} onOk={criarLancamento} onCancel={() => setModalOpen(false)} okText="Salvar" cancelText="Cancelar">
        <Form form={form} layout="vertical">
          <Form.Item name="data" label="Data" rules={[{ required: true }]}>
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="tipo" label="Tipo" rules={[{ required: true }]}>
            <Select options={[
              { value: 'ENTRADA', label: 'Entrada' },
              { value: 'SAIDA', label: 'Saida' },
            ]} />
          </Form.Item>
          <Form.Item name="categoria" label="Categoria" rules={[{ required: true }]}>
            <Select
              options={(tipoSelecionado === 'ENTRADA' ? categorias.entrada : categorias.saida).map(
                (c) => ({ value: c, label: c })
              )}
            />
          </Form.Item>
          <Form.Item name="descricao" label="Descricao">
            <Input />
          </Form.Item>
          <Form.Item name="valor" label="Valor (R$)" rules={[{ required: true }]}>
            <InputNumber style={{ width: '100%' }} min={0.01} step={0.01} />
          </Form.Item>
          <Form.Item name="observacoes" label="Observacoes">
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
