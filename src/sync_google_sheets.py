"""
Sincronizador Automático da Planilha Google Sheets e Gerador XLSX (Versão 3.0 - Formato Original)
Gera:
- Aba 1: Total Anual (8 Seções Canônicas, Categorias em Ordem Alfabética, 12 Meses + Total + Média)
- Abas 2 a 13: Janeiro a Dezembro no formato clássico original (Dias 1 a 31, =SUM(D:AH), Subtotais, Rendas, Balanço + Auditoria no rodapé)
- Aba 14: Resumo & Metas 2026-2027 (Balanço Simétrico do Casal, Parcelas Futuras e Assinaturas)
- Abas 15 a 18: Histórico Original Preservado (Orig - Total Anual, Abril, Maio, Julho)
E atualiza diretamente a planilha na nuvem via Google Drive API v3.
"""

import os
import sys
import json
import requests
import openpyxl
from collections import defaultdict
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config_regras as regras

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONSOLIDADO_PATH = os.path.join(BASE_DIR, "data", "consolidado_2026_2027.json")
OUTPUT_XLSX = os.path.join(os.path.dirname(BASE_DIR), "Planilha_Controle_Financeiro_2026_2027.xlsx")
ORIGINAL_XLSX = os.path.join(os.path.dirname(BASE_DIR), "Planilha_Controle_Financeiro_Original.xlsx")
GCP_CREDS_PATH = r"C:\Dropbox\Análise\caderno_analise_scripts\projeto_caderno_automatizado\gcp_credentials.json"

FONT_TITLE = Font(name="Calibri", size=14, bold=True, color="1F4E79")
FONT_SECTION = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
FONT_HEADER = Font(name="Calibri", size=10, bold=True, color="1F4E79")
FONT_BOLD = Font(name="Calibri", size=10, bold=True)
FONT_NORMAL = Font(name="Calibri", size=10)
FONT_MUTED = Font(name="Calibri", size=9, italic=True, color="595959")

FILL_HEADER = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
FILL_SECTION = PatternFill(start_color="2F5597", end_color="2F5597", fill_type="solid")
FILL_SUBTOTAL = PatternFill(start_color="EDF2F8", end_color="EDF2F8", fill_type="solid")
FILL_ZEBRA = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
FILL_ALERT = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")
FILL_SUCCESS = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")

ALIGN_CENTER = Alignment(horizontal="center", vertical="center")
ALIGN_RIGHT = Alignment(horizontal="right", vertical="center")
ALIGN_LEFT = Alignment(horizontal="left", vertical="center")

THIN_SIDE = Side(style="thin", color="D9D9D9")
BORDER_CELL = Border(left=THIN_SIDE, right=THIN_SIDE, top=THIN_SIDE, bottom=THIN_SIDE)

MESES_NOMES = [
    ("2026-01", "Janeiro"),
    ("2026-02", "Fevereiro"),
    ("2026-03", "Março"),
    ("2026-04", "Abril"),
    ("2026-05", "Maio"),
    ("2026-06", "Junho"),
    ("2026-07", "Julho"),
    ("2026-08", "Agosto"),
    ("2026-09", "Setembro"),
    ("2026-10", "Outubro"),
    ("2026-11", "Novembro"),
    ("2026-12", "Dezembro"),
]


def formatar_moeda(cell):
    cell.number_format = '"R$" #,##0.00;[Red]-"R$" #,##0.00;"R$" 0.00'


def auto_fit_columns(ws, max_width=45, min_width=10):
    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = 0
        for cell in col:
            v = str(cell.value or "")
            if v.startswith("="):
                v = "R$ 99.999,99"
            if len(v) > max_len:
                max_len = len(v)
        ws.column_dimensions[col_letter].width = min(max(max_len + 3, min_width), max_width)


def _extract_day(tx):
    """Extrai o dia (1 a 31) de uma transação."""
    d = str(tx.get("date", ""))
    if re_match_iso := (len(d) == 10 and d[4] == "-"):
        try:
            return max(1, min(31, int(d[8:10])))
        except ValueError:
            return 1
    if "/" in d:
        try:
            return max(1, min(31, int(d.split("/")[0])))
        except ValueError:
            return 1
    return 1


