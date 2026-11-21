r"""
Sincronizador Automático da Planilha Google Sheets e Gerador XLSX
Gera a planilha limpa com 4 abas estruturadas (sem erros de fórmula) em
C:\Dropbox\Controle_Financeiro\Planilha_Controle_Financeiro_2026_2027.xlsx
e sincroniza com a nuvem (Google Sheets) via Apps Script Webhook ou API.
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

# Estilos Visuais Elegantes (Paleta Moderna Azul Marinho / Cinza / Verde)
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
    """Ajusta automaticamente a largura das colunas."""
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
    ws["A2"] = f"Metas, Semáforos e Balanço Integrado (Atualizado em {data['metadata']['gerado_em'][:10]})"
    ws["A2"].font = FONT_MUTED

    # 1. TETOS E METAS DE CONTROLE ATIVO
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
        c4.alignment = ALIGN_LEFT

    # 2. STATUS DOS 4 POTES DE RESERVA
    start_r = 15
    ws.merge_cells(f"A{start_r}:D{start_r}")
    ws[f"A{start_r}"] = "2. STATUS DOS 4 POTES DE RESERVA E COFRINHOS"
    ws[f"A{start_r}"].font = FONT_SECTION
    ws[f"A{start_r}"].fill = FILL_SECTION

    h2 = ["Pote de Reserva", "Saldo Atual Auditado", "Objetivo / Função", "Regra de Aporte"]
    for col_idx, h in enumerate(h2, 1):
        c = ws.cell(row=start_r + 1, column=col_idx, value=h)
        c.font = FONT_HEADER
        c.fill = FILL_HEADER
        c.border = BORDER_CELL
        c.alignment = ALIGN_CENTER if col_idx == 2 else ALIGN_LEFT

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

    # 3. BALANÇO REAL DE 2026: REPASSES JÉSSICA VS. CARTÕES ADICIONAIS
    start_r3 = 22
    ws.merge_cells(f"A{start_r3}:E{start_r3}")
    ws[f"A{start_r3}"] = "3. BALANÇO REAL DE REPASSES DA JÉSSICA VS. CARTÕES ADICIONAIS (JAN A NOV/2026)"
    ws[f"A{start_r3}"].font = FONT_SECTION
    ws[f"A{start_r3}"].fill = FILL_SECTION

    h3 = ["Mês", "Repasses Líquidos Jéssica", "Fatura Cartões Jéssica", "Saldo Líquido Jé", "Observação Diagnóstica"]
    for col_idx, h in enumerate(h3, 1):
        c = ws.cell(row=start_r3 + 1, column=col_idx, value=h)
        c.font = FONT_HEADER
        c.fill = FILL_HEADER
        c.border = BORDER_CELL
        c.alignment = ALIGN_CENTER

    for idx, rm in enumerate(data["resumo_mensal"], start_r3 + 2):
        c1 = ws.cell(row=idx, column=1, value=rm["mes"])
        c2 = ws.cell(row=idx, column=2, value=rm["jessica_repasses_liquido"])
        c3 = ws.cell(row=idx, column=3, value=rm["cartao_jessica"])
        c4 = ws.cell(row=idx, column=4, value=f"=B{idx}-C{idx}")
        obs = "Equilibrado" if rm["jessica_repasses_liquido"] >= rm["cartao_jessica"] else "Fatura superou repasses"
        c5 = ws.cell(row=idx, column=5, value=obs)
        for c in [c1, c2, c3, c4, c5]:
            c.font = FONT_NORMAL
            c.border = BORDER_CELL
        c1.alignment = ALIGN_CENTER
        c2.alignment = ALIGN_RIGHT
        c3.alignment = ALIGN_RIGHT
        c4.alignment = ALIGN_RIGHT
        formatar_moeda(c2)
        formatar_moeda(c3)
        formatar_moeda(c4)
        if obs == "Equilibrado":
            c4.fill = FILL_SUCCESS
        else:
            c4.fill = FILL_ALERT

    # Linha Total
    tot_r = start_r3 + 2 + len(data["resumo_mensal"])
    ws.cell(row=tot_r, column=1, value="TOTAL 2026").font = FONT_BOLD
    c_tot_rep = ws.cell(row=tot_r, column=2, value=f"=SUM(B{start_r3+2}:B{tot_r-1})")
    c_tot_cart = ws.cell(row=tot_r, column=3, value=f"=SUM(C{start_r3+2}:C{tot_r-1})")
    c_tot_dif = ws.cell(row=tot_r, column=4, value=f"=B{tot_r}-C{tot_r}")
    ws.cell(row=tot_r, column=5, value="Déficit coberto por reservas").font = FONT_BOLD
    for c in [ws.cell(row=tot_r, column=1), c_tot_rep, c_tot_cart, c_tot_dif, ws.cell(row=tot_r, column=5)]:
        c.font = FONT_BOLD
        c.border = BORDER_CELL
        c.fill = FILL_HEADER
    formatar_moeda(c_tot_rep)
    formatar_moeda(c_tot_cart)
    formatar_moeda(c_tot_dif)

    auto_fit_columns(ws)


def criar_aba_anual_blocos(wb, data):
    """Aba 2: Anual por Blocos 2026 (Visão Canônica dos Gastos Familiares)"""
    ws = wb.create_sheet(title="Anual por Blocos 2026")
    ws.views.sheetView[0].showGridLines = True

    ws["A1"] = "RAIO-X ANUAL POR BLOCOS ORÇAMENTÁRIOS — 2026"
    ws["A1"].font = FONT_TITLE

    meses = [rm["mes"][5:] for rm in data["resumo_mensal"]]
    headers = ["Bloco / Linha de Custo"] + meses + ["Total Ano", "Média/Mês"]
    for col_idx, h in enumerate(headers, 1):
        c = ws.cell(row=3, column=col_idx, value=h)
        c.font = FONT_HEADER
        c.fill = FILL_HEADER
        c.border = BORDER_CELL
        c.alignment = ALIGN_CENTER if col_idx > 1 else ALIGN_LEFT

    # Linhas de dados
    linhas_blocos = [
        ("RENDAS: Salário Líquido Guto (Banrisul)", [rm["salario_liquido"] for rm in data["resumo_mensal"]]),
        ("RENDAS: Férias / PLR / Restituição IRPF", [rm["ferias_plr_irpf"] for rm in data["resumo_mensal"]]),
        ("RENDAS: Repasses Líquidos Jéssica", [rm["jessica_repasses_liquido"] for rm in data["resumo_mensal"]]),
        ("CARTÕES: Fatura Augusto (4110 + 2762 + Nubank)", [rm["cartao_augusto"] for rm in data["resumo_mensal"]]),
        ("CARTÕES: Fatura Jéssica (4219 + 9994 + 1229)", [rm["cartao_jessica"] for rm in data["resumo_mensal"]]),
        ("CLARA: Colégio Bom Conselho (Mensalidade)", [rm["colegio_clara"] for rm in data["resumo_mensal"]]),
        ("CASA: Boletos Fixos Dia 10 (Condomínio / Aluguel)", [rm["boletos_casa"] for rm in data["resumo_mensal"]]),
        ("CASA: CEEE Equatorial (Energia Elétrica)", [rm["ceee_luz"] for rm in data["resumo_mensal"]]),
        ("CASA: Claro / NET (Internet & TV)", [rm["claro_net"] for rm in data["resumo_mensal"]]),
        ("PESSOAL: Pix Mensal Thiago Dallo", [rm["pix_thiago"] for rm in data["resumo_mensal"]]),
        ("PESSOAL: Pix Mensal Luiz Antonio", [rm["pix_luiz"] for rm in data["resumo_mensal"]]),
        ("VALE-ALIMENTAÇÃO: Crédito Recebido", [rm["va_credito"] for rm in data["resumo_mensal"]]),
        ("VALE-ALIMENTAÇÃO: Gastos Zaffari", [rm["va_gasto_zaffari"] for rm in data["resumo_mensal"]]),
        ("VALE-ALIMENTAÇÃO: Gastos Feira de Sábado", [rm["va_gasto_feira"] for rm in data["resumo_mensal"]]),
        ("VALE-ALIMENTAÇÃO: Gastos Farmácia/Restaurante", [rm["va_gasto_outros"] for rm in data["resumo_mensal"]]),
    ]

    for r_idx, (nome_linha, valores) in enumerate(linhas_blocos, 4):
        c_nome = ws.cell(row=r_idx, column=1, value=nome_linha)
        c_nome.font = FONT_NORMAL
        c_nome.border = BORDER_CELL
        if "RENDAS" in nome_linha:
            c_nome.font = FONT_BOLD
            c_nome.fill = FILL_SUCCESS
        elif "CARTÕES" in nome_linha:
            c_nome.fill = FILL_ALERT

        for m_idx, val in enumerate(valores, 2):
            c_val = ws.cell(row=r_idx, column=m_idx, value=val)
            c_val.font = FONT_NORMAL
            c_val.border = BORDER_CELL
            c_val.alignment = ALIGN_RIGHT
            formatar_moeda(c_val)

        # Fórmulas de Total e Média
        start_col_letter = get_column_letter(2)
        end_col_letter = get_column_letter(len(valores) + 1)
        tot_col = len(valores) + 2
        med_col = len(valores) + 3

        c_tot = ws.cell(row=r_idx, column=tot_col, value=f"=SUM({start_col_letter}{r_idx}:{end_col_letter}{r_idx})")
        c_med = ws.cell(row=r_idx, column=med_col, value=f"=AVERAGE({start_col_letter}{r_idx}:{end_col_letter}{r_idx})")
        for c in [c_tot, c_med]:
            c.font = FONT_BOLD
            c.border = BORDER_CELL
            c.alignment = ALIGN_RIGHT
            formatar_moeda(c)

    auto_fit_columns(ws)


def criar_aba_parcelas_assinaturas(wb, data):
    """Aba 3: Parcelas Futuras & Assinaturas"""
    ws = wb.create_sheet(title="Parcelas Futuras & Assinaturas")
    ws.views.sheetView[0].showGridLines = True

    ws["A1"] = "PROJEÇÃO DE PARCELAS FUTURAS E AUDITORIA DE RECORRÊNCIAS"
    ws["A1"].font = FONT_TITLE

    # 1. CRONOGRAMA DE PARCELAS
    ws.merge_cells("A3:E3")
    ws["A3"] = "1. CRONOGRAMA DE QUEDA DAS PARCELAS DE CARTÃO (DEZ/2026 A OUT/2027)"
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

    # 2. AUDITORIA DE ASSINATURAS
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
    """Aba 4: Lançamentos Auditados 2026 (Amostra e Transações Recentes)"""
    ws = wb.create_sheet(title="Lançamentos Auditados 2026")
    ws.views.sheetView[0].showGridLines = True

    ws["A1"] = "TRANSAÇÕES RECENTES AUDITADAS (CARTÕES E CONTAS)"
    ws["A1"].font = FONT_TITLE

    headers = ["Mês da Fatura", "Data", "Origem / Cartão", "Titular", "Descrição do Lançamento", "Valor (R$)", "Parcela"]
    for col_idx, h in enumerate(headers, 1):
        c = ws.cell(row=3, column=col_idx, value=h)
        c.font = FONT_HEADER
        c.fill = FILL_HEADER
        c.border = BORDER_CELL
        c.alignment = ALIGN_CENTER

    txs = data.get("transacoes_recentes_novembro", [])
    for idx, t in enumerate(txs, 4):
        c1 = ws.cell(row=idx, column=1, value=t.get("bill_ym", ""))
        c2 = ws.cell(row=idx, column=2, value=t.get("date", ""))
        c3 = ws.cell(row=idx, column=3, value=t.get("source", ""))
        c4 = ws.cell(row=idx, column=4, value=t.get("holder", ""))
        c5 = ws.cell(row=idx, column=5, value=t.get("desc", ""))
        c6 = ws.cell(row=idx, column=6, value=t.get("amount", 0.0))
        parc = f"{t.get('inst_cur')}/{t.get('inst_tot')}" if t.get("inst_cur") else "-"
        c7 = ws.cell(row=idx, column=7, value=parc)

        for c in [c1, c2, c3, c4, c5, c6, c7]:
            c.font = FONT_NORMAL
            c.border = BORDER_CELL
        c1.alignment = ALIGN_CENTER
        c2.alignment = ALIGN_CENTER
        c3.alignment = ALIGN_CENTER
        c4.alignment = ALIGN_CENTER
        c6.alignment = ALIGN_RIGHT
        c7.alignment = ALIGN_CENTER
        formatar_moeda(c6)

    auto_fit_columns(ws)


def sincronizar_planilha():
    """Gera a planilha XLSX local e envia para a nuvem caso webhook esteja configurado."""
    if not os.path.exists(CONSOLIDADO_PATH):
        raise FileNotFoundError(f"Consolidado não encontrado em {CONSOLIDADO_PATH}. Execute o extrator primeiro.")

    with open(CONSOLIDADO_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    print("Gerando arquivo XLSX com 4 abas estruturadas...")
    wb = openpyxl.Workbook()
    criar_aba_resumo(wb, data)
    criar_aba_anual_blocos(wb, data)
    criar_aba_parcelas_assinaturas(wb, data)
    criar_aba_lancamentos_auditados(wb, data)

    wb.save(OUTPUT_XLSX)
    print(f"Planilha XLSX gerada com sucesso: {OUTPUT_XLSX} ({os.path.getsize(OUTPUT_XLSX)} bytes)")

    # Sincronização em nuvem via Webhook Google Apps Script se configurado
    webhook_url = regras.GOOGLE_APPS_SCRIPT_WEBHOOK_URL
    if webhook_url:
        print(f"Enviando atualização para o Google Sheets via Webhook: {webhook_url[:40]}...")
        try:
            # Prepara estrutura tabular simplificada para o Apps Script
            payload = {
                "updated_at": data["metadata"]["gerado_em"],
                "resumo_mensal": data["resumo_mensal"],
                "parcelas_futuras": data["parcelas_futuras"],
                "assinaturas": data["assinaturas"],
            }
            resp = requests.post(webhook_url, json=payload, timeout=20)
            print(f"Resposta Webhook: status={resp.status_code} text={resp.text[:120]}")
        except Exception as e:
            print(f"Aviso: Não foi possível enviar webhook para o Google Sheets ({e})")
    else:
        print("Webhook do Google Apps Script não configurado em .env (consulte docs/COMO_CONECTAR_PLANILHA_AUTOMATICA.md)")


if __name__ == "__main__":
    sincronizar_planilha()
