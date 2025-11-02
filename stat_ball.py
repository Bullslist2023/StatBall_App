# statball_v2_1.py
"""
StatBall - Análise de Estatística Esportiva (v2.0.1)
Ajustes visuais: fonte dos nomes dos times, rótulos, legendas e tabelas para melhor contraste
Tema: Verde-esmeralda escuro + botões amarelos
Funcionalidades mantidas: Poisson 0..10, P(X>=5), P(A>B), interpretação automática, PDF sob demanda
"""
import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import poisson
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table as RLTable, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors as rl_colors
from PIL import Image
import datetime

# ----------------------- Page config -----------------------
st.set_page_config(page_title="StatBall - Análise de Estatística Esportiva",
                   page_icon="⚽",
                   layout="wide")

# ----------------------- Theme CSS (verde-esmeralda escuro + botões amarelos) -----------------------
st.markdown("""
<style>
:root{
  --emerald-dark: #013220;  /* fundo principal */
  --emerald: #0FA37F;       /* acentos */
  --button-yellow: #FFD700; /* botões */
  --button-yellow-hover: #FFEA00;
  --muted: #b7c6bd;
  --card-bg: #022a22;
  --title-gold: #FFD700;
  --text-light: #FFFFFF;
  --muted-2: #cfe9df;
}
html, body, .main, .block-container {
    background-color: var(--emerald-dark) !important;
    color: var(--text-light) !important;
}
h1, h2, h3, h4, h5 { color: var(--emerald) !important; }
.stApp .css-1y4p8pa { padding-top: 1rem; }
.stButton>button {
    background-color: var(--button-yellow) !important;
    color: #013220 !important;
    border-radius:10px !important;
    padding:0.45rem 0.9rem !important;
    border: 2px solid #b08900 !important;
    font-weight:700;
}
.stButton>button:hover {
    background-color: var(--button-yellow-hover) !important;
    color: #013220 !important;
}
[data-testid="stSidebar"] { background-color:#022a22 !important; border-left: 1px solid rgba(255,255,255,0.04); color: var(--text-light) !important; }
.css-1d391kg { background-color: rgba(255,255,255,0.03) !important; border-radius: 8px; padding: 6px; }
.small-muted { font-size:12px; color: var(--muted-2) !important; }
.footer-small { font-size:12px; color:#d0d7d3; padding-top:8px; padding-bottom:8px; }
.table-display td, .table-display th { color: var(--text-light) !important; }
</style>
""", unsafe_allow_html=True)

# ----------------------- Header / logo -----------------------
colh1, colh2 = st.columns([0.78, 0.22])
with colh1:
    st.title("StatBall — Análise de Estatística Esportiva (v2.0.1)")
    st.markdown("<div style='color: #cfe9df'>Distribuição de Poisson • Probabilidades 0→10, P(X≥5), P(A>B) e interpretação automática (misto).</div>", unsafe_allow_html=True)
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
    total_matches_a = st.number_input("Total de jogos (A) usados para médias", min_value=0, max_value=1000, value=20, step=1)
    media_gols_a = st.number_input("⚽ Média de Gols (A)", min_value=0.0, max_value=20.0, value=1.8, step=0.1)
    media_cart_a = st.number_input("🟨 Média de Cartões (A)", min_value=0.0, max_value=20.0, value=2.3, step=0.1)
    media_final_a = st.number_input("🎯 Média de Finalizações (A)", min_value=0.0, max_value=200.0, value=13.4, step=0.1)
    media_esc_a = st.number_input("🚩 Média de Escanteios (A)", min_value=0.0, max_value=100.0, value=6.2, step=0.1)
with c2:
    time_b = st.text_input("Nome do Time B", "Time B")
    total_matches_b = st.number_input("Total de jogos (B) usados para médias", min_value=0, max_value=1000, value=18, step=1)
    media_gols_b = st.number_input("⚽ Média de Gols (B)", min_value=0.0, max_value=20.0, value=1.5, step=0.1)
    media_cart_b = st.number_input("🟨 Média de Cartões (B)", min_value=0.0, max_value=20.0, value=2.0, step=0.1)
    media_final_b = st.number_input("🎯 Média de Finalizações (B)", min_value=0.0, max_value=200.0, value=12.9, step=0.1)
    media_esc_b = st.number_input("🚩 Média de Escanteios (B)", min_value=0.0, max_value=100.0, value=5.8, step=0.1)

