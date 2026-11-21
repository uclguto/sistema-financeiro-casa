r"""
Sincronizador Automático da Planilha Google Sheets e Gerador XLSX
Gera a planilha limpa com as 28 categorias, lançamentos completos e abas originais em:
C:\Dropbox\Controle_Financeiro\Planilha_Controle_Financeiro_2026_2027.xlsx
e atualiza diretamente a planilha na nuvem (Google Drive API v3).
"""

import os
import sys
import json
import requests
import openpyxl
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
FILL_ZEBRA = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
FILL_ALERT = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")
FILL_SUCCESS = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")

ALIGN_CENTER = Alignment(horizontal="center", vertical="center")
ALIGN_LEFT = Alignment(horizontal="left", vertical="center")
ALIGN_RIGHT = Alignment(horizontal="right", vertical="center")

THIN_SIDE = Side(border_style="thin", color="D9D9D9")
BORDER_CELL = Border(left=THIN_SIDE, right=THIN_SIDE, top=THIN_SIDE, bottom=THIN_SIDE)


def auto_fit_columns(ws, min_width=12, max_width=45):
    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = 0
        for cell in col:
            v = str(cell.value or "")
            if len(v) > max_len:
                max_len = len(v)
        ws.column_dimensions[col_letter].width = min(max(max_len + 3, min_width), max_width)


def formatar_moeda(cell):
    cell.number_format = '"R$" #,##0.00;[Red]-"R$" #,##0.00;"R$" 0.00'