def criar_aba_total_anual(wb, data):
    """Aba 1: Total Anual no formato das 8 Seções em Ordem Alfabética x 12 Meses."""
    ws = wb.active
    ws.title = "Total Anual"
    ws.views.sheetView[0].showGridLines = True

    ws["A1"] = "CONTROLE FINANCEIRO ANUAL 2026 — 8 SEÇÕES EM ORDEM ALFABÉTICA"
    ws["A1"].font = FONT_TITLE
    ws["A2"] = f"Consolidado de extratos reais e contracheques (Atualizado em {data['metadata']['gerado_em'][:10]})"
    ws["A2"].font = FONT_MUTED

    headers = ["Seção / Categoria"] + [nome for _, nome in MESES_NOMES] + ["Total 2026", "Média/Mês"]
    for col_idx, h in enumerate(headers, 1):
        c = ws.cell(row=4, column=col_idx, value=h)
        c.font = FONT_HEADER
        c.fill = FILL_HEADER
        c.border = BORDER_CELL
        c.alignment = ALIGN_CENTER if col_idx > 1 else ALIGN_LEFT

    secoes = data.get("secoes_resumo", [])
    cur_row = 5
    subtotal_rows = []

    for sec_idx, sec in enumerate(secoes, 1):
        # Cabeçalho da Seção
        ws.merge_cells(start_row=cur_row, start_column=1, end_row=cur_row, end_column=len(headers))
        c_sec = ws.cell(row=cur_row, column=1, value=sec["secao"])
        c_sec.font = FONT_SECTION
        c_sec.fill = FILL_SECTION
        c_sec.alignment = ALIGN_LEFT
        cur_row += 1

        sec_start = cur_row
        cats = sorted(sec.get("categorias", []), key=lambda x: x["categoria"].lower())
        for cat in cats:
            c_cat = ws.cell(row=cur_row, column=1, value=cat["categoria"])
            c_cat.font = FONT_NORMAL
            c_cat.border = BORDER_CELL

            for m_idx, (ym, _) in enumerate(MESES_NOMES, 2):
                val = cat.get("por_mes", {}).get(ym, 0.0)
                c_m = ws.cell(row=cur_row, column=m_idx, value=val)
                c_m.font = FONT_NORMAL
                c_m.border = BORDER_CELL
                c_m.alignment = ALIGN_RIGHT
                formatar_moeda(c_m)

            # Total e Média (considerando os 11 meses com dados Jan-Nov = cols B..L)
            c_tot = ws.cell(row=cur_row, column=14, value=f"=SUM(B{cur_row}:M{cur_row})")
            c_med = ws.cell(row=cur_row, column=15, value=f"=AVERAGE(B{cur_row}:L{cur_row})")
            for c in [c_tot, c_med]:
                c.font = FONT_BOLD
                c.border = BORDER_CELL
                c.alignment = ALIGN_RIGHT
                formatar_moeda(c)
            cur_row += 1

        sec_end = cur_row - 1
        # Linha Subtotal da Seção
        c_sub = ws.cell(row=cur_row, column=1, value=f"Subtotal {sec_idx} ({sec['secao']})")
        c_sub.font = FONT_BOLD
        c_sub.fill = FILL_SUBTOTAL
        c_sub.border = BORDER_CELL
        for col_i in range(2, len(headers) + 1):
            col_let = get_column_letter(col_i)
            if col_i == 15:
                formula = f"=AVERAGE(B{cur_row}:L{cur_row})"
            else:
                formula = f"=SUM({col_let}{sec_start}:{col_let}{sec_end})"
            c_sv = ws.cell(row=cur_row, column=col_i, value=formula)
            c_sv.font = FONT_BOLD
            c_sv.fill = FILL_SUBTOTAL
            c_sv.border = BORDER_CELL
            c_sv.alignment = ALIGN_RIGHT
            formatar_moeda(c_sv)

        subtotal_rows.append(cur_row)
        cur_row += 1

    # TOTAL GERAL DESPESAS
    cur_row += 1
    total_desp_row = cur_row
    ws.cell(row=total_desp_row, column=1, value="TOTAL DESPESAS").font = FONT_SECTION
    ws.cell(row=total_desp_row, column=1).fill = FILL_SECTION
    for col_i in range(2, len(headers) + 1):
        col_let = get_column_letter(col_i)
        refs = "+".join(f"{col_let}{sr}" for sr in subtotal_rows)
        c_td = ws.cell(row=total_desp_row, column=col_i, value=f"={refs}")
        c_td.font = FONT_BOLD
        c_td.fill = FILL_HEADER
        c_td.border = BORDER_CELL
        c_td.alignment = ALIGN_RIGHT
        formatar_moeda(c_td)

    # BLOCO DE RENDAS & BALANÇO NO RODAPÉ
    cur_row += 2
    rendas_start = cur_row
    rm_map = {rm["mes"]: rm for rm in data.get("resumo_mensal", [])}
    rendas_itens = [
        ("Salário Líquido Guto", "salario_liquido"),
        ("13º, Férias, PLR e Extras Guto", "ferias_plr_irpf"),
        ("Banricard (Vale-Alimentação)", "va_credito"),
        ("Repasses Jéssica (Clínica)", "jessica_repasses_clinica"),
        ("Resgates Cofrinhos MP", "cofrinhos_resgates"),
        ("Descontos Retidos em Folha (Contracheques)", "descontos_folha"),
    ]
    for label, key in rendas_itens:
        ws.cell(row=cur_row, column=1, value=label).font = FONT_NORMAL
        ws.cell(row=cur_row, column=1).border = BORDER_CELL
        for m_idx, (ym, _) in enumerate(MESES_NOMES, 2):
            val = rm_map.get(ym, {}).get(key, 0.0)
            c_r = ws.cell(row=cur_row, column=m_idx, value=val)
            c_r.font = FONT_NORMAL
            c_r.border = BORDER_CELL
            c_r.alignment = ALIGN_RIGHT
            formatar_moeda(c_r)
        c_rtot = ws.cell(row=cur_row, column=14, value=f"=SUM(B{cur_row}:M{cur_row})")
        c_rmed = ws.cell(row=cur_row, column=15, value=f"=AVERAGE(B{cur_row}:L{cur_row})")
        for c in [c_rtot, c_rmed]:
            c.font = FONT_BOLD
            c.border = BORDER_CELL
            c.alignment = ALIGN_RIGHT
            formatar_moeda(c)
        cur_row += 1

    rendas_end = cur_row - 1
    rendas_tot_row = cur_row
    ws.cell(row=rendas_tot_row, column=1, value="RENDAS TOTAIS").font = FONT_BOLD
    ws.cell(row=rendas_tot_row, column=1).fill = FILL_SUBTOTAL
    ws.cell(row=rendas_tot_row, column=1).border = BORDER_CELL
    for col_i in range(2, len(headers) + 1):
        col_let = get_column_letter(col_i)
        c_rt = ws.cell(row=rendas_tot_row, column=col_i, value=f"=SUM({col_let}{rendas_start}:{col_let}{rendas_end})")
        c_rt.font = FONT_BOLD
        c_rt.fill = FILL_SUBTOTAL
        c_rt.border = BORDER_CELL
        c_rt.alignment = ALIGN_RIGHT
        formatar_moeda(c_rt)

    cur_row += 1
    balanco_row = cur_row
    ws.cell(row=balanco_row, column=1, value="BALANÇO (RENDAS - DESPESAS)").font = FONT_SECTION
    ws.cell(row=balanco_row, column=1).fill = FILL_SECTION
    for col_i in range(2, len(headers) + 1):
        col_let = get_column_letter(col_i)
        c_b = ws.cell(row=balanco_row, column=col_i, value=f"={col_let}{rendas_tot_row}-{col_let}{total_desp_row}")
        c_b.font = FONT_BOLD
        c_b.fill = FILL_SUCCESS
        c_b.border = BORDER_CELL
        c_b.alignment = ALIGN_RIGHT
        formatar_moeda(c_b)

    ws.freeze_panes = "B5"
    auto_fit_columns(ws, max_width=42, min_width=13)


