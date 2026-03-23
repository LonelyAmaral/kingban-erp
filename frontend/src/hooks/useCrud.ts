import { useState, useEffect, useCallback } from 'react'
import { message } from 'antd'
import api from '../api/client'

interface PaginacaoResponse<T> {
  itens: T[]
  total: number
  pagina: number
  paginas: number
}

interface UseCrudOptions {
  endpoint: string
  defaultPageSize?: number
}

export function useCrud<T extends { id: number }>({ endpoint, defaultPageSize = 50 }: UseCrudOptions) {
  const [data, setData] = useState<T[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [pagina, setPagina] = useState(1)
  const [porPagina, setPorPagina] = useState(defaultPageSize)
  const [busca, setBusca] = useState('')

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const params: Record<string, any> = {
        pagina,
        por_pagina: porPagina,
      }
      if (busca) params.busca = busca

      const { data: res } = await api.get<PaginacaoResponse<T>>(endpoint, { params })
      setData(res.itens)
      setTotal(res.total)
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Erro ao carregar dados')
    } finally {
      setLoading(false)
    }
  }, [endpoint, pagina, porPagina, busca])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const criar = async (valores: Partial<T>): Promise<T | null> => {
    try {
      const { data: novo } = await api.post<T>(endpoint, valores)
      message.success('Registro criado com sucesso!')
      await fetchData()
      return novo
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Erro ao criar registro')
      return null
    }
  }

  const atualizar = async (id: number, valores: Partial<T>): Promise<T | null> => {
    try {
      const { data: atualizado } = await api.put<T>(`${endpoint}/${id}`, valores)
      message.success('Registro atualizado com sucesso!')
      await fetchData()
      return atualizado
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Erro ao atualizar registro')
      return null
    }
  }

  const excluir = async (id: number): Promise<boolean> => {
    try {
      await api.delete(`${endpoint}/${id}`)
      message.success('Registro desativado com sucesso!')
      await fetchData()
      return true
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Erro ao excluir registro')
      return false
    }
  }

  return {
    data,
    loading,
    total,
    pagina,
    porPagina,
    busca,
    setPagina,
    setPorPagina,
    setBusca,
    fetchData,
    criar,
    atualizar,
    excluir,
  }
}
