# 🏠 Sistema Financeiro Doméstico (Guto & Jé)

Sistema financeiro familiar completo, automatizado e com **isolamento total de segurança (Air-Gap)** em relação aos ambientes corporativos/VPS do Hermes.

## 🔐 Pilares de Arquitetura e Segurança
1. **Zero Contato com Hermes:** Sem conexão com as VPSs da Oracle (`137.131.245.71` / `147.15.71.7`) nem com o domínio `cadernodesonhos.com.br`.
2. **Criptografia Client-Side (AES-256-GCM + PBKDF2 100k):** Os dados exportados para o Web App (`web/payload.enc.json`) são 100% criptografados matematicamente. O celular descriptografa em memória RAM usando a WebCrypto API após a inserção do PIN do casal definido no `.env`.
3. **PWA Mobile-First Instalável:** Funciona no Android e iOS como um app nativo, com semáforos de controle semanal (VA, Uber, Comer Fora, Compras Online), faturas dos cartões, acertos da Jé (dia 10/20) e simulador da caixinha (30%).
4. **Sincronização com Google Sheets:** Gera a planilha atualizada com 4 abas estruturadas, sem erros de fórmula, para análise executiva no computador sem necessidade de Excel instalado.

## 📁 Estrutura do Projeto
```text
sistema_financeiro/
├── docs/
│   ├── ROADMAP_FASE2_BOT_TELEGRAM.md      # Planejamento do Bot Telegram para Fase 2
│   └── COMO_CONECTAR_PLANILHA_AUTOMATICA.md # Instruções de conexão Google Sheets
├── data/
│   └── consolidado_2026_2027.json         # Dados locais brutos (ignorado no git)
├── src/
│   ├── config_regras.py                   # Tetos orçamentários, regras e metas
│   ├── extrator_unificado.py              # Motor de extração de 73 extratos
│   ├── crypto_pwa.py                      # Cifrador AES-256-GCM para o PWA
│   ├── sync_google_sheets.py              # Gerador XLSX e sincronizador Sheets
│   └── preview_local.py                   # Servidor de teste local (porta 8095)
├── web/                                   # PWA Estático para deploy (Cloudflare/GitHub Pages)
│   ├── index.html                         # Interface Mobile-First
│   ├── styles.css                         # Estilo Nubank Dark/Light
│   ├── app.js                             # Descriptografia WebCrypto e Lógica
│   ├── payload.enc.json                   # Pacote Criptografado
│   ├── manifest.json                      # PWA Manifesto
│   ├── sw.js                              # Service Worker offline
│   └── icon.svg                           # Ícone do App
└── tests/
    └── test_motor_financeiro.py           # Bateria de testes automatizados
```

## 🚀 Como Executar em 1 Clique
No diretório `C:\Dropbox\Controle_Financeiro`, clique duas vezes em `sincronizar_tudo.bat`.
O script irá:
1. Ler e consolidar todos os extratos em `extratos/`;
2. Criptografar o pacote para `web/payload.enc.json`;
3. Gerar a planilha `Planilha_Controle_Financeiro_2026_2027.xlsx` com 4 abas limpas;
4. Executar os testes automatizados com `pytest`.