def criar_aba_mensal_original(wb, ym, mes_nome, data):
    """Cria uma aba mensal (Janeiro a Dezembro) no formato original: Dias 1 a 31 (Cols D..AH), Mensal =SUM(D:AH)."""
    ws = wb.create_sheet(title=mes_nome)
    ws.views.sheetView[0].showGridLines = True

    # Linha 1: Cabeçalho clássico
    ws.cell(row=1, column=1, value=f"{mes_nome.upper()} / 2026").font = FONT_TITLE
    ws.cell(row=1, column=2, value="Mensal").font = FONT_HEADER
    ws.cell(row=1, column=3, value="Estimativa").font = FONT_HEADER
    ws.cell(row=1, column=2).fill = FILL_HEADER
    ws.cell(row=1, column=3).fill = FILL_HEADER
    ws.cell(row=1, column=2).alignment = ALIGN_CENTER
    ws.cell(row=1, column=3).alignment = ALIGN_CENTER

    for day in range(1, 32):
        c_d = ws.cell(row=1, column=3 + day, value=day)
        c_d.font = FONT_HEADER
        c_d.fill = FILL_HEADER
        c_d.alignment = ALIGN_CENTER
        c_d.border = BORDER_CELL

    # Filtra transações do mês
    all_txs = data.get("todas_transacoes", [])
    if ym == "2026-12":
        # Para Dezembro/26, projeta as parcelas futuras conhecidas no dia 25
        mes_txs = []
        p_dez = next((p for p in data.get("parcelas_futuras", []) if p["mes"] == "2026-12"), None)
        if p_dez:
            for item in p_dez.get("itens", []):
                mes_txs.append({
                    "ym": "2026-12",
                    "date": "25/12",
                    "source": item["cartao"],
                    "holder": item["titular"],
                    "section": "PARCELAMENTO CARTÃO & ASSINATURAS",
                    "category": f"{item['descricao']} ({item['parcela']})",
                    "desc": f"{item['descricao']} ({item['parcela']})",
                    "amount": item["valor"],
                    "inst_cur": 1,
                    "inst_tot": 2,
                    "tipo": "CARTAO"
                })
    else:
        mes_txs = [t for t in all_txs if t["ym"] == ym]

    # Separa parcelamentos (inst_tot > 1) para listar individualmente na Seção 7 (evitando dupla contagem)
    parcelamentos_mes = [t for t in mes_txs if t.get("inst_tot") and t.get("inst_tot") > 1]
    txs_normais = [t for t in mes_txs if not (t.get("inst_tot") and t.get("inst_tot") > 1)]

    # Mapeia (secao, categoria, dia) -> lista de valores
    grid_vals = defaultdict(lambda: defaultdict(list))
    for t in txs_normais:
        sec = t.get("section", "FAMÍLIA")
        cat = t.get("category", "Outros")
        day = _extract_day(t)
        grid_vals[(sec, cat)][day].append(t["amount"])

    # Garante que todas as categorias canônicas de cada seção apareçam ordenadas (A-Z)
    cats_by_sec = {}
    for sec_obj in data.get("secoes_resumo", []):
        cats_by_sec[sec_obj["secao"]] = sorted([c["categoria"] for c in sec_obj.get("categorias", [])], key=lambda s: s.lower())

    cur_row = 2
    subtotal_rows = []
    secoes_ordem = data["metadata"].get("secoes_canonicas", [])

    for sec_idx, sec_name in enumerate(secoes_ordem, 1):
        # Cabeçalho da Seção
        c_sec = ws.cell(row=cur_row, column=1, value=sec_name)
        c_sec.font = FONT_SECTION
        c_sec.fill = FILL_SECTION
        for col_i in range(2, 35):
            ws.cell(row=cur_row, column=col_i).fill = FILL_SECTION
        cur_row += 1

        sec_start = cur_row
        cat_list = list(cats_by_sec.get(sec_name, []))
        # Se for Seção 7, remove 'Grandes Parcelamentos' genérico e adiciona cada parcelamento individual do mês em ordem alfabética
        if sec_name == "PARCELAMENTO CARTÃO & ASSINATURAS":
            cat_list = [c for c in cat_list if c != "Grandes Parcelamentos"]
            parc_grupos = defaultdict(lambda: defaultdict(list))
            for pt in parcelamentos_mes:
                label_p = pt["desc"]
                day_p = _extract_day(pt)
                parc_grupos[label_p][day_p].append(pt["amount"])
            for label_p in sorted(parc_grupos.keys(), key=lambda s: s.lower()):
                grid_vals[(sec_name, label_p)] = parc_grupos[label_p]
            all_sec_cats = sorted(list(set(cat_list) | set(parc_grupos.keys())), key=lambda s: s.lower())
        else:
            all_sec_cats = sorted(cat_list, key=lambda s: s.lower())

        for cat_name in all_sec_cats:
            c_name = ws.cell(row=cur_row, column=1, value=cat_name)
            c_name.font = FONT_NORMAL
            c_name.border = BORDER_CELL

            # Mensal =SUM(D{row}:AH{row})
            c_mensal = ws.cell(row=cur_row, column=2, value=f"=SUM(D{cur_row}:AH{cur_row})")
            c_mensal.font = FONT_BOLD
            c_mensal.border = BORDER_CELL
            c_mensal.alignment = ALIGN_RIGHT
            formatar_moeda(c_mensal)

            # Estimativa (em branco para preenchimento ou meta)
            c_est = ws.cell(row=cur_row, column=3, value=None)
            c_est.border = BORDER_CELL

            # Dias 1 a 31
            day_map = grid_vals.get((sec_name, cat_name), {})
            for day in range(1, 32):
                vals = day_map.get(day, [])
                if vals:
                    if len(vals) == 1:
                        cell_val = round(vals[0], 2)
                    else:
                        cell_val = "=" + "+".join(f"{round(v, 2)}" for v in vals)
                    c_day = ws.cell(row=cur_row, column=3 + day, value=cell_val)
                    c_day.font = FONT_NORMAL
                    c_day.alignment = ALIGN_RIGHT
                    formatar_moeda(c_day)
                else:
                    c_day = ws.cell(row=cur_row, column=3 + day, value=None)
                c_day.border = BORDER_CELL
            cur_row += 1

        sec_end = cur_row - 1
        if sec_end < sec_start:
            # Caso seção vazia (ex: Dezembro)
            ws.cell(row=cur_row, column=1, value="-").border = BORDER_CELL
            sec_end = cur_row
            cur_row += 1

        # Subtotal da Seção
        c_sub = ws.cell(row=cur_row, column=1, value=f"Subtotal {sec_idx}")
        c_sub.font = FONT_BOLD
        c_sub.fill = FILL_SUBTOTAL
        c_sub.border = BORDER_CELL

        c_sub_val = ws.cell(row=cur_row, column=2, value=f"=SUM(B{sec_start}:B{sec_end})")
        c_sub_val.font = FONT_BOLD
        c_sub_val.fill = FILL_SUBTOTAL
        c_sub_val.border = BORDER_CELL
        c_sub_val.alignment = ALIGN_RIGHT
        formatar_moeda(c_sub_val)

        subtotal_rows.append(cur_row)
        cur_row += 1

    # TOTAL DESPESAS
    total_row = cur_row
    ws.cell(row=total_row, column=1, value="TOTAL").font = FONT_SECTION
    ws.cell(row=total_row, column=1).fill = FILL_SECTION
    refs = "+".join(f"B{sr}" for sr in subtotal_rows)
    c_tot = ws.cell(row=total_row, column=2, value=f"={refs}")
    c_tot.font = FONT_BOLD
    c_tot.fill = FILL_HEADER
    c_tot.border = BORDER_CELL
    c_tot.alignment = ALIGN_RIGHT
    formatar_moeda(c_tot)

    # RENDAS & BALANÇO
    cur_row += 1
    rendas_start = cur_row
    rm = next((r for r in data.get("resumo_mensal", []) if r["mes"] == ym), {})
    rendas_rows = [
        ("Salário Líquido Guto", rm.get("salario_liquido", 0.0)),
        ("13º, Férias, PLR e Extras Guto", rm.get("ferias_plr_irpf", 0.0)),
        ("Banricard (Vale-Alimentação)", rm.get("va_credito", 0.0)),
        ("Repasses Jéssica (Clínica)", rm.get("jessica_repasses_clinica", 0.0)),
        ("Resgates Cofrinhos MP", rm.get("cofrinhos_resgates", 0.0)),
        ("Descontos Retidos em Folha (Contracheques)", rm.get("descontos_folha", 0.0)),
    ]
    for label, val in rendas_rows:
        ws.cell(row=cur_row, column=1, value=label).font = FONT_NORMAL
        ws.cell(row=cur_row, column=1).border = BORDER_CELL
        c_rv = ws.cell(row=cur_row, column=2, value=val)
        c_rv.font = FONT_NORMAL
        c_rv.border = BORDER_CELL
        c_rv.alignment = ALIGN_RIGHT
        formatar_moeda(c_rv)
        cur_row += 1

    rendas_end = cur_row - 1
    rendas_tot_row = cur_row
    ws.cell(row=rendas_tot_row, column=1, value="RENDAS").font = FONT_BOLD
    ws.cell(row=rendas_tot_row, column=1).fill = FILL_SUBTOTAL
    ws.cell(row=rendas_tot_row, column=1).border = BORDER_CELL
    c_rt = ws.cell(row=rendas_tot_row, column=2, value=f"=SUM(B{rendas_start}:B{rendas_end})")
    c_rt.font = FONT_BOLD
    c_rt.fill = FILL_SUBTOTAL
    c_rt.border = BORDER_CELL
    c_rt.alignment = ALIGN_RIGHT
    formatar_moeda(c_rt)

    cur_row += 1
    bal_row = cur_row
    ws.cell(row=bal_row, column=1, value="BALANÇO").font = FONT_SECTION
    ws.cell(row=bal_row, column=1).fill = FILL_SECTION
    c_bal = ws.cell(row=bal_row, column=2, value=f"=B{rendas_tot_row}-B{total_row}")
    c_bal.font = FONT_BOLD
    c_bal.fill = FILL_SUCCESS
    c_bal.border = BORDER_CELL
    c_bal.alignment = ALIGN_RIGHT
    formatar_moeda(c_bal)

    # TABELA DE AUDITORIA DETALHADA NO RODAPÉ (PARA VER O NOME DE CADA LOJA NO MÊS)
    cur_row += 3
    ws.cell(row=cur_row, column=1, value=f"AUDITORIA DETALHADA DAS COMPRAS DE {mes_nome.upper()}/2026").font = FONT_TITLE
    cur_row += 1
    h_aud = ["Dia", "Seção", "Categoria", "Estabelecimento / Descrição", "Cartão / Meio", "Titular", "Parcela", "Valor (R$)"]
    for col_idx, h in enumerate(h_aud, 1):
        c_h = ws.cell(row=cur_row, column=col_idx, value=h)
        c_h.font = FONT_HEADER
        c_h.fill = FILL_HEADER
        c_h.border = BORDER_CELL
        c_h.alignment = ALIGN_CENTER
    cur_row += 1

    txs_sorted = sorted(mes_txs, key=lambda x: (
        secoes_ordem.index(x.get("section", "FAMÍLIA")) if x.get("section", "FAMÍLIA") in secoes_ordem else 99,
        x.get("category", "").lower(),
        _extract_day(x)
    ))
    for t in txs_sorted:
        ws.cell(row=cur_row, column=1, value=_extract_day(t)).alignment = ALIGN_CENTER
        ws.cell(row=cur_row, column=2, value=t.get("section", ""))
        ws.cell(row=cur_row, column=3, value=t.get("category", ""))
        ws.cell(row=cur_row, column=4, value=t.get("desc", ""))
        ws.cell(row=cur_row, column=5, value=t.get("source", "")).alignment = ALIGN_CENTER
        ws.cell(row=cur_row, column=6, value=t.get("holder", "")).alignment = ALIGN_CENTER
        parc_s = f"{t.get('inst_cur')}/{t.get('inst_tot')}" if t.get("inst_cur") else "-"
        ws.cell(row=cur_row, column=7, value=parc_s).alignment = ALIGN_CENTER
        c_v = ws.cell(row=cur_row, column=8, value=t.get("amount", 0.0))
        c_v.alignment = ALIGN_RIGHT
        formatar_moeda(c_v)
        for col_i in range(1, 9):
            c_cell = ws.cell(row=cur_row, column=col_i)
            c_cell.font = FONT_NORMAL
            c_cell.border = BORDER_CELL
        cur_row += 1

    ws.freeze_panes = "D2"
    ws.column_dimensions["A"].width = 36
    ws.column_dimensions["B"].width = 14
    ws.column_dimensions["C"].width = 13
    for d_col in range(4, 35):
        ws.column_dimensions[get_column_letter(d_col)].width = 11


