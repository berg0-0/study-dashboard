"""
ENEM Study Queue Dashboard
Streamlit + Supabase (supabase-py)
"""

import os
from datetime import date, datetime, timedelta

import streamlit as st
from supabase import Client, create_client

# ── Constants ────────────────────────────────────────────────────────────────

CYCLE: list[str] = [
    "Matemática",   # 0
    "Linguagens",   # 1
    "Redação",      # 2
    "Matemática",   # 3
    "Humanas",      # 4
    "Matemática",   # 5
    "Redação",      # 6
    "Linguagens",   # 7
    "Matemática",   # 8
    "Natureza",     # 9
]

SUBJECTS: list[str] = ["Matemática", "Redação", "Linguagens", "Humanas", "Natureza"]

KILL_SWITCH_MINUTES = 240  # 4 hours

SUBJECT_COLORS: dict[str, str] = {
    "Matemática": "#6C63FF",
    "Redação":    "#FF6584",
    "Linguagens": "#43D9AD",
    "Humanas":    "#FFB347",
    "Natureza":   "#5CE1E6",
}

SUBJECT_ICONS: dict[str, str] = {
    "Matemática": "∑",
    "Redação":    "✍",
    "Linguagens": "◈",
    "Humanas":    "🌐",
    "Natureza":   "⬡",
}

# ── Styling ───────────────────────────────────────────────────────────────────

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@400;600;700;800&display=swap');

/* ── Reset & base ── */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #0A0A0F !important;
    color: #E8E8F0 !important;
    font-family: 'Syne', sans-serif !important;
}

[data-testid="stSidebar"] {
    background-color: #0F0F1A !important;
    border-right: 1px solid #1E1E30 !important;
}

[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stToolbar"] { display: none; }

/* Botão de reabrir sidebar — cobre todos os seletores possíveis do Streamlit */
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"],
button[kind="header"],
section[data-testid="stSidebarCollapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    background: #13131F !important;
    border: 1px solid #2A2A45 !important;
    border-radius: 8px !important;
    color: #E8E8F0 !important;
    z-index: 9999 !important;
}

/* ── Typography ── */
h1, h2, h3, h4, h5, h6 { font-family: 'Syne', sans-serif !important; }

.mono { font-family: 'DM Mono', monospace; }

/* ── Current block card ── */
.block-card {
    background: linear-gradient(135deg, #13131F 0%, #1A1A2E 100%);
    border: 1px solid #2A2A45;
    border-radius: 16px;
    padding: 32px 36px;
    margin-bottom: 24px;
    position: relative;
    overflow: hidden;
}
.block-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: var(--accent);
}
.block-label {
    font-size: 11px;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: #666680;
    margin-bottom: 8px;
    font-family: 'DM Mono', monospace;
}
.block-subject {
    font-size: 42px;
    font-weight: 800;
    line-height: 1;
    margin-bottom: 4px;
}
.block-index {
    font-family: 'DM Mono', monospace;
    font-size: 12px;
    color: #44445A;
    margin-top: 8px;
}
.subject-icon {
    font-size: 64px;
    position: absolute;
    right: 36px;
    top: 50%;
    transform: translateY(-50%);
    opacity: 0.12;
    line-height: 1;
}

/* ── Progress dots ── */
.cycle-dots {
    display: flex;
    gap: 6px;
    margin-bottom: 28px;
    flex-wrap: wrap;
}
.dot {
    width: 28px;
    height: 6px;
    border-radius: 3px;
    background: #1E1E30;
    transition: background 0.3s;
}
.dot.active { background: var(--accent); }
.dot.done   { background: #2A2A45; }

/* ── Metric cards ── */
.metric-row { display: flex; gap: 12px; margin-bottom: 24px; flex-wrap: wrap; }
.metric-card {
    flex: 1;
    min-width: 120px;
    background: #13131F;
    border: 1px solid #1E1E30;
    border-radius: 12px;
    padding: 16px 20px;
}
.metric-card .val {
    font-size: 28px;
    font-weight: 700;
    font-family: 'DM Mono', monospace;
}
.metric-card .lbl {
    font-size: 11px;
    color: #55556A;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-top: 2px;
}

/* ── Kill switch alert ── */
.kill-alert {
    background: rgba(255, 60, 60, 0.08);
    border: 1px solid rgba(255, 60, 60, 0.4);
    border-radius: 10px;
    padding: 12px 16px;
    color: #FF6B6B;
    font-size: 13px;
    font-weight: 600;
    margin-top: 12px;
}
.kill-ok {
    background: rgba(67, 217, 173, 0.06);
    border: 1px solid rgba(67, 217, 173, 0.2);
    border-radius: 10px;
    padding: 12px 16px;
    color: #43D9AD;
    font-size: 13px;
    margin-top: 12px;
}

/* ── Streamlit widget overrides ── */
[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input {
    background: #13131F !important;
    border: 1px solid #2A2A45 !important;
    border-radius: 8px !important;
    color: #E8E8F0 !important;
    font-family: 'DM Mono', monospace !important;
}
[data-testid="stNumberInput"] input:focus,
[data-testid="stTextInput"] input:focus {
    border-color: #6C63FF !important;
    box-shadow: 0 0 0 2px rgba(108, 99, 255, 0.2) !important;
}

/* Primary button */
[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(135deg, #6C63FF, #9B59B6) !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 12px 28px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 14px !important;
    letter-spacing: 1px !important;
    color: #fff !important;
    width: 100%;
    transition: opacity 0.2s !important;
}
[data-testid="stButton"] > button[kind="primary"]:hover { opacity: 0.85 !important; }

/* Secondary button */
[data-testid="stButton"] > button[kind="secondary"] {
    background: #13131F !important;
    border: 1px solid #2A2A45 !important;
    border-radius: 10px !important;
    color: #888 !important;
    font-family: 'Syne', sans-serif !important;
    font-size: 13px !important;
    width: 100%;
}

/* Section dividers */
.section-title {
    font-size: 10px;
    letter-spacing: 4px;
    text-transform: uppercase;
    color: #44445A;
    font-family: 'DM Mono', monospace;
    margin: 28px 0 16px;
    border-bottom: 1px solid #1A1A2E;
    padding-bottom: 8px;
}

/* Chart area */
[data-testid="stVegaLiteChart"] { border-radius: 12px; overflow: hidden; }
.stPlotlyChart { border-radius: 12px; }

/* Sidebar label */
.sidebar-section {
    font-size: 10px;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: #44445A;
    font-family: 'DM Mono', monospace;
    margin: 20px 0 10px;
}

/* Selectbox override */
[data-testid="stSelectbox"] > div > div {
    background: #13131F !important;
    border: 1px solid #2A2A45 !important;
    border-radius: 8px !important;
    color: #E8E8F0 !important;
}
</style>
"""

# ── Supabase client ───────────────────────────────────────────────────────────

@st.cache_resource
def get_supabase() -> Client:
    url = os.environ.get("SUPABASE_URL") or st.secrets["SUPABASE_URL"]
    key = os.environ.get("SUPABASE_KEY") or st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


# ── Data access layer ─────────────────────────────────────────────────────────

def fetch_current_index(client: Client) -> int:
    try:
        res = client.table("estado_sistema").select("indice_bloco_atual").eq("id", 1).single().execute()
        return res.data["indice_bloco_atual"]
    except Exception as e:
        st.error(f"Erro ao buscar estado: {e}")
        return 0


def advance_index(client: Client, current: int) -> int:
    next_idx = (current + 1) % len(CYCLE)
    try:
        client.table("estado_sistema").update({"indice_bloco_atual": next_idx}).eq("id", 1).execute()
    except Exception as e:
        st.error(f"Erro ao avançar bloco: {e}")
    return next_idx


def set_index(client: Client, idx: int) -> bool:
    try:
        client.table("estado_sistema").update({"indice_bloco_atual": idx}).eq("id", 1).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao definir bloco: {e}")
        return False


def delete_last_registro(client: Client) -> bool:
    try:
        res = (
            client.table("progresso_questoes")
            .select("id")
            .order("data_registro", desc=True)
            .limit(1)
            .execute()
        )
        if not res.data:
            return False
        last_id = res.data[0]["id"]
        client.table("progresso_questoes").delete().eq("id", last_id).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao desfazer registro: {e}")
        return False


def save_questoes(client: Client, materia: str, quantidade: int) -> bool:
    try:
        client.table("progresso_questoes").insert({
            "materia": materia,
            "quantidade": quantidade,
            "data_registro": datetime.utcnow().isoformat(),
        }).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar questões: {e}")
        return False


def fetch_weekly_totals(client: Client) -> dict[str, int]:
    since = (date.today() - timedelta(days=6)).isoformat()
    try:
        res = (
            client.table("progresso_questoes")
            .select("materia, quantidade")
            .gte("data_registro", since)
            .execute()
        )
        totals: dict[str, int] = {s: 0 for s in SUBJECTS}
        for row in res.data:
            m = row["materia"]
            if m in totals:
                totals[m] += row["quantidade"]
        return totals
    except Exception as e:
        st.error(f"Erro ao buscar totais: {e}")
        return {s: 0 for s in SUBJECTS}


def fetch_daily_minutes(client: Client) -> int:
    today = date.today().isoformat()
    try:
        res = (
            client.table("log_tempo")
            .select("minutos_estudados")
            .eq("data_registro", today)
            .execute()
        )
        return sum(r["minutos_estudados"] for r in res.data)
    except Exception as e:
        st.error(f"Erro ao buscar tempo: {e}")
        return 0


def save_tempo(client: Client, minutos: int) -> bool:
    try:
        client.table("log_tempo").insert({
            "data_registro": date.today().isoformat(),
            "minutos_estudados": minutos,
        }).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar tempo: {e}")
        return False


# ── UI helpers ────────────────────────────────────────────────────────────────

def render_cycle_dots(current_idx: int) -> str:
    dots = ""
    for i in range(len(CYCLE)):
        if i == current_idx:
            cls = "dot active"
        elif i < current_idx:
            cls = "dot done"
        else:
            cls = "dot"
        dots += f'<div class="{cls}" title="Bloco {i+1}: {CYCLE[i]}"></div>'
    return f'<div class="cycle-dots">{dots}</div>'


def render_block_card(idx: int) -> str:
    subject = CYCLE[idx]
    color   = SUBJECT_COLORS[subject]
    icon    = SUBJECT_ICONS[subject]
    return f"""
<div class="block-card" style="--accent: {color};">
    <div class="block-label">Bloco Atual · {idx + 1} de {len(CYCLE)}</div>
    <div class="block-subject" style="color:{color};">{subject}</div>
    <div class="block-index mono">CICLO #{idx + 1:02d} — próximo: {CYCLE[(idx + 1) % len(CYCLE)]}</div>
    <div class="subject-icon">{icon}</div>
</div>
"""


def render_kill_switch_status(total_minutes: int) -> str:
    hours   = total_minutes // 60
    minutes = total_minutes % 60
    label   = f"{hours}h {minutes:02d}m"
    if total_minutes >= KILL_SWITCH_MINUTES:
        return f"""
<div class="kill-alert">
    ⚠ KILL SWITCH — {label} estudados hoje.<br>
    Limite de 4h atingido. Descanse para consolidar o aprendizado.
</div>"""
    remaining = KILL_SWITCH_MINUTES - total_minutes
    r_h, r_m = remaining // 60, remaining % 60
    return f"""
<div class="kill-ok">
    ✓ {label} estudados — {r_h}h {r_m:02d}m restantes hoje.
</div>"""


# ── Main app ──────────────────────────────────────────────────────────────────

def main() -> None:
    st.set_page_config(
        page_title="ENEM Queue",
        page_icon="∑",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    client = get_supabase()

    # ── Sidebar — Kill Switch ─────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("## ∑ ENEM Queue")
        st.markdown('<div class="sidebar-section">Kill Switch · Tempo Diário</div>', unsafe_allow_html=True)

        col_h, col_m = st.columns(2)
        with col_h:
            horas = st.number_input("Horas", min_value=0, max_value=12, value=0, step=1, key="sb_h")
        with col_m:
            mins  = st.number_input("Min", min_value=0, max_value=59, value=0, step=5, key="sb_m")

        if st.button("Registrar Tempo", key="btn_tempo"):
            total_input = int(horas) * 60 + int(mins)
            if total_input > 0:
                if save_tempo(client, total_input):
                    st.success("Tempo registrado.")
                    st.cache_data.clear()
            else:
                st.warning("Insira um tempo maior que zero.")

        daily_minutes = fetch_daily_minutes(client)
        st.markdown(render_kill_switch_status(daily_minutes), unsafe_allow_html=True)

        st.markdown("---")
        st.markdown('<div class="sidebar-section">Controles do Ciclo</div>', unsafe_allow_html=True)

        # Voltar um bloco
        if st.button("← Voltar um bloco", key="btn_voltar"):
            current_idx = fetch_current_index(client)
            prev_idx = (current_idx - 1) % len(CYCLE)
            if set_index(client, prev_idx):
                st.success(f"Voltou para bloco {prev_idx + 1}: {CYCLE[prev_idx]}")
                st.rerun()

        # Desfazer último registro
        if st.button("↩ Desfazer último registro", key="btn_undo"):
            current_idx = fetch_current_index(client)
            prev_idx = (current_idx - 1) % len(CYCLE)
            if delete_last_registro(client):
                if set_index(client, prev_idx):
                    st.success("Último registro removido e bloco revertido.")
                    st.cache_data.clear()
                    st.rerun()
            else:
                st.warning("Nenhum registro encontrado para desfazer.")

        # Ir para bloco específico
        st.markdown('<div style="margin-top:8px"></div>', unsafe_allow_html=True)
        bloco_escolhido = st.selectbox(
            "Ir para bloco:",
            options=list(range(len(CYCLE))),
            format_func=lambda i: f"{i+1:02d} · {CYCLE[i]}",
            key="select_bloco",
        )
        if st.button("→ Ir para este bloco", key="btn_goto"):
            if set_index(client, bloco_escolhido):
                st.success(f"Bloco definido: {CYCLE[bloco_escolhido]}")
                st.rerun()

        st.markdown("---")
        st.markdown('<div class="sidebar-section">Ciclo de Execução</div>', unsafe_allow_html=True)
        for i, s in enumerate(CYCLE):
            color = SUBJECT_COLORS[s]
            st.markdown(
                f'<div style="font-family:\'DM Mono\',monospace;font-size:12px;'
                f'color:#44445A;padding:2px 0;">'
                f'<span style="color:{color};font-weight:600;">{i+1:02d}</span> · {s}</div>',
                unsafe_allow_html=True,
            )

    # ── Main content ──────────────────────────────────────────────────────────
    idx     = fetch_current_index(client)
    subject = CYCLE[idx]

    # Block card + cycle progress
    st.markdown(render_block_card(idx), unsafe_allow_html=True)
    st.markdown(render_cycle_dots(idx), unsafe_allow_html=True)

    # Input + action
    col_input, col_btn = st.columns([3, 1], gap="medium")
    with col_input:
        quantidade = st.number_input(
            "Questões resolvidas neste bloco",
            min_value=1,
            max_value=500,
            value=10,
            step=1,
            help="Quantas questões você resolveu agora?",
        )
    with col_btn:
        st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
        avancar = st.button("Registrar e Avançar →", type="primary", key="btn_avancar")

    if avancar:
        if save_questoes(client, subject, int(quantidade)):
            new_idx = advance_index(client, idx)
            st.success(f"✓ {int(quantidade)} questões de **{subject}** salvas. Próximo bloco: **{CYCLE[new_idx]}**.")
            st.cache_data.clear()
            st.rerun()

    # ── Weekly chart ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">Questões por Matéria — Últimos 7 Dias</div>', unsafe_allow_html=True)

    weekly = fetch_weekly_totals(client)
    total_week = sum(weekly.values())

    # Summary metric cards
    cols = st.columns(len(SUBJECTS))
    for col, s in zip(cols, SUBJECTS):
        with col:
            color = SUBJECT_COLORS[s]
            icon  = SUBJECT_ICONS[s]
            st.markdown(
                f'<div class="metric-card">'
                f'<div class="val" style="color:{color};">{weekly[s]}</div>'
                f'<div class="lbl">{icon} {s}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown(f'<div style="text-align:right;font-family:\'DM Mono\',monospace;'
                f'font-size:12px;color:#44445A;margin-bottom:16px;">'
                f'Total semanal: <span style="color:#E8E8F0;font-weight:600;">{total_week} questões</span></div>',
                unsafe_allow_html=True)

    # Plotly bar chart
    try:
        import plotly.graph_objects as go

        fig = go.Figure(
            go.Bar(
                x=SUBJECTS,
                y=[weekly[s] for s in SUBJECTS],
                marker_color=[SUBJECT_COLORS[s] for s in SUBJECTS],
                marker_line_width=0,
                text=[str(weekly[s]) for s in SUBJECTS],
                textposition="outside",
                textfont=dict(family="DM Mono", size=12, color="#E8E8F0"),
            )
        )
        fig.update_layout(
            plot_bgcolor="#0A0A0F",
            paper_bgcolor="#0A0A0F",
            font=dict(family="Syne", color="#888899"),
            xaxis=dict(showgrid=False, tickfont=dict(size=12)),
            yaxis=dict(showgrid=True, gridcolor="#1A1A2E", zeroline=False),
            margin=dict(l=0, r=0, t=16, b=0),
            height=260,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    except ImportError:
        chart_data = {s: [weekly[s]] for s in SUBJECTS}
        import pandas as pd
        st.bar_chart(pd.DataFrame(chart_data))


if __name__ == "__main__":
    main()