def criar_aba_resumo(wb, data):
    """Aba 1: Resumo & Metas 2026-2027"""
    ws = wb.active
    ws.title = "Resumo & Metas 2026-2027"
    ws.views.sheetView[0].showGridLines = True

    ws["A1"] = "CONTROLE FINANCEIRO DOMÉSTICO — GUTO & JÉ"
    ws["A1"].font = FONT_TITLE
    ws["A2"] = f"Metas, Semáforos e Balanço Auditado (Atualizado em {data['metadata']['gerado_em'][:10]})"
    ws["A2"].font = FONT_MUTED

    # 1. TETOS
    ws.merge_cells("A4:D4")
    ws["A4"] = "1. TETOS MENSAIS E SEMANAIS DE CONTROLE ATIVO (SEMÁFOROS)"
    ws["A4"].font = FONT_SECTION
    ws["A4"].fill = FILL_SECTION

    headers = ["Categoria / Centro de Custo", "Teto Semanal", "Teto Mensal", "Diretriz de Controle"]
    for col_idx, h in enumerate(headers, 1):
        c = ws.cell(row=5, column=col_idx, value=h)
        c.font = FONT_HEADER
        c.fill = FILL_HEADER
        c.border = BORDER_CELL
        c.alignment = ALIGN_CENTER if col_idx > 1 else ALIGN_LEFT

    tetos = [
        ("🛒 Vale-Alimentação (Zaffari & Feira de Sábado)", 630.00, 2763.10, "100% abastecimento da casa; feira até R$ 220/sábado"),
        ("💳 Cartão de Crédito Guto (4110 + 2762 + Nubank)", "-", 3500.00, "Teto máximo da fatura mensal consolidada do Guto"),
        ("💳 Cartão de Crédito Jéssica (4219 + 9994 + 1229)", "-", 2500.00, "Teto máximo da fatura mensal dos cartões da Jé"),
        ("🚗 Uber & 99 Guto (Mobilidade)", 100.00, 400.00, "R$ 100 por semana para deslocamentos de trabalho"),
        ("🚗 Uber & 99 Jéssica (Mobilidade)", 100.00, 400.00, "R$ 100 por semana para consultório e deslocamentos"),
        ("🍕 Comer Fora, Baru, Cafés & iFood (Casal)", 250.00, 1000.00, "Lazer do fim de semana; evitar iFood em dias úteis"),
        ("📦 Compras Online, Roupas e Jogos", "-", 700.00, "Amazon, Shopee, Mercado Livre, Shein e eShop"),
    ]

    for r_idx, t in enumerate(tetos, 6):
        c1 = ws.cell(row=r_idx, column=1, value=t[0])
        c2 = ws.cell(row=r_idx, column=2, value=t[1])
        c3 = ws.cell(row=r_idx, column=3, value=t[2])
        c4 = ws.cell(row=r_idx, column=4, value=t[3])
        for c in [c1, c2, c3, c4]:
            c.font = FONT_NORMAL
            c.border = BORDER_CELL
        if isinstance(t[1], (int, float)): formatar_moeda(c2)
        if isinstance(t[2], (int, float)): formatar_moeda(c3)
        c2.alignment = ALIGN_RIGHT
        c3.alignment = ALIGN_RIGHT

    # 2. STATUS DOS 4 POTES
    start_r = 15
    ws.merge_cells(f"A{start_r}:D{start_r}")
    ws[f"A{start_r}"] = "2. STATUS DOS 4 POTES DE RESERVA E COFRINHOS"
    ws[f"A{start_r}"].font = FONT_SECTION
    ws[f"A{start_r}"].fill = FILL_SECTION

    h2 = ["Pote de Reserva", "Saldo Atual Auditado", "Função / Destinação", "Regra de Aporte"]
    for col_idx, h in enumerate(h2, 1):
        c = ws.cell(row=start_r + 1, column=col_idx, value=h)
        c.font = FONT_HEADER
        c.fill = FILL_HEADER
        c.border = BORDER_CELL

    potes = [
        ("👶 Poupança Clara (Mercado Pago)", 2515.00, "Patrimônio futuro da Clara (reposto com a PLR)", "Intocável; rendimento automático"),
        ("🛡️ Cofrinho Reserva Familiar (Mercado Pago)", 0.00, "Reserva de emergência do casal (zerada em Maio/26)", "Reconstruir a partir de Dez/26 com queda das parcelas"),
        ("⚡ RDB Imediato Nubank (Augusto)", 240.00, "Liquidez diária para imprevistos imediatos", "Aportar sobras do mês"),
        ("⚖️ Equalizador de Sobreaviso 2x1 (Jun/2027)", 0.00, "Estabilizar renda em R$ 8.350/mês nos meses sem sobreaviso", "Guardar R$ 1.050 nos 2 meses sim p/ resgatar R$ 2.100 no mês não"),
    ]

    for r_idx, p in enumerate(potes, start_r + 2):
        c1 = ws.cell(row=r_idx, column=1, value=p[0])
        c2 = ws.cell(row=r_idx, column=2, value=p[1])
        c3 = ws.cell(row=r_idx, column=3, value=p[2])
        c4 = ws.cell(row=r_idx, column=4, value=p[3])
        for c in [c1, c2, c3, c4]:
            c.font = FONT_NORMAL
            c.border = BORDER_CELL
        formatar_moeda(c2)
        c2.alignment = ALIGN_RIGHT

    # 3. BALANÇO REAL DE REPASSES DA JÉSSICA VS. COFRINHOS VS. CARTÕES
    start_r3 = 22
    ws.merge_cells(f"A{start_r3}:F{start_r3}")
    ws[f"A{start_r3}"] = "3. BALANÇO REAL: REPASSES DA CLÍNICA DA JÉSSICA VS. RESGATES COFRINHOS VS. CARTÕES"
    ws[f"A{start_r3}"].font = FONT_SECTION
    ws[f"A{start_r3}"].fill = FILL_SECTION

    h3 = ["Mês", "Repasse Real Clínica Jé", "Resgates Cofrinhos MP", "Fatura Cartões Jé", "Saldo Líquido Jé", "Diagnóstico"]
    for col_idx, h in enumerate(h3, 1):
        c = ws.cell(row=start_r3 + 1, column=col_idx, value=h)
        c.font = FONT_HEADER
        c.fill = FILL_HEADER
        c.border = BORDER_CELL
        c.alignment = ALIGN_CENTER

    for idx, rm in enumerate(data["resumo_mensal"], start_r3 + 2):
        c1 = ws.cell(row=idx, column=1, value=rm["mes"])
        c2 = ws.cell(row=idx, column=2, value=rm["jessica_repasses_clinica"])
        c3 = ws.cell(row=idx, column=3, value=rm["cofrinhos_resgates"])
        c4 = ws.cell(row=idx, column=4, value=rm["cartao_jessica"])
        c5 = ws.cell(row=idx, column=5, value=f"=B{idx}-D{idx}")
        obs = "Equilibrado" if rm["jessica_repasses_clinica"] >= rm["cartao_jessica"] else "Fatura superou repasses"
        c6 = ws.cell(row=idx, column=6, value=obs)

        for c in [c1, c2, c3, c4, c5, c6]:
            c.font = FONT_NORMAL
            c.border = BORDER_CELL
        c1.alignment = ALIGN_CENTER
        c2.alignment = ALIGN_RIGHT
        c3.alignment = ALIGN_RIGHT
        c4.alignment = ALIGN_RIGHT
        c5.alignment = ALIGN_RIGHT
        formatar_moeda(c2)
        formatar_moeda(c3)
        formatar_moeda(c4)
        formatar_moeda(c5)
        if obs == "Equilibrado":
            c5.fill = FILL_SUCCESS
        else:
            c5.fill = FILL_ALERT

    # Linha Total
    tot_r = start_r3 + 2 + len(data["resumo_mensal"])
    ws.cell(row=tot_r, column=1, value="TOTAL 2026").font = FONT_BOLD
    c_tot_rep = ws.cell(row=tot_r, column=2, value=f"=SUM(B{start_r3+2}:B{tot_r-1})")
    c_tot_resg = ws.cell(row=tot_r, column=3, value=f"=SUM(C{start_r3+2}:C{tot_r-1})")
    c_tot_cart = ws.cell(row=tot_r, column=4, value=f"=SUM(D{start_r3+2}:D{tot_r-1})")
    c_tot_dif = ws.cell(row=tot_r, column=5, value=f"=B{tot_r}-D{tot_r}")
    ws.cell(row=tot_r, column=6, value="Déficit coberto por reservas").font = FONT_BOLD
    for c in [ws.cell(row=tot_r, column=1), c_tot_rep, c_tot_resg, c_tot_cart, c_tot_dif, ws.cell(row=tot_r, column=6)]:
        c.font = FONT_BOLD
        c.border = BORDER_CELL
        c.fill = FILL_HEADER
    formatar_moeda(c_tot_rep)
    formatar_moeda(c_tot_resg)
    formatar_moeda(c_tot_cart)
    formatar_moeda(c_tot_dif)

    auto_fit_columns(ws)


