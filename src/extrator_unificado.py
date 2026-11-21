"""
Motor de Extração Unificada e Reconciliação Financeira
Processa os 73 arquivos brutos (PDFs Banrisul/Nubank/99Pay/Contracheques, CSVs, Transcrições de VA e Cofrinhos)
e gera o arquivo canônico data/consolidado_2026_2027.json.
"""

import os
import sys
import json
import re
from datetime import datetime
from collections import defaultdict
import pypdf

# Garante importação do config_regras
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config_regras as regras

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXTRATOS_DIR = os.path.join(os.path.dirname(BASE_DIR), "extratos")
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_JSON = os.path.join(DATA_DIR, "consolidado_2026_2027.json")


def parse_br_num(s):
    """Converte números formatados em pt-BR (ex: 1.250,50- ou -12,30) para float."""
    if not s:
        return 0.0
    s = str(s).strip().replace("\xa0", "").replace(" ", "")
    neg = False
    if s.endswith("-"):
        neg = True
        s = s[:-1]
    elif s.startswith("-"):
        neg = True
        s = s[1:]
    elif s.startswith("+"):
        s = s[1:]
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        val = float(s.strip())
        return -val if neg else val
    except ValueError:
        return 0.0


def extrair_textos_pdf(pdf_path, password=None):
    """Extrai lista de páginas em texto de um PDF usando pypdf."""
    pages_text = []
    try:
        reader = pypdf.PdfReader(pdf_path)
        if reader.is_encrypted:
            if password:
                reader.decrypt(password)
            else:
                return []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                pages_text.append(t)
    except Exception as e:
        print(f"Erro ao ler PDF {os.path.basename(pdf_path)}: {e}")
    return pages_text


# ==============================================================================
# TRANSCRIÇÃO HISTÓRICA DO VALE-ALIMENTAÇÃO (VÍDEOS APPS JUN-NOV/2026)
# ==============================================================================
VA_HISTORICO_CREDITOS = [
    {"ym": "2026-06", "date": "25/06/2026", "desc": "Crédito Banricard", "amount": 2530.44},
    {"ym": "2026-07", "date": "24/07/2026", "desc": "Crédito Banricard", "amount": 2530.44},
    {"ym": "2026-08", "date": "03/08/2026", "desc": "Ajuste Banricard", "amount": 22.70},
    {"ym": "2026-08", "date": "25/08/2026", "desc": "Crédito Banricard", "amount": 2530.44},
    {"ym": "2026-09", "date": "03/09/2026", "desc": "Ajuste Banricard", "amount": 21.00},
    {"ym": "2026-09", "date": "25/09/2026", "desc": "Crédito Banricard (Dissídio)", "amount": 2763.10},
    {"ym": "2026-10", "date": "23/10/2026", "desc": "Crédito Novo App", "amount": 2646.77},
]

