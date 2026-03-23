import { useState, useEffect } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout, Menu, Button, Dropdown, Typography, Drawer } from 'antd'
import {
  DashboardOutlined,
  TeamOutlined,
  ShopOutlined,
  AppstoreOutlined,
  UserOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  MenuOutlined,
  LogoutOutlined,
  FileTextOutlined,
  ShoppingCartOutlined,
  InboxOutlined,
  DollarOutlined,
  BankOutlined,
  PercentageOutlined,
  CalculatorOutlined,
  ShoppingOutlined,
  BarChartOutlined,
  AuditOutlined,
} from '@ant-design/icons'
import { useAuthStore } from '../../store/authStore'

const { Header, Sider, Content } = Layout
const { Text } = Typography

// Brand colors do desktop KING BAN
const SIDEBAR_BG = '#0D3311'
const SIDEBAR_TEXT = '#E8F5E9'
const PRIMARY_GREEN = '#1B5E20'
const ACCENT_ORANGE = '#FF8F00'

const menuItems = [
  { key: '/', icon: <DashboardOutlined />, label: 'Dashboard' },
  { type: 'divider' as const },
  { key: '/clientes', icon: <TeamOutlined />, label: 'Clientes' },
  { key: '/fornecedores', icon: <ShopOutlined />, label: 'Fornecedores' },
  { key: '/produtos', icon: <AppstoreOutlined />, label: 'Produtos' },
  { key: '/vendedores', icon: <UserOutlined />, label: 'Vendedores' },
  { type: 'divider' as const },
  { key: '/orcamentos', icon: <FileTextOutlined />, label: 'Orcamentos' },
  { key: '/vendas', icon: <ShoppingCartOutlined />, label: 'Vendas' },
  { key: '/estoque', icon: <InboxOutlined />, label: 'Estoque' },
  { key: '/compras', icon: <ShoppingOutlined />, label: 'Compras' },
  { type: 'divider' as const },
  { key: '/financeiro', icon: <DollarOutlined />, label: 'Financeiro' },
  { key: '/fluxo-caixa', icon: <BankOutlined />, label: 'Fluxo de Caixa' },
  { key: '/comissoes', icon: <PercentageOutlined />, label: 'Comissoes' },
  { key: '/difal', icon: <CalculatorOutlined />, label: 'DIFAL' },
  { type: 'divider' as const },
  { key: '/relatorios', icon: <BarChartOutlined />, label: 'Relatorios (DRE)' },
  { key: '/auditoria', icon: <AuditOutlined />, label: 'Auditoria' },
]

export default function AppLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const [isMobile, setIsMobile] = useState(false)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuthStore()

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
      if (window.innerWidth >= 768) setDrawerOpen(false)
    }
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const handleMenuClick = (key: string) => {
    navigate(key)
    if (isMobile) setDrawerOpen(false)
  }

  const userMenu = {
    items: [
      {
        key: 'role',
        label: `Perfil: ${user?.role || ''}`,
        disabled: true,
      },
      { type: 'divider' as const },
      {
        key: 'logout',
        icon: <LogoutOutlined />,
        label: 'Sair',
        onClick: handleLogout,
      },
    ],
  }

  const sidebarMenu = (
    <Menu
      mode="inline"
      selectedKeys={[location.pathname]}
      items={menuItems}
      onClick={({ key }) => handleMenuClick(key)}
      style={{
        borderRight: 0,
        background: 'transparent',
        color: SIDEBAR_TEXT,
      }}
      theme="dark"
    />
  )

  const sidebarLogo = (
    <div
      style={{
        height: 64,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        borderBottom: '1px solid rgba(255,255,255,0.15)',
      }}
    >
      <Text strong style={{ fontSize: collapsed ? 14 : 18, color: SIDEBAR_TEXT }}>
        {collapsed ? 'KB' : 'KING BAN'}
      </Text>
    </div>
  )

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* Desktop/Tablet: Sidebar */}
      {!isMobile && (
        <Sider
          trigger={null}
          collapsible
          collapsed={collapsed}
          width={220}
          style={{ background: SIDEBAR_BG }}
        >
          {sidebarLogo}
          {sidebarMenu}
        </Sider>
      )}

      {/* Mobile: Drawer */}
      {isMobile && (
        <Drawer
          placement="left"
          open={drawerOpen}
          onClose={() => setDrawerOpen(false)}
          width={250}
          styles={{ body: { padding: 0, background: SIDEBAR_BG } }}
          style={{ padding: 0 }}
        >
          {sidebarLogo}
          {sidebarMenu}
        </Drawer>
      )}

      <Layout>
        <Header
          style={{
            padding: '0 16px',
            background: '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '1px solid #f0f0f0',
            boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
          }}
        >
          {isMobile ? (
            <Button
              type="text"
              icon={<MenuOutlined />}
              onClick={() => setDrawerOpen(true)}
              style={{ fontSize: 18 }}
            />
          ) : (
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setCollapsed(!collapsed)}
            />
          )}
          <Dropdown menu={userMenu} placement="bottomRight">
            <Button type="text" icon={<UserOutlined />}>
              {!isMobile && (user?.full_name || user?.username || '')}
            </Button>
          </Dropdown>
        </Header>
        <Content
          style={{
            margin: isMobile ? 8 : 24,
            padding: isMobile ? 12 : 24,
            background: '#fff',
            borderRadius: 8,
          }}
        >
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}
