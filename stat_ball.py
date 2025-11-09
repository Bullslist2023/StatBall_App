# app.py
"""
StatBall - Análise de Estatística Esportiva - Versão 3
Atualizações:
- Interpretação Automática dos Insights (tom misto: técnico + narrativo)
- Texto explicativo logo abaixo das métricas pp
- Mantém P(X >= 5), tabelas 0..10, eventos especiais e PDF sob demanda
"""
import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import poisson
import plotly.express as px
from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table as RLTable, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors as rl_colors
from PIL import Image
import datetime

# ----------------------- Page config -----------------------
st.set_page_config(page_title="🏆StatBall - Análise de Estatística Esportiva",
                   page_icon="⚽",
                   layout="wide")

# ----------------------- Theme (verde-esmeralda vibrante) -----------------------
st.markdown("""
<style>
:root{
  --emerald: #0FA37F;
  --accent: #2BB673;
  --dourado: #C9A516;
  --muted: #5f6b6b;
  --bg: #f4fbf9;
}
body { background-color: var(--bg); color: #0b2a26; }
h1,h2,h3 { color: var(--emerald); }
.stButton>button { background-color: var(--emerald); color: white; border-radius:8px; padding:0.45rem 0.8rem; border: 2px solid var(--dourado); font-weight:700; }
.stButton>button:hover { background-color: var(--dourado); color: black; }
[data-testid="stSidebar"] { background-color: white; border-left: 1px solid #e6e6e6; }
.small-muted { font-size:12px; color: var(--muted); }
.footer-small { font-size:12px; color:#666; padding-top:8px; padding-bottom:8px; }
</style>
""", unsafe_allow_html=True)

# ----------------------- Header / logo -----------------------
colh1, colh2 = st.columns([0.82, 0.18])
with colh1:
    st.title("🏆StatBall — Análise de Estatística Esportiva")
    st.markdown("**Distribuição de Poisson** • Probabilidades 0→10, P(X≥5) por evento, isto é probabilidade de evento aleatório X assumir um valor maior ou igual a 5. A seguir veja também comparação entre times, interpretação automática e conselhos técnico e narrativo.")
with colh2:
    logo_file = st.file_uploader("Upload do logotipo (opcional)", type=['png','jpg','jpeg'])
    if logo_file:
        try:
            img = Image.open(logo_file).convert("RGB")
            st.image(img, use_column_width=True)
        except:
            st.text("Arquivo de logo inválido.")

st.divider()

# ----------------------- Inputs -----------------------
st.header("📥 Entradas — Dados dos Times")
c1, c2 = st.columns(2)
with c1:
    time_a = st.text_input("Nome do Time A", "Time A")
    total_matches_a = st.number_input("Total de jogos (A) usados para médias", min_value=0, max_value=500, value=20, step=1)
    media_gols_a = st.number_input("⚽ Média de Gols (A)", min_value=0.0, max_value=20.0, value=0.0, step=0.1)
    media_cart_a = st.number_input("🟨 Média de Cartões (A)", min_value=0.0, max_value=20.0, value=0.0, step=0.1)
    media_final_a = st.number_input("🎯 Média de Finalizações (A)", min_value=0.0, max_value=100.0, value=0.0, step=0.1)
    media_esc_a = st.number_input("🚩 Média de Escanteios (A)", min_value=0.0, max_value=50.0, value=0.0, step=0.1)
with c2:
    time_b = st.text_input("Nome do Time B", "Time B")
    total_matches_b = st.number_input("Total de jogos (B) usados para médias", min_value=0, max_value=500, value=0.0, step=1)
    media_gols_b = st.number_input("⚽ Média de Gols (B)", min_value=0.0, max_value=20.0, value=0.0, step=0.1)
    media_cart_b = st.number_input("🟨 Média de Cartões (B)", min_value=0.0, max_value=20.0, value=0.0, step=0.1)
    media_final_b = st.number_input("🎯 Média de Finalizações (B)", min_value=0.0, max_value=100.0, value=0.0, step=0.1)
    media_esc_b = st.number_input("🚩 Média de Escanteios (B)", min_value=0.0, max_value=50.0, value=0.0, step=0.1)

st.markdown(f"<div class='small-muted'>Nota: médias baseadas em {total_matches_a} jogos (Time A) e {total_matches_b} jogos (Time B). Amostras maiores aumentam confiança nas estimativas.</div>", unsafe_allow_html=True)
st.divider()

# ----------------------- Estatística: Poisson 0..10 + acumuladas -----------------------
def poisson_probs(mu, k_max=10):
    ks = np.arange(0, k_max + 1)
    pmf = poisson.pmf(ks, mu)
    pmf_pct = np.round(pmf * 100, 4)
    cdf_pct = np.round(np.cumsum(pmf) * 100, 4)
    return ks, pmf_pct, cdf_pct

def make_event_table(mu):
    ks, pmf_pct, cdf_pct = poisson_probs(mu, 10)
    return pd.DataFrame({
        "k": ks,
        "P(X=k) (%)": pmf_pct,
        "P(X ≤ k) (%)": cdf_pct
    })

# Build tables per event & per team
events = ["Finalizações", "Cartões", "Gols", "Escanteios"]
tables_a = {
    "Finalizações": make_event_table(media_final_a),
    "Cartões": make_event_table(media_cart_a),
    "Gols": make_event_table(media_gols_a),
    "Escanteios": make_event_table(media_esc_a)
}
tables_b = {
    "Finalizações": make_event_table(media_final_b),
    "Cartões": make_event_table(media_cart_b),
    "Gols": make_event_table(media_gols_b),
    "Escanteios": make_event_table(media_esc_b)
}

# P(X >= 5) used for the pie charts
def prob_at_least_k(mu, k=5):
    # P(X >= k) = 1 - P(X <= k-1)
    return 1 - poisson.cdf(k-1, mu)

probs_a_at5 = [
    prob_at_least_k(media_final_a, 5),
    prob_at_least_k(media_cart_a, 5),
    prob_at_least_k(media_gols_a, 5),
    prob_at_least_k(media_esc_a, 5)
]
probs_b_at5 = [
    prob_at_least_k(media_final_b, 5),
    prob_at_least_k(media_cart_b, 5),
    prob_at_least_k(media_gols_b, 5),
    prob_at_least_k(media_esc_b, 5)
]

df_pie_a = pd.DataFrame({"Evento": events, "Probabilidade P(X ≥ 5) (%)": np.round(np.array(probs_a_at5) * 100, 2)})
df_pie_b = pd.DataFrame({"Evento": events, "Probabilidade P(X ≥ 5) (%)": np.round(np.array(probs_b_at5) * 100, 2)})

# ----------------------- UI: Botões interativos -----------------------
if 'show_charts' not in st.session_state:
    st.session_state.show_charts = False
if 'show_specials' not in st.session_state:
    st.session_state.show_specials = False

colbtn1, colbtn2, colbtn3 = st.columns([1,1,1])
with colbtn1:
    if st.button("Gerar Gráficos (P(X ≥ 5))"):
        st.session_state.show_charts = True
with colbtn2:
    if st.button("Exibir Eventos Especiais (Time A > Time B)"):
        st.session_state.show_specials = True
with colbtn3:
    st.write("")  # placeholder for layout alignment

st.divider()

# ----------------------- Charts: Pie for P(X >= 5) -----------------------
if st.session_state.show_charts:
    st.header("📊 Probabilidade de o Evento Ocorre ao Menos 5 Vezes (P(X ≥ 5))")
    colL, colR = st.columns(2)
    pie_colors = ["#0FA37F", "#C9A516", "#1F6FEB", "#E04848"]  # emerald, gold, blue, red

    with colL:
        fig_a = px.pie(df_pie_a, values="Probabilidade P(X ≥ 5) (%)", names="Evento",
                       color="Evento", color_discrete_sequence=pie_colors,
                       title=f"{time_a} — P(X ≥ 5) por evento")
        fig_a.update_traces(textinfo="percent+label", pull=[0.02]*4)
        fig_a.update_layout(template="plotly_white", title_font_color="#0FA37F",
                            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                            transition={"duration": 600})
        fig_a.update_traces(marker=dict(line=dict(color='white', width=2)))
        st.plotly_chart(fig_a, use_container_width=True)

    with colR:
        fig_b = px.pie(df_pie_b, values="Probabilidade P(X ≥ 5) (%)", names="Evento",
                       color="Evento", color_discrete_sequence=pie_colors,
                       title=f"{time_b} — P(X ≥ 5) por evento")
        fig_b.update_traces(textinfo="percent+label", pull=[0.02]*4)
        fig_b.update_layout(template="plotly_white", title_font_color="#0FA37F",
                            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                            transition={"duration": 600})
        fig_b.update_traces(marker=dict(line=dict(color='white', width=2)))
        st.plotly_chart(fig_b, use_container_width=True)

    st.markdown("**O que o gráfico mostra:** cada fatia indica a probabilidade de o evento (Finalizações, Cartões, Gols, Escanteios) ocorrer **pelo menos 5 vezes** em uma partida, com base na média histórica informada e na distribuição de Poisson.")
    st.markdown("**Como usar:** mercados que pagam por altos volumes (ex.: mercados de muitos escanteios ou finalizações) beneficiam-se de P(X ≥ 5). Use essa métrica para detectar jogos com potencial de eventos em número alto.")

st.divider()

# ----------------------- Tables 0..10 with explanation about pp -----------------------
st.header("📈 Tabelas 0 → 10 — Probabilidades Exatas e Acumuladas")
st.markdown("**Explicação sobre 'pp' (pontos percentuais):** ao comparar probabilidades entre os dois times, 'pp' representa a diferença absoluta em pontos percentuais. Ex.: 10 pp = Time A tem 10% a mais de chance que Time B naquele evento. Use pp para avaliar vantagem relativa entre os times.")

for event_key, label_event in zip(["Finalizações", "Cartões", "Gols", "Escanteios"], ["🎯 Finalizações", "🟨 Cartões", "⚽ Gols", "🚩 Escanteios"]):
    st.subheader(f"{label_event} — {time_a} (Tabela 0→10)")
    st.table(tables_a[event_key].rename(columns={"k":"Número de eventos (k)", "P(X=k) (%)":"P(X=k) (%)", "P(X ≤ k) (%)":"P(X ≤ k) (%)"}).set_index("Número de eventos (k)"))
    st.subheader(f"{label_event} — {time_b} (Tabela 0→10)")
    st.table(tables_b[event_key].rename(columns={"k":"Número de eventos (k)", "P(X=k) (%)":"P(X=k) (%)", "P(X ≤ k) (%)":"P(X ≤ k) (%)"}).set_index("Número de eventos (k)"))
    st.markdown("---")

# ----------------------- Quick insights (pp differences) -----------------------
st.header("📊 Insights Rápidos (Diferenças em pp)")
diffs_pp = np.round((np.array(probs_a_at5) - np.array(probs_b_at5)) * 100, 2)
k1, k2, k3, k4 = st.columns(4)
k1.metric("Finalizações (A - B, pp)", f"{diffs_pp[0]} pp")
k2.metric("Cartões (A - B, pp)", f"{diffs_pp[1]} pp")
k3.metric("Gols (A - B, pp)", f"{diffs_pp[2]} pp")
k4.metric("Escanteios (A - B, pp)", f"{diffs_pp[3]} pp")
st.markdown("<div class='small-muted'>pp = pontos percentuais</div>", unsafe_allow_html=True)

# ----------------------- Interpretation: automatic mixed tone -----------------------
def interpret_pp(diffs_pp_array, events_list, time_a_name, time_b_name):
    """
    Produces a mixed-style interpretation (technical + narrative) of pp differences.
    Rules:
      - > +7 pp : vantagem clara para A
      - +3..+7 pp : vantagem moderada para A
      - -3..+3 pp : equilíbrio
      - -7..-3 pp : vantagem moderada para B
      - < -7 pp : vantagem clara para B
    """
    statements = []
    technical_parts = []
    narrative_parts = []

    for idx, ev in enumerate(events_list):
        pp = diffs_pp_array[idx]
        # Technical note
        tech = f"{ev}: diferença de {pp:.2f} pp (P(X≥5) A vs B)."
        technical_parts.append(tech)

        # Narrative determination
        if pp > 7:
            narr = f"{time_a_name} apresenta **vantagem clara** em {ev} (+{pp:.2f} pp), indicando maior probabilidade de alto volume neste evento."
        elif pp > 3:
            narr = f"{time_a_name} possui **vantagem moderada** em {ev} (+{pp:.2f} pp) — tendência ofensiva/volume superior."
        elif pp >= -3 and pp <= 3:
            narr = f"Há **equilíbrio** em {ev} (diferença de {pp:.2f} pp) — probabilidades muito próximas."
        elif pp < -7:
            narr = f"{time_b_name} apresenta **vantagem clara** em {ev} ({pp:.2f} pp), sugerindo maior tendência naquele evento."
        else:  # -7..-3
            narr = f"{time_b_name} possui **vantagem moderada** em {ev} ({pp:.2f} pp)."

        narrative_parts.append(narr)

    # Compose overall summary
    # Find strongest advantages
    strongest_idx = int(np.argmax(diffs_pp_array))
    weakest_idx = int(np.argmin(diffs_pp_array))
    strong_ev = events_list[strongest_idx]
    weak_ev = events_list[weakest_idx]
    strong_pp = diffs_pp_array[strongest_idx]
    weak_pp = diffs_pp_array[weakest_idx]

    overall = []
    # Technical summary
    overall.append("**Resumo técnico:**")
    for t in technical_parts:
        overall.append("- " + t)

    # Narrative summary
    overall.append("")
    overall.append("**Leitura tática (interpretação):**")
    if strong_pp > 3:
        overall.append(f"- O maior destaque é {strong_ev}, onde {time_a_name} tem +{strong_pp:.2f} pp vs {time_b_name}, sinalizando vantagem na produção/volume.")
    elif strong_pp < -3:
        overall.append(f"- O maior destaque é {weak_ev}, onde {time_b_name} tem vantagem de {abs(weak_pp):.2f} pp sobre {time_a_name}.")
    else:
        overall.append("- Não há diferenças muito fortes entre os times; o jogo tende a ser equilibrado em volume estatístico.")

    # Tactical advice
    advice = []
    for idx, ev in enumerate(events_list):
        pp = diffs_pp_array[idx]
        if ev == "Gols":
            if pp > 5:
                advice.append(f"- Em termos de gols, considerar mercados 'ambas marcam' com atenção, ou apostas em resultado favorável a {time_a_name}.")
            elif pp < -5:
                advice.append(f"- Em termos de gols, {time_b_name} tem maior chance; avalie mercados que favoreçam o time B.")
        if ev == "Escanteios":
            if abs(pp) > 5:
                advice.append(f"- Escanteios: mercado 'mais de X escanteios' pode ser explorado se o time com vantagem é o favorito para ataque.")
        if ev == "Cartões":
            if pp < -5:
                advice.append(f"- Cartões: {time_b_name} tende a receber mais cartões; cuidado com mercados de cartões.")
    if not advice:
        advice = ["- Nenhuma recomendação tática forte detectada; use as tabelas 0→10 para decisões pontuais."]

    # Combine
    final_lines = overall + [""] + ["**Resumo executivo (rápido):**"] + narrative_parts + [""] + ["**Sugestões práticas:**"] + advice
    return "\n".join(final_lines)

# Generate and show interpretation immediately below the metrics
interpre_text = interpret_pp(diffs_pp, ["Finalizações", "Cartões", "Gols", "Escanteios"], time_a, time_b)
st.markdown("### 🧠 Interpretação Automática (técnico + narrativo)")
st.markdown(interpre_text)

st.divider()

# ----------------------- Events Special: P(A > B) for each event -----------------------
def prob_A_greater_B(muA, muB, k_max=30):
    ks = np.arange(0, k_max+1)
    pmfA = poisson.pmf(ks, muA)
    # cdf_B(i-1) = P(B < i)
    cdfB = poisson.cdf(ks - 1, muB)
    prob = np.sum(pmfA * cdfB)
    return prob

if st.session_state.show_specials:
    st.header("🔍 Eventos Especiais — Probabilidade de Time A ter MAIS que Time B")
    special_results = {}
    pairs = [
        ("Finalizações", media_final_a, media_final_b),
        ("Cartões", media_cart_a, media_cart_b),
        ("Gols", media_gols_a, media_gols_b),
        ("Escanteios", media_esc_a, media_esc_b)
    ]
    for label, muA, muB in pairs:
        pA_gt_B = prob_A_greater_B(muA, muB, k_max=40)
        special_results[label] = pA_gt_B
        st.markdown(f"**{label}:** Probabilidade de **{time_a} > {time_b}** = **{pA_gt_B*100:.2f}%**")

    st.markdown("**Interpretação (automática):**")
    for label, p in special_results.items():
        if p >= 0.6:
            veredict = "vantagem estatística relevante"
        elif p >= 0.5:
            veredict = "leve vantagem"
        else:
            veredict = "desvantagem relativa"
        st.markdown(f"- Para **{label}**, com base nas médias e na distribuição de Poisson, **{time_a} tem {p*100:.2f}% de chance** de superar {time_b} — {veredict}.")
    st.markdown("**Como foi calculado:** para cada i possíveis eventos do Time A (i=0..40) multiplicamos P_A(i) * P_B(< i) e somamos, obtendo P(A > B).")

st.divider()

# ----------------------- PDF generation (on demand) -----------------------
def fig_to_png_bytes(fig):
    try:
        return fig.to_image(format="png", scale=2)
    except Exception:
        return None

def df_to_table_rows(df):
    rows = []
    for _, r in df.iterrows():
        rows.append([str(int(r['k'])), f"{r['P(X=k) (%)']}%", f"{r['P(X ≤ k) (%)']}%"])
    return rows

def generate_pdf(title, time_a, total_a, df_pie_a, tables_a_dict, fig_a_bytes, time_b, total_b, df_pie_b, tables_b_dict, fig_b_bytes, logo_bytes=None):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=18, leftMargin=18, topMargin=18, bottomMargin=18)
    elements = []
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TitleStyle", fontSize=18, alignment=1, textColor=rl_colors.HexColor("#0FA37F")))
    styles.add(ParagraphStyle(name="Body", fontSize=10, textColor=rl_colors.black))

    # header logo/title
    if logo_bytes:
        try:
            logo_io = BytesIO(logo_bytes)
            logo_img = RLImage(logo_io, width=120, height=40)
            elements.append(logo_img)
        except:
            pass
    elements.append(Paragraph(title, styles['TitleStyle']))
    elements.append(Spacer(1,6))
    elements.append(Paragraph(f"Gerado em: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Body']))
    elements.append(Spacer(1,10))

    # Pie A image
    if fig_a_bytes:
        elements.append(RLImage(BytesIO(fig_a_bytes), width=360, height=220))
        elements.append(Spacer(1,8))

    # Tables A (all 4)
    elements.append(Paragraph(f"{time_a} — Total jogos usados: {total_a}", styles['Body']))
    for ev in ["Finalizações", "Cartões", "Gols", "Escanteios"]:
        elements.append(Paragraph(f"{ev}", styles['Body']))
        table_rows = [["k", "P(X=k) (%)", "P(X ≤ k) (%)"]] + df_to_table_rows(tables_a_dict[ev])
        t = RLTable(table_rows, hAlign='LEFT', colWidths=[40, 120, 120])
        t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), rl_colors.HexColor("#0FA37F")),
                               ('TEXTCOLOR',(0,0),(-1,0), rl_colors.white),
                               ('GRID', (0,0), (-1,-1), 0.25, rl_colors.grey)]))
        elements.append(t)
        elements.append(Spacer(1,8))

    # Pie B image
    if fig_b_bytes:
        elements.append(RLImage(BytesIO(fig_b_bytes), width=360, height=220))
        elements.append(Spacer(1,8))

    # Tables B
    elements.append(Paragraph(f"{time_b} — Total jogos usados: {total_b}", styles['Body']))
    for ev in ["Finalizações", "Cartões", "Gols", "Escanteios"]:
        elements.append(Paragraph(f"{ev}", styles['Body']))
        table_rows = [["k", "P(X=k) (%)", "P(X ≤ k) (%)"]] + df_to_table_rows(tables_b_dict[ev])
        t2 = RLTable(table_rows, hAlign='LEFT', colWidths=[40, 120, 120])
        t2.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), rl_colors.HexColor("#0FA37F")),
                               ('TEXTCOLOR',(0,0),(-1,0), rl_colors.white),
                               ('GRID', (0,0), (-1,-1), 0.25, rl_colors.grey)]))
        elements.append(t2)
        elements.append(Spacer(1,8))

    # Special event summary
    elements.append(Paragraph("Resumo e Observações", styles['Body']))
    pairs = [
        ("Finalizações", media_final_a, media_final_b),
        ("Cartões", media_cart_a, media_cart_b),
        ("Gols", media_gols_a, media_gols_b),
        ("Escanteios", media_esc_a, media_esc_b)
    ]
    for label, muA, muB in pairs:
        pA_gt_B = prob_A_greater_B(muA, muB, k_max=40)
        elements.append(Paragraph(f"{label}: Probabilidade de {time_a} > {time_b} = {pA_gt_B*100:.2f}%", styles['Body']))

    elements.append(Spacer(1,12))
    elements.append(Paragraph("Desenvolvido por Juan Santos — Projeto iniciado em 2025", styles['Body']))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

# ----------------------- PDF Button -----------------------
st.header("📤 Relatório (PDF) — sob demanda")
colp1, colp2 = st.columns([0.4, 0.6])
with colp1:
    if st.button("Gerar Relatório PDF"):
        logo_bytes = None
        if logo_file:
            try:
                logo_file.seek(0)
                logo_bytes = logo_file.read()
            except:
                logo_bytes = None

        fig_a_png = None
        fig_b_png = None
        if st.session_state.show_charts:
            try:
                fig_a_png = fig_a.to_image(format="png", scale=2)
            except Exception:
                fig_a_png = None
            try:
                fig_b_png = fig_b.to_image(format="png", scale=2)
            except Exception:
                fig_b_png = None

        pdf_bytes = generate_pdf("StatBall - Relatório", time_a, total_matches_a, df_pie_a, tables_a, fig_a_png,
                                 time_b, total_matches_b, df_pie_b, tables_b, fig_b_png, logo_bytes=logo_bytes)
        st.success("Relatório PDF gerado.")
        st.download_button("Download PDF", data=pdf_bytes, file_name=f"StatBall_Report_{time_a}_vs_{time_b}.pdf", mime="application/pdf")
with colp2:
    st.markdown("""
    O relatório contém:
    - Gráficos P(X ≥ 5) (quando disponível como imagem)  
    - Tabelas 0→10 para cada evento e time  
    - Probabilidades de Time A > Time B (sumário)  
    - Interpretação automática (resumo técnico + narrativo)  
    - Rodapé com autor/ano
    """)

st.divider()

# ----------------------- Footer -----------------------
st.markdown("""
<div style="width:100%; text-align:center; padding:10px 0; color:#444; border-top:1px solid #e6e6e6;">
    Desenvolvido por <b>Juan Santos</b> — Projeto iniciado em <b>2025</b> • StatBall v3.0
</div>
""", unsafe_allow_html=True)
a

