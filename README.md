# 💰 FinControl Bot & Dashboard

> Sistema inteligente e seguro para gestão financeira pessoal com integração entre **Telegram Bot**, **Banco de Dados Relacional (SQLite)** e **Dashboard Web (Streamlit)** com suporte a relatórios em Excel e PDF.

---

## 📸 Visão Geral do Sistema

O **FinControl** foi desenvolvido para simplificar o registro e o acompanhamento de finanças pessoais de forma rápida e segura. A aplicação permite registrar gastos e receitas no dia a dia via comandos no Telegram e visualizar relatórios consolidados e indicadores em um painel web interativo.

### 🌟 Principais Funcionalidades

- 🤖 **Bot do Telegram com Menu Interativo:**
  - Lançamento rápido de despesas e receitas por texto (ex: `22.00 Almoço`).
  - Reconhecimento automático de **compras parceladas** via notação `(X/Y)` (ex: `60.00 Equipamento (9/10)`).
  - Menu com botões rápidos (*Inline Keyboards*) para consultar saldo, últimos gastos e compromissos futuros.
  - **Segurança & Whitelist:** Bloqueio de acesso para IDs não autorizados do Telegram.

- 📊 **Dashboard Web Interativo (Streamlit):**
  - Autenticação e seleção de usuário protegidas por senha.
  - **Isolamento de Dados:** Cada usuário visualiza estritamente os seus próprios lançamentos (`WHERE usuario_id = ?`).
  - Painel de métricas (Receitas, Despesas, Saldo Atual).
  - **Aba de Gestão de Cartões & Parcelas:** Cálculo automático do saldo devedor recluso e parcelas remanescentes.
  - Exportação nativa de relatórios em **Excel (`.xlsx`)** e **PDF (`.pdf`)**.

- 🔒 **Arquitetura Isolada & Pronta para Nuvem:**
  - Desenvolvido no **GitHub Codespaces** para evitar conflitos de variáveis de ambiente e dependências locais.
  - Banco de dados leve em arquivo **SQLite** gerenciado com chaves estrangeiras (`FOREIGN KEYS`).

---

## 🛠️ Tecnologias Utilizadas

- **Linguagem:** Python 3.12+
- **Banco de Dados:** SQLite3
- **Interface Web:** Streamlit
- **Integração Telegram:** `python-telegram-bot`
- **Análise & Manipulação de Dados:** Pandas
- **Geração de Relatórios:** FPDF2, OpenPyXL

---

## 📐 Estrutura do Banco de Dados (ER)

O banco de dados armazena os dados de forma relacional garantindo integridade referencial:

```text
  ┌──────────────────┐         ┌──────────────────┐
  │     usuarios     │         │    categorias    │
  ├──────────────────┤         ├──────────────────┤
  │ id (PK)          │         │ id (PK)          │
  │ telegram_id (UQ) │         │ nome             │
  │ nome             │         │ tipo             │
  └────────┬─────────┘         └────────┬─────────┘
           │                            │
           │ 1                        1 │
           │                            │
           │ N                        N │
  ┌────────┴────────────────────────────┴─────────┐
  │                  transacoes                   │
  ├───────────────────────────────────────────────┤
  │ id (PK)                                       │
  │ usuario_id (FK -> usuarios.id)                │
  │ categoria_id (FK -> categorias.id)            │
  │ valor                                         │
  │ tipo (RECEITA / DESPESA)                      │
  │ descricao                                     │
  │ data_transacao                                │
  └───────────────────────────────────────────────┘
