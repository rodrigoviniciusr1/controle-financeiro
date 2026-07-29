import sqlite3
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# ⚠️ SUBSTITUA PELO SEU TOKEN GERADO NO BOTFATHER
TOKEN = '8883966144:AAGCQB9Wngj7lv-d5BdtSSZjcH4ZRuVfh5I'

# Função para registrar o usuário do Telegram na tabela 'usuarios'
def registrar_usuario(telegram_id, nome):
    conn = sqlite3.connect('controle_financeiro.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO usuarios (telegram_id, nome)
        VALUES (?, ?)
    ''', (telegram_id, nome))
    conn.commit()
    conn.close()

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    registrar_usuario(user.id, user.first_name)
    
    mensagem = (
        f"Olá, {user.first_name}! 👋\n\n"
        "Seu cadastro foi realizado com sucesso no Controle Financeiro.\n\n"
        "Para registrar um gasto ou receita, envie no formato:\n"
        "👉 `valor descricao`\n"
        "Exemplo: `45.50 Almoço`"
    )
    await update.message.reply_text(mensagem, parse_mode='Markdown')

# Função para processar e salvar transações digitadas
async def registrar_transacao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    partes = texto.split(' ', 1)

    # Verifica se o primeiro item digitado é um número válido (valor)
    try:
        valor = float(partes[0].replace(',', '.'))
        descricao = partes[1] if len(partes) > 1 else "Sem descrição"
    except ValueError:
        await update.message.reply_text("❌ Formato inválido! Envie o valor seguido da descrição.\nExemplo: `25.00 Uber`", parse_mode='Markdown')
        return

    telegram_id = update.effective_user.id

    conn = sqlite3.connect('controle_financeiro.db')
    cursor = conn.cursor()

    # Busca o ID do usuário no banco
    cursor.execute("SELECT id FROM usuarios WHERE telegram_id = ?", (telegram_id,))
    usuario = cursor.fetchone()

    if not usuario:
        await update.message.reply_text("Usuário não encontrado. Digite /start primeiro!")
        conn.close()
        return

    usuario_id = usuario[0]
    
    # Categoria padrão id=8 ('Outros') caso não especifique
    categoria_id = 8 
    tipo = 'DESPESA'

    # Insere a transação no banco de dados SQLite
    cursor.execute('''
        INSERT INTO transacoes (usuario_id, categoria_id, valor, tipo, descricao)
        VALUES (?, ?, ?, ?, ?)
    ''', (usuario_id, categoria_id, valor, tipo, descricao))

    conn.commit()
    conn.close()

    await update.message.reply_text(f"✅ Registrado com sucesso:\n💰 **Valor:** R$ {valor:.2f}\n📝 **Descrição:** {descricao}", parse_mode='Markdown')

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    # Handlers dos comandos e mensagens
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, registrar_transacao))

    print("🤖 Bot em execução no Telegram...")
    app.run_polling()