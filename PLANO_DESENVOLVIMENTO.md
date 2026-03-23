# KING BAN ERP Web — Plano de Desenvolvimento

> Documento vivo: atualizado a cada fase concluida.
> Ultima atualizacao: 2026-03-22

---

## 1. VISAO GERAL

Sistema ERP web para a KING BAN (banheiros quimicos, Avare-SP).
Substitui o sistema desktop (Python + PySide6 + SQLite) por uma aplicacao web
moderna com suporte a multi-usuario, multi-empresa e acesso remoto.

### Stack
- **Backend:** Python 3.12 + FastAPI + SQLAlchemy 2.0 + Alembic
- **Banco:** PostgreSQL 16
- **Frontend:** React 18 + TypeScript + Ant Design
- **Infra:** Docker Compose

### Principios
- Interface 100% em portugues (PT-BR)
- Mensagens de erro, labels, endpoints descritivos em portugues
- Comentarios no codigo em portugues
- Multi-tenant (multi-empresa) desde o inicio
- Auth JWT com 5 roles (admin, gerente, vendedor, financeiro, estoquista)
- Toda logica de negocio no service layer (nunca nos endpoints)

---

## 2. FASES DE IMPLEMENTACAO

### FASE 1: FUNDACAO (backend) ✅ CONCLUIDA
**Data:** 2026-03-21

Arquivos criados:
- `backend/pyproject.toml` — dependencias Python
- `backend/app/main.py` — FastAPI app com 14 routers
- `backend/app/config.py` — configuracao via env vars
- `backend/app/database.py` — SQLAlchemy async engine
- `backend/app/models/` — 13 models SQLAlchemy (16 tabelas)
- `backend/app/core/auth.py` — JWT + bcrypt
- `backend/app/core/permissions.py` — RBAC 5 roles
- `backend/app/core/tenant.py` — multi-tenant middleware
- `backend/app/core/audit.py` — log de auditoria
- `backend/app/core/constants.py` — constantes de negocio
- `backend/app/api/auth.py` — login/register/me
- `backend/app/api/*.py` — 13 router stubs
- `backend/app/seed/__init__.py` — seed KING BAN + KING PLAST + admin
- `backend/alembic/` — configuracao de migracoes
- `docker-compose.yml` — PostgreSQL + Backend
- `Dockerfile`, `.env`

Decisoes:
- Todas as tabelas com tenant_id (multi-empresa)
- Modelo Supplier NOVO (nao existia no desktop)
- Inventory com campo location (multi-localizacao)
- AuditLog ativo (vs desktop onde era tabela morta)

---

### FASE 2: CADASTROS (backend + frontend) ✅ CONCLUIDA
**Objetivo:** CRUDs completos + frontend funcional com login

#### 2A — Backend: APIs de Cadastro ✅
- [x] Schemas Pydantic (request/response) para todos os cadastros
- [x] Models alinhados com nomes PT (nome, endereco, cidade, telefone, etc.)
- [x] API Clientes: listar, criar, editar, excluir, buscar
- [x] API Fornecedores: listar, criar, editar, excluir, buscar + filtro categoria
- [x] API Produtos: listar, criar, editar, excluir + 6 faixas de preco + endpoint /categorias
- [x] API Vendedores: listar, criar, editar, excluir
- [x] Paginacao padrao em todas as listagens
- [x] Filtros: busca por nome, CNPJ, codigo, categoria
- [x] Audit log em todas as operacoes de escrita
- [x] Validacao de codigo duplicado em produtos
- [x] Soft delete (desativar) em vez de excluir registros

#### 2B — Frontend: React + Ant Design ✅
- [x] Setup: Vite + React + TypeScript + Ant Design (locale pt-BR)
- [x] API client (axios) com interceptor JWT + redirect 401
- [x] AuthStore (Zustand) — login/logout/token/fetchUser
- [x] Layout: Sidebar com icones + Header com dropdown usuario
- [x] Pagina Login — formulario estilizado com gradiente
- [x] Pagina Dashboard (placeholder com 4 cards)
- [x] Pagina Clientes — tabela com busca, paginacao, CRUD modal
- [x] Pagina Fornecedores — mesmo padrao + campo categoria
- [x] Pagina Produtos — com abas (Geral + Faixas de Preco) no modal
- [x] Pagina Vendedores — CRUD simples com salario fixo
- [x] Hook useCrud generico reutilizavel para todos os CRUDs
- [x] Utilitarios: formatCurrency (R$), formatPercent (%)
- [x] Docker Compose atualizado com servico frontend

---

### FASE 3: VENDAS E ESTOQUE ✅ CONCLUIDA
**Data:** 2026-03-22

#### 3A — Backend ✅
- [x] Services portados do desktop:
  - `services/pricing.py` — motor de precos (6 faixas), resolve_price, calculate_order_totals
  - `services/order_workflow.py` — pipeline 7 status, change_order_status com VALID_TRANSITIONS
  - `services/inventory_service.py` — add_entry, add_exit, get_current_stock, recalculate_inventory
  - `services/commission.py` — calculate_commission_line, generate_commission_report