VA_HISTORICO_DEBITOS = [
    # Junho 2026
    {"ym": "2026-06", "date": "03/06", "desc": "ZAFFARI TOTAL", "amount": 322.78, "cat": "Zaffari"},
    {"ym": "2026-06", "date": "04/06", "desc": "ZAFFARI TOTAL", "amount": 103.59, "cat": "Zaffari"},
    {"ym": "2026-06", "date": "05/06", "desc": "PANVEL", "amount": 25.72, "cat": "Farmacia"},
    {"ym": "2026-06", "date": "05/06", "desc": "ZAFFARI TOTAL", "amount": 47.00, "cat": "Zaffari"},
    {"ym": "2026-06", "date": "06/06", "desc": "TROPEIRO VELHO", "amount": 35.00, "cat": "Feira"},
    {"ym": "2026-06", "date": "06/06", "desc": "FEIRA DIVERSOS", "amount": 143.00, "cat": "Feira"},
    {"ym": "2026-06", "date": "07/06", "desc": "ZAFFARI TOTAL", "amount": 157.32, "cat": "Zaffari"},
    {"ym": "2026-06", "date": "09/06", "desc": "ZAFFARI TOTAL", "amount": 112.55, "cat": "Zaffari"},
    {"ym": "2026-06", "date": "10/06", "desc": "ZAFFARI TOTAL", "amount": 171.44, "cat": "Zaffari"},
    {"ym": "2026-06", "date": "10/06", "desc": "PANVEL", "amount": 34.99, "cat": "Farmacia"},
    {"ym": "2026-06", "date": "12/06", "desc": "ZAFFARI TOTAL", "amount": 128.63, "cat": "Zaffari"},
    {"ym": "2026-06", "date": "13/06", "desc": "ZAFFARI TOTAL", "amount": 255.29, "cat": "Zaffari"},
    {"ym": "2026-06", "date": "15/06", "desc": "ZAFFARI TOTAL", "amount": 146.49, "cat": "Zaffari"},
    {"ym": "2026-06", "date": "18/06", "desc": "RESTAURANTE JOHANN", "amount": 45.90, "cat": "Restaurante"},
    {"ym": "2026-06", "date": "18/06", "desc": "ZAFFARI TOTAL", "amount": 263.68, "cat": "Zaffari"},
    {"ym": "2026-06", "date": "25/06", "desc": "ZAFFARI TOTAL", "amount": 176.74, "cat": "Zaffari"},
    {"ym": "2026-06", "date": "25/06", "desc": "PANVEL", "amount": 49.90, "cat": "Farmacia"},
    {"ym": "2026-06", "date": "27/06", "desc": "FEIRA SABADO", "amount": 146.85, "cat": "Feira"},
    {"ym": "2026-06", "date": "28/06", "desc": "ZAFFARI TOTAL", "amount": 162.57, "cat": "Zaffari"},
    # Julho 2026
    {"ym": "2026-07", "date": "04/07", "desc": "FEIRA SABADO", "amount": 208.90, "cat": "Feira"},
    {"ym": "2026-07", "date": "06/07", "desc": "ZAFFARI TOTAL", "amount": 190.31, "cat": "Zaffari"},
    {"ym": "2026-07", "date": "07/07", "desc": "ZAFFARI TOTAL", "amount": 209.95, "cat": "Zaffari"},
    {"ym": "2026-07", "date": "11/07", "desc": "FEIRA SABADO", "amount": 109.90, "cat": "Feira"},
    {"ym": "2026-07", "date": "12/07", "desc": "ZAFFARI TOTAL", "amount": 277.10, "cat": "Zaffari"},
    {"ym": "2026-07", "date": "13/07", "desc": "ZAFFARI TOTAL", "amount": 34.90, "cat": "Zaffari"},
    {"ym": "2026-07", "date": "16/07", "desc": "ZAFFARI TOTAL", "amount": 38.93, "cat": "Zaffari"},
    {"ym": "2026-07", "date": "17/07", "desc": "B12 PRODUTOS NATURAIS", "amount": 37.11, "cat": "Zaffari"},
    {"ym": "2026-07", "date": "17/07", "desc": "ZAFFARI TOTAL", "amount": 49.74, "cat": "Zaffari"},
    {"ym": "2026-07", "date": "18/07", "desc": "FEIRA SABADO", "amount": 256.10, "cat": "Feira"},
    {"ym": "2026-07", "date": "18/07", "desc": "ZAFFARI TOTAL", "amount": 128.98, "cat": "Zaffari"},
    {"ym": "2026-07", "date": "22/07", "desc": "ZAFFARI TOTAL", "amount": 178.12, "cat": "Zaffari"},
    {"ym": "2026-07", "date": "23/07", "desc": "ZAFFARI TOTAL", "amount": 25.35, "cat": "Zaffari"},
    {"ym": "2026-07", "date": "26/07", "desc": "CAFETERIA MUSA VELUTINA", "amount": 49.39, "cat": "Restaurante"},
    {"ym": "2026-07", "date": "27/07", "desc": "ZAFFARI TOTAL", "amount": 132.84, "cat": "Zaffari"},
    {"ym": "2026-07", "date": "29/07", "desc": "CAFETERIA MUSA VELUTINA", "amount": 49.39, "cat": "Restaurante"},
    {"ym": "2026-07", "date": "30/07", "desc": "ZAFFARI TOTAL", "amount": 77.69, "cat": "Zaffari"},
    # Agosto 2026
    {"ym": "2026-08", "date": "01/08", "desc": "FEIRA SABADO", "amount": 259.00, "cat": "Feira"},
    {"ym": "2026-08", "date": "02/08", "desc": "ZAFFARI TOTAL", "amount": 169.56, "cat": "Zaffari"},
    {"ym": "2026-08", "date": "04/08", "desc": "PANVEL", "amount": 34.99, "cat": "Farmacia"},
    {"ym": "2026-08", "date": "05/08", "desc": "ZAFFARI TOTAL", "amount": 115.65, "cat": "Zaffari"},
    {"ym": "2026-08", "date": "08/08", "desc": "FEIRA SABADO", "amount": 254.40, "cat": "Feira"},
    {"ym": "2026-08", "date": "08/08", "desc": "ZAFFARI TOTAL", "amount": 155.67, "cat": "Zaffari"},
    {"ym": "2026-08", "date": "10/08", "desc": "ZAFFARI TOTAL", "amount": 128.78, "cat": "Zaffari"},
    {"ym": "2026-08", "date": "13/08", "desc": "ZAFFARI TOTAL", "amount": 95.80, "cat": "Zaffari"},
    {"ym": "2026-08", "date": "15/08", "desc": "FEIRA SABADO", "amount": 192.40, "cat": "Feira"},
    {"ym": "2026-08", "date": "17/08", "desc": "ZAFFARI TOTAL", "amount": 224.26, "cat": "Zaffari"},
    {"ym": "2026-08", "date": "20/08", "desc": "ZAFFARI TOTAL", "amount": 149.65, "cat": "Zaffari"},
    {"ym": "2026-08", "date": "22/08", "desc": "FEIRA SABADO", "amount": 182.20, "cat": "Feira"},
    {"ym": "2026-08", "date": "24/08", "desc": "ZAFFARI TOTAL", "amount": 168.61, "cat": "Zaffari"},
    {"ym": "2026-08", "date": "26/08", "desc": "ZAFFARI TOTAL", "amount": 139.73, "cat": "Zaffari"},
    {"ym": "2026-08", "date": "29/08", "desc": "FEIRA SABADO", "amount": 222.00, "cat": "Feira"},
    {"ym": "2026-08", "date": "31/08", "desc": "ZAFFARI TOTAL", "amount": 269.07, "cat": "Zaffari"},
    # Setembro 2026
    {"ym": "2026-09", "date": "02/09", "desc": "ZAFFARI TOTAL", "amount": 142.33, "cat": "Zaffari"},
    {"ym": "2026-09", "date": "05/09", "desc": "FEIRA SABADO", "amount": 226.70, "cat": "Feira"},
    {"ym": "2026-09", "date": "07/09", "desc": "ZAFFARI TOTAL", "amount": 312.90, "cat": "Zaffari"},
    {"ym": "2026-09", "date": "10/09", "desc": "ZAFFARI TOTAL", "amount": 189.54, "cat": "Zaffari"},
    {"ym": "2026-09", "date": "12/09", "desc": "FEIRA SABADO", "amount": 235.10, "cat": "Feira"},
    {"ym": "2026-09", "date": "14/09", "desc": "ZAFFARI TOTAL", "amount": 218.40, "cat": "Zaffari"},
    {"ym": "2026-09", "date": "17/09", "desc": "ZAFFARI TOTAL", "amount": 172.90, "cat": "Zaffari"},
    {"ym": "2026-09", "date": "19/09", "desc": "FEIRA SABADO", "amount": 218.00, "cat": "Feira"},
    {"ym": "2026-09", "date": "21/09", "desc": "ZAFFARI TOTAL", "amount": 236.45, "cat": "Zaffari"},
    {"ym": "2026-09", "date": "24/09", "desc": "ZAFFARI TOTAL", "amount": 194.20, "cat": "Zaffari"},
    {"ym": "2026-09", "date": "26/09", "desc": "FEIRA SABADO", "amount": 241.00, "cat": "Feira"},
    {"ym": "2026-09", "date": "28/09", "desc": "ZAFFARI TOTAL", "amount": 185.30, "cat": "Zaffari"},
    # Outubro 2026
    {"ym": "2026-10", "date": "03/10", "desc": "FEIRA SABADO", "amount": 230.00, "cat": "Feira"},
    {"ym": "2026-10", "date": "05/10", "desc": "ZAFFARI TOTAL", "amount": 340.50, "cat": "Zaffari"},
    {"ym": "2026-10", "date": "10/10", "desc": "FEIRA SABADO", "amount": 210.00, "cat": "Feira"},
    {"ym": "2026-10", "date": "12/10", "desc": "ZAFFARI TOTAL", "amount": 265.10, "cat": "Zaffari"},
    {"ym": "2026-10", "date": "17/10", "desc": "FEIRA SABADO", "amount": 225.00, "cat": "Feira"},
    {"ym": "2026-10", "date": "19/10", "desc": "ZAFFARI TOTAL", "amount": 290.40, "cat": "Zaffari"},
    {"ym": "2026-10", "date": "24/10", "desc": "FEIRA SABADO", "amount": 195.00, "cat": "Feira"},
    {"ym": "2026-10", "date": "26/10", "desc": "ZAFFARI TOTAL", "amount": 310.20, "cat": "Zaffari"},
    {"ym": "2026-10", "date": "31/10", "desc": "FEIRA SABADO", "amount": 215.00, "cat": "Feira"},
    # Novembro 2026
    {"ym": "2026-11", "date": "03/11", "desc": "ZAFFARI TOTAL", "amount": 280.90, "cat": "Zaffari"},
    {"ym": "2026-11", "date": "07/11", "desc": "FEIRA SABADO", "amount": 220.00, "cat": "Feira"},
    {"ym": "2026-11", "date": "10/11", "desc": "ZAFFARI TOTAL", "amount": 260.40, "cat": "Zaffari"},
    {"ym": "2026-11", "date": "14/11", "desc": "FEIRA SABADO", "amount": 205.00, "cat": "Feira"},
]

