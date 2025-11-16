
# Imports
import pandas as pd
import streamlit as st
import numpy as np

from datetime import datetime
from PIL import Image
from io import BytesIO


# -----------------------------
# CACHE
# -----------------------------
@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')


@st.cache_data
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    processed_data = output.getvalue()
    return processed_data


# -----------------------------
# FUNÇÕES DE SEGMENTAÇÃO RFV
# -----------------------------
def recencia_class(x, r, q_dict):
    if x <= q_dict[r][0.25]:
        return 'A'
    elif x <= q_dict[r][0.50]:
        return 'B'
    elif x <= q_dict[r][0.75]:
        return 'C'
    else:
        return 'D'


def freq_val_class(x, fv, q_dict):
    if x <= q_dict[fv][0.25]:
        return 'D'
    elif x <= q_dict[fv][0.50]:
        return 'C'
    elif x <= q_dict[fv][0.75]:
        return 'B'
    else:
        return 'A'


# -----------------------------
# APLICAÇÃO STREAMLIT
# -----------------------------
def main():
    st.set_page_config(
        page_title='RFV',
        layout="wide",
        initial_sidebar_state='expanded'
    )

    st.title("RFV - Segmentação de Clientes")

    st.write("""
    O método RFV (Recência, Frequência e Valor) é usado para entender o comportamento dos clientes e segmentá-los
    para ações de CRM, marketing e retenção.
    """)

    st.markdown("---")

    # UPLOAD DO ARQUIVO
    st.sidebar.write("## Suba o arquivo")
    data_file_1 = st.sidebar.file_uploader(
        "Selecione o arquivo", type=['csv', 'xlsx']
    )

    # -----------------------------
    # PROCESSAMENTO DO ARQUIVO
    # -----------------------------
    if data_file_1 is not None:

        try:
            # CSV ou Excel automaticamente
            df_compras = pd.read_csv(data_file_1, parse_dates=['DiaCompra'])
        except:
            df_compras = pd.read_excel(data_file_1, parse_dates=['DiaCompra'])

        # -----------------------------
        # RECÊNCIA
        # -----------------------------
        st.write("## Recência (R)")

        dia_atual = df_compras['DiaCompra'].max()
        st.write("Dia mais recente:", dia_atual)

        df_recencia = (
            df_compras.groupby('ID_cliente')['DiaCompra']
            .max()
            .reset_index()
            .rename(columns={'DiaCompra': 'DiaUltimaCompra'})
        )

        df_recencia['Recencia'] = (dia_atual - df_recencia['DiaUltimaCompra']).dt.days
        df_recencia.drop('DiaUltimaCompra', axis=1, inplace=True)

        st.write(df_recencia.head())

        # -----------------------------
        # FREQUÊNCIA
        # -----------------------------
        st.write("## Frequência (F)")

        df_frequencia = (
            df_compras.groupby('ID_cliente')['CodigoCompra']
            .count()
            .reset_index()
            .rename(columns={'CodigoCompra': 'Frequencia'})
        )

        st.write(df_frequencia.head())

        # -----------------------------
        # VALOR
        # -----------------------------
        st.write("## Valor (V)")

        df_valor = (
            df_compras.groupby('ID_cliente')['ValorTotal']
            .sum()
            .reset_index()
            .rename(columns={'ValorTotal': 'Valor'})
        )

        st.write(df_valor.head())

        # -----------------------------
        # TABELA RFV FINAL
        # -----------------------------
        st.write("## Tabela RFV Final")

        df_RFV = (
            df_recencia
            .merge(df_frequencia, on='ID_cliente')
            .merge(df_valor, on='ID_cliente')
        )

        df_RFV.set_index('ID_cliente', inplace=True)
        st.write(df_RFV.head())

        # -----------------------------
        # SEGMENTAÇÃO
        # -----------------------------
        st.write("## Segmentação RFV")

        quartis = df_RFV.quantile(q=[0.25, 0.5, 0.75])

        df_RFV['R_quartil'] = df_RFV['Recencia'].apply(
            recencia_class, args=('Recencia', quartis)
        )
        df_RFV['F_quartil'] = df_RFV['Frequencia'].apply(
            freq_val_class, args=('Frequencia', quartis)
        )
        df_RFV['V_quartil'] = df_RFV['Valor'].apply(
            freq_val_class, args=('Valor', quartis)
        )

        df_RFV['RFV_Score'] = (
            df_RFV['R_quartil']
            + df_RFV['F_quartil']
            + df_RFV['V_quartil']
        )

        st.write(df_RFV.head())

        st.write("### Quantidade por grupo")
        st.write(df_RFV['RFV_Score'].value_counts())

        # -----------------------------
        # AÇÕES DE MARKETING
        # -----------------------------
        st.write("### Ações de Marketing sugeridas")

        dict_acoes = {
            'AAA': 'Enviar cupons de desconto. Priorizar este cliente.',
            'DDD': 'Cliente de baixo valor. Não priorizar ações.',
            'DAA': 'Cliente valioso que sumiu. Enviar cupom de recuperação.',
            'CAA': 'Cliente quase perdido de alto valor. Ação urgente.'
        }

        df_RFV['Acoes'] = df_RFV['RFV_Score'].map(dict_acoes)

        st.write(df_RFV.head())

        # -----------------------------
        # DOWNLOAD DO EXCEL
        # -----------------------------
        df_xlsx = to_excel(df_RFV)

        st.download_button(
            label="📥 Download da Tabela RFV",
            data=df_xlsx,
            file_name="RFV_resultado.xlsx"
        )

        st.write("### Ações por categoria")
        st.write(df_RFV['Acoes'].value_counts(dropna=False))


if __name__ == '__main__':
    main()
    