def criar_aba_resumo_metas(wb, data):
    """Aba 14: Resumo & Metas 2026-2027 (Com Balanço Simétrico do Casal, Parcelas e Assinaturas)."""
    ws = wb.create_sheet(title="Resumo & Metas 2026-2027")
    ws.views.sheetView[0].showGridLines = True

    ws["A1"] = "CONTROLE FINANCEIRO DOMÉSTICO — GUTO & JÉ (BALANÇO SIMÉTRICO)"
    ws["A1"].font = FONT_TITLE
    ws["A2"] = f"Metas, Balanço Conjunto da Família, Parcelas Futuras e Assinaturas (Atualizado em {data['metadata']['gerado_em'][:10]})"
    ws["A2"].font = FONT_MUTED

    # 1. BALANÇO SIMÉTRICO DO CASAL E DA CASA
    ws.merge_cells("A4:H4")
    ws["A4"] = "1. BALANÇO SIMÉTRICO DA FAMÍLIA (ENTRADAS VS. CARTÕES DE AMBOS VS. FIXOS CASA)"
    ws["A4"].font = FONT_SECTION
    ws["A4"].fill = FILL_SECTION

    h1 = [
        "Mês",
        "Entradas Guto (Salário+Extras+VA)",
        "Entradas Jéssica (Clínica)",
        "Resgates Cofrinhos MP",
        "Faturas Cartões Guto",
        "Faturas Cartões Jéssica",
        "Total Cartões Casal",
        "Fixos Casa & Clara (Boletos/Pix)"
    ]
    for col_idx, h in enumerate(h1, 1):
        c = ws.cell(row=5, column=col_idx, value=h)
        c.font = FONT_HEADER
        c.fill = FILL_HEADER
        c.border = BORDER_CELL
        c.alignment = ALIGN_CENTER

    for idx, rm in enumerate(data["resumo_mensal"], 6):
        ent_guto = rm["salario_liquido"] + rm["ferias_plr_irpf"] + rm["va_credito"]
        fixos_casa = rm["colegio_clara"] + rm["boletos_casa"] + rm["claro_net"] + rm["ceee_luz"] + rm["pix_thiago"] + rm["pix_luiz"]

        vals = [
            rm["mes"],
            ent_guto,
            rm["jessica_repasses_clinica"],
            rm["cofrinhos_resgates"],
            rm["cartao_augusto"],
            rm["cartao_jessica"],
            f"=E{idx}+F{idx}",
            fixos_casa,
        ]
        for col_i, val in enumerate(vals, 1):
            c = ws.cell(row=idx, column=col_i, value=val)
            c.font = FONT_NORMAL
            c.border = BORDER_CELL
            if col_i == 1:
                c.alignment = ALIGN_CENTER
            else:
                c.alignment = ALIGN_RIGHT
                formatar_moeda(c)

    # 2. CRONOGRAMA DE QUEDA DAS PARCELAS
    start_p = 19
    ws.merge_cells(f"A{start_p}:E{start_p}")
    ws[f"A{start_p}"] = "2. CRONOGRAMA DE QUEDA DAS PARCELAS FUTURAS (DEZ/2026 A OUT/2027)"
    ws[f"A{start_p}"].font = FONT_SECTION
    ws[f"A{start_p}"].fill = FILL_SECTION

    h2 = ["Mês de Vencimento", "Total em Parcelas", "Qtd Compras", "Alívio vs. Dez/26", "Status Orçamentário"]
    for col_idx, h in enumerate(h2, 1):
        c = ws.cell(row=start_p + 1, column=col_idx, value=h)
        c.font = FONT_HEADER
        c.fill = FILL_HEADER
        c.border = BORDER_CELL
        c.alignment = ALIGN_CENTER

    base_dez = data["parcelas_futuras"][0]["total_parcelas"] if data["parcelas_futuras"] else 1764.16
    for idx, pf in enumerate(data["parcelas_futuras"], start_p + 2):
        alivio = base_dez - pf["total_parcelas"]
        status = "Parcelas altas" if pf["total_parcelas"] > 1000 else ("Alívio expressivo" if pf["total_parcelas"] < 500 else "Transição")
        row_v = [pf["mes"], pf["total_parcelas"], pf["quantidade_itens"], alivio, status]
        for col_i, val in enumerate(row_v, 1):
            c = ws.cell(row=idx, column=col_i, value=val)
            c.font = FONT_NORMAL
            c.border = BORDER_CELL
            if col_i in (1, 3):
                c.alignment = ALIGN_CENTER
            elif col_i in (2, 4):
                c.alignment = ALIGN_RIGHT
                formatar_moeda(c)

    # 3. ASSINATURAS ATIVAS (SEM ALERTAS DE AQUARIUS/IFOOD E KOTAS R$ 8,70)
    start_a = start_p + 15
    ws.merge_cells(f"A{start_a}:E{start_a}")
    ws[f"A{start_a}"] = "3. ASSINATURAS E RECORRÊNCIAS ATIVAS (ORDEM ALFABÉTICA)"
    ws[f"A{start_a}"].font = FONT_SECTION
    ws[f"A{start_a}"].fill = FILL_SECTION

    h3 = ["Assinatura / Serviço", "Valor Mensal Atual", "Total Pago em 2026", "Meses Ativos", "Situação"]
    for col_idx, h in enumerate(h3, 1):
        c = ws.cell(row=start_a + 1, column=col_idx, value=h)
        c.font = FONT_HEADER
        c.fill = FILL_HEADER
        c.border = BORDER_CELL
        c.alignment = ALIGN_CENTER

    for idx, sub in enumerate(data["assinaturas"], start_a + 2):
        vals = [sub["nome"], sub["ultimo_valor"], sub["total_2026"], sub["meses_ativos_count"], sub["status_recomendacao"]]
        for col_i, val in enumerate(vals, 1):
            c = ws.cell(row=idx, column=col_i, value=val)
            c.font = FONT_NORMAL
            c.border = BORDER_CELL
            if col_i in (2, 3):
                c.alignment = ALIGN_RIGHT
                formatar_moeda(c)
            elif col_i == 4:
                c.alignment = ALIGN_CENTER

    auto_fit_columns(ws)


