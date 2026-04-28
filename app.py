"""
ENEM Study Queue Dashboard
Streamlit + Supabase (supabase-py)
"""

import os
import json
from datetime import date, datetime, timedelta

import streamlit as st
from supabase import Client, create_client

# ── Constants ────────────────────────────────────────────────────────────────

DEFAULT_CYCLE: list[str] = [
    "Matemática",
    "Linguagens",
    "Redação",
    "Matemática",
    "Humanas",
    "Matemática",
    "Redação",
    "Linguagens",
    "Matemática",
    "Natureza",
]

SUBJECTS: list[str] = ["Matemática", "Redação", "Linguagens", "Humanas", "Natureza"]

KILL_SWITCH_MINUTES = 240

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

html, body, [data-testid="stAppViewContainer"] {
    background-color: #0A0A0F !important;
    color: #E8E8F0 !important;
    font-family: 'Syne', sans-serif !important;
}
[data-testid="stSidebar"] {
    background-color: #0F0F1A !important;
    border-right: 1px solid #1E1E30 !important;
}
[data-testid="stHeader"] {
    background: #0A0A0F !important;
    border-bottom: 1px solid #1A1A2E !important;
}
[data-testid="stToolbar"] { display: none; }
[data-testid="stDecoration"] { display: none; }
[data-testid="stHeader"] button,
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    color: #E8E8F0 !important;
    z-index: 9999 !important;
}
[data-testid="stHeader"] button:hover { opacity: 0.7 !important; }

h1, h2, h3, h4, h5, h6 { font-family: 'Syne', sans-serif !important; }
.mono { font-family: 'DM Mono', monospace; }

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