- [x] Schemas PT: order.py (PedidoCriar/Atualizar/Response + ItemPedido + MudarStatus)
- [x] Schemas PT: sale.py (VendaResponse + ResumoVendas)
- [x] Schemas PT: inventory.py (EstoqueAtual + EntradaCriar/Response + SaidaCriar/Response)
- [x] API Orcamentos: CRUD + pipeline 7 status + proximo-numero + acoes automaticas
- [x] API Vendas: listagem paginada + resumo por periodo (total/custos/impostos/lucro)
- [x] API Estoque: saldo atual + entradas/saidas CRUD + recalcular por produto
- [ ] PDF generator (portado do desktop, ReportLab) — pendente para Fase 4

#### 3B — Frontend ✅
- [x] Pagina Orcamentos — lista com filtros de status (tags coloridas) + modal mudar status
- [x] Pagina Vendas — cards resumo (vendas/custos/impostos/lucro) + tabela + filtro por periodo
- [x] Pagina Estoque — 3 abas (Saldo Atual, Entradas, Saidas) + modais criar entrada/saida
- [x] Menu lateral atualizado com secao Orcamentos/Vendas/Estoque
- [ ] Pagina Novo Orcamento — formulario builder (pendente para refinamento)
- [ ] Download PDF de orcamento — pendente para Fase 4

---

### FASE 4: FINANCEIRO E COMISSOES ✅ CONCLUIDA
**Data:** 2026-03-22
**Objetivo:** Contas a pagar/receber, fluxo de caixa, DRE, comissoes, DIFAL

#### 4A — Backend ✅
- [x] Models novos: CashFlowEntry, Purchase, PurchaseItem, DifalRate
- [x] Schemas PT: account.py, cashflow.py, commission.py, difal.py, purchase.py
- [x] API Contas: CRUD + pagamento parcial/total + auto fluxo de caixa
- [x] API Fluxo de Caixa (NOVO): lancamentos auto + manuais + resumo + categorias
- [x] Servico cashflow_service.py (NOVO): create_entry + get_summary
- [x] API Relatorios: DRE simplificado (receita - impostos - custos - despesas = lucro)
- [x] API Comissoes: relatorio por periodo/vendedor + custos base + lista vendedores
- [x] Servico commission.py (portado na Fase 3 — formula completa)
- [x] API DIFAL: calculadora + estados + CRUD aliquotas
- [x] Servico difal.py (portado — formula padrao + formula MG)
- [x] API Compras: CRUD + auto conta a pagar + receber (auto entrada estoque) + cancelar

#### 4B — Frontend ✅
- [x] Pagina Financeiro — contas AR/AP com filtros tipo/status + cores + modal pagamento
- [x] Pagina Fluxo de Caixa — cards resumo (entradas/saidas/saldo) + filtro periodo/tipo + lancamento manual
- [x] Pagina Comissoes — formulario vendedor/periodo + cards resumo + tabela detalhada com totais
- [x] Pagina DIFAL — calculadora interativa + tabela aliquotas por estado/NCM
- [x] Pagina Compras — CRUD com itens dinamicos + receber/cancelar + expandir itens + auto conta a pagar
- [x] Menu lateral atualizado com secao Financeiro (5 itens novos)
- [ ] Exportar Excel comissoes — pendente para Fase 5

---

### FASE 5: DASHBOARD, RELATORIOS, AUDITORIA ✅ CONCLUIDA
**Data:** 2026-03-22
**Objetivo:** Visao gerencial completa

- [x] Dashboard com KPIs: faturamento, lucro, ticket medio, contas AR/AP, cadastros, operacional
- [x] Tabelas: vendas por mes, top 5 clientes, top 5 produtos
- [x] Pagina DRE: receita - impostos - custos = lucro bruto - despesas = lucro liquido + margens
- [x] Tela de Audit Log — consulta paginada com filtros tabela/acao
- [x] API Audit: listagem + endpoints tabelas/acoes
- [ ] Exportacao Excel — pendente para Fase 6
- [ ] Configuracoes empresa/usuarios — pendente para Fase 6

---

### FASE 6: POLIMENTO ✅ CONCLUIDA
**Data:** 2026-03-22
**Objetivo:** Qualidade e deploy

- [x] Testes automatizados: 43 testes (pricing 11, commission 6, difal 8, validators 12, utils 6)
- [x] Docker Compose production-ready (Dockerfile.prod multi-stage + nginx + gunicorn)
- [x] Seed completo: 20 produtos, 27 estados x 2 NCMs DIFAL, 3 vendedores, custos comissao
- [x] Validacao CNPJ/CPF: backend (validators.py) + frontend (validators.ts + cnpjCpfRule)
- [x] README.md com instrucoes de instalacao, modulos, regras de negocio, estrutura
- [x] .env.example para configuracao
- [x] nginx.conf com rate limiting, gzip, proxy reverso, SSL preparado