def copiar_abas_originais(wb):
    """Preserva as 4 abas históricas originais digitadas pelo casal."""
    if not os.path.exists(ORIGINAL_XLSX):
        return
    try:
        wb_orig = openpyxl.load_workbook(ORIGINAL_XLSX, data_only=True)
        for sname in wb_orig.sheetnames:
            ws_src = wb_orig[sname]
            ws_dst = wb.create_sheet(title=f"Orig - {sname[:20]}")
            ws_dst.views.sheetView[0].showGridLines = True
            for row in ws_src.iter_rows(values_only=True):
                ws_dst.append(list(row))
        print("Abas originais históricas preservadas com sucesso no arquivo XLSX!")
    except Exception as e:
        print(f"Aviso ao copiar abas originais: {e}")


def enviar_xlsx_para_google_drive(xlsx_path: str, sheet_id: str) -> bool:
    """Atualiza a planilha online do Google Sheets diretamente via Google Drive API v3."""
    if not os.path.exists(GCP_CREDS_PATH):
        print(f"Aviso: Credencial Google Drive não localizada em {GCP_CREDS_PATH}")
        return False

    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request

        creds = service_account.Credentials.from_service_account_file(
            GCP_CREDS_PATH,
            scopes=["https://www.googleapis.com/auth/drive"]
        )
        creds.refresh(Request())

        with open(xlsx_path, "rb") as f:
            xlsx_bytes = f.read()

        url = f"https://www.googleapis.com/upload/drive/v3/files/{sheet_id}?uploadType=media&supportsAllDrives=true"
        headers = {
            "Authorization": f"Bearer {creds.token}",
            "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }
        resp = requests.patch(url, headers=headers, data=xlsx_bytes, timeout=45)
        if resp.status_code == 200:
            info = resp.json()
            print(f"✅ Planilha Google Drive atualizada na nuvem com sucesso! ID={info.get('id')} Nome='{info.get('name')}'")
            return True
        else:
            print(f"❌ Erro ao atualizar Google Drive API v3 (status {resp.status_code}): {resp.text[:300]}")
            return False
    except Exception as e:
        print(f"❌ Exceção ao conectar na Google Drive API v3: {e}")
        return False


def sincronizar_planilha():
    """Gera a planilha XLSX no formato original (Total Anual + 12 Abas Mensais + Resumo + Histórico) e envia para a nuvem."""
    if not os.path.exists(CONSOLIDADO_PATH):
        raise FileNotFoundError(f"Consolidado não encontrado em {CONSOLIDADO_PATH}. Execute o extrator primeiro.")

    with open(CONSOLIDADO_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    print("Gerando arquivo XLSX no formato original (Total Anual + 12 Abas Mensais + Resumo)...")
    wb = openpyxl.Workbook()
    criar_aba_total_anual(wb, data)

    for ym, mes_nome in MESES_NOMES:
        criar_aba_mensal_original(wb, ym, mes_nome, data)

    criar_aba_resumo_metas(wb, data)
    copiar_abas_originais(wb)

    wb.save(OUTPUT_XLSX)
    print(f"Planilha XLSX gerada com sucesso: {OUTPUT_XLSX} ({os.path.getsize(OUTPUT_XLSX)} bytes)")

    sheet_id = regras.GOOGLE_SHEET_ID
    if sheet_id:
        print(f"Enviando para a planilha Google Drive ID={sheet_id}...")
        enviar_xlsx_para_google_drive(OUTPUT_XLSX, sheet_id)


if __name__ == "__main__":
    sincronizar_planilha()