def criar_aba_categorias_mensais(wb, data):
    """Aba 2: Gastos Mensais por Categoria (As 28 categorias completas de Jan a Nov/2026)"""
    ws = wb.create_sheet(title="Gastos Mensais por Categoria")
    ws.views.sheetView[0].showGridLines = True

    ws["A1"] = "MATRIZ COMPLETA DE GASTOS POR CATEGORIA — 2026 (JAN A NOV)"
    ws["A1"].font = FONT_TITLE

    meses = [rm["mes"][5:] for rm in data["resumo_mensal"]]
    headers = ["Categoria de Gasto"] + meses + ["Total Ano", "Média/Mês", "Guto", "Jéssica"]
    for col_idx, h in enumerate(headers, 1):
        c = ws.cell(row=3, column=col_idx, value=h)
        c.font = FONT_HEADER
        c.fill = FILL_HEADER
        c.border = BORDER_CELL
        c.alignment = ALIGN_CENTER if col_idx > 1 else ALIGN_LEFT

    # Categorias
    cats = data.get("categorias_resumo", [])
    for r_idx, cat in enumerate(cats, 4):
        c_nome = ws.cell(row=r_idx, column=1, value=cat["categoria"])
        c_nome.font = FONT_NORMAL
        c_nome.border = BORDER_CELL

        for m_idx, ym in enumerate([rm["mes"] for rm in data["resumo_mensal"]], 2):
            val = cat["por_mes"].get(ym, 0.0)
            c_val = ws.cell(row=r_idx, column=m_idx, value=val)
            c_val.font = FONT_NORMAL
            c_val.border = BORDER_CELL
            c_val.alignment = ALIGN_RIGHT
            formatar_moeda(c_val)

        # Total e Média
        start_col = get_column_letter(2)
        end_col = get_column_letter(len(meses) + 1)
        tot_col = len(meses) + 2
        med_col = len(meses) + 3
        guto_col = len(meses) + 4
        je_col = len(meses) + 5

        c_tot = ws.cell(row=r_idx, column=tot_col, value=f"=SUM({start_col}{r_idx}:{end_col}{r_idx})")
        c_med = ws.cell(row=r_idx, column=med_col, value=f"=AVERAGE({start_col}{r_idx}:{end_col}{r_idx})")
        c_guto = ws.cell(row=r_idx, column=guto_col, value=cat["total_guto"])
        c_je = ws.cell(row=r_idx, column=je_col, value=cat["total_je"])

        for c in [c_tot, c_med, c_guto, c_je]:
            c.font = FONT_BOLD if c in [c_tot, c_med] else FONT_NORMAL
            c.border = BORDER_CELL
            c.alignment = ALIGN_RIGHT
            formatar_moeda(c)

    # Linha Total
    tot_row = len(cats) + 4
    ws.cell(row=tot_row, column=1, value="TOTAL GERAL").font = FONT_BOLD
    ws.cell(row=tot_row, column=1).fill = FILL_SECTION
    ws.cell(row=tot_row, column=1).font = FONT_SECTION

    for col in range(2, len(headers) + 1):
        col_let = get_column_letter(col)
        c = ws.cell(row=tot_row, column=col, value=f"=SUM({col_let}4:{col_let}{tot_row-1})")
        c.font = FONT_BOLD
        c.border = BORDER_CELL
        c.fill = FILL_HEADER
        c.alignment = ALIGN_RIGHT
        formatar_moeda(c)

    auto_fit_columns(ws)


