import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import AppLayout from './components/Layout/AppLayout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Clientes from './pages/Clientes'
import Fornecedores from './pages/Fornecedores'
import Produtos from './pages/Produtos'
import Vendedores from './pages/Vendedores'
import Orcamentos from './pages/Orcamentos'
import OrcamentoBuilder from './pages/OrcamentoBuilder'
import Vendas from './pages/Vendas'
import Estoque from './pages/Estoque'
import Financeiro from './pages/Financeiro'
import FluxoCaixa from './pages/FluxoCaixa'
import Comissoes from './pages/Comissoes'
import Difal from './pages/Difal'
import Compras from './pages/Compras'
import Relatorios from './pages/Relatorios'
import Auditoria from './pages/Auditoria'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token)
  if (!token) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <PrivateRoute>
            <AppLayout />
          </PrivateRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="clientes" element={<Clientes />} />
        <Route path="fornecedores" element={<Fornecedores />} />
        <Route path="produtos" element={<Produtos />} />
        <Route path="vendedores" element={<Vendedores />} />
        <Route path="orcamentos" element={<Orcamentos />} />
        <Route path="orcamentos/novo" element={<OrcamentoBuilder />} />
        <Route path="orcamentos/:id/editar" element={<OrcamentoBuilder />} />
        <Route path="vendas" element={<Vendas />} />
        <Route path="estoque" element={<Estoque />} />
        <Route path="compras" element={<Compras />} />
        <Route path="financeiro" element={<Financeiro />} />
        <Route path="fluxo-caixa" element={<FluxoCaixa />} />
        <Route path="comissoes" element={<Comissoes />} />
        <Route path="difal" element={<Difal />} />
        <Route path="relatorios" element={<Relatorios />} />
        <Route path="auditoria" element={<Auditoria />} />
      </Route>
    </Routes>
  )
}
