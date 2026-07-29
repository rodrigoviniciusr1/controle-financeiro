import sqlite3

conn = sqlite3.connect('controle_financeiro.db')
cursor = conn.cursor()

# 1. Descobrir os IDs internos dos dois registros
cursor.execute("SELECT id FROM usuarios WHERE telegram_id = 6768257537")
user_real = cursor.fetchone()

cursor.execute("SELECT id FROM usuarios WHERE nome = 'Rodrigo' AND telegram_id != 6768257537")
user_antigo = cursor.fetchone()

if user_real and user_antigo:
    id_real = user_real[0]
    id_antigo = user_antigo[0]

    # 2. Transferir todas as transações do ID antigo para o ID real
    cursor.execute("UPDATE transacoes SET usuario_id = ? WHERE usuario_id = ?", (id_real, id_antigo))
    
    # 3. Remover o usuário antigo para não deixar sujeira no banco
    cursor.execute("DELETE FROM usuarios WHERE id = ?", (id_antigo,))
    
    conn.commit()
    print("✅ Sucesso! Lançamentos transferidos para a sua conta real do Telegram.")

elif user_real and not user_antigo:
    print("ℹ️ As transações já estão vinculadas ao seu Telegram ID real!")

else:
    print("⚠️ Registro não encontrado. Digite /start no bot do Telegram primeiro.")

conn.close()