def criar_aba_parcelas_assinaturas(wb, data):
    """Aba 3: Parcelas Futuras & Assinaturas"""
    ws = wb.create_sheet(title="Parcelas Futuras & Assinaturas")
    ws.views.sheetView[0].showGridLines = True

    ws["A1"] = "PROJEÇÃO DE PARCELAS FUTURAS E AUDITORIA DE RECORRÊNCIAS"
    ws["A1"].font = FONT_TITLE

    # 1. CRONOGRAMA
    ws.merge_cells("A3:E3")
    ws["A3"] = "1. CRONOGRAMA DE QUEDA DAS PARCELAS (DEZ/2026 A OUT/2027)"
    ws["A3"].font = FONT_SECTION
    ws["A3"].fill = FILL_SECTION

    h1 = ["Mês de Vencimento", "Total em Parcelas", "Qtd Compras", "Alívio Mensal vs. Dez/26", "Status Orçamentário"]
    for col_idx, h in enumerate(h1, 1):
        c = ws.cell(row=4, column=col_idx, value=h)
        c.font = FONT_HEADER
        c.fill = FILL_HEADER
        c.border = BORDER_CELL
        c.alignment = ALIGN_CENTER

    base_dez = data["parcelas_futuras"][0]["total_parcelas"] if data["parcelas_futuras"] else 1764.16

    for idx, pf in enumerate(data["parcelas_futuras"], 5):
        c1 = ws.cell(row=idx, column=1, value=pf["mes"])
        c2 = ws.cell(row=idx, column=2, value=pf["total_parcelas"])
        c3 = ws.cell(row=idx, column=3, value=pf["quantidade_itens"])
        alivio = base_dez - pf["total_parcelas"]
        c4 = ws.cell(row=idx, column=4, value=alivio)
        status = "Parcelas altas" if pf["total_parcelas"] > 1000 else ("Alívio expressivo" if pf["total_parcelas"] < 500 else "Transição")
        c5 = ws.cell(row=idx, column=5, value=status)

        for c in [c1, c2, c3, c4, c5]:
            c.font = FONT_NORMAL
            c.border = BORDER_CELL
        c1.alignment = ALIGN_CENTER
        c2.alignment = ALIGN_RIGHT
        c3.alignment = ALIGN_CENTER
        c4.alignment = ALIGN_RIGHT
        formatar_moeda(c2)
        formatar_moeda(c4)
        if status == "Alívio expressivo":
            c2.fill = FILL_SUCCESS
            c4.fill = FILL_SUCCESS

    # 2. AUDITORIA ASSINATURAS
    start_r2 = 18
    ws.merge_cells(f"A{start_r2}:E{start_r2}")
    ws[f"A{start_r2}"] = "2. CHECKLIST E AUDITORIA DE ASSINATURAS E RECORRÊNCIAS"
    ws[f"A{start_r2}"].font = FONT_SECTION
    ws[f"A{start_r2}"].fill = FILL_SECTION

    h2 = ["Assinatura / Serviço", "Último Valor", "Total Pago em 2026", "Meses Ativos", "Ação Recomendada"]
    for col_idx, h in enumerate(h2, 1):
        c = ws.cell(row=start_r2 + 1, column=col_idx, value=h)
        c.font = FONT_HEADER
        c.fill = FILL_HEADER
        c.border = BORDER_CELL
        c.alignment = ALIGN_CENTER

    for idx, sub in enumerate(data["assinaturas"], start_r2 + 2):
        c1 = ws.cell(row=idx, column=1, value=sub["nome"])
        c2 = ws.cell(row=idx, column=2, value=sub["ultimo_valor"])
        c3 = ws.cell(row=idx, column=3, value=sub["total_2026"])
        c4 = ws.cell(row=idx, column=4, value=sub["meses_ativos_count"])
        c5 = ws.cell(row=idx, column=5, value=sub["status_recomendacao"])

        for c in [c1, c2, c3, c4, c5]:
            c.font = FONT_NORMAL
            c.border = BORDER_CELL
        c1.alignment = ALIGN_LEFT
        c2.alignment = ALIGN_RIGHT
        c3.alignment = ALIGN_RIGHT
        c4.alignment = ALIGN_CENTER
        formatar_moeda(c2)
        formatar_moeda(c3)
        if "CANCELAR" in sub["status_recomendacao"].upper():
            c5.fill = FILL_ALERT
            c5.font = FONT_BOLD

    auto_fit_columns(ws)


