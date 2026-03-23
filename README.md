# KING BAN ERP

Sistema de Gestao Empresarial para KING BAN — fabricante de banheiros quimicos.

## Stack

- **Backend:** Python 3.12 + FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL 16
- **Frontend:** React 18 + TypeScript + Ant Design + Vite
- **Infra:** Docker Compose + Nginx

## Inicio Rapido (Desenvolvimento)

```bash
# 1. Clonar e acessar
cd kingban-erp

# 2. Subir com Docker Compose
docker compose up -d

# 3. Executar seed (dados iniciais)
docker compose exec backend python -m scripts.seed

# 4. Acessar
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
# Login: admin / admin123
```

## Inicio Rapido (Sem Docker)

```bash
# Backend
cd backend
pip install -e ".[dev]"
# Configurar DATABASE_URL no .env
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

## Testes

```bash
cd backend
pytest tests/ -v
```

## Deploy Producao

```bash
# Configurar variaveis de ambiente
cp .env.example .env
# Editar DB_PASSWORD e SECRET_KEY

# Subir producao
docker compose -f docker-compose.prod.yml up -d
```

## Modulos

| Modulo | Descricao |
|--------|-----------|
| Clientes | Cadastro com CNPJ/CPF, endereco, contato |
| Fornecedores | Cadastro por categoria |
| Produtos | 6 faixas de preco, custo, comissao |
| Vendedores | Salario fixo, comissao variavel |
| Orcamentos | Pipeline 7 status com workflow automatico |
| Vendas | Registro com custos, impostos, lucro |
| Estoque | Entradas/saidas, saldo, estoque critico |
| Compras | CRUD + conta a pagar + entrada estoque automatica |
| Financeiro | Contas a receber/pagar com pagamento parcial |
| Fluxo de Caixa | Lancamentos auto/manuais + resumo |
| Comissoes | Formula: custo + deposito + NF*8.5% = lucro * taxa |
| DIFAL | Calculadora 27 estados + formula especial MG |
| Dashboard | KPIs, vendas mensal, top clientes/produtos |
| DRE | Receita - impostos - custos - despesas = lucro |
| Auditoria | Log de todas as acoes com filtros |

## Regras de Negocio

### Faixas de Preco
1. NF INTEGRAL — preco cheio
2. NF BAIXA 1-3 un — desconto padrao
3. NF BAIXA 4+ un — desconto maior
4. NF CHEIA 4+ un — variante
5. NF INTEGRAL 10+ — volume
6. FABRICA 10+ — direto da fabrica

### Comissao
```
CUSTO = base + IF(DEPOSITO, 65) + NF * 8.5%
LIQUIDO = preco - CUSTO
COMISSAO = LIQUIDO * taxa (15% principal, 20% acessorio)
```

### DIFAL
```
Padrao: (valor / (1 - (aliq_interna + fcp))) * (aliq_interna - aliq_inter + fcp)
MG:     (valor * 1/3) * (aliq_interna - aliq_inter + fcp)
```

## Estrutura

```
kingban-erp/
├── backend/
│   ├── app/
│   │   ├── api/          # Endpoints FastAPI
│   │   ├── core/         # Auth, audit, constants
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Regras de negocio
│   │   └── utils/        # Validadores
│   ├── scripts/          # Seed, migrations
│   └── tests/            # Testes unitarios
├── frontend/
│   └── src/
│       ├── components/   # Layout
│       ├── hooks/        # useCrud generico
│       ├── pages/        # 15 paginas
│       ├── store/        # Zustand (auth)
│       └── utils/        # Formatacao, validacao
├── nginx/                # Nginx config
└── docker-compose.yml    # Desenvolvimento
```

---

KING BAN — Avare/SP — CNPJ 96.453.840/0001-89