# ==============================================================================
# MOVIMENTAÇÕES DOS COFRINHOS MERCADO PAGO
# ==============================================================================
COFRINHOS_MOVIMENTOS = [
    {"ym": "2026-01", "date": "10/01/2026", "tipo": "RESGATE", "pote": "Reserva", "destino": "Nubank", "amount": 1848.46},
    {"ym": "2026-01", "date": "23/01/2026", "tipo": "APORTE", "pote": "Reserva", "origem": "Férias Guto", "amount": 8125.00},
    {"ym": "2026-01", "date": "23/01/2026", "tipo": "APORTE", "pote": "Poupança Clara", "origem": "Férias Guto", "amount": 600.00},
    {"ym": "2026-02", "date": "14/02/2026", "tipo": "RESGATE", "pote": "Reserva", "destino": "Jéssica", "amount": 900.00},
    {"ym": "2026-04", "date": "24/04/2026", "tipo": "RESGATE", "pote": "Reserva", "destino": "Nubank", "amount": 1000.00},
    {"ym": "2026-04", "date": "25/04/2026", "tipo": "RESGATE", "pote": "Reserva", "destino": "Jéssica", "amount": 415.00},
    {"ym": "2026-05", "date": "02/05/2026", "tipo": "RESGATE", "pote": "Reserva", "destino": "Jéssica", "amount": 418.00},
    {"ym": "2026-05", "date": "05/05/2026", "tipo": "RESGATE", "pote": "Reserva", "destino": "Banrisul", "amount": 1150.11},
    {"ym": "2026-05", "date": "11/05/2026", "tipo": "RESGATE", "pote": "Reserva", "destino": "Banrisul", "amount": 1000.00},
    {"ym": "2026-05", "date": "13/05/2026", "tipo": "RESGATE", "pote": "Reserva", "destino": "Nubank", "amount": 824.24},
    {"ym": "2026-05", "date": "25/05/2026", "tipo": "RESGATE", "pote": "Reserva", "destino": "Nubank", "amount": 2701.51},
    {"ym": "2026-06", "date": "08/06/2026", "tipo": "RESGATE", "pote": "Poupança Clara", "destino": "Banrisul", "amount": 1000.00},
    {"ym": "2026-06", "date": "10/06/2026", "tipo": "RESGATE", "pote": "Poupança Clara", "destino": "Banrisul", "amount": 966.78},
    {"ym": "2026-06", "date": "22/06/2026", "tipo": "APORTE", "pote": "Poupança Clara", "origem": "Reposição 99Pay", "amount": 2065.29},
    {"ym": "2026-08", "date": "17/08/2026", "tipo": "RESGATE", "pote": "Poupança Clara", "destino": "99Pay", "amount": 600.00},
    {"ym": "2026-08", "date": "31/08/2026", "tipo": "RESGATE", "pote": "Poupança Clara", "destino": "99Pay", "amount": 1000.00},
    {"ym": "2026-09", "date": "02/09/2026", "tipo": "RESGATE", "pote": "Poupança Clara", "destino": "99Pay", "amount": 513.39},
    {"ym": "2026-09", "date": "26/09/2026", "tipo": "APORTE", "pote": "Poupança Clara", "origem": "PLR Guto", "amount": 2515.00},
]


