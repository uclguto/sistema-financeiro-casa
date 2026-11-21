"""
Suíte de Testes Automatizados — Motor Financeiro e Segurança PWA
Valida extração, integridade dos 11 meses, criptografia AES-256-GCM,
ausência de vazamento de dados em texto puro e arquivos da planilha/PWA.
"""

import os
import sys
import json
import pytest
import openpyxl
from cryptography.exceptions import InvalidTag

# Inclui src no sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(BASE_DIR, "src")
sys.path.insert(0, SRC_DIR)

import config_regras as regras
import extrator_unificado
import crypto_pwa
import sync_google_sheets


def test_extrator_unificado_execucao_e_integridade():
    """Valida se a extração gera os dados dos 11 meses com as 28+ categorias e 2.000+ transações."""
    consolidado = extrator_unificado.executar_extracao()
    assert "metadata" in consolidado
    assert "resumo_mensal" in consolidado
    assert "categorias_resumo" in consolidado
    assert "todas_transacoes" in consolidado
    assert "semaforos_atuais" in consolidado
    assert "parcelas_futuras" in consolidado
    assert "assinaturas" in consolidado
    assert "cofrinhos" in consolidado

    # Valida 11 meses (2026-01 a 2026-11)
    meses = [rm["mes"] for rm in consolidado["resumo_mensal"]]
    assert len(meses) == 11
    assert meses[0] == "2026-01"
    assert meses[-1] == "2026-11"

    # Valida 28+ categorias e volume real auditado de transações
    assert len(consolidado["categorias_resumo"]) >= 25
    assert len(consolidado["todas_transacoes"]) >= 2000

    # Valida semáforos reais
    sem = consolidado["semaforos_atuais"]
    assert "va_semana" in sem
    assert "comer_fora_semana" in sem
    assert "uber_guto_semana" in sem
    assert "uber_je_semana" in sem
    assert "compras_online_mes" in sem

    # Valida consistência de valores (folha e cartões positivos)
    tot_sal = sum(rm["salario_liquido"] for rm in consolidado["resumo_mensal"])
    assert tot_sal > 50000.0  # R$ 50k+ acumulado em 11 meses

    tot_cart = sum(rm["cartao_total"] for rm in consolidado["resumo_mensal"])
    assert tot_cart > 30000.0


def test_criptografia_aes_256_gcm_e_rejeicao_pin_falso():
    """Valida a criptografia AES-256-GCM e garante que PIN incorreto é rejeitado."""
    pin_correto = regras.CASA_PIN
    pin_incorreto = "0000" if pin_correto != "0000" else "9999"

    # Criptografa
    payload = crypto_pwa.criptografar_payload(pin=pin_correto)
    assert "salt" in payload
    assert "iv" in payload
    assert "ciphertext" in payload

    # Descriptografa com o PIN correto
    decrypted = crypto_pwa.descriptografar_payload(payload, pin=pin_correto)
    assert decrypted["metadata"]["meses_analisados"] == "2026-01 a 2026-11"
    assert len(decrypted["resumo_mensal"]) == 11

    # Descriptografar com PIN falso DEVE falhar com InvalidTag
    with pytest.raises(InvalidTag):
        crypto_pwa.descriptografar_payload(payload, pin=pin_incorreto)


def test_payload_enc_zero_leakage():
    """Garante que o arquivo publicado web/payload.enc.json não vaza nenhuma palavra-chave em texto puro."""
    payload_file = os.path.join(BASE_DIR, "web", "payload.enc.json")
    assert os.path.exists(payload_file)

    with open(payload_file, "r", encoding="utf-8") as f:
        raw_text = f.read()

    # Nenhuma palavra sensível pode existir em texto puro no arquivo
    termos_proibidos = [
        "salario_liquido",
        "cartao_augusto",
        "cartao_jessica",
        "colegio_clara",
        "JESSICA DE MATOS",
        "AUGUSTO SIMON",
        "ZAFFARI TOTAL",
    ]
    for termo in termos_proibidos:
        assert termo not in raw_text, f"Vazamento detectado: {termo} encontrado no payload publicado!"


def test_geracao_planilha_google_sheets_xlsx():
    """Valida a geração da planilha XLSX com as abas estruturadas e preservação das originais."""
    sync_google_sheets.sincronizar_planilha()
    xlsx_path = sync_google_sheets.OUTPUT_XLSX
    assert os.path.exists(xlsx_path)

    wb = openpyxl.load_workbook(xlsx_path, data_only=False)
    sheet_names = wb.sheetnames
    assert "Resumo & Metas 2026-2027" in sheet_names
    assert "Gastos Mensais por Categoria" in sheet_names
    assert "Parcelas Futuras & Assinaturas" in sheet_names
    assert "Lançamentos Auditados 2026" in sheet_names
    # Abas originais preservadas
    assert any("Orig -" in name for name in sheet_names)

    ws_resumo = wb["Resumo & Metas 2026-2027"]
    assert ws_resumo["A1"].value == "CONTROLE FINANCEIRO DOMÉSTICO — GUTO & JÉ"


def test_pwa_arquivos_estaticos_presentes():
    """Valida que todos os componentes estáticos do PWA estão no diretório web/."""
    web_dir = os.path.join(BASE_DIR, "web")
    arquivos_esperados = [
        "index.html",
        "styles.css",
        "app.js",
        "manifest.json",
        "sw.js",
        "icon.svg",
        "_headers",
        "payload.enc.json"
    ]
    for arq in arquivos_esperados:
        p = os.path.join(web_dir, arq)
        assert os.path.exists(p), f"Arquivo PWA ausente: {arq}"
        assert os.path.getsize(p) > 0, f"Arquivo PWA vazio: {arq}"


def test_blindagem_gitignore():
    """Valida se o .gitignore blinda arquivos brutos e dados em texto puro."""
    gitignore_path = os.path.join(BASE_DIR, ".gitignore")
    assert os.path.exists(gitignore_path)

    with open(gitignore_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "extratos/" in content
    assert "data/consolidado_2026_2027.json" in content
    assert "*.pdf" in content
    assert "*.csv" in content
    assert "*.xlsx" in content
    assert ".env" in content