st.markdown(f"<div class='small-muted'>Nota: médias baseadas em <b style='color:#FFD700'>{total_matches_a}</b> jogos (Time A) e <b style='color:#FFD700'>{total_matches_b}</b> jogos (Time B). Amostras maiores aumentam confiança nas estimativas.</div>", unsafe_allow_html=True)
st.divider()

# Display team names prominently with gold color for better visibility
col_t1, col_t2 = st.columns([1,1])
with col_t1:
    st.markdown(f"<h3 style='color:#FFD700; margin-bottom:0'>{time_a}</h3>", unsafe_allow_html=True)
    st.markdown(f"<div style='color:#ffffff; margin-top:0.1rem'>Médias — Gols: {media_gols_a} • Finalizações: {media_final_a} • Escanteios: {media_esc_a} • Cartões: {media_cart_a}</div>", unsafe_allow_html=True)
with col_t2:
    st.markdown(f"<h3 style='color:#FFD700; margin-bottom:0'>{time_b}</h3>", unsafe_allow_html=True)
    st.markdown(f"<div style='color:#ffffff; margin-top:0.1rem'>Médias — Gols: {media_gols_b} • Finalizações: {media_final_b} • Escanteios: {media_esc_b} • Cartões: {media_cart_b}</div>", unsafe_allow_html=True)

st.divider()

# ----------------------- Poisson helpers -----------------------
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

def prob_at_least_k(mu, k=5):
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

# ----------------------- Session state for UI -----------------------
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
    if st.button("Limpar Visuais"):
        st.session_state.show_charts = False
        st.session_state.show_specials = False

st.divider()

# ----------------------- Pie charts (with readable font colors) -----------------------
if st.session_state.show_charts:
    st.header("📊 Probabilidade de o Evento Ocorre ao Menos 5 Vezes (P(X ≥ 5))")
    colL, colR = st.columns(2)
    pie_colors = ["#0FA37F", "#FFD700", "#1F6FEB", "#E04848"]  # emerald, yellow, blue, red

    with colL:
        fig_a = px.pie(df_pie_a, values="Probabilidade P(X ≥ 5) (%)", names="Evento",
                       color="Evento", color_discrete_sequence=pie_colors,
                       title=f"{time_a} — P(X ≥ 5) por evento")
        # ensure all text and legend are visible on dark background
        fig_a.update_traces(textinfo="percent+label", pull=[0.02]*4, textfont=dict(color="white"))
        fig_a.update_layout(template="plotly_dark",
                            title_font=dict(color="#FFD700", size=16),
                            font=dict(color="white"),
                            legend=dict(font=dict(color="white")),
                            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        fig_a.update_traces(marker=dict(line=dict(color='#013220', width=2)))
        st.plotly_chart(fig_a, use_container_width=True)

    with colR:
        fig_b = px.pie(df_pie_b, values="Probabilidade P(X ≥ 5) (%)", names="Evento",
                       color="Evento", color_discrete_sequence=pie_colors,
                       title=f"{time_b} — P(X ≥ 5) por evento")
        fig_b.update_traces(textinfo="percent+label", pull=[0.02]*4, textfont=dict(color="white"))
        fig_b.update_layout(template="plotly_dark",
                            title_font=dict(color="#FFD700", size=16),
                            font=dict(color="white"),
                            legend=dict(font=dict(color="white")),
                            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        fig_b.update_traces(marker=dict(line=dict(color='#013220', width=2)))
        st.plotly_chart(fig_b, use_container_width=True)

    st.markdown("<div style='color:#cfe9df'><b>O que o gráfico mostra:</b></div>", unsafe_allow_html=True)
    st.markdown("<div style='color:#ffffff'>Cada fatia indica a probabilidade do evento (Finalizações, Cartões, Gols, Escanteios) ocorrer <b>pelo menos 5 vezes</b> em uma partida.</div>", unsafe_allow_html=True)
    st.markdown("<div style='color:#cfe9df'>Use P(X ≥ 5) para identificar jogos com alta chance de volume.</div>", unsafe_allow_html=True)

st.divider()

# ----------------------- Tables + pp explanation (styled DataFrame) -----------------------
st.header("📈 Tabelas 0 → 10 — Probabilidades Exatas e Acumuladas")
st.markdown("<div style='color:#cfe9df'><b>Explicação sobre 'pp' (pontos percentuais):</b> ao comparar probabilidades entre os dois times, 'pp' representa a diferença absoluta em pontos percentuais. Ex.: 10 pp = Time A tem 10% a mais de chance que Time B naquele evento.</div>", unsafe_allow_html=True)

# helper to style DataFrame for dark bg
def style_table(df):
    sty = (df.style
           .set_table_styles([
               {'selector': 'th', 'props': [('background-color', '#025939'), ('color', 'white'), ('font-weight', '600')]},
               {'selector': 'td', 'props': [('background-color', '#013220'), ('color', 'white')]}
           ])
           .set_properties(**{'border': '0px solid #013220'}))
    return sty

for event_key, label_event in zip(["Finalizações", "Cartões", "Gols", "Escanteios"],
                                  ["🎯 Finalizações", "🟨 Cartões", "⚽ Gols", "🚩 Escanteios"]):
    st.subheader(f"{label_event} — {time_a}")
    st.dataframe(style_table(tables_a[event_key]).set_precision(4), use_container_width=True)
    st.subheader(f"{label_event} — {time_b}")
    st.dataframe(style_table(tables_b[event_key]).set_precision(4), use_container_width=True)
    st.markdown("---")

# ----------------------- Insights pp metrics -----------------------
st.header("📊 Insights Rápidos (Diferenças em pp)")
diffs_pp = np.round((np.array(probs_a_at5) - np.array(probs_b_at5)) * 100, 2)
k1, k2, k3, k4 = st.columns(4)
k1.metric("Finalizações (A - B, pp)", f"{diffs_pp[0]} pp")
k2.metric("Cartões (A - B, pp)", f"{diffs_pp[1]} pp")
k3.metric("Gols (A - B, pp)", f"{diffs_pp[2]} pp")
k4.metric("Escanteios (A - B, pp)", f"{diffs_pp[3]} pp")
st.markdown("<div class='small-muted'>pp = pontos percentuais</div>", unsafe_allow_html=True)

# ----------------------- Interpretation automatic (mixed tone) -----------------------
def interpret_pp(diffs_pp_array, events_list, time_a_name, time_b_name):
    statements = []
    technical_parts = []
    narrative_parts = []

    for idx, ev in enumerate(events_list):
        pp = diffs_pp_array[idx]
        tech = f"{ev}: diferença de {pp:.2f} pp (P(X≥5) A vs B)."
        technical_parts.append(tech)

        if pp > 8:
            narr = f"{time_a_name} apresenta **vantagem clara** em {ev} (+{pp:.2f} pp), indicando maior probabilidade de alto volume neste evento."
        elif pp > 4:
            narr = f"{time_a_name} possui **vantagem moderada** em {ev} (+{pp:.2f} pp) — tendência ofensiva/volume superior."
        elif -4 <= pp <= 4:
            narr = f"Há **equilíbrio** em {ev} (diferença de {pp:.2f} pp) — probabilidades muito próximas."
        elif pp < -8:
            narr = f"{time_b_name} apresenta **vantagem clara** em {ev} ({pp:.2f} pp), sugerindo maior tendência naquele evento."
        else:
            narr = f"{time_b_name} possui **vantagem moderada** em {ev} ({pp:.2f} pp)."

        narrative_parts.append(narr)

    strongest_idx = int(np.argmax(diffs_pp_array))
    weakest_idx = int(np.argmin(diffs_pp_array))
    strong_ev = events_list[strongest_idx]
    weak_ev = events_list[weakest_idx]
    strong_pp = diffs_pp_array[strongest_idx]
    weak_pp = diffs_pp_array[weakest_idx]

    overall = ["**Resumo técnico:**"]
    for t in technical_parts:
        overall.append("- " + t)

    overall.append("")
    overall.append("**Leitura tática (interpretação):**")
    if strong_pp > 4:
        overall.append(f"- Destaque: {strong_ev} — {time_a_name} tem +{strong_pp:.2f} pp vs {time_b_name}, sinalizando vantagem em volume.")
    elif strong_pp < -4:
        overall.append(f"- Destaque: {weak_ev} — {time_b_name} tem vantagem de {abs(weak_pp):.2f} pp sobre {time_a_name}.")
    else:
        overall.append("- Jogo tende a ser equilibrado em volume estatístico.")

    advice = []
    for idx, ev in enumerate(events_list):
        pp = diffs_pp_array[idx]
        if ev == "Gols":
            if pp > 5:
                advice.append(f"- Gols: considerar mercados 'ambas marcam' e oportunidades favoráveis ao {time_a_name}.")
            elif pp < -5:
                advice.append(f"- Gols: {time_b_name} pode ser favorito para marcar; ajuste estratégias.")
        if ev == "Escanteios":
            if abs(pp) > 5:
                advice.append(f"- Escanteios: mercado 'mais de X escanteios' pode ser explorado se o time com vantagem atacar mais.")
        if ev == "Cartões":
            if pp < -5:
                advice.append(f"- Cartões: {time_b_name} tende a receber mais cartões; cautela em apostas de cartões.")
    if not advice:
        advice = ["- Nenhuma recomendação tática forte detectada; use as tabelas 0→10 para decisões pontuais."]

    final_lines = overall + [""] + ["**Resumo executivo (rápido):**"] + narrative_parts + [""] + ["**Sugestões práticas:**"] + advice
    return "\n".join(final_lines)

interpre_text = interpret_pp(diffs_pp, ["Finalizações", "Cartões", "Gols", "Escanteios"], time_a, time_b)
st.markdown("### 🧠 Interpretação Automática (técnico + narrativo)")
st.markdown(f"<div style='color:#cfe9df'>{interpre_text.replace(chr(10), '<br>')}</div>", unsafe_allow_html=True)

st.divider()

# ----------------------- P(A > B) calculation -----------------------
def prob_A_greater_B(muA, muB, k_max=40):
    ks = np.arange(0, k_max+1)
    pmfA = poisson.pmf(ks, muA)
    cdfB = poisson.cdf(ks - 1, muB)  # P(B < i)
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
        st.markdown(f"<div style='color:#FFD700'><b>{label}:</b></div> <div style='color:#ffffff'>Probabilidade de <b>{time_a} > {time_b}</b> = <b>{pA_gt_B*100:.2f}%</b></div>", unsafe_allow_html=True)

    st.markdown("<div style='color:#cfe9df'><b>Interpretação (automática):</b></div>", unsafe_allow_html=True)
    for label, p in special_results.items():
        if p >= 0.6:
            veredict = "vantagem estatística relevante"
        elif p >= 0.5:
            veredict = "leve vantagem"
        else:
            veredict = "desvantagem relativa"
        st.markdown(f"<div style='color:#ffffff'>- Para <b>{label}</b>, com base nas médias e na distribuição de Poisson, <b>{time_a} tem {p*100:.2f}% de chance</b> de superar {time_b} — {veredict}.</div>", unsafe_allow_html=True)
    st.markdown("<div style='color:#cfe9df'>Como foi calculado: para cada i possíveis eventos do Time A (i=0..40) multiplicamos P_A(i) * P_B(&lt; i) e somamos.</div>", unsafe_allow_html=True)

st.divider()

# ----------------------- PDF generation (keeps previous logic) -----------------------
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

    if fig_a_bytes:
        elements.append(RLImage(BytesIO(fig_a_bytes), width=360, height=220))
        elements.append(Spacer(1,8))

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

    if fig_b_bytes:
        elements.append(RLImage(BytesIO(fig_b_bytes), width=360, height=220))
        elements.append(Spacer(1,8))

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
    st.markdown("<div style='color:#cfe9df'>O relatório contém: gráficos P(X ≥ 5), tabelas 0→10, prob. P(A>B), interpretação automática e rodapé com autor/ano.</div>", unsafe_allow_html=True)

st.divider()

# ----------------------- Footer -----------------------
st.markdown(f"""
<div style="width:100%; text-align:center; padding:10px 0; color:#d0d7d3; border-top:1px solid rgba(255,255,255,0.04);">
    Desenvolvido por <b style='color:#FFD700'>Juan Santos</b> — Projeto iniciado em <b style='color:#FFD700'>2025</b> • StatBall v2.0.1
</div>
""", unsafe_allow_html=True)
