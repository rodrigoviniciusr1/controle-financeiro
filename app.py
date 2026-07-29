import sqlite3
import pandas as pd
import re
import streamlit as st
from fpdf import FPDF
from io import BytesIO

st.set_page_config(page_title="Controle Financeiro", page_icon="🔒", layout="wide")

# Senha global para acesso ao dashboard (pode alterar aqui)
SENHA_ACESSO = "123456"

def buscar_usuarios():
    conn = sqlite3.connect('controle_financeiro.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome FROM usuarios")
    usuarios = cursor.fetchall()
    conn.close()
    return usuarios

def carregar_dados_usuario(usuario_id):
    conn = sqlite3.connect('controle_financeiro.db')
    query = '''
        SELECT 
            t.id, 
            u.nome as usuario, 
            c.nome as categoria, 
            t.valor, 
            t.tipo, 
            t.descricao, 
            t.data_transacao 
        FROM transacoes t
        JOIN usuarios u ON t.usuario_id = u.id
        JOIN categorias c ON t.categoria_id = c.id
        WHERE t.usuario_id = ?
        ORDER BY t.data_transacao DESC
    '''
    df = pd.read_sql_query(query, conn, params=(usuario_id,))
    conn.close()
    return df

def extrair_info_parcelas(df):
    parcelas = []
    padrao = r'(\d+)/(\d+)'
    
    for _, row in df.iterrows():
        match = re.search(padrao, str(row['descricao']))
        if match:
            atual = int(match.group(1))
            total = int(match.group(2))
            restantes = total - atual
            valor_parcela = float(row['valor'])
            saldo_devedor = restantes * valor_parcela
            nome_limpo = re.sub(r'\s*\(\d+/\d+\)', '', row['descricao']).strip()
            
            parcelas.append({
                "Item": nome_limpo,
                "Valor Parcela (R$)": valor_parcela,
                "Parcela Atual": atual,
                "Total Parcelas": total,
                "Parcelas Faltantes": restantes,
                "Saldo Devedor Total (R$)": saldo_devedor
            })
            
    return pd.DataFrame(parcelas)

def gerar_pdf(df, nome_usuario):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=16, style='B')
    pdf.cell(200, 10, txt=f"Relatorio Financeiro - {nome_usuario}", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Helvetica", size=10, style='B')
    pdf.cell(30, 8, "Data", border=1)
    pdf.cell(40, 8, "Categoria", border=1)
    pdf.cell(30, 8, "Tipo", border=1)
    pdf.cell(30, 8, "Valor (R$)", border=1)
    pdf.cell(60, 8, "Descricao", border=1)
    pdf.ln()

    pdf.set_font("Helvetica", size=9)
    for _, row in df.iterrows():
        data_formatada = str(row['data_transacao'])[:10]
        pdf.cell(30, 8, data_formatada, border=1)
        pdf.cell(40, 8, str(row['categoria'])[:20], border=1)
        pdf.cell(30, 8, str(row['tipo']), border=1)
        pdf.cell(30, 8, f"{row['valor']:.2f}", border=1)
        pdf.cell(60, 8, str(row['descricao'])[:30], border=1)
        pdf.ln()

    return bytes(pdf.output())

# --- TELA DE AUTENTICAÇÃO E LOGIN ---
st.sidebar.title("🔐 Autenticação")

lista_usuarios = buscar_usuarios()

if not lista_usuarios:
    st.error("Nenhum usuário cadastrado no banco. Registre-se via Telegram rodando /start.")
else:
    opcoes_usuarios = {nome: user_id for user_id, nome in lista_usuarios}
    usuario_selecionado = st.sidebar.selectbox("Selecione o Usuário:", list(opcoes_usuarios.keys()))
    senha_digitada = st.sidebar.text_input("Senha de Acesso:", type="password")

    if senha_digitada == SENHA_ACESSO:
        st.sidebar.success(f"Conectado como: **{usuario_selecionado}**")
        usuario_id = opcoes_usuarios[usuario_selecionado]

        # Carrega estritamente os dados do usuário autenticado
        df = carregar_dados_usuario(usuario_id)

        st.title(f"📊 Painel Financeiro - {usuario_selecionado}")

        if df.empty:
            st.info("Nenhuma transação encontrada para este usuário.")
        else:
            aba_geral, aba_parcelamento = st.tabs(["📌 Visão Geral", "💳 Parcelas & Cartões"])

            with aba_geral:
                total_despesas = df[df['tipo'] == 'DESPESA']['valor'].sum()
                total_receitas = df[df['tipo'] == 'RECEITA']['valor'].sum()
                saldo = total_receitas - total_despesas

                c1, c2, c3 = st.columns(3)
                c1.metric("Total Receitas", f"R$ {total_receitas:.2f}")
                c2.metric("Total Despesas", f"R$ {total_despesas:.2f}")
                c3.metric("Saldo Atual", f"R$ {saldo:.2f}")

                st.markdown("---")

                col_esq, col_dir = st.columns([2, 1])
                with col_esq:
                    st.subheader("📋 Suas Transações")
                    st.dataframe(df[['data_transacao', 'categoria', 'tipo', 'valor', 'descricao']], use_container_width=True)

                with col_dir:
                    st.subheader("📈 Gastos por Categoria")
                    df_despesas = df[df['tipo'] == 'DESPESA']
                    if not df_despesas.empty:
                        gastos_cat = df_despesas.groupby('categoria')['valor'].sum()
                        st.bar_chart(gastos_cat)

                st.markdown("---")
                st.subheader("📥 Exportar Seus Dados")
                col_exp1, col_exp2 = st.columns(2)

                buffer_excel = BytesIO()
                with pd.ExcelWriter(buffer_excel, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Minhas_Transacoes')
                
                col_exp1.download_button(
                    label="📊 Baixar Excel (.xlsx)",
                    data=buffer_excel.getvalue(),
                    file_name=f"relatorio_{usuario_selecionado}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

                pdf_data = gerar_pdf(df, usuario_selecionado)
                col_exp2.download_button(
                    label="📄 Baixar PDF (.pdf)",
                    data=pdf_data,
                    file_name=f"relatorio_{usuario_selecionado}.pdf",
                    mime="application/pdf"
                )

            with aba_parcelamento:
                st.subheader("💳 Compras Parceladas")
                df_parcelas = extrair_info_parcelas(df)
                
                if df_parcelas.empty:
                    st.warning("Nenhuma compra parcelada cadastrada.")
                else:
                    total_comprometido = df_parcelas['Saldo Devedor Total (R$)'].sum()
                    
                    m1, m2 = st.columns(2)
                    m1.metric("Saldo Devedor Futuro Total", f"R$ {total_comprometido:.2f}")
                    m2.metric("Total de Itens Parcelados", f"{len(df_parcelas)}")

                    st.markdown("---")
                    st.dataframe(
                        df_parcelas,
                        column_config={
                            "Valor Parcela (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                            "Saldo Devedor Total (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                        },
                        use_container_width=True
                    )
                    st.bar_chart(df_parcelas.set_index("Item")["Saldo Devedor Total (R$)"])
    else:
        st.warning("⚠️ Digite a senha correta no menu lateral para visualizar o painel.")