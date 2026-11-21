# 📊 Como Conectar a Sincronização Automática com o Google Sheets

A planilha oficial da família está localizada em:
`https://docs.google.com/spreadsheets/d/1ZfxdNBoyLw0zwLweDWROLEL1uUemtv3jlgWj120bexo/edit?usp=sharing`

O sistema já gera automaticamente um arquivo XLSX completo e formatado:
`C:\Dropbox\Controle_Financeiro\Planilha_Controle_Financeiro_2026_2027.xlsx`
com as 4 abas estruturadas, cores, bordas e fórmulas 100% corrigidas.

---

## Opção 1: Abrir / Importar o XLSX no Google Drive (Imediato, Zero Configuração)
1. Abra o Google Drive no navegador.
2. Arraste `Planilha_Controle_Financeiro_2026_2027.xlsx` para sua pasta do Drive ou abra a planilha existente e clique em **Arquivo -> Importar -> Fazer upload**.
3. Selecione **Substituir planilha** ou **Criar novas páginas**.

---

## Opção 2: Conexão Automática via Google Apps Script (1-Clique via Script)
Para que o comando `python src/sync_google_sheets.py` (ou `sincronizar_tudo.bat`) envie os dados diretamente para as abas da planilha na nuvem sem precisar abrir o Google Drive:

1. Na sua planilha do Google Sheets, clique no menu superior: **Extensões -> Apps Script**.
2. Apague o código padrão e cole o seguinte script:

```javascript
function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents);
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    
    // Atualiza ou cria as 4 abas
    for (var sheetName in data.sheets) {
      var sheet = ss.getSheetByName(sheetName);
      if (!sheet) {
        sheet = ss.insertSheet(sheetName);
      }
      sheet.clear();
      var rows = data.sheets[sheetName];
      if (rows.length > 0) {
        sheet.getRange(1, 1, rows.length, rows[0].length).setValues(rows);
      }
    }
    return ContentService.createTextOutput(JSON.stringify({status: "ok"})).setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({status: "error", message: err.toString()})).setMimeType(ContentService.MimeType.JSON);
  }
}
```

3. Clique em **Implantar -> Nova implantação**.
4. Tipo: **App da Web**.
5. Executar como: **Eu (seu email)**.
6. Quem tem acesso: **Qualquer pessoa** (já que a planilha é privada/compartilhada via link).
7. Clique em **Implantar** e copie a **URL do App da Web**.
8. Cole a URL no seu arquivo `.env`:
```env
GOOGLE_APPS_SCRIPT_WEBHOOK_URL=https://script.google.com/macros/s/.../exec
```

Pronto! Sempre que rodar `sincronizar_tudo.bat`, a planilha na nuvem será atualizada automaticamente em 3 segundos.
