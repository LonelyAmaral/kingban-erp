import { create } from 'zustand'
import api from '../api/client'

interface User {
  id: number
  username: string
  full_name: string
  email: string | null
  role: string
  tenant_id: number
}

interface AuthState {
  token: string | null
  user: User | null
  loading: boolean
  error: string | null
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  fetchUser: () => Promise<void>
}

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem('token'),
  user: JSON.parse(localStorage.getItem('user') || 'null'),
  loading: false,
  error: null,

  login: async (username: string, password: string) => {
    set({ loading: true, error: null })
    try {
      const { data } = await api.post('/auth/login', { username, password })
      localStorage.setItem('token', data.access_token)
      set({ token: data.access_token, loading: false })

      // Buscar dados do usuario
      const userRes = await api.get('/auth/me', {
        headers: { Authorization: `Bearer ${data.access_token}` },
      })
      localStorage.setItem('user', JSON.stringify(userRes.data))
      set({ user: userRes.data })
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Erro ao fazer login'
      set({ error: msg, loading: false })
      throw new Error(msg)
    }
  },

  logout: () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    set({ token: null, user: null })
  },

  fetchUser: async () => {
    try {
      const { data } = await api.get('/auth/me')
      localStorage.setItem('user', JSON.stringify(data))
      set({ user: data })
    } catch {
      // Token invalido
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      set({ token: null, user: null })
    }
  },
}))