def criar_aba_lancamentos_auditados(wb, data):
    """Aba 4: Lançamentos Auditados 2026 (Todas as transações completas com categoria)"""
    ws = wb.create_sheet(title="Lançamentos Auditados 2026")
    ws.views.sheetView[0].showGridLines = True

    ws["A1"] = "BASE COMPLETA DE TRANSAÇÕES AUDITADAS 2026 (JAN A NOV)"
    ws["A1"].font = FONT_TITLE

    headers = ["Mês", "Data", "Origem", "Titular", "Categoria", "Descrição", "Valor (R$)", "Parcela", "Tipo"]
    for col_idx, h in enumerate(headers, 1):
        c = ws.cell(row=3, column=col_idx, value=h)
        c.font = FONT_HEADER
        c.fill = FILL_HEADER
        c.border = BORDER_CELL
        c.alignment = ALIGN_CENTER

    txs = data.get("todas_transacoes", [])
    for idx, t in enumerate(txs, 4):
        c1 = ws.cell(row=idx, column=1, value=t.get("ym", ""))
        c2 = ws.cell(row=idx, column=2, value=t.get("date", ""))
        c3 = ws.cell(row=idx, column=3, value=t.get("source", ""))
        c4 = ws.cell(row=idx, column=4, value=t.get("holder", ""))
        c5 = ws.cell(row=idx, column=5, value=t.get("category", ""))
        c6 = ws.cell(row=idx, column=6, value=t.get("desc", ""))
        c7 = ws.cell(row=idx, column=7, value=t.get("amount", 0.0))
        parc = f"{t.get('inst_cur')}/{t.get('inst_tot')}" if t.get("inst_cur") else "-"
        c8 = ws.cell(row=idx, column=8, value=parc)
        c9 = ws.cell(row=idx, column=9, value=t.get("tipo", ""))

        for c in [c1, c2, c3, c4, c5, c6, c7, c8, c9]:
            c.font = FONT_NORMAL
            c.border = BORDER_CELL
        c1.alignment = ALIGN_CENTER
        c2.alignment = ALIGN_CENTER
        c3.alignment = ALIGN_CENTER
        c4.alignment = ALIGN_CENTER
        c7.alignment = ALIGN_RIGHT
        c8.alignment = ALIGN_CENTER
        c9.alignment = ALIGN_CENTER
        formatar_moeda(c7)

    auto_fit_columns(ws)


def copiar_abas_originais(wb):
    """Preserva as 4 abas históricas originais digitadas pelo Guto."""
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
        resp = requests.patch(url, headers=headers, data=xlsx_bytes, timeout=40)
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
    """Gera a planilha XLSX local e envia para a nuvem Google Drive."""
    if not os.path.exists(CONSOLIDADO_PATH):
        raise FileNotFoundError(f"Consolidado não encontrado em {CONSOLIDADO_PATH}. Execute o extrator primeiro.")

    with open(CONSOLIDADO_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    print("Gerando arquivo XLSX com as 28 categorias e lançamentos completos...")
    wb = openpyxl.Workbook()
    criar_aba_resumo(wb, data)
    criar_aba_categorias_mensais(wb, data)
    criar_aba_parcelas_assinaturas(wb, data)
    criar_aba_lancamentos_auditados(wb, data)
    copiar_abas_originais(wb)

    wb.save(OUTPUT_XLSX)
    print(f"Planilha XLSX gerada com sucesso: {OUTPUT_XLSX} ({os.path.getsize(OUTPUT_XLSX)} bytes)")

    # Upload direto na nuvem Google Drive
    sheet_id = regras.GOOGLE_SHEET_ID
    if sheet_id:
        print(f"Enviando para a planilha Google Drive ID={sheet_id}...")
        enviar_xlsx_para_google_drive(OUTPUT_XLSX, sheet_id)


if __name__ == "__main__":
    sincronizar_planilha()