---

## 3. REGRAS DE NEGOCIO (portadas do desktop)

### 3.1 Faixas de Preco (6 tiers)
1. NF INTEGRAL — preco cheio
2. NF BAIXA 1-3 unidades — preco com desconto
3. NF BAIXA 4+ unidades — desconto maior
4. NF CHEIA 4+ unidades — variante
5. NF INTEGRAL 10+ — volume grande
6. FABRICA 10+ — direto da fabrica

### 3.2 Formula de Comissao
```
CUSTO_TOTAL = custo_base + IF(DEPOSITO, 65, 0) + valor_NF * 8.5%
LIQUIDO = preco_venda - CUSTO_TOTAL
COMISSAO = LIQUIDO * taxa (15% produtos, 20% acessorios)
```

### 3.3 Pipeline de Pedidos (7 status)
ORCAMENTO → CONFIRMADO → RESERVAR ESTOQUE → PRODUCAO → EXPEDIDO → ENTREGUE → CANCELADO

Acoes automaticas:
- CONFIRMADO: cria conta a receber
- RESERVAR ESTOQUE / PRODUCAO: reserva estoque
- ENTREGUE: cria venda + baixa estoque (ou vincula reserva)
- CANCELADO: estorna reserva de estoque

### 3.4 DIFAL
- Calculo por estado destino (27 estados)
- Formula padrao: (valor / (1 - (aliq_interna + fcp))) * (aliq_interna - aliq_inter + fcp)
- Formula especial MG: (valor * 1/3) * (aliq_interna - aliq_inter + fcp)
- Taxa NF: 8.5% (TAX_RATE_NF = 0.085)

### 3.5 Codigos de Produtos
- 01XX-04XX: banheiros montados (MR, PRIME, POLYBAN, usados)
- 21XX-23XX: banheiros desmontados
- 05XX-20XX: pecas avulsas
- 30XX: SACHEBAN (sanitizantes)
- 90XX: diversos
- 3o digito = modelo, 4o digito = cor

---

## 4. DECISOES TECNICAS

### 4.1 Idioma
- **Interface:** 100% portugues
- **Codigo:** nomes de variaveis e funcoes em ingles (padrao Python/React)
- **Mensagens ao usuario:** portugues (erros, labels, placeholders)
- **Comentarios:** portugues
- **API responses:** mensagens em portugues

### 4.2 Multi-Tenant
- Coluna `tenant_id` em todas as tabelas via `TenantModel` base
- Middleware extrai tenant do JWT e injeta na request
- Queries filtram automaticamente por tenant
- Admin pode ver todos os tenants (futuro)

### 4.3 Autenticacao
- JWT com expiracao de 8 horas
- 5 roles: admin, gerente, vendedor, financeiro, estoquista
- Senha com bcrypt (passlib)
- Login: POST /api/auth/login → {access_token, token_type}

### 4.4 Paginacao
- Padrao: `?pagina=1&por_pagina=50&busca=texto&ordenar=nome&direcao=asc`
- Response: `{itens: [...], total: N, pagina: N, paginas: N}`

---

## 5. HISTORICO DE ALTERACOES

| Data | Fase | Descricao |
|------|------|-----------|
| 2026-03-21 | 1 | Fundacao: 50 arquivos criados (models, auth, docker, alembic) |
| 2026-03-21 | 2A | Schemas Pydantic + models PT + 4 CRUDs completos (clients, suppliers, products, salespeople) |
| 2026-03-21 | 2B | Frontend: Vite + React + TS + AntD + Login + Layout + 4 paginas CRUD + hook generico |
| 2026-03-22 | 3A | 4 services portados (pricing, workflow, inventory, commission) + 3 APIs completas (orders, sales, inventory) |
| 2026-03-22 | 3B | Frontend: 3 paginas (Orcamentos com pipeline, Vendas com resumo, Estoque com 3 abas) |
| 2026-03-22 | 4A | 4 models novos + 6 schemas PT + 2 services (difal, cashflow) + 6 APIs completas (accounts, cashflow, commissions, difal, reports, purchases) |
| 2026-03-22 | 4B | Frontend: 5 paginas novas (Financeiro, Fluxo Caixa, Comissoes, DIFAL, Compras) + menu lateral atualizado |
| 2026-03-22 | 5A | API Dashboard (KPIs + vendas mensal + top clientes/produtos) + API Audit Log (paginado + filtros) |
| 2026-03-22 | 5B | Dashboard completo com KPIs + DRE formatado + Auditoria + menu atualizado (18 itens) |
| 2026-03-22 | 6 | 43 testes unitarios + Docker prod (multi-stage + nginx + gunicorn) + seed 52 registros + CNPJ/CPF + README |
