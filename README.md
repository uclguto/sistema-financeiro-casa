# 🏠 Sistema Financeiro Doméstico (Guto & Jé) — Arquitetura V3.0

Sistema financeiro familiar automatizado, auditável e com **isolamento total de segurança (Air-Gap)** em relação aos ambientes corporativos/VPS do Hermes.

---

## 🔗 Links e Recursos Oficiais

- 📱 **PWA Mobile-First (GitHub Pages):** [https://uclguto.github.io/sistema-financeiro-casa/](https://uclguto.github.io/sistema-financeiro-casa/)
- 📊 **Planilha Google Sheets Oficial (18 Abas):** ID `1ZfxdNBoyLw0zwLweDWROLEL1uUemtv3jlgWj120bexo` (*Controle de Gastos 2026*)
- 💻 **Repositório GitHub Privado:** [https://github.com/uclguto/sistema-financeiro-casa](https://github.com/uclguto/sistema-financeiro-casa)

---

## 🔐 Pilares de Arquitetura e Segurança

1. **Zero Contato com Hermes (Air-Gap):** Sem conexão com as VPSs da Oracle (`137.131.245.71` / `147.15.71.7`) nem com o domínio `cadernodesonhos.com.br`.
2. **Criptografia Client-Side (AES-256-GCM + PBKDF2 100k):** Os dados exportados para o Web App (`web/payload.enc.json`) são 100% criptografados matematicamente. O celular descriptografa em memória RAM usando a WebCrypto API nativa após a inserção do PIN de 4 dígitos do casal (armazenado apenas no `.env` local). Zero dados abertos no repositório.
3. **PWA Mobile-First Responsivo:** Funciona no Android e iOS como um app nativo, com semáforos de controle semanal (VA, Uber, Comer Fora, Compras Online), faturas consolidadas por titular (Guto vs. Jé), acertos da Jé (dia 10/20), simulador da caixinha (30%), matriz panorâmica com drill-down modal interativo e lista de assinaturas ativas em ordem alfabética.
4. **Sincronização Direta no Google Drive (API v3):** Atualiza a planilha XLSX na nuvem diretamente via Service Account (`credentials.json`), preservando 100% da formatação e cores sem depender de macros ou Google Apps Script Webhooks.

---

## 📊 Estrutura Canônica das 18 Abas da Planilha

A planilha `Controle de Gastos 2026` é composta por 18 abas estruturadas:

1. **4 Abas Históricas Originais (100% Preservadas):**
   - `Orig - Total Anual`
   - `Orig - Abril`
   - `Orig - Maio`
   - `Orig - Julho`
   *(Mantêm estilos, fontes, larguras de coluna e cores originais da família)*.

2. **Aba Consolidada:**
   - `Total Anual`: 8 Seções Canônicas com 28 categorias em estrita ordem alfabética, somatórios e meses de Jan a Dez.

3. **12 Abas Mensais no Formato Original (Janeiro a Dezembro):**
   - Cada mês possui as 8 seções divididas nas 28 categorias em ordem alfabética;
   - Colunas diárias de 1 a 31 (`D` a `AH`) com somatório dinâmico em `=SUM(D:AH)`;
   - Tabela detalhada de auditoria de compras parceladas e assinaturas no rodapé de cada mês (linhas 45 a 90), detalhando data, estabelecimento, parcela atual/total e valor.

4. **Painel Gerencial:**
   - `Resumo & Metas 2026-2027`: Indicadores executivos, metas orçamentárias e equalizador de sobreaviso.

---

## 🏷️ As 8 Seções Canônicas (Ordem Alfabética de Categorias)

1. **FAMÍLIA**
   - 01. Alimentação Fora / Lazer Família
   - 02. Farmácia e Saúde Família
   - 03. Supermercado / Feira / Açougue (Total Zaffari)
   - 04. Viagens e Férias Família
2. **CLARA**
   - 05. Colégio Bom Conselho (Mensalidade e Boletos)
   - 06. Natação / Atividades Clara
   - 07. Vestuário / Material / Lazer Clara
3. **JÉ**
   - 08. Cartão Adicional Jé (Fatura 1229 / 4219 / 9994)
   - 09. Cursos / Pós-Graduação / Livros Jé
   - 10. Despesas Pessoais / Salão / Vestuário Jé
   - 11. Uber Jé
4. **GUTO**
   - 12. Cartão Titular Guto (Fatura 4110 / 2762 / Nubank)
   - 13. Cursos / Certificações / Livros Guto
   - 14. Despesas Pessoais / Barbeiro Guto
   - 15. Jogos / Games / Lazer Guto
   - 16. Uber Guto
5. **PETS**
   - 17. Veterinário, Ração e Cuidados Pets
6. **CASA**
   - 18. Aluguel / Condomínio / IPTU Casa
   - 19. Energia Elétrica (CEEE Equatorial)
   - 20. Internet Fibra / Telefonia
   - 21. Manutenção / Limpeza / Diarista
7. **PARCELAMENTO CARTÃO & ASSINATURAS**
   - 22. Assinaturas e Streaming (YouTube, Netflix, Prime, Kotas, etc.)
   - 23. Compras Parceladas em Andamento
   - 24. Financiamento / Empréstimos
8. **DESCONTOS EM FOLHA**
   - 25. IRPF Retido na Fonte
   - 26. INSS
   - 27. Plano de Saúde Unimed
   - 28. Previdência Privada / Outros Descontos

---

## 📁 Estrutura do Repositório

```text
sistema_financeiro/
├── .env                                   # Segredos locais (CASA_PIN, SENHA_PDF_99PAY - IGNORADO NO GIT)
├── .env.example                           # Modelo de configuração sem segredos
├── credentials.json                       # Chave Service Account Google Drive API (IGNORADO NO GIT)
├── Planilha_Controle_Financeiro_Original.xlsx # Template mestre com formatação original
├── sincronizar_tudo.bat                   # Script principal de execução em 5 etapas
├── docs/
│   └── ROADMAP_FASE2_BOT_TELEGRAM.md      # Planejamento do Bot Telegram para Fase 2
├── data/
│   └── consolidado_2026_2027.json         # Base unificada extraída (62 extratos, IGNORADO NO GIT)
├── src/
│   ├── config_regras.py                   # Tetos orçamentários, regras e cartões
│   ├── extrator_unificado.py              # Motor de extração (PDF, CSV, OFX, HTML) V3.0
│   ├── crypto_pwa.py                      # Cifrador WebCrypto AES-256-GCM + PBKDF2
│   ├── sync_google_sheets.py              # Gerador XLSX de 18 abas e uploader Google Drive API v3
│   ├── deploy_github_pages.py             # Publicador automático no GitHub e GitHub Pages
│   └── preview_local.py                   # Servidor de teste local (porta 8095)
├── web/                                   # PWA Estático para deploy
│   ├── index.html                         # Interface Mobile-First
│   ├── styles.css                         # CSS responsivo (Mobile e Desktop 1120px)
│   ├── app.js                             # Descriptografia WebCrypto e Drill-Down interativo
│   ├── payload.enc.json                   # Pacote Criptografado (publicável com segurança)
│   ├── manifest.json                      # PWA Manifesto
│   ├── sw.js                              # Service Worker offline
│   └── icon.svg                           # Ícone do App
└── tests/
    └── test_motor_financeiro.py           # Bateria de testes automatizados (pytest)
```

---

## 🚀 Como Executar a Sincronização Completa

Basta clicar duas vezes em `sincronizar_tudo.bat` na pasta raiz `C:\Dropbox\Controle_Financeiro` (ou dentro de `sistema_financeiro`).

O pipeline executará automaticamente as 5 etapas:
1. `[1/5] Extraindo e reconciliando extratos nas 8 Seções Canônicas (A-Z)...` (`python src\extrator_unificado.py`)
2. `[2/5] Criptografando cofre PWA com WebCrypto AES-256-GCM...` (`python src\crypto_pwa.py`)
3. `[3/5] Atualizando Planilha (18 Abas) no Google Drive via API v3...` (`python src\sync_google_sheets.py`)
4. `[4/5] Executando suíte de testes automatizados (pytest)...` (`python -m pytest tests\test_motor_financeiro.py -q`)
5. `[5/5] Publicando atualizações no GitHub e GitHub Pages...` (`python src\deploy_github_pages.py`)

---

## 🧪 Testes Automatizados

Para executar os testes a qualquer momento:
```bash
python -m pytest tests\test_motor_financeiro.py -q
```
Cobertura:
- Integridade do payload criptografado (`payload.enc.json`);
- Existência das chaves criptográficas (`salt`, `iv`, `ciphertext`);
- Tetos orçamentários e regras do casal;
- Formato e integridade do consolidado JSON.

---

## 🤖 Contexto para Futuras Sessões de IA

Se você for uma inteligência artificial iniciando uma nova sessão de pair programming ou manutenção deste projeto:
- **Dossiê Diagnóstico Estratégico:** Consulte [DIAGNOSTICO_E_PLANO_FINANCEIRO_2026_2027.md](../DIAGNOSTICO_E_PLANO_FINANCEIRO_2026_2027.md) na pasta pai para detalhes analíticos completos da vida financeira do casal, histórico de faturas, rendas, equalizador e decisões.
- **Histórico de Compras de Jogos:** Consulte [Historico_Jogos_Nintendo_eShop_2026.md](../Historico_Jogos_Nintendo_eShop_2026.md) para a lista de itens adquiridos na Nintendo eShop.
- **Isolamento:** Mantenha total separação em relação ao projeto Hermes/Caderno de Sonhos.
- **Pipeline Canônico:** Qualquer alteração deve ser validada rodando `sincronizar_tudo.bat` e garantindo que os 6 testes do `pytest` continuem passando 100%.
