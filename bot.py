import sqlite3
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# ⚠️ SEU TOKEN DO BOT
TOKEN = '8883966144:AAGCQB9Wngj7lv-d5BdtSSZjcH4ZRuVfh5I'

# 🔒 LISTA DE TELEGRAM IDs PERMITIDOS (Adicione o seu ID numérico e o de quem mais tiver acesso)
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Validação de Segurança
    if not usuario_autorizado(user.id):
        await update.message.reply_text("⛔ Acesso Negado! Você não tem permissão para utilizar este bot.")
        return

    registrar_usuario(user.id, user.first_name)
    
    mensagem = (
        f"Olá, {user.first_name}! 👋\n\n"
        "Seu acesso foi validado no Controle Financeiro.\n\n"
        "Envie lançamentos no formato:\n"
        "👉 `valor descricao`\n"
        "Exemplo: `45.50 Almoço`\n"
        "Exemplo parcelado: `60.00 Equipamento (1/10)`"
    )
    await update.message.reply_text(mensagem, parse_mode='Markdown')

async def registrar_transacao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Validação de Segurança
    if not usuario_autorizado(user.id):
        await update.message.reply_text("⛔ Acesso Negado!")
        return

    texto = update.message.text.strip()
    partes = texto.split(' ', 1)

    try:
        valor = float(partes[0].replace(',', '.'))
        descricao = partes[1] if len(partes) > 1 else "Sem descrição"
    except ValueError:
        await update.message.reply_text("❌ Formato inválido! Envie: `valor descricao`", parse_mode='Markdown')
        return

    conn = sqlite3.connect('controle_financeiro.db')
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM usuarios WHERE telegram_id = ?", (user.id,))
    usuario = cursor.fetchone()

    if not usuario:
        await update.message.reply_text("Digite /start para se cadastrar primeiro.")
        conn.close()
        return

    usuario_id = usuario[0]
    categoria_id = 8  # Outros
    tipo = 'DESPESA'

    cursor.execute('''
        INSERT INTO transacoes (usuario_id, categoria_id, valor, tipo, descricao)
        VALUES (?, ?, ?, ?, ?)
    ''', (usuario_id, categoria_id, valor, tipo, descricao))

    conn.commit()
    conn.close()

    await update.message.reply_text(f"✅ Registrado para {user.first_name}:\n💰 R$ {valor:.2f}\n📝 {descricao}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, registrar_transacao))

    print("🤖 Bot seguro em execução no Telegram...")
    app.run_polling()