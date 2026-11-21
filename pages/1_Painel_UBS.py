"""Painel da UBS: visão da unidade de saúde sobre o próprio estoque."""
import plotly.express as px
import streamlit as st

from src.regras import ORDEM_VALIDADE
from src.ui import COR_ESTOQUE, COR_VALIDADE, colorir, configurar_pagina, moeda, numero, resultados_de_hoje, rodape

configurar_pagina("Painel da UBS")

r = resultados_de_hoje()
lotes, resumo = r["lotes"], r["resumo"]

# ---------------- Filtros (barra lateral) ----------------
st.sidebar.header("🔍 Filtros")
ubs_nome = st.sidebar.selectbox("Unidade de Saúde", sorted(resumo["ubs"].unique()))
busca = st.sidebar.text_input("Buscar medicamento", placeholder="ex.: Losartana")

res_ubs = resumo[resumo["ubs"] == ubs_nome]
lot_ubs = lotes[lotes["ubs"] == ubs_nome]
if busca:
    res_ubs = res_ubs[res_ubs["medicamento"].str.contains(busca, case=False)]
    lot_ubs = lot_ubs[lot_ubs["medicamento"].str.contains(busca, case=False)]

em_falta = res_ubs[res_ubs["status_estoque"].isin(["Em falta", "Escasso"])].sort_values("cobertura_meses")
a_vencer = lot_ubs[lot_ubs["status_validade"].isin(["Crítico", "Atenção"])]
vencidos = lot_ubs[lot_ubs["status_validade"] == "Vencido"]

# ---------------- Cabeçalho e indicadores ----------------
st.title(f"🏥 {ubs_nome}")
st.caption("Situação do estoque de medicamentos da unidade")

c1, c2, c3, c4 = st.columns(4)
c1.metric("🔴 Em falta", int((res_ubs["status_estoque"] == "Em falta").sum()))
c2.metric("🟡 Escassos (< 1 mês)", int((res_ubs["status_estoque"] == "Escasso").sum()))
c3.metric("🟠 Lotes vencendo em 90 dias", len(a_vencer), help=f"Valor: {moeda(a_vencer['valor_total'].sum())}")
c4.metric("⚫ Valor em lotes vencidos", moeda(vencidos["valor_total"].sum()),
          help=f"{len(vencidos)} lote(s) vencido(s)")

# ---------------- Abas ----------------
aba1, aba2, aba3, aba4 = st.tabs(["🔴 Em falta / Escassos", "🟠 Perto de vencer", "⚫ Vencidos", "📦 Estoque completo"])

with aba1:
    if em_falta.empty:
        st.success("Nenhum medicamento em falta ou escasso nesta unidade. 🎉")
    else:
        st.write("Medicamentos sem estoque ou com menos de 1 mês de cobertura. "
                 "O **pedido sugerido** repõe o estoque para 2 meses de consumo.")
        tabela = em_falta[["medicamento", "status_estoque", "estoque_valido", "consumo_medio_mensal",
                           "cobertura_meses", "pedido_sugerido"]].rename(columns={
            "medicamento": "Medicamento", "status_estoque": "Situação", "estoque_valido": "Estoque válido",
            "consumo_medio_mensal": "Consumo/mês", "cobertura_meses": "Cobertura (meses)",
            "pedido_sugerido": "Pedido sugerido"})
        st.dataframe(
            tabela.style.map(colorir("Situação", COR_ESTOQUE), subset=["Situação"])
            .format({"Estoque válido": numero, "Consumo/mês": numero, "Pedido sugerido": numero,
                     "Cobertura (meses)": "{:.1f}"}),
            hide_index=True,
        )

