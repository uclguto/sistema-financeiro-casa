# 🤖 Roadmap Fase 2: Bot Telegram Financeiro Doméstico ("Hermes Casa")

> **Status:** Documentado para Implementação Futura (Pós-Validação do PWA)  
> **Objetivo:** Permitir lançamentos rápidos por texto/áudio e alertas proativos no Telegram para Guto e Jéssica, mantendo isolamento total em relação aos bots clínicos e de gestão do Hermes.

---

## 1. Por Que Adiar o Bot para a Fase 2?
Conforme alinhado com o Guto:
> *"Pela minha experiência, o bot vai dar trabalho até deixar 100% funcional. Vamos começar apenas com a página baixável como app para visualizar a situação atual e controlar. Deixe a proposta no app em um plano pro futuro."*

O PWA Mobile estático com criptografia AES-256-GCM entrega **100% da visualização, semáforos em tempo real, calculadoras e controle** imediatamente, sem risco de downtime, conflito de polling ou despesas de servidor.

---

## 2. Arquitetura Proposta para a Fase 2

### 2.1. Princípio de Isolamento Estrito
- **Token Dedicado Exclusivo:** Um novo bot criado no `@BotFather` (ex.: `@GutoJeCasaBot`).
- **NÃO rodar na VPS Prod:** Para evitar qualquer interferência com `@AssistenteJornadaProdBot` ou `@hermes_gestao_ops_bot`.
- **Hospedagem Leve:** Pode rodar em container Docker isolado, Cloudflare Worker (via Webhook) ou como serviço systemd secundário com usuário restrito.

### 2.2. Funcionalidades Planejadas
1. **Lançamento Rápido via Prosa Falada ou Escrita:**
   - Exemplo Guto: *"Almoço no Baru 142 reais no cartão Banrisul"* -> Parser extrai categoria (`Comer Fora`), valor (`R$ 142,00`), cartão (`4110`) e atualiza o semáforo semanal.
   - Exemplo Jé: *"Recebi 250 da paciente Mariana no Pix"* -> Bot responde:
     ```text
     ✅ Consulta registrada: R$ 250,00!
     💰 Guardar na Caixinha (30%): R$ 75,00
     💳 Livre para consultório: R$ 175,00
     ```
2. **Alertas Proativos de Semáforo (Quinta e Sexta-feira):**
   - *"Atenção Guto: Comer fora já atingiu R$ 210 dos R$ 250 da semana! Restam R$ 40 para o fim de semana."*
   - *"Lembrete Jé: Hoje é dia 09. O boleto do colégio da Clara vence amanhã (R$ 1.340,00)."*
3. **Comando `/resumo` e `/fatura`:**
   - Mostra o fechamento previsto do mês e os tetos em barras de progresso ASCII.
