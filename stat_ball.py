# app.py
"""
StatBall v4 - Estatística Esportiva (Gols, Escanteios, Cartões, Impedimentos)
- Tabelas 0..10
- Gráficos P(X >= 5) (pizza)
- Botões: calcular P(A > B) por evento
- Aba de Comentários / Interpretação objetiva
- Estética vibrante com hover (aura amarelo / verde)
Desenvolvido por Juan Santos — Versão 4 - Tecnologia ZIP4 Computers
"""
import streamlit as st
import numpy as np
import pandas as pd
from scipy.stats import poisson
import plotly.express as px

# ----------------------- Page config -----------------------
st.set_page_config(page_title="StatBall v4", page_icon="🏆", layout="wide")

# ----------------------- Theme CSS (cores vibrantes + hover aura) -----------------------
st.markdown(
    """
    <style>
    :root{
      --emerald: #0FA37F;
      --accent: #2BB673;
      --dourado: #C9A516;
      --muted: #5f6b6b;
      --bg: #f4fbf9;
      --deep: #062926;
    }
    body { background-color: var(--bg); color: var(--deep); }
    h1,h2,h3 { color: var(--emerald); }
    .stButton>button {
        background-color: var(--emerald);
        color: white;
        border-radius:8px;
        padding:0.45rem 0.8rem;
        border: 2px solid var(--dourado);
        font-weight:700;
        box-shadow: 0 4px 10px rgba(15,163,127,0.08);
        transition: all 0.18s ease-in-out;
    }
    .stButton>button:hover {
        background-color: var(--dourado);
        color: var(--deep);
        transform: translateY(-2px);
        box-shadow: 0 8px 22px rgba(201,165,22,0.15), 0 0 18px rgba(11,42,38,0.05);
        border-color: var(--emerald);
    }
    /* special smaller secondary buttons (outline) */
    .btn-outline {
        background-color: transparent !important;
        color: var(--emerald) !important;
        border: 2px dashed var(--emerald) !important;
        font-weight:700;
    }
    .btn-outline:hover {
        background-color: rgba(15,163,127,0.06) !important;
        color: var(--deep) !important;
        border-color: var(--dourado) !important;
        box-shadow: 0 6px 18px rgba(11,42,38,0.06), 0 0 20px rgba(201,165,22,0.08);
    }

    .small-muted { font-size:12px; color: var(--muted); }
    .footer { font-size:13px; color:#444; padding-top:12px; padding-bottom:12px; border-top:1px solid #e6e6e6; text-align:center; }
    .card { background: white; border-radius:10px; padding:12px; box-shadow: 0 6px 18px rgba(11,42,38,0.03); }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------- Helper functions -----------------------
def poisson_probs(mu, k_max=10):
    ks = np.arange(0, k_max + 1)
    pmf = poisson.pmf(ks, mu)
    pmf_pct = np.round(pmf * 100, 4)
    cdf_pct = np.round(np.cumsum(pmf) * 100, 4)
    return ks, pmf_pct, cdf_pct

def make_event_table(mu):
    ks, pmf_pct, cdf_pct = poisson_probs(mu, 10)
    df = pd.DataFrame({
        "k": ks,
        "P(X=k) (%)": pmf_pct,
        "P(X ≤ k) (%)": cdf_pct
    })
    return df

def prob_at_least_k(mu, k=5):
    return 1 - poisson.cdf(k-1, mu)

def prob_A_greater_B(muA, muB, k_max=60):
    # Efficiently compute P(A > B) summing over k of A * P(B < k)
    ks = np.arange(0, k_max+1)
    pmfA = poisson.pmf(ks, muA)
    cdfB_less = poisson.cdf(ks-1, muB)  # P(B < k)
    prob = np.sum(pmfA * cdfB_less)
    return prob

# ----------------------- UI Header -----------------------
col1, col2 = st.columns([0.82, 0.18])
with col1:
    st.title("🏆 StatBall v4 — Análise Estatística Esportiva")
    st.markdown("**Eventos modelados:** Gols • Escanteios • Cartões • Impedimentos (Poisson). Visualize P(X=k) 0→10, P(X ≥ 5) por evento e compare Times (P(A > B)).")
with col2:
    logo = st.file_uploader("Upload logo (opcional)", type=["png","jpg","jpeg"])

st.divider()

# ----------------------- Sidebar inputs -----------------------
st.sidebar.header("📥 Entradas — Dados dos Times")
time_a = st.sidebar.text_input("Nome do Time A", "Time A")
time_b = st.sidebar.text_input("Nome do Time B", "Time B")

st.sidebar.markdown("---")
st.sidebar.subheader(f"{time_a} — médias (históricas)")
total_matches_a = st.sidebar.number_input("Total jogos (A)", min_value=1, max_value=1000, value=20, step=1)
media_gols_a = st.sidebar.number_input("⚽ Média de Gols (A)", min_value=0.0, max_value=10.0, value=1.8, step=0.1)
media_esc_a = st.sidebar.number_input("🚩 Média de Escanteios (A)", min_value=0.0, max_value=50.0, value=6.2, step=0.1)
media_cart_a = st.sidebar.number_input("🟨 Média de Cartões (A)", min_value=0.0, max_value=20.0, value=2.3, step=0.1)
media_imp_a = st.sidebar.number_input("🚫 Média de Impedimentos (A)", min_value=0.0, max_value=10.0, value=1.5, step=0.1)

st.sidebar.markdown("---")
st.sidebar.subheader(f"{time_b} — médias (históricas)")
total_matches_b = st.sidebar.number_input("Total jogos (B)", min_value=1, max_value=1000, value=18, step=1)
media_gols_b = st.sidebar.number_input("⚽ Média de Gols (B)", min_value=0.0, max_value=10.0, value=1.5, step=0.1)
media_esc_b = st.sidebar.number_input("🚩 Média de Escanteios (B)", min_value=0.0, max_value=50.0, value=5.8, step=0.1)
media_cart_b = st.sidebar.number_input("🟨 Média de Cartões (B)", min_value=0.0, max_value=20.0, value=2.0, step=0.1)
media_imp_b = st.sidebar.number_input("🚫 Média de Impedimentos (B)", min_value=0.0, max_value=10.0, value=1.4, step=0.1)

st.sidebar.markdown("---")
st.sidebar.markdown("<div class='small-muted'>Nota: use médias de amostras recentes (ex.: últimos 10 jogos) para melhorar confiabilidade.</div>", unsafe_allow_html=True)

# ----------------------- Main navigation tabs -----------------------
tab = st.tabs(["📊 Análises", "📈 Tabelas 0→10", "🔍 P(A > B) - Eventos", "📖 Comentários"])

# Precompute tables and P(X>=5) for all events
events = ["Gols", "Escanteios", "Cartões", "Impedimentos"]
mus_a = {
    "Gols": media_gols_a,
    "Escanteios": media_esc_a,
    "Cartões": media_cart_a,
    "Impedimentos": media_imp_a
}
mus_b = {
    "Gols": media_gols_b,
    "Escanteios": media_esc_b,
    "Cartões": media_cart_b,
    "Impedimentos": media_imp_b
}

tables_a = {ev: make_event_table(mus_a[ev]) for ev in events}
tables_b = {ev: make_event_table(mus_b[ev]) for ev in events}

probs_a_at5 = {ev: prob_at_least_k(mus_a[ev], 5) for ev in events}
probs_b_at5 = {ev: prob_at_least_k(mus_b[ev], 5) for ev in events}

# ----------------------- Tab 1: Análises (pies & quick insights) -----------------------
with tab[0]:
    st.header("📊 Probabilidade P(X ≥ 5) — Visão por evento")
    # Show warning if samples small
    if total_matches_a < 5 or total_matches_b < 5:
        st.warning("⚠️ Amostras pequenas (menos de 5 jogos). Resultados podem ser instáveis.")
    colL, colR = st.columns(2)
    # Build dataframes for pies
    df_pie_a = pd.DataFrame({
        "Evento": events,
        "P(X ≥ 5) (%)": [round(probs_a_at5[ev]*100, 2) for ev in events]
    })
    df_pie_b = pd.DataFrame({
        "Evento": events,
        "P(X ≥ 5) (%)": [round(probs_b_at5[ev]*100, 2) for ev in events]
    })

    # color palette
    pie_colors = ["#0FA37F", "#C9A516", "#1F6FEB", "#E04848"]  # green, gold, blue, red

    with colL:
        st.subheader(f"{time_a} — P(X ≥ 5)")
        fig_a = px.pie(df_pie_a, names="Evento", values="P(X ≥ 5) (%)", color="Evento",
                       color_discrete_sequence=pie_colors, title=f"{time_a} — Probabilidades P(X ≥ 5)")
        fig_a.update_traces(textinfo="percent+label", pull=[0.02]*4)
        fig_a.update_layout(template="plotly_white", title_font_color="#0FA37F",
                            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_a, use_container_width=True)

    with colR:
        st.subheader(f"{time_b} — P(X ≥ 5)")
        fig_b = px.pie(df_pie_b, names="Evento", values="P(X ≥ 5) (%)", color="Evento",
                       color_discrete_sequence=pie_colors, title=f"{time_b} — Probabilidades P(X ≥ 5)")
        fig_b.update_traces(textinfo="percent+label", pull=[0.02]*4)
        fig_b.update_layout(template="plotly_white", title_font_color="#0FA37F",
                            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_b, use_container_width=True)

    st.markdown("**O que o gráfico mostra:** cada fatia representa a probabilidade de o evento ocorrer **pelo menos 5 vezes** na partida, dada a média histórica informada e assumindo Poisson.")
    st.divider()
    st.header("📊 Insights Rápidos (Diferença em pontos percentuais — pp)")

    diffs_pp = {ev: round((probs_a_at5[ev] - probs_b_at5[ev]) * 100, 2) for ev in events}
    cols = st.columns(4)
    for i, ev in enumerate(events):
        cols[i].metric(f"{ev} (A - B, pp)", f"{diffs_pp[ev]} pp")

    st.markdown("<div class='small-muted'>pp = pontos percentuais (diferença absoluta entre P(X ≥ 5) de A e B)</div>", unsafe_allow_html=True)

# ----------------------- Tab 2: Tables 0..10 -----------------------
with tab[1]:
    st.header("📈 Tabelas 0 → 10 — Probabilidades Exatas e Acumuladas")
    st.markdown("Cada tabela mostra P(X=k) e P(X ≤ k) em porcentagem (0→10). Use para decisões pontuais sobre mercados e volumes.")
    for ev in events:
        st.subheader(f"🔹 {ev} — {time_a} (Tabela 0→10)")
        t_a = tables_a[ev].rename(columns={"k":"Número de eventos (k)", "P(X=k) (%)":"P(X=k) (%)", "P(X ≤ k) (%)":"P(X ≤ k) (%)"}).set_index("Número de eventos (k)")
        st.table(t_a)
        st.subheader(f"🔹 {ev} — {time_b} (Tabela 0→10)")
        t_b = tables_b[ev].rename(columns={"k":"Número de eventos (k)", "P(X=k) (%)":"P(X=k) (%)", "P(X ≤ k) (%)":"P(X ≤ k) (%)"}).set_index("Número de eventos (k)")
        st.table(t_b)
        st.markdown("---")

# ----------------------- Tab 3: P(A > B) per event (buttons) -----------------------
with tab[2]:
    st.header("🔍 Probabilidade de Time A ter MAIS que Time B — por evento")
    st.markdown("Clique no botão do evento desejado para calcular P(A > B) com soma até k=60 (precisão adequada para médias típicas).")

    col_btns = st.columns(4)
    event_probs = {}
    for i, ev in enumerate(events):
        with col_btns[i]:
            # style outline button by injecting class via markdown wrapper
            if st.button(f"P(A > B) — {ev}"):
                muA = mus_a[ev]
                muB = mus_b[ev]
                pA_gt_B = prob_A_greater_B(muA, muB, k_max=60)
                pB_gt_A = 1 - pA_gt_B - poisson.pmf(0, muB)*poisson.pmf(0, muA)  # approx but we will show pA_gt_B and pB_gt_A=1-pA
                # For simplicity show both complementary probabilities
                st.success(f"**{ev}:** Probabilidade de **{time_a} > {time_b}** = **{pA_gt_B*100:.2f}%**")
                # Interpretation
                if pA_gt_B >= 0.7:
                    st.markdown(f"🔔 Vantagem estatística clara para **{time_a}** em {ev}.")
                elif pA_gt_B >= 0.55:
                    st.markdown(f"🔎 Vantagem moderada para **{time_a}** em {ev}.")
                elif pA_gt_B >= 0.45:
                    st.info("Equilíbrio estatístico — probabilidade próxima de 50%.")
                else:
                    st.markdown(f"⚠️ **{time_b}** tem vantagem relativa em {ev} (P(A>B) baixa).")
                event_probs[ev] = pA_gt_B

    st.divider()
    if event_probs:
        st.markdown("**Resumo das probabilidades calculadas nesta sessão:**")
        for ev, p in event_probs.items():
            st.write(f"- {ev}: P({time_a} > {time_b}) = {p*100:.2f}%")

# ----------------------- Tab 4: Comments / Interpretation concise -----------------------
with tab[3]:
    st.header("📖 Comentários — Uso e Interpretação (conciso & objetivo)")
    st.markdown("""
    **Resumo rápido — como usar o StatBall v4**
    - O app aplica a **Distribuição de Poisson** para estimar a probabilidade de ocorrerem X eventos (0→10) e a chance de ocorrer **pelo menos 5** (P(X ≥ 5)).
    - Eventos modelados: **Gols, Escanteios, Cartões, Impedimentos**. Impedimentos são recomendados quando busca-se maior aderência à Poisson.
    - **Interpretação de P(X ≥ 5):** indicam probabilidade de alto volume naquele evento. Use para avaliar mercados de volume (ex.: muitos escanteios).
    - **P(A > B):** calcula a probabilidade de o Time A registrar mais ocorrências do que o Time B (útil para mercados comparativos).

    **Limitações importantes**
    - O modelo **assume independência e homogeneidade** durante o jogo — fatores como tática, árbitro, clima ou lesões não são considerados.
    - **Amostras pequenas** (menos de 5 jogos) reduzem a confiabilidade dos resultados.
    - Finalizações não estão modeladas aqui (imprevisíveis) — usamos Impedimentos como alternativa mais estável.

    **Recomendações práticas**
    - Use médias dos últimos **8–12 jogos** para capturar forma atual.
    - Combine o StatBall com análise qualitativa (notícias, escalações, estilo tático).
    - Se desejar, conecte o app a uma base de dados/API para atualizar médias automaticamente (próxima evolução).

    **Glossário rápido**
    - *P(X=k)* = probabilidade exata de ocorrer k eventos.
    - *P(X ≤ k)* = probabilidade acumulada até k.
    - *P(X ≥ 5)* = probabilidade de ocorrer 5 ou mais eventos.
    """)

    st.markdown("---")
    st.subheader("🧭 Guia rápido de decisão")
    st.markdown("""
    - P(X ≥ 5) alto em Escanteios → considere mercado 'mais de X escanteios'.  
    - P(A > B) alto em Cartões → avalie exposição disciplinar do adversário.  
    - Em Gols, combine P(X ≥ 5) com xG e escalações para decisões de apostas.  
    """)

# ----------------------- Footer -----------------------
st.markdown("<div class='footer'>Desenvolvido por <b>Juan Santos</b> — Versão 4 - Tecnologia ZIP4 Computers</div>", unsafe_allow_html=True)
