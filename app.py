"""
Estoque Vital - tela inicial.

Rodar localmente:
    pip install -r requirements.txt
    streamlit run app.py
"""
import streamlit as st

from src.ui import CORES, configurar_pagina, moeda, resultados_de_hoje, rodape

configurar_pagina("Início")

col_logo, col_texto = st.columns([1, 2], vertical_alignment="center")
with col_logo:
    st.image("assets/logo.jpeg")
with col_texto:
    st.title("Estoque Vital")
    st.markdown(
        "#### Gestão inteligente de medicamentos na Atenção Básica\n"
        "Painéis que mostram **o que está faltando**, **o que está para vencer** e **o que já venceu** "
        "nas Unidades Básicas de Saúde, e sugerem **remanejamentos entre UBSs** para evitar "
        "desperdício e desabastecimento. Projeto alinhado ao **ODS 3 – Saúde e Bem-Estar**."
    )

r = resultados_de_hoje()
resumo = r["resumo"]

st.subheader("Rede municipal hoje (cidade piloto: Porto Alegre)")
c1, c2, c3, c4 = st.columns(4)
c1.metric("UBSs monitoradas", resumo["id_ubs"].nunique())
c2.metric("Medicamentos monitorados", resumo["co_catmat"].nunique())
c3.metric("🔴 Itens em falta na rede", int((resumo["status_estoque"] == "Em falta").sum()))
c4.metric("💸 Perdido com vencidos", moeda(resumo["valor_vencido"].sum()))

st.subheader("Escolha o seu perfil")
p1, p2 = st.columns(2)
with p1:
    with st.container(border=True):
        st.markdown(f"### <span style='color:{CORES['azul']}'>🏥 Painel da UBS</span>", unsafe_allow_html=True)
        st.write("Para o farmacêutico ou gestor da unidade: medicamentos em falta, lotes perto do "
                 "vencimento, lotes vencidos e o pedido sugerido de reposição.")
        st.page_link("pages/1_Painel_UBS.py", label="Abrir Painel da UBS", icon="➡️")
with p2:
    with st.container(border=True):
        st.markdown(f"### <span style='color:{CORES['azul']}'>🏛️ Painel da CAF / Secretaria</span>",
                    unsafe_allow_html=True)
        st.write("Para a Central de Abastecimento Farmacêutico: quais UBSs estão com escassez ou com "
                 "vencidos, sugestões de remanejamento e o pedido consolidado de reposição.")
        st.page_link("pages/2_Painel_CAF.py", label="Abrir Painel da CAF", icon="➡️")

with st.expander("Como funcionam os alertas?"):
    st.markdown(
        """
| Alerta | Regra |
|---|---|
| 🔴 **Em falta** | Nenhuma unidade dentro da validade |
| 🟡 **Escasso** | Estoque válido cobre menos de 1 mês de consumo |
| 🟠 **Vencimento crítico** | Lote vence em até 30 dias |
| 🟡 **Atenção** | Lote vence entre 31 e 90 dias |
| ⚫ **Vencido** | Lote passou da validade: retirar e descartar |
| 🔁 **Remanejar** | Uma UBS tem sobra (ou lote que venceria sem uso) e outra está em falta |
"""
    )

rodape()