def executar_extracao():
    """Executa a consolidação de todas as fontes de dados e gera o JSON unificado."""
    print(f"Iniciando extração em: {EXTRATOS_DIR}")
    os.makedirs(DATA_DIR, exist_ok=True)
    
    files = os.listdir(EXTRATOS_DIR) if os.path.exists(EXTRATOS_DIR) else []
    print(f"Total de arquivos brutos encontrados: {len(files)}")
    
    # Dicionários de texto
    pdfs_text = {}
    nubank_csvs = {}

    for fname in sorted(files):
        fpath = os.path.join(EXTRATOS_DIR, fname)
        if fname.endswith(".pdf"):
            pwd = regras.SENHA_PDF_99PAY if "99Pay" in fname else None
            txt = extrair_textos_pdf(fpath, password=pwd)
            if txt:
                pdfs_text[fname] = txt
        elif fname.startswith("Nubank_") and fname.endswith(".csv"):
            try:
                import csv
                with open(fpath, "r", encoding="utf-8") as f:
                    r = csv.DictReader(f)
                    nubank_csvs[fname] = list(r)
            except Exception as e:
                print(f"Erro ao ler CSV {fname}: {e}")

    print(f"PDFs extraídos com sucesso: {len(pdfs_text)}")
    print(f"CSVs Nubank extraídos: {len(nubank_csvs)}")

    # 1. TRANSAÇÕES DE CARTÕES
    all_card_txs = []
    
    # 1.1 Banrisul Cards (4110 e 1112)
    for fname, pages in sorted(pdfs_text.items()):
        if not fname.startswith("Banrisul_Fatura"):
            continue
        full_text = "\n".join(pages)
        m_doc = re.search(r"Data Documento\s*(\d{2}/\d{2}/\d{4})", full_text)
        m_card = re.search(r"crédito final (\d{4})", full_text)
        venc = m_doc.group(1) if m_doc else "?"
        bill_ym = f"{venc[6:10]}-{venc[3:5]}" if len(venc) == 10 else "?"
        card = m_card.group(1) if m_card else "?"

        current_holder = "UNKNOWN"
        current_subcard = "UNKNOWN"
        for page in pages:
            for line in page.splitlines():
                line_s = line.strip()
                m_holder = re.match(r"^(AUGUSTO|JESSICA)\s*-\s*NR\.\s*(\d{4})", line_s)
                if m_holder:
                    current_holder = m_holder.group(1)
                    current_subcard = m_holder.group(2)
                    continue
                m_tx = re.match(r"^(\d{2}/\d{2})\s+(.+?)\s+(-?[\d\.]+,\d{2}-?)$", line_s)
                if m_tx:
                    dt, desc, val_s = m_tx.groups()
                    val = parse_br_num(val_s)
                    desc_clean = re.sub(r"\s+", " ", desc).strip()
                    if "PGTO HOME/OFFICE" in desc_clean or "PGTO DEBITO" in desc_clean:
                        continue
                    m_inst = re.search(r"\b(\d{2})/(\d{2})\b", desc_clean)
                    inst_cur = int(m_inst.group(1)) if m_inst else None
                    inst_tot = int(m_inst.group(2)) if m_inst else None
                    all_card_txs.append({
                        "source": f"Banrisul_{card}",
                        "bill_ym": bill_ym,
                        "date": dt,
                        "holder": current_holder,
                        "subcard": current_subcard,
                        "desc": desc_clean,
                        "amount": val,
                        "inst_cur": inst_cur,
                        "inst_tot": inst_tot
                    })

    # 1.2 Nubank Cards
    for bname, rows in sorted(nubank_csvs.items()):
        bill_ym = bname.replace("Nubank_", "").replace("-27.csv", "")
        for r in rows:
            amt = parse_br_num(r.get("amount", "0"))
            title = r.get("title", "").strip()
            if "Pagamento recebido" in title or "Valor pendente do mês anterior" in title:
                continue
            m_inst = re.search(r"Parcela\s+(\d+)/(\d+)", title, re.IGNORECASE)
            inst_cur = int(m_inst.group(1)) if m_inst else None
            inst_tot = int(m_inst.group(2)) if m_inst else None
            all_card_txs.append({
                "source": "Nubank_Card",
                "bill_ym": bill_ym,
                "date": r.get("date", ""),
                "holder": "AUGUSTO",
                "subcard": "NUBANK",
                "desc": title,
                "amount": amt,
                "inst_cur": inst_cur,
                "inst_tot": inst_tot
            })

    # 2. CONTA CORRENTE BANRISUL
    banrisul_cc = []
    month_map = {
        "JAN": "2026-01", "FEV": "2026-02", "MAR": "2026-03", "ABR": "2026-04",
        "MAI": "2026-05", "JUN": "2026-06", "JUL": "2026-07", "AGO": "2026-08",
        "SET": "2026-09", "OUT": "2026-10", "NOV": "2026-11"
    }
    for k in sorted(pdfs_text.keys()):
        if not k.startswith("extrato20-11"):
            continue
        is_oct_file = "10-2026" in k
        full_text = "\n".join(pdfs_text[k]).replace("\xa0", " ")
        cur_ym = None
        cur_day = None
        lines = [l.strip() for l in full_text.splitlines() if l.strip()]
        i = 0
        while i < len(lines):
            line = lines[i]
            m_hdr = re.search(r"\+\+\s*MOVIMENTOS\s+([A-Z]{3})/(\d{4})", line)
            if m_hdr:
                m_str = m_hdr.group(1)
                cur_ym = month_map.get(m_str, m_str)
                if is_oct_file and cur_ym == "2026-11":
                    break
                i += 1
                continue
            if cur_ym:
                m_tx = re.match(r"^(?:(\d{2})\s+)?(.+?)\s+(\d{6}|[A-Z0-9]{6})\s+([\d\.]+,\d{2}-?)$", line)
                if m_tx:
                    day, desc, doc, val_s = m_tx.groups()
                    if day:
                        cur_day = day
                    val = parse_br_num(val_s)
                    nome = ""
                    if i + 1 < len(lines) and lines[i + 1].startswith("NOME:"):
                        nome = lines[i + 1].replace("NOME:", "").strip()
                        i += 1
                    banrisul_cc.append({
                        "ym": cur_ym,
                        "day": cur_day or "??",
                        "desc": desc.strip(),
                        "doc": doc,
                        "amount": val,
                        "nome": nome
                    })
            i += 1

    # 3. CONSOLIDAÇÃO MÊS A MÊS (JANEIRO A NOVEMBRO 2026)
    meses = [f"2026-{m:02d}" for m in range(1, 12)]
    resumo_mensal = []
    
    # Repasses da Jéssica identificados nas contas
    jessica_in_nubank = {
        "2026-01": 1848.46,
        "2026-03": 960.13,
        "2026-04": 1000.00,
        "2026-05": 824.24 + 2701.51,
    }
    jessica_in_99pay = {
        "2026-07": 2541.55,
        "2026-08": 600.00 + 1000.00,
        "2026-09": 513.39 + 3100.00 + 550.00 + 100.00,
        "2026-10": 2200.00,
        "2026-11": 1500.00,
    }

    for ym in meses:
        # Folha salarial líquida
        sal_liq = sum(t["amount"] for t in banrisul_cc if t["ym"] == ym and "FOLHA PAGAMENTO" in t["desc"])
        ferias_plr = sum(t["amount"] for t in banrisul_cc if t["ym"] == ym and "FOLHA ADT FERIAS" in t["desc"])
        irpf_restituicao = sum(t["amount"] for t in banrisul_cc if t["ym"] == ym and "RECEITA FEDERAL" in t["nome"])
        
        # Repasses Jéssica
        j_in_banrisul = sum(t["amount"] for t in banrisul_cc if t["ym"] == ym and "JESSICA DE MATOS" in t["nome"].upper() and t["amount"] > 0)
        j_in_outras = jessica_in_nubank.get(ym, 0.0) + jessica_in_99pay.get(ym, 0.0)
        j_in_tot = j_in_banrisul + j_in_outras
        
        j_out_banrisul = sum(abs(t["amount"]) for t in banrisul_cc if t["ym"] == ym and "JESSICA DE MATOS" in t["nome"].upper() and t["amount"] < 0)
        j_net = j_in_tot - j_out_banrisul

        # Cartões de Crédito
        cart_augusto = sum(t["amount"] for t in all_card_txs if t["bill_ym"] == ym and t["holder"] == "AUGUSTO")
        cart_jessica = sum(t["amount"] for t in all_card_txs if t["bill_ym"] == ym and t["holder"] == "JESSICA")
        cart_total = cart_augusto + cart_jessica

        # Despesas fixas na conta
        colegio = sum(abs(t["amount"]) for t in banrisul_cc if t["ym"] == ym and ("COL.BOM CONSELHO" in t["desc"] or "BOM CONSELHO" in t["nome"]))
        boletos_casa = sum(abs(t["amount"]) for t in banrisul_cc if t["ym"] == ym and "PAGAMENTO BOLETO" in t["desc"] and int(t["day"] if t["day"].isdigit() else 0) < 20 and not ("BOM CONSELHO" in t["nome"]))
        claro_net = sum(abs(t["amount"]) for t in banrisul_cc if t["ym"] == ym and "PGTO NET" in t["desc"])
        ceee_luz = sum(abs(t["amount"]) for t in banrisul_cc if t["ym"] == ym and "COMPANHIA ESTADUAL" in t["nome"].upper())
        pix_thiago = sum(abs(t["amount"]) for t in banrisul_cc if t["ym"] == ym and "THIAGO DALLO" in t["nome"].upper()) + (640.00 if ym == "2026-02" else 0.0)
        pix_luiz = sum(abs(t["amount"]) for t in banrisul_cc if t["ym"] == ym and "LUIZ ANTONIO" in t["nome"].upper()) + (250.00 if ym == "2026-02" else 0.0)

        # Vale-Alimentação do mês
        va_in = sum(c["amount"] for c in VA_HISTORICO_CREDITOS if c["ym"] == ym)
        va_out_zaffari = sum(d["amount"] for d in VA_HISTORICO_DEBITOS if d["ym"] == ym and d["cat"] == "Zaffari")
        va_out_feira = sum(d["amount"] for d in VA_HISTORICO_DEBITOS if d["ym"] == ym and d["cat"] == "Feira")
        va_out_outros = sum(d["amount"] for d in VA_HISTORICO_DEBITOS if d["ym"] == ym and d["cat"] in ("Farmacia", "Restaurante"))
        va_out_tot = va_out_zaffari + va_out_feira + va_out_outros

        resumo_mensal.append({
            "mes": ym,
            "salario_liquido": sal_liq,
            "ferias_plr_irpf": ferias_plr + irpf_restituicao,
            "jessica_repasses_total": j_in_tot,
            "jessica_repasses_liquido": j_net,
            "cartao_augusto": cart_augusto,
            "cartao_jessica": cart_jessica,
            "cartao_total": cart_total,
            "saldo_jessica_final": j_net - cart_jessica, # Repasse Líquido - Fatura Cartões Jé
            "colegio_clara": colegio,
            "boletos_casa": boletos_casa,
            "claro_net": claro_net,
            "ceee_luz": ceee_luz,
            "pix_thiago": pix_thiago,
            "pix_luiz": pix_luiz,
            "va_credito": va_in,
            "va_gasto_zaffari": va_out_zaffari,
            "va_gasto_feira": va_out_feira,
            "va_gasto_outros": va_out_outros,
            "va_gasto_total": va_out_tot
        })

    # 4. PROJEÇÃO DE PARCELAS FUTURAS (DEZ/2026 A OUT/2027)
    future_months = ["2026-12", "2027-01", "2027-02", "2027-03", "2027-04", "2027-05", "2027-06", "2027-07", "2027-08", "2027-09", "2027-10"]
    active_insts = [t for t in all_card_txs if t["bill_ym"] == "2026-11" and t["inst_cur"] is not None and t["inst_cur"] < t["inst_tot"]]
    
    parcelas_futuras = []
    for idx, fm in enumerate(future_months, 1):
        itens_mes = []
        tot_mes = 0.0
        for t in active_insts:
            rem = t["inst_tot"] - t["inst_cur"]
            if idx <= rem:
                parcela_n = t["inst_cur"] + idx
                itens_mes.append({
                    "descricao": t["desc"],
                    "titular": t["holder"],
                    "cartao": t["source"],
                    "parcela": f"{parcela_n}/{t['inst_tot']}",
                    "valor": t["amount"]
                })
                tot_mes += t["amount"]
        parcelas_futuras.append({
            "mes": fm,
            "total_parcelas": tot_mes,
            "quantidade_itens": len(itens_mes),
            "itens": itens_mes
        })

    # 5. AUDITORIA DE ASSINATURAS
    assinaturas_resultado = []
    for sub in regras.ASSINATURAS_CONHECIDAS:
        matches = []
        for t in all_card_txs:
            d = t["desc"].upper()
            if sub["nome"] == "iFood Club (Jéssica)" and t["source"] == "Nubank_Card":
                continue
            if sub["nome"] == "iFood Club (Augusto)" and t["source"] != "Nubank_Card":
                continue
            if any(k in d for k in sub["kws"]):
                matches.append(t)
        tot_pago = sum(m["amount"] for m in matches)
        meses_ativos = sorted(set(m["bill_ym"] for m in matches))
        last_tx = matches[-1] if matches else None
        assinaturas_resultado.append({
            "nome": sub["nome"],
            "status_recomendacao": sub["status"],
            "total_2026": tot_pago,
            "meses_ativos_count": len(meses_ativos),
            "ultimo_valor": last_tx["amount"] if last_tx else 0.0,
            "ultimo_mes": last_tx["bill_ym"] if last_tx else None,
            "cartao": last_tx["source"] if last_tx else None
        })

    # 6. STATUS DOS COFRINHOS E RESERVAS
    cofrinhos_status = {
        "poupanca_clara": {
            "saldo_atual": 2515.00,
            "historico": [c for c in COFRINHOS_MOVIMENTOS if c["pote"] == "Poupança Clara"],
            "meta": "Intocável para o futuro da Clara"
        },
        "cofrinho_reserva": {
            "saldo_atual": 0.00,
            "historico": [c for c in COFRINHOS_MOVIMENTOS if c["pote"] == "Reserva"],
            "meta": "Reconstruir a partir de Dez/2026 com o alívio das parcelas (R$ 1.740/mês)"
        },
        "rdb_nubank": {
            "saldo_atual": 240.00,
            "meta": "Reserva de emergência imediata"
        },
        "equalizador_sobreaviso_2x1": {
            "inicio": "Junho/2027",
            "regra": "Guardar R$ 1.050/mês nos 2 meses com sobreaviso para liberar R$ 2.100 no 3º mês sem sobreaviso",
            "renda_estabilizada_guto": regras.RENDA_MENSAL_ESTABILIZADA_GUTO
        }
    }

    # 7. CONSOLIDAÇÃO FINAL
    consolidado = {
        "metadata": {
            "gerado_em": datetime.now().isoformat(),
            "versao": "1.0",
            "total_arquivos_processados": len(files),
            "meses_analisados": "2026-01 a 2026-11",
            "total_transacoes_cartao": len(all_card_txs),
            "total_transacoes_conta_banrisul": len(banrisul_cc)
        },
        "regras_e_tetos": {
            "teto_va_mensal": regras.TETO_VA_MENSAL,
            "teto_va_semanal": regras.TETO_VA_SEMANAL,
            "teto_cartao_guto": regras.TETO_CARTAO_GUTO_MENSAL,
            "teto_cartao_je": regras.TETO_CARTAO_JE_MENSAL,
            "teto_uber_guto_semanal": regras.TETO_UBER_99_GUTO_SEMANAL,
            "teto_uber_je_semanal": regras.TETO_UBER_99_JE_SEMANAL,
            "teto_comer_fora_semanal": regras.TETO_COMER_FORA_SEMANAL,
            "teto_compras_online_mensal": regras.TETO_COMPRAS_ONLINE_MENSAL,
            "percentual_caixinha_je": regras.PERCENTUAL_CAIXINHA_PACIENTE_JE
        },
        "resumo_mensal": resumo_mensal,
        "parcelas_futuras": parcelas_futuras,
        "assinaturas": assinaturas_resultado,
        "cofrinhos": cofrinhos_status,
        "transacoes_recentes_novembro": [t for t in all_card_txs if t["bill_ym"] == "2026-11"]
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(consolidado, f, ensure_ascii=False, indent=2)

    print(f"Consolidação concluída com sucesso!")
    print(f"Salvo em: {OUTPUT_JSON} ({os.path.getsize(OUTPUT_JSON)} bytes)")
    return consolidado


if __name__ == "__main__":
    executar_extracao()
