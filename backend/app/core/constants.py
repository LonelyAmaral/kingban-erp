"""Business constants — single source of truth for all modules."""

# Tax
TAX_RATE_NF = 0.085          # 8.5% tax on NF value
DEPOSITO_SURCHARGE = 65.0    # Additional cost when shipping from DEPOSITO

# NF types
NF_TYPES = ["NF INTEGRAL", "NF BAIXA", "NF CHEIA"]
SHIPPING_ORIGINS = ["FABRICA", "DEPOSITO"]

# Document flow
DOCUMENT_TYPES = ["ORCAMENTO", "PEDIDO"]
ORDER_STATUSES = [
    "ORCAMENTO", "CONFIRMADO", "RESERVAR ESTOQUE",
    "PRODUCAO", "EXPEDIDO", "ENTREGUE", "CANCELADO"
]

# Inventory
ENTRY_TYPES = ["Compra", "Item Montagem", "Devolucao", "Ajuste", "Cancelamento Reserva"]
EXIT_TYPES = ["BAIXA DE VENDA", "Reserva de Pedido", "Ajuste", "Perda", "Devolucao Fornecedor"]

# Financial
PAYMENT_METHODS = [
    "PIX OU DEPOSITO BANCARIO", "PIX", "DEPOSITO BANCARIO",
    "TRANSFERENCIA", "BOLETO", "CARTAO", "DINHEIRO",
]
PAYMENT_TERMS_OPTIONS = [
    "A VISTA", "50% ENTRADA + 50% NA ENTREGA",
    "30% ENTRADA + 70% PEDIDO PRONTO", "A COMBINAR",
]
AVAILABILITY_OPTIONS = [
    "A PRONTA ENTREGA", "A CONFIRMAR",
    "15 DIAS UTEIS", "20 DIAS UTEIS", "25 DIAS UTEIS", "30 DIAS UTEIS",
]
PRODUCT_CATEGORIES = [
    "BANHEIRO QUIMICO", "PIA / LAVATORIO", "TANQUE", "GUARITA", "CABINE",
    "MICTORIO", "CHUVEIRO", "SACHEBAN / SANITIZANTE", "KIT / ACESSORIO",
    "PECA / REPOSICAO", "FRENTE / PORTA", "OUTRO",
]
ACCOUNT_TYPES = ["RECEIVABLE", "PAYABLE"]
ACCOUNT_STATUSES = ["PENDING", "PARTIAL", "PAID", "OVERDUE"]

# Commission
COMMISSION_RATE_MAIN = 0.15    # 15% for main products
COMMISSION_RATE_ACCESSORY = 0.20  # 20% for accessories

# Roles
ROLES = {
    "admin": ["*"],
    "gerente": ["read:*", "write:*", "delete:orders"],
    "vendedor": ["read:clients", "read:products", "write:orders", "read:commissions"],
    "financeiro": ["read:*", "write:accounts", "write:cashflow"],
    "estoquista": ["read:products", "write:inventory", "read:orders"],
}
