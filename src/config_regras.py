"""
Configuração Canônica de Regras, Tetos Orçamentários e Parâmetros Financeiros
Família Augusto (Guto), Jéssica (Jé) e Clara.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Senhas e IDs Sensíveis — OBRIGATÓRIOS DO .ENV (ZERO HARDCODED NO CÓDIGO)
CASA_PIN = os.getenv("CASA_PIN")
if not CASA_PIN:
    raise ValueError("Variável de ambiente CASA_PIN não encontrada no arquivo .env!")

SENHA_PDF_99PAY = os.getenv("SENHA_PDF_99PAY")
if not SENHA_PDF_99PAY:
    raise ValueError("Variável de ambiente SENHA_PDF_99PAY não encontrada no arquivo .env!")

GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "1ZfxdNBoyLw0zwLweDWROLEL1uUemtv3jlgWj120bexo")

# ==============================================================================
# 1. TETOS MENSAIS E SEMANAIS DE CONTROLE ATIVO (SEMÁFOROS PWA)
# ==============================================================================

# Vale-Alimentação (Banricard / Novo App)
# Destinado 100% ao supermercado (Zaffari Total) e Feira de Rua de Sábado
TETO_VA_MENSAL = 2763.10
TETO_VA_SEMANAL = 630.00

# Fatura Consolidada dos Cartões de Crédito (Teto Total: R$ 6.000,00)
TETO_CARTAO_GUTO_MENSAL = 3500.00  # Cartões 4110 + 2762 + Nubank
TETO_CARTAO_JE_MENSAL = 2500.00    # Cartões adicionais 4219 + 9994 + 1229

# Mobilidade (Uber + 99)
TETO_UBER_99_GUTO_MENSAL = 400.00
TETO_UBER_99_GUTO_SEMANAL = 100.00
TETO_UBER_99_JE_MENSAL = 400.00
TETO_UBER_99_JE_SEMANAL = 100.00

# Gastos de Lazer e Convívio
TETO_COMER_FORA_MENSAL = 1000.00  # Restaurantes, Baru, Cafeterias, Gelateria e iFood
TETO_COMER_FORA_SEMANAL = 250.00
TETO_COMPRAS_ONLINE_MENSAL = 700.00  # Amazon, Mercado Livre, Shopee, Jogos Nintendo

# ==============================================================================
# 2. MODELO DE RENDAS E EQUALIZADOR DE SOBREAVISO 2x1 (A PARTIR DE JUNHO/2027)
# ==============================================================================
# Base salarial Guto:
SALARIO_BRUTO_BASE_GUTO = 10433.00
SALARIO_LIQUIDO_SEM_SOBREAVISO = 6250.00
SOBREAVISO_BRUTO_ESTIMADO = 4800.00
SOBREAVISO_LIQUIDO_ESTIMADO = 3150.00
SALARIO_LIQUIDO_COM_SOBREAVISO = 9400.00

# Equalizador 2x1:
# Nos 2 meses com sobreaviso: guarda R$ 1.050/mês
# No 3º mês sem sobreaviso: resgata R$ 2.100,00 da reserva
APORTE_MENSAL_EQUALIZADOR_2X1 = 1050.00
RESGATE_MENSAL_EQUALIZADOR_2X1 = 2100.00
RENDA_MENSAL_ESTABILIZADA_GUTO = 8350.00

# ==============================================================================
# 3. PARÂMETROS DA CLÍNICA E REPASSES DA JÉSSICA
# ==============================================================================
CUSTOS_FIXOS_CONSULTORIO_JE = 3223.31
PERCENTUAL_CAIXINHA_PACIENTE_JE = 0.30  # 30% de cada Pix recebido vai para "Casa & Cartão"
META_REPASSE_DIA_10_COLEGIO = 1500.00   # Boleto Colégio Bom Conselho (Clara)
TETO_FATURA_CARTAO_ADICIONAL_JE = 2500.00 # Pago no dia 20 com o saldo da caixinha

# ==============================================================================
# 4. MAPEAMENTO DE CARTOES E TITULARES
# ==============================================================================
CARTOES_GUTO = {"1112", "2553", "4110", "2762", "NUBANK"}
CARTOES_JE = {"1211", "1229", "4946", "4219", "9994"}

# Identificadores de assinaturas para auditoria
ASSINATURAS_CONHECIDAS = [
    {"nome": "YouTube Premium", "kws": ["YOUTUBE"], "status": "Ativo (Essencial)"},
    {"nome": "Netflix", "kws": ["NETFLIX"], "status": "Ativo"},
    {"nome": "Clube Quindim", "kws": ["QUINDIM"], "status": "Ativo (Clara)"},
    {"nome": "Canva Pro", "kws": ["CANVA"], "status": "Ativo (Trabalho Jé)"},
    {"nome": "Google One / AI", "kws": ["GOOGLE ONE", "G1AI101M"], "status": "Ativo (Fotos/Drive)"},
    {"nome": "Aquarius Streaming", "kws": ["AQUARIUS"], "status": "Ativo (Em uso pela família)"},
    {"nome": "iFood Club", "kws": ["IFOOD CLUB", "IFD*IFOOD CLUB"], "status": "Ativo (2ª assinatura já cancelada)"},
    {"nome": "Meli+ (Mercado Livre)", "kws": ["MELIMAIS"], "status": "Ativo"},
    {"nome": "Uber One", "kws": ["UBER ONE"], "status": "Ativo"},
    {"nome": "Asaas Kotas", "kws": ["KOTAS"], "status": "Ativo (R$ 8,70/mês)"},
    {"nome": "Amazon Prime", "kws": ["AMAZON PRIME", "AMAZONPRIMEBR", "AMAZON DIGITAL"], "status": "Ativo"},
    {"nome": "Nubank+", "kws": ["NUBANK+"], "status": "Ativo (Isento por gastos)"},
    {"nome": "APIs IA / Cloud", "kws": ["OPENROUTER", "GOOGLE CLOUD", "REPLICATE"], "status": "Ativo (Monitorar FinOps)"},
]