.cycle-dots { display: flex; gap: 6px; margin-bottom: 28px; flex-wrap: wrap; }
.dot { width: 28px; height: 6px; border-radius: 3px; background: #1E1E30; transition: background 0.3s; }
.dot.active { background: var(--accent); }
.dot.done   { background: #2A2A45; }

.metric-card {
    background: #13131F;
    border: 1px solid #1E1E30;
    border-radius: 12px;
    padding: 16px 20px;
}
.metric-card .val { font-size: 28px; font-weight: 700; font-family: 'DM Mono', monospace; }
.metric-card .lbl { font-size: 11px; color: #55556A; letter-spacing: 2px; text-transform: uppercase; margin-top: 2px; }

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

/* Cycle builder drag item */
.cycle-item {
    display: flex;
    align-items: center;
    gap: 10px;
    background: #13131F;
    border: 1px solid #2A2A45;
    border-radius: 8px;
    padding: 8px 12px;
    margin-bottom: 6px;
    font-family: 'DM Mono', monospace;
    font-size: 13px;
}
.cycle-item-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    display: inline-block;
}

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

[data-testid="stButton"] > button[kind="secondary"] {
    background: #13131F !important;
    border: 1px solid #2A2A45 !important;
    border-radius: 10px !important;
    color: #888 !important;
    font-family: 'Syne', sans-serif !important;
    font-size: 13px !important;
    width: 100%;
}

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

[data-testid="stVegaLiteChart"] { border-radius: 12px; overflow: hidden; }
.stPlotlyChart { border-radius: 12px; }

.sidebar-section {
    font-size: 10px;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: #44445A;
    font-family: 'DM Mono', monospace;
    margin: 20px 0 10px;
}

[data-testid="stSelectbox"] > div > div {
    background: #13131F !important;
    border: 1px solid #2A2A45 !important;
    border-radius: 8px !important;
    color: #E8E8F0 !important;
}
</style>
"""

# ── Supabase ──────────────────────────────────────────────────────────────────

@st.cache_resource
def get_supabase() -> Client:
    url = os.environ.get("SUPABASE_URL") or st.secrets["SUPABASE_URL"]
    key = os.environ.get("SUPABASE_KEY") or st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


# ── Cycle persistence (session + localStorage via query params) ───────────────

def load_cycle() -> list[str]:
    """Carrega ciclo customizado da session_state ou retorna o padrão."""
    if "custom_cycle" not in st.session_state:
        st.session_state.custom_cycle = DEFAULT_CYCLE.copy()
    return st.session_state.custom_cycle


def save_cycle(cycle: list[str]) -> None:
    st.session_state.custom_cycle = cycle


# ── Data access ───────────────────────────────────────────────────────────────

def fetch_current_index(client: Client) -> int:
    try:
        res = client.table("estado_sistema").select("indice_bloco_atual").eq("id", 1).single().execute()
        return res.data["indice_bloco_atual"]
    except Exception as e:
        st.error(f"Erro ao buscar estado: {e}")
        return 0


def set_index(client: Client, idx: int) -> bool:
    cycle = load_cycle()
    safe_idx = idx % len(cycle)
    try:
        client.table("estado_sistema").update({"indice_bloco_atual": safe_idx}).eq("id", 1).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao definir bloco: {e}")
        return False


def advance_index(client: Client, current: int) -> int:
    cycle = load_cycle()
    next_idx = (current + 1) % len(cycle)
    try:
        client.table("estado_sistema").update({"indice_bloco_atual": next_idx}).eq("id", 1).execute()
    except Exception as e:
        st.error(f"Erro ao avançar bloco: {e}")
    return next_idx


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
        client.table("progresso_questoes").delete().eq("id", res.data[0]["id"]).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao desfazer registro: {e}")
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

def render_cycle_dots(current_idx: int, cycle: list[str]) -> str:
    dots = ""
    for i, s in enumerate(cycle):
        color = SUBJECT_COLORS[s]
        if i == current_idx:
            style = f"background:{color};"
            cls = "dot active"
        elif i < current_idx:
            cls = "dot done"
            style = ""
        else:
            cls = "dot"
            style = ""
        dots += f'<div class="{cls}" style="{style}" title="Bloco {i+1}: {s}"></div>'
    return f'<div class="cycle-dots">{dots}</div>'


def render_block_card(idx: int, cycle: list[str]) -> str:
    subject = cycle[idx]
    color   = SUBJECT_COLORS[subject]
    icon    = SUBJECT_ICONS[subject]
    next_s  = cycle[(idx + 1) % len(cycle)]
    return f"""
<div class="block-card" style="--accent: {color};">
    <div class="block-label">Bloco Atual · {idx + 1} de {len(cycle)}</div>
    <div class="block-subject" style="color:{color};">{subject}</div>
    <div class="block-index mono">CICLO #{idx + 1:02d} — próximo: {next_s}</div>
    <div class="subject-icon">{icon}</div>
</div>
"""


def render_kill_switch_status(total_minutes: int) -> str:
    hours   = total_minutes // 60
    minutes = total_minutes % 60
    label   = f"{hours}h {minutes:02d}m"
    if total_minutes >= KILL_SWITCH_MINUTES:
        return f'<div class="kill-alert">⚠ KILL SWITCH — {label} estudados hoje.<br>Limite de 4h atingido. Descanse.</div>'
    remaining = KILL_SWITCH_MINUTES - total_minutes
    r_h, r_m = remaining // 60, remaining % 60
    return f'<div class="kill-ok">✓ {label} estudados — {r_h}h {r_m:02d}m restantes hoje.</div>'


def render_cycle_preview(cycle: list[str]) -> str:
    items = ""
    for i, s in enumerate(cycle):
        color = SUBJECT_COLORS[s]
        icon  = SUBJECT_ICONS[s]
        items += (
            f'<div class="cycle-item">'
            f'<span class="cycle-item-dot" style="background:{color};"></span>'
            f'<span style="color:#44445A;font-size:11px;">{i+1:02d}</span>'
            f'<span style="color:{color};">{icon}</span>'
            f'<span style="color:#C8C8D8;">{s}</span>'
            f'</div>'
        )
    return items


# ── Cycle builder UI ──────────────────────────────────────────────────────────

def render_cycle_builder(cycle: list[str]) -> None:
    st.markdown('<div class="sidebar-section">🛠 Personalizar Ciclo</div>', unsafe_allow_html=True)

    with st.expander("Editar ordem do ciclo", expanded=False):
        st.caption("Monte seu ciclo adicionando blocos na ordem desejada.")

        # Preview atual
        st.markdown(render_cycle_preview(cycle), unsafe_allow_html=True)

        st.markdown("---")

        # Adicionar bloco
        col_add, col_btn = st.columns([2, 1])
        with col_add:
            nova_materia = st.selectbox(
                "Adicionar matéria:",
                SUBJECTS,
                key="sb_nova_materia",
                label_visibility="collapsed",
            )
        with col_btn:
            if st.button("＋ Add", key="btn_add_bloco"):
                new_cycle = cycle + [nova_materia]
                save_cycle(new_cycle)
                st.rerun()

        # Remover último bloco
        col_rem, col_rst = st.columns(2)
        with col_rem:
            if st.button("－ Remover último", key="btn_rem_ultimo"):
                if len(cycle) > 1:
                    save_cycle(cycle[:-1])
                    st.rerun()
                else:
                    st.warning("O ciclo precisa ter ao menos 1 bloco.")

        # Mover bloco (subir/descer por índice)
        st.markdown("**Reordenar bloco:**")
        col_idx, col_up, col_dn = st.columns([2, 1, 1])
        with col_idx:
            bloco_idx = st.number_input(
                "Nº do bloco",
                min_value=1,
                max_value=len(cycle),
                value=1,
                step=1,
                key="sb_bloco_idx",
                label_visibility="collapsed",
            )
        with col_up:
            if st.button("↑ Subir", key="btn_up"):
                i = int(bloco_idx) - 1
                if i > 0:
                    c = cycle.copy()
                    c[i], c[i - 1] = c[i - 1], c[i]
                    save_cycle(c)
                    st.rerun()
        with col_dn:
            if st.button("↓ Descer", key="btn_dn"):
                i = int(bloco_idx) - 1
                if i < len(cycle) - 1:
                    c = cycle.copy()
                    c[i], c[i + 1] = c[i + 1], c[i]
                    save_cycle(c)
                    st.rerun()

        # Remover bloco específico
        if st.button("🗑 Remover bloco selecionado", key="btn_rem_spec"):
            i = int(bloco_idx) - 1
            if len(cycle) > 1:
                c = cycle.copy()
                c.pop(i)
                save_cycle(c)
                st.rerun()
            else:
                st.warning("O ciclo precisa ter ao menos 1 bloco.")

        st.markdown("---")

        # Restaurar padrão
        with col_rst:
            if st.button("↺ Padrão", key="btn_rst"):
                save_cycle(DEFAULT_CYCLE.copy())
                st.rerun()

        st.caption(f"**{len(cycle)} blocos** no ciclo atual.")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    st.set_page_config(
        page_title="ENEM Queue",
        page_icon="∑",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    client  = get_supabase()
    cycle   = load_cycle()

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("## ∑ ENEM Queue")

        # Kill Switch
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

        # Controles do ciclo
        st.markdown('<div class="sidebar-section">Controles do Ciclo</div>', unsafe_allow_html=True)

        if st.button("← Voltar um bloco", key="btn_voltar"):
            current_idx = fetch_current_index(client)
            prev_idx = (current_idx - 1) % len(cycle)
            if set_index(client, prev_idx):
                st.success(f"Voltou para bloco {prev_idx + 1}: {cycle[prev_idx]}")
                st.rerun()

        if st.button("↩ Desfazer último registro", key="btn_undo"):
            current_idx = fetch_current_index(client)
            prev_idx = (current_idx - 1) % len(cycle)
            if delete_last_registro(client):
                if set_index(client, prev_idx):
                    st.success("Último registro removido e bloco revertido.")
                    st.cache_data.clear()
                    st.rerun()
            else:
                st.warning("Nenhum registro encontrado para desfazer.")

        st.markdown('<div style="margin-top:8px"></div>', unsafe_allow_html=True)
        bloco_escolhido = st.selectbox(
            "Ir para bloco:",
            options=list(range(len(cycle))),
            format_func=lambda i: f"{i+1:02d} · {cycle[i]}",
            key="select_bloco",
        )
        if st.button("→ Ir para este bloco", key="btn_goto"):
            if set_index(client, bloco_escolhido):
                st.success(f"Bloco definido: {cycle[bloco_escolhido]}")
                st.rerun()

        st.markdown("---")

        # Cycle builder
        render_cycle_builder(cycle)

        # Preview do ciclo atual
        st.markdown('<div class="sidebar-section">Ciclo de Execução</div>', unsafe_allow_html=True)
        current_idx_preview = fetch_current_index(client)
        for i, s in enumerate(cycle):
            color   = SUBJECT_COLORS[s]
            is_curr = i == current_idx_preview
            weight  = "700" if is_curr else "400"
            bg      = f"background:rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.08);border-radius:6px;padding:2px 6px;" if is_curr else "padding:2px 6px;"
            st.markdown(
                f'<div style="font-family:\'DM Mono\',monospace;font-size:12px;color:#44445A;{bg}margin-bottom:2px;">'
                f'<span style="color:{color};font-weight:{weight};">{i+1:02d}</span> · '
                f'<span style="color:{"#E8E8F0" if is_curr else "#88889A"};font-weight:{weight};">{s}</span>'
                f'{"  ◀" if is_curr else ""}</div>',
                unsafe_allow_html=True,
            )

    # ── Main content ──────────────────────────────────────────────────────────
    idx     = fetch_current_index(client)
    safe_idx = idx % len(cycle)
    subject  = cycle[safe_idx]

    st.markdown(render_block_card(safe_idx, cycle), unsafe_allow_html=True)
    st.markdown(render_cycle_dots(safe_idx, cycle), unsafe_allow_html=True)

    col_input, col_btn = st.columns([3, 1], gap="medium")
    with col_input:
        quantidade = st.number_input(
            "Questões resolvidas neste bloco",
            min_value=1, max_value=500, value=10, step=1,
            help="Quantas questões você resolveu agora?",
        )
    with col_btn:
        st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
        avancar = st.button("Registrar e Avançar →", type="primary", key="btn_avancar")

    if avancar:
        if save_questoes(client, subject, int(quantidade)):
            new_idx = advance_index(client, safe_idx)
            st.success(f"✓ {int(quantidade)} questões de **{subject}** salvas. Próximo: **{cycle[new_idx]}**.")
            st.cache_data.clear()
            st.rerun()

    # ── Weekly chart ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">Questões por Matéria — Últimos 7 Dias</div>', unsafe_allow_html=True)

    weekly     = fetch_weekly_totals(client)
    total_week = sum(weekly.values())

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

    st.markdown(
        f'<div style="text-align:right;font-family:\'DM Mono\',monospace;font-size:12px;color:#44445A;margin-bottom:16px;">'
        f'Total semanal: <span style="color:#E8E8F0;font-weight:600;">{total_week} questões</span></div>',
        unsafe_allow_html=True,
    )

    try:
        import plotly.graph_objects as go
        fig = go.Figure(go.Bar(
            x=SUBJECTS,
            y=[weekly[s] for s in SUBJECTS],
            marker_color=[SUBJECT_COLORS[s] for s in SUBJECTS],
            marker_line_width=0,
            text=[str(weekly[s]) for s in SUBJECTS],
            textposition="outside",
            textfont=dict(family="DM Mono", size=12, color="#E8E8F0"),
        ))
        fig.update_layout(
            plot_bgcolor="#0A0A0F", paper_bgcolor="#0A0A0F",
            font=dict(family="Syne", color="#888899"),
            xaxis=dict(showgrid=False, tickfont=dict(size=12)),
            yaxis=dict(showgrid=True, gridcolor="#1A1A2E", zeroline=False),
            margin=dict(l=0, r=0, t=16, b=0),
            height=260,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    except ImportError:
        import pandas as pd
        st.bar_chart(pd.DataFrame({s: [weekly[s]] for s in SUBJECTS}))


if __name__ == "__main__":
    main()