with aba2:
    if a_vencer.empty:
        st.success("Nenhum lote vence nos próximos 90 dias.")
    else:
        st.write("Lotes que vencem nos próximos 90 dias. Use-os primeiro ou peça remanejamento à CAF.")
        tabela = a_vencer[["medicamento", "id_lote", "quantidade", "data_validade", "dias_para_vencer",
                           "status_validade", "valor_total"]].rename(columns={
            "medicamento": "Medicamento", "id_lote": "Lote", "quantidade": "Quantidade",
            "data_validade": "Validade", "dias_para_vencer": "Dias restantes",
            "status_validade": "Situação", "valor_total": "Valor"})
        st.dataframe(
            tabela.style.map(colorir("Situação", COR_VALIDADE), subset=["Situação"])
            .format({"Quantidade": numero, "Valor": moeda, "Validade": "{:%d/%m/%Y}"}),
            hide_index=True,
        )

with aba3:
    if vencidos.empty:
        st.success("Nenhum lote vencido nesta unidade.")
    else:
        st.error(f"{len(vencidos)} lote(s) vencido(s), totalizando **{moeda(vencidos['valor_total'].sum())}**. "
                 "Retire-os da dispensação e encaminhe para descarte.")
        tabela = vencidos[["medicamento", "id_lote", "quantidade", "data_validade", "dias_para_vencer",
                           "valor_total"]].copy()
        tabela["dias_para_vencer"] = -tabela["dias_para_vencer"]
        tabela = tabela.rename(columns={
            "medicamento": "Medicamento", "id_lote": "Lote", "quantidade": "Quantidade",
            "data_validade": "Venceu em", "dias_para_vencer": "Vencido há (dias)", "valor_total": "Valor perdido"})
        st.dataframe(
            tabela.style.format({"Quantidade": numero, "Valor perdido": moeda, "Venceu em": "{:%d/%m/%Y}"}),
            hide_index=True,
        )

with aba4:
    tabela = res_ubs[["medicamento", "status_estoque", "estoque_valido", "consumo_medio_mensal",
                      "cobertura_meses", "dias_lote_mais_proximo"]].sort_values("medicamento").rename(columns={
        "medicamento": "Medicamento", "status_estoque": "Situação", "estoque_valido": "Estoque válido",
        "consumo_medio_mensal": "Consumo/mês", "cobertura_meses": "Cobertura (meses)",
        "dias_lote_mais_proximo": "Lote mais próximo vence em (dias)"})
    st.dataframe(
        tabela.style.map(colorir("Situação", COR_ESTOQUE), subset=["Situação"])
        .format({"Estoque válido": numero, "Consumo/mês": numero, "Cobertura (meses)": "{:.1f}",
                 "Lote mais próximo vence em (dias)": "{:.0f}"}, na_rep="—"),
        hide_index=True,
    )

# ---------------- Gráficos ----------------
st.subheader("📊 Visão geral da unidade")
g1, g2 = st.columns(2)

with g1:
    por_validade = (lot_ubs.groupby("status_validade")["valor_total"].sum()
                    .reindex(ORDEM_VALIDADE, fill_value=0).reset_index())
    fig = px.bar(por_validade, x="status_validade", y="valor_total", color="status_validade",
                 color_discrete_map=COR_VALIDADE, title="Valor em estoque por situação de validade",
                 labels={"status_validade": "", "valor_total": "Valor (R$)"})
    fig.update_layout(showlegend=False, plot_bgcolor="white")
    st.plotly_chart(fig)

with g2:
    cobertura = res_ubs.sort_values("cobertura_meses").head(12)
    fig = px.bar(cobertura, x="cobertura_meses", y="medicamento", orientation="h", color="status_estoque",
                 color_discrete_map=COR_ESTOQUE, title="12 medicamentos com menor cobertura",
                 labels={"cobertura_meses": "Meses de estoque", "medicamento": "", "status_estoque": "Situação"})
    fig.add_vline(x=1, line_dash="dash", line_color="gray")
    fig.update_layout(plot_bgcolor="white", yaxis={"categoryorder": "total descending"})
    st.plotly_chart(fig)

rodape()
