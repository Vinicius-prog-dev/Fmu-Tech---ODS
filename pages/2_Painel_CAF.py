"""Painel da CAF (Central de Abastecimento Farmacêutico) / Secretaria de Saúde."""
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from src.regras import ORDEM_ESTOQUE
from src.ui import CORES, COR_ESTOQUE, colorir, configurar_pagina, moeda, numero, resultados_de_hoje, rodape

configurar_pagina("Painel da CAF", "🏛️")

r = resultados_de_hoje()
resumo, remanej, pedido = r["resumo"], r["remanejamentos"], r["pedido"]

# ---------------- Filtros ----------------
st.sidebar.header("🔍 Filtros")
todas_ubs = sorted(resumo["ubs"].unique())
ubs_sel = st.sidebar.multiselect("UBSs", todas_ubs, default=todas_ubs)
so_criticos = st.sidebar.toggle("Mostrar só medicamentos com algum problema", value=True)

res = resumo[resumo["ubs"].isin(ubs_sel)]
rem = remanej[remanej["origem"].isin(ubs_sel) | remanej["destino"].isin(ubs_sel)]

# ---------------- Indicadores da rede ----------------
st.title("🏛️ Painel da CAF / Secretaria de Saúde")
st.caption("Visão de toda a rede: onde falta, onde sobra e onde está vencendo")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("🔴 Itens em falta", int((res["status_estoque"] == "Em falta").sum()),
          help="Pares UBS × medicamento sem estoque válido")
c2.metric("🟡 Itens escassos", int((res["status_estoque"] == "Escasso").sum()))
c3.metric("⚫ Perdido com vencidos", moeda(res["valor_vencido"].sum()))
c4.metric("🟠 Em risco de vencer", moeda(res["valor_em_risco"].sum()),
          help="Valor dos lotes que devem vencer antes de serem consumidos, no ritmo atual")
c5.metric("🔁 Economia com remanejamento", moeda(rem["perda_evitada"].sum()),
          help="Valor que deixa de vencer se as sugestões de remanejamento forem feitas")

# ---------------- Mapa de calor ----------------
st.subheader("🗺️ Mapa de situação: UBS × medicamento")
mapa = res.copy()
if so_criticos:
    com_problema = mapa.loc[mapa["status_estoque"].isin(["Em falta", "Escasso"]) | (mapa["qtd_vencida"] > 0),
                            "medicamento"].unique()
    mapa = mapa[mapa["medicamento"].isin(com_problema)]

if mapa.empty:
    st.info("Nenhum medicamento com problema para as UBSs selecionadas.")
else:
    codigo = {s: i for i, s in enumerate(ORDEM_ESTOQUE)}
    tabela = mapa.pivot(index="medicamento", columns="ubs", values="status_estoque")
    z = tabela.apply(lambda col: col.map(codigo))
    n = len(ORDEM_ESTOQUE)
    escala = []
    for i, s in enumerate(ORDEM_ESTOQUE):
        escala += [[i / n, COR_ESTOQUE[s]], [(i + 1) / n, COR_ESTOQUE[s]]]
    fig = go.Heatmap(
        z=z.values, x=z.columns, y=z.index, text=tabela.values, colorscale=escala,
        zmin=-0.5, zmax=n - 0.5, xgap=2, ygap=2,
        hovertemplate="%{y}<br>%{x}<br><b>%{text}</b><extra></extra>",
        colorbar={"tickvals": list(range(n)), "ticktext": ORDEM_ESTOQUE, "title": "Situação"},
    )
    figura = go.Figure(fig)
    figura.update_layout(height=max(350, 28 * len(z)), plot_bgcolor="white", margin={"l": 10, "r": 10, "t": 10})
    st.plotly_chart(figura)

