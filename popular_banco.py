import sqlite3

def atualizar_dados():
    conn = sqlite3.connect('controle_financeiro.db')
    cursor = conn.cursor()

    # 1. Habilitar suporte a chaves estrangeiras
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 2. Limpar dados anteriores (deleta transações de teste e usuários)
    cursor.execute("DELETE FROM transacoes;")
    cursor.execute("DELETE FROM usuarios;")
    # Reseta os autoincrementos do SQLite
    cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('transacoes', 'usuarios');")

    print("🧹 Dados de teste anteriores removidos com sucesso!")

    # 3. Criar usuário padrão (Rodrigo)
    cursor.execute("INSERT INTO usuarios (telegram_id, nome) VALUES (?, ?)", (12345678, 'Rodrigo'))
    usuario_id = cursor.lastrowid

    # Mapeamento de categorias padrão
    cursor.execute("SELECT id, nome FROM categorias")
    categorias_dict = {nome: cat_id for cat_id, nome in cursor.fetchall()}

    # Lista com todos os seus gastos da imagem
    gastos = [
        # Parcelados
        ("Kabum Equipamentos (9/10)", 60.00, "DESPESA", "Outros"),
        ("Pré-treino (1/2)", 44.88, "DESPESA", "Saúde"),
        ("Jogo Monster Hunter (1/2)", 22.00, "DESPESA", "Lazer"),
        ("Ventilador (2/4)", 27.00, "DESPESA", "Moradia"),
        ("Presente Afilhado (3/5)", 54.65, "DESPESA", "Outros"),
        ("SmartWatch (5/7)", 50.70, "DESPESA", "Outros"),
        ("Cadeira de Escritório (2/10)", 79.00, "DESPESA", "Moradia"),
        
        # Custos Fixos
        ("Aluguel", 500.00, "DESPESA", "Moradia"),
        ("Alimentação", 400.00, "DESPESA", "Alimentação"),
        ("Energia", 110.00, "DESPESA", "Moradia"),
        ("Academia", 95.00, "DESPESA", "Saúde"),
        ("Internet", 55.00, "DESPESA", "Moradia"),
        ("Água", 44.00, "DESPESA", "Moradia"),
        
        # Meta / Investimento
        ("Reserva Casamento", 92.00, "RECEITA", "Investimentos")
    ]

    # 4. Inserir os novos lançamentos no banco
    for descricao, valor, tipo, nome_categoria in gastos:
        cat_id = categorias_dict.get(nome_categoria, categorias_dict['Outros'])
        cursor.execute('''
            INSERT INTO transacoes (usuario_id, categoria_id, valor, tipo, descricao)
            VALUES (?, ?, ?, ?, ?)
        ''', (usuario_id, cat_id, valor, tipo, descricao))

    conn.commit()
    conn.close()
    print("✅ Novos lançamentos cadastrados com sucesso no SQLite!")

if __name__ == '__main__':
    atualizar_dados()