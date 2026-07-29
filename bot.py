import sqlite3
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    ContextTypes, 
    MessageHandler, 
    CallbackQueryHandler,
    filters
)

# ⚠️ SEU TOKEN DO BOT
TOKEN = '8883966144:AAGCQB9Wngj7lv-d5BdtSSZjcH4ZRuVfh5I'

# 🔒 LISTA DE TELEGRAM IDs PERMITIDOS
USUARIOS_PERMITIDOS = [
    6768257537,  # Substitua pelo seu Telegram ID real
]

def usuario_autorizado(telegram_id):
    return telegram_id in USUARIOS_PERMITIDOS

def registrar_usuario(telegram_id, nome):
    conn = sqlite3.connect('controle_financeiro.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO usuarios (telegram_id, nome)
        VALUES (?, ?)
    ''', (telegram_id, nome))
    conn.commit()
    conn.close()

# --- FUNÇÃO DO MENU PRINCIPAL COM BOTÕES ---
def obter_menu_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("📊 Resumo do Mês", callback_data="resumo_mes"),
            InlineKeyboardButton("💳 Parcelas Pendentes", callback_data="parcelas")
        ],
        [
            InlineKeyboardButton("📋 Últimos 5 Gastos", callback_data="ultimos_gastos"),
            InlineKeyboardButton("❓ Como Registrar", callback_data="ajuda")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- COMANDOS E HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not usuario_autorizado(user.id):
        await update.message.reply_text("⛔ Acesso Negado!")
        return

    registrar_usuario(user.id, user.first_name)
    
    texto = (
        f"Olá, *{user.first_name}*! 👋\n\n"
        "Bem-vindo ao seu **Controle Financeiro**.\n"
        "Escolha uma das opções no menu abaixo ou simplesmente envie uma mensagem no formato `valor descrição` para registrar um gasto."
    )
    await update.message.reply_text(texto, reply_markup=obter_menu_keyboard(), parse_mode='Markdown')

async def menu_comando(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not usuario_autorizado(user.id):
        return
    await update.message.reply_text("📱 **Menu Principal:**", reply_markup=obter_menu_keyboard(), parse_mode='Markdown')

# --- LÓGICA DE RESPOSTA AOS BOTÕES (CALLBACK QUERIES) ---

async def tratar_botoes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() # Confirma a recepção do clique
    
    user_id = query.from_user.id
    opcao = query.data

    conn = sqlite3.connect('controle_financeiro.db')
    cursor = conn.cursor()

    # Busca ID interno do usuário
    cursor.execute("SELECT id FROM usuarios WHERE telegram_id = ?", (user_id,))
    res = cursor.fetchone()
    if not res:
        await query.edit_message_text("Usuário não encontrado. Digite /start")
        conn.close()
        return
    usuario_id = res[0]

    if opcao == "resumo_mes":
        cursor.execute('''
            SELECT tipo, SUM(valor) 
            FROM transacoes 
            WHERE usuario_id = ? 
            GROUP BY tipo
        ''', (usuario_id,))
        totais = dict(cursor.fetchall())
        
        receitas = totais.get('RECEITA', 0.0)
        despesas = totais.get('DESPESA', 0.0)
        saldo = receitas - despesas

        resposta = (
            "📊 **Resumo Financeiro Geral:**\n\n"
            f"🟢 **Receitas:** R$ {receitas:.2f}\n"
            f"🔴 **Despesas:** R$ {despesas:.2f}\n"
            f"💰 **Saldo:** R$ {saldo:.2f}"
        )
        await query.message.reply_text(resposta, reply_markup=obter_menu_keyboard(), parse_mode='Markdown')

    elif opcao == "ultimos_gastos":
        cursor.execute('''
            SELECT valor, descricao, data_transacao 
            FROM transacoes 
            WHERE usuario_id = ? AND tipo = 'DESPESA'
            ORDER BY id DESC LIMIT 5
        ''', (usuario_id,))
        registros = cursor.fetchall()

        if not registros:
            resposta = "📋 Nenhum gasto registrado ainda."
        else:
            resposta = "📋 **Últimos 5 Gastos:**\n\n"
            for val, desc, data in registros:
                dt_f = data[:10]
                resposta += f"• `{dt_f}` | R$ {val:.2f} - *{desc}*\n"

        await query.message.reply_text(resposta, reply_markup=obter_menu_keyboard(), parse_mode='Markdown')

    elif opcao == "parcelas":
        cursor.execute('''
            SELECT valor, descricao 
            FROM transacoes 
            WHERE usuario_id = ? AND descricao LIKE '%/%'
        ''', (usuario_id,))
        registros = cursor.fetchall()

        saldo_devedor_total = 0.0
        linhas_parcelas = []

        padrao = r'(\d+)/(\d+)'
        for val, desc in registros:
            match = re.search(padrao, desc)
            if match:
                atual = int(match.group(1))
                total = int(match.group(2))
                restantes = total - atual
                saldo_item = restantes * val
                saldo_devedor_total += saldo_item
                linhas_parcelas.append(f"• *{desc}*: {restantes}x de R$ {val:.2f} (Restante: R$ {saldo_item:.2f})")

        if not linhas_parcelas:
            resposta = "💳 Nenhuma compra parcelada encontrada."
        else:
            resposta = "💳 **Compras Parceladas Pendentes:**\n\n" + "\n".join(linhas_parcelas)
            resposta += f"\n\n🚨 **Saldo Devedor Futuro Total:** R$ {saldo_devedor_total:.2f}"

        await query.message.reply_text(resposta, reply_markup=obter_menu_keyboard(), parse_mode='Markdown')

    elif opcao == "ajuda":
        resposta = (
            "❓ **Como registrar lançamentos:**\n\n"
            "• **Gasto comum:** `22.00 Almoço`\n"
            "• **Gasto parcelado:** `60.00 Kabum (9/10)`\n"
            "• **Receita/Ganho:** Para cadastrar como receita, adicione via Dashboard web."
        )
        await query.message.reply_text(resposta, reply_markup=obter_menu_keyboard(), parse_mode='Markdown')

    conn.close()

# --- REGISTRO DE TRANSAÇÕES VIA MENSAGEM DE TEXTO ---

async def registrar_transacao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not usuario_autorizado(user.id):
        await update.message.reply_text("⛔ Acesso Negado!")
        return

    texto = update.message.text.strip()
    partes = texto.split(' ', 1)

    try:
        valor = float(partes[0].replace(',', '.'))
        descricao = partes[1] if len(partes) > 1 else "Sem descrição"
    except ValueError:
        await update.message.reply_text("❌ Formato inválido! Envie: `valor descricao` ou use o /menu", parse_mode='Markdown')
        return

    conn = sqlite3.connect('controle_financeiro.db')
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM usuarios WHERE telegram_id = ?", (user.id,))
    usuario = cursor.fetchone()

    if not usuario:
        await update.message.reply_text("Digite /start para se cadastrar.")
        conn.close()
        return

    usuario_id = usuario[0]
    categoria_id = 8  # Categoria "Outros"
    tipo = 'DESPESA'

    cursor.execute('''
        INSERT INTO transacoes (usuario_id, categoria_id, valor, tipo, descricao)
        VALUES (?, ?, ?, ?, ?)
    ''', (usuario_id, categoria_id, valor, tipo, descricao))

    conn.commit()
    conn.close()

    await update.message.reply_text(
        f"✅ Registrado com sucesso:\n💰 R$ {valor:.2f}\n📝 {descricao}",
        reply_markup=obter_menu_keyboard()
    )

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu_comando))
    app.add_handler(CallbackQueryHandler(tratar_botoes))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, registrar_transacao))

    print("🤖 Bot com Menu Interativo rodando...")
    app.run_polling()