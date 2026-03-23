import { useState, useEffect } from 'react'
import { Card, Row, Col, Typography, Statistic, Table, Divider, Spin, message } from 'antd'
import {
  TeamOutlined,
  ShopOutlined,
  AppstoreOutlined,
  UserOutlined,
  DollarOutlined,
  FileTextOutlined,
  ShoppingCartOutlined,
  WarningOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  RiseOutlined,
} from '@ant-design/icons'
import api from '../api/client'
import { formatCurrency } from '../utils/currency'

const { Title, Text } = Typography

interface DashboardData {
  cadastros: {
    clientes: number
    fornecedores: number
    produtos: number
    vendedores: number
  }
  operacional: {
    orcamentos_abertos: number
    pedidos_andamento: number
    estoque_critico: number
  }
  financeiro: {
    faturamento_mes: number
    lucro_mes: number
    ticket_medio: number
    qtd_vendas_mes: number
    contas_receber: number
    contas_pagar: number
  }
}

interface VendaMensal {
  mes: string
  faturamento: number
  lucro: number
  quantidade: number
}

interface TopCliente {
  cliente: string
  total: number
  qtd: number
}

interface TopProduto {
  codigo: string
  produto: string
  quantidade: number
  total: number
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [vendasMensal, setVendasMensal] = useState<VendaMensal[]>([])
  const [topClientes, setTopClientes] = useState<TopCliente[]>([])
  const [topProdutos, setTopProdutos] = useState<TopProduto[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const [kpis, vendas, clientes, produtos] = await Promise.all([
          api.get('/dashboard'),
          api.get('/dashboard/vendas-mensal', { params: { meses: 6 } }),
          api.get('/dashboard/top-clientes', { params: { limite: 5 } }),
          api.get('/dashboard/top-produtos', { params: { limite: 5 } }),
        ])
        setData(kpis.data)
        setVendasMensal(vendas.data)
        setTopClientes(clientes.data)
        setTopProdutos(produtos.data)
      } catch {
        message.error('Erro ao carregar dashboard')
      } finally {
        setLoading(false)
      }
    }
    fetchAll()
  }, [])

  if (loading) return <Spin size="large" style={{ display: 'flex', justifyContent: 'center', marginTop: 100 }} />
  if (!data) return null

  const { cadastros, operacional, financeiro } = data

  return (
    <div>
      <Title level={3}>Dashboard</Title>

      {/* KPIs Financeiros */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Faturamento do Mes"
              value={financeiro.faturamento_mes}
              prefix={<DollarOutlined />}
              precision={2}
              suffix="R$"
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Lucro do Mes"
              value={financeiro.lucro_mes}
              prefix={<RiseOutlined />}
              precision={2}
              suffix="R$"
              valueStyle={{ color: financeiro.lucro_mes >= 0 ? '#3f8600' : '#cf1322' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Ticket Medio"
              value={financeiro.ticket_medio}
              prefix="R$"
              precision={2}
            />
            <Text type="secondary">{financeiro.qtd_vendas_mes} vendas no mes</Text>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="A Receber"
              value={financeiro.contas_receber}
              prefix={<ArrowUpOutlined />}
              precision={2}
              suffix="R$"
              valueStyle={{ color: '#3f8600' }}
            />
            <Statistic
              title="A Pagar"
              value={financeiro.contas_pagar}
              prefix={<ArrowDownOutlined />}
              precision={2}
              suffix="R$"
              valueStyle={{ color: '#cf1322', fontSize: 16, marginTop: 4 }}
            />
          </Card>
        </Col>
      </Row>

      {/* KPIs Operacionais */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={12} sm={8} lg={4}>
          <Card><Statistic title="Clientes" value={cadastros.clientes} prefix={<TeamOutlined />} /></Card>
        </Col>
        <Col xs={12} sm={8} lg={4}>
          <Card><Statistic title="Fornecedores" value={cadastros.fornecedores} prefix={<ShopOutlined />} /></Card>
        </Col>
        <Col xs={12} sm={8} lg={4}>
          <Card><Statistic title="Produtos" value={cadastros.produtos} prefix={<AppstoreOutlined />} /></Card>
        </Col>
        <Col xs={12} sm={8} lg={4}>
          <Card><Statistic title="Vendedores" value={cadastros.vendedores} prefix={<UserOutlined />} /></Card>
        </Col>
        <Col xs={12} sm={8} lg={4}>
          <Card>
            <Statistic title="Orcamentos Abertos" value={operacional.orcamentos_abertos} prefix={<FileTextOutlined />} />
          </Card>
        </Col>
        <Col xs={12} sm={8} lg={4}>
          <Card>
            <Statistic title="Pedidos Andamento" value={operacional.pedidos_andamento} prefix={<ShoppingCartOutlined />} />
          </Card>
        </Col>
      </Row>

      {operacional.estoque_critico > 0 && (
        <Card style={{ marginTop: 16, borderColor: '#ff4d4f' }}>
          <Statistic
            title="Estoque Critico"
            value={operacional.estoque_critico}
            prefix={<WarningOutlined />}
            suffix="produtos abaixo do minimo"
            valueStyle={{ color: '#cf1322' }}
          />
        </Card>
      )}

      <Divider />

      {/* Vendas por Mes */}
      {vendasMensal.length > 0 && (
        <Card title="Vendas por Mes (ultimos 6 meses)" style={{ marginBottom: 16 }}>
          <Table
            dataSource={vendasMensal}
            rowKey="mes"
            size="small"
            pagination={false}
            columns={[
              { title: 'Mes', dataIndex: 'mes', key: 'mes' },
              { title: 'Qtd Vendas', dataIndex: 'quantidade', key: 'quantidade', width: 100 },
              { title: 'Faturamento', dataIndex: 'faturamento', key: 'faturamento', width: 140, render: (v: number) => formatCurrency(v) },
              { title: 'Lucro', dataIndex: 'lucro', key: 'lucro', width: 140, render: (v: number) => <span style={{ color: v >= 0 ? '#3f8600' : '#cf1322' }}>{formatCurrency(v)}</span> },
            ]}
          />
        </Card>
      )}

      {/* Top Clientes e Produtos */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title="Top 5 Clientes (por faturamento)">
            <Table
              dataSource={topClientes}
              rowKey="cliente"
              size="small"
              pagination={false}
              columns={[
                { title: 'Cliente', dataIndex: 'cliente', key: 'cliente', ellipsis: true },
                { title: 'Vendas', dataIndex: 'qtd', key: 'qtd', width: 70 },
                { title: 'Total', dataIndex: 'total', key: 'total', width: 130, render: (v: number) => formatCurrency(v) },
              ]}
            />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="Top 5 Produtos (por quantidade)">
            <Table
              dataSource={topProdutos}
              rowKey="codigo"
              size="small"
              pagination={false}
              columns={[
                { title: 'Codigo', dataIndex: 'codigo', key: 'codigo', width: 80 },
                { title: 'Produto', dataIndex: 'produto', key: 'produto', ellipsis: true },
                { title: 'Qtd', dataIndex: 'quantidade', key: 'quantidade', width: 60 },
                { title: 'Total', dataIndex: 'total', key: 'total', width: 120, render: (v: number) => formatCurrency(v) },
              ]}
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}