# ---------------- Ranking das UBSs ----------------
st.subheader("🏥 Ranking de UBSs que precisam de atenção")
ranking = (
    res.groupby("ubs")
    .agg(em_falta=("status_estoque", lambda s: int((s == "Em falta").sum())),
         escassos=("status_estoque", lambda s: int((s == "Escasso").sum())),
         valor_vencido=("valor_vencido", "sum"),
         valor_em_risco=("valor_em_risco", "sum"))
    .reset_index()
)
ranking["pontuacao"] = ranking["em_falta"] * 3 + ranking["escassos"] * 2 + (ranking["valor_vencido"] > 0)
ranking = ranking.sort_values(["pontuacao", "valor_vencido"], ascending=False)

g1, g2 = st.columns([3, 2])
with g1:
    barras = ranking.melt(id_vars="ubs", value_vars=["valor_vencido", "valor_em_risco"],
                          var_name="tipo", value_name="valor")
    barras["tipo"] = barras["tipo"].map({"valor_vencido": "Já vencido", "valor_em_risco": "Vai vencer sem uso"})
    fig = px.bar(barras, x="ubs", y="valor", color="tipo", barmode="stack",
                 color_discrete_map={"Já vencido": CORES["vermelho"], "Vai vencer sem uso": CORES["ambar"]},
                 title="Desperdício por UBS (R$)", labels={"ubs": "", "valor": "R$", "tipo": ""})
    fig.update_layout(plot_bgcolor="white")
    st.plotly_chart(fig)
with g2:
    st.dataframe(
        ranking.drop(columns="pontuacao").rename(columns={
            "ubs": "UBS", "em_falta": "Em falta", "escassos": "Escassos",
            "valor_vencido": "Vencido (R$)", "valor_em_risco": "Em risco (R$)"})
        .style.format({"Vencido (R$)": moeda, "Em risco (R$)": moeda}),
        hide_index=True,
    )

# ---------------- Remanejamentos ----------------
st.subheader("🔁 Sugestões de remanejamento entre UBSs")
if rem.empty:
    st.success("Nenhum remanejamento necessário no momento.")
else:
    st.write(
        f"O sistema encontrou **{len(rem)} transferências** que atendem UBSs em falta usando sobras de outras "
        f"unidades, evitando **{moeda(rem['perda_evitada'].sum())}** em medicamentos vencidos."
    )
    st.dataframe(
        rem.drop(columns="co_catmat").rename(columns={
            "medicamento": "Medicamento", "origem": "De (origem)", "destino": "Para (destino)",
            "situacao_destino": "Situação do destino", "quantidade": "Quantidade",
            "valor_transferido": "Valor transferido", "perda_evitada": "Perda evitada", "motivo": "Motivo"})
        .style.map(colorir("Situação do destino", COR_ESTOQUE), subset=["Situação do destino"])
        .format({"Quantidade": numero, "Valor transferido": moeda, "Perda evitada": moeda}),
        hide_index=True,
    )
    st.download_button("⬇️ Baixar sugestões (CSV)", rem.to_csv(index=False).encode("utf-8-sig"),
                       "remanejamentos.csv", "text/csv")

# ---------------- Pedido de reposição ----------------
st.subheader("🚚 Pedido de reposição consolidado")
st.write("Quantidade que a CAF ainda precisa enviar (já descontando os remanejamentos) para que cada UBS "
         "fique com 2 meses de estoque. Custo estimado com o **preço mediano real do BPS 2026**.")
st.dataframe(
    pedido.drop(columns="co_catmat").rename(columns={
        "medicamento": "Medicamento", "preco_unitario": "Preço unitário (BPS)",
        "ubs_atendidas": "UBSs atendidas", "quantidade": "Quantidade", "custo_estimado": "Custo estimado"})
    .style.format({"Preço unitário (BPS)": "R$ {:.4f}", "Quantidade": numero, "Custo estimado": moeda}),
    hide_index=True,
)
st.metric("Custo total estimado da reposição", moeda(pedido["custo_estimado"].sum()))

rodape()
