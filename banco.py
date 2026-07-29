import sqlite3

def inicializar_banco():
    # Conecta ou cria o arquivo do banco SQLite na pasta do projeto
    conn = sqlite3.connect('controle_financeiro.db')
    cursor = conn.cursor()

    # Habilita suporte a chaves estrangeiras no SQLite
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Cria as tabelas de Usuários, Categorias e Transações
    cursor.executescript('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER UNIQUE NOT NULL,
        nome TEXT NOT NULL,
        criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS categorias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        tipo TEXT CHECK(tipo IN ('RECEITA', 'DESPESA')) NOT NULL
    );

    CREATE TABLE IF NOT EXISTS transacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL,
        categoria_id INTEGER NOT NULL,
        valor REAL NOT NULL,
        tipo TEXT CHECK(tipo IN ('RECEITA', 'DESPESA')) NOT NULL,
        descricao TEXT,
        data_transacao DATETIME DEFAULT CURRENT_TIMESTAMP,
        criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
        FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE RESTRICT
    );
    ''')

    # Insere categorias padrão caso a tabela esteja vazia
    cursor.execute("SELECT COUNT(*) FROM categorias")
    if cursor.fetchone()[0] == 0:
        categorias_padrao = [
            ('Alimentação', 'DESPESA'),
            ('Transporte', 'DESPESA'),
            ('Moradia', 'DESPESA'),
            ('Lazer', 'DESPESA'),
            ('Saúde', 'DESPESA'),
            ('Salário', 'RECEITA'),
            ('Investimentos', 'RECEITA'),
            ('Outros', 'DESPESA')
        ]
        cursor.executemany("INSERT INTO categorias (nome, tipo) VALUES (?, ?)", categorias_padrao)
        print("Categorias padrão inseridas com sucesso!")

    conn.commit()
    conn.close()
    print("Banco de dados 'controle_financeiro.db' criado com sucesso!")

if __name__ == '__main__':
    inicializar_banco()