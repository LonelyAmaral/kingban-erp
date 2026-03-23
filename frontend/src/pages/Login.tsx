import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Form, Input, Button, Card, Typography, message, Space } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { useAuthStore } from '../store/authStore'

const { Title, Text } = Typography

export default function Login() {
  const [loading, setLoading] = useState(false)
  const login = useAuthStore((s) => s.login)
  const navigate = useNavigate()

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true)
    try {
      await login(values.username, values.password)
      message.success('Login realizado com sucesso!')
      navigate('/')
    } catch (err: any) {
      message.error(err.message || 'Erro ao fazer login')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      }}
    >
      <Card style={{ width: 400, boxShadow: '0 8px 32px rgba(0,0,0,0.1)' }}>
        <Space direction="vertical" size="large" style={{ width: '100%', textAlign: 'center' }}>
          <div>
            <Title level={2} style={{ marginBottom: 4 }}>KING BAN ERP</Title>
            <Text type="secondary">Sistema de Gestao Empresarial</Text>
          </div>

          <Form layout="vertical" onFinish={onFinish} autoComplete="off" style={{ textAlign: 'left' }}>
            <Form.Item
              name="username"
              rules={[{ required: true, message: 'Informe o usuario' }]}
            >
              <Input
                prefix={<UserOutlined />}
                placeholder="Usuario"
                size="large"
              />
            </Form.Item>

            <Form.Item
              name="password"
              rules={[{ required: true, message: 'Informe a senha' }]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="Senha"
                size="large"
              />
            </Form.Item>

            <Form.Item>
              <Button type="primary" htmlType="submit" loading={loading} block size="large">
                Entrar
              </Button>
            </Form.Item>
          </Form>
        </Space>
      </Card>
    </div>
  )
}
