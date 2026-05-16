"""
ENEM Ultimate Dashboard
Streamlit + Supabase — Sistema completo de aprovação
"""

import os
import json
import random
from datetime import date, datetime, timedelta
from collections import defaultdict

import streamlit as st
from supabase import Client, create_client

# ── Constants ─────────────────────────────────────────────────────────────────

DEFAULT_CYCLE: list[str] = [
    "Matemática", "Linguagens", "Redação", "Matemática", "Humanas",
    "Matemática", "Redação", "Linguagens", "Matemática", "Natureza",
]

SUBJECTS: list[str] = ["Matemática", "Redação", "Linguagens", "Humanas", "Natureza"]

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

KILL_SWITCH_MINUTES = 240

FRASES_FOCO = [
    "A aprovação pertence a quem executa, não a quem planeja.",
    "Cada questão resolvida é um ponto a mais na sua nota.",
    "Consistência bate talento quando talento não é consistente.",
    "O ENEM não reprova quem estuda todos os dias.",
    "Hoje é o dia mais próximo da sua aprovação. Não desperdice.",
    "Médicos não nascem prontos. Eles são construídos questão por questão.",
    "Foco. Execução. Resultado. Nessa ordem.",
    "Quem resolve mais questões, erra menos na prova.",
]

POMODORO_WORK  = 25 * 60
POMODORO_BREAK = 5  * 60

META_DIARIA_QUESTOES = 30
META_SEMANAL_HORAS   = 20

# ── CSS ───────────────────────────────────────────────────────────────────────

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@400;600;700;800&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background-color: #07070F !important;
    color: #E8E8F0 !important;
    font-family: 'Syne', sans-serif !important;
}
[data-testid="stSidebar"] {
    background-color: #0C0C18 !important;
    border-right: 1px solid #1A1A2E !important;
}
[data-testid="stHeader"] {
    background: #07070F !important;
    border-bottom: 1px solid #1A1A2E !important;
}
[data-testid="stToolbar"] { display: none; }
[data-testid="stDecoration"] { display: none; }
[data-testid="stHeader"] button,
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"] {
    display: flex !important; visibility: visible !important;
    opacity: 1 !important; color: #E8E8F0 !important; z-index: 9999 !important;
}

/* Tabs */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: #0C0C18 !important;
    border-radius: 12px !important;
    padding: 4px !important;
    gap: 4px !important;
    border: 1px solid #1A1A2E !important;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 8px !important;
    color: #55556A !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    padding: 8px 20px !important;
    border: none !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    background: #1A1A2E !important;
    color: #E8E8F0 !important;
}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] { display: none !important; }
[data-testid="stTabs"] [data-baseweb="tab-border"]    { display: none !important; }

/* Cards */
.hero-card {
    background: linear-gradient(135deg, #0F0F1F 0%, #171730 100%);
    border: 1px solid #2A2A45;
    border-radius: 20px;
    padding: 28px 32px;
    position: relative;
    overflow: hidden;
    margin-bottom: 20px;
}
.hero-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 2px;
    background: var(--accent, #6C63FF);
}
.hero-label {
    font-size: 10px; letter-spacing: 3px; text-transform: uppercase;
    color: #555570; font-family: 'DM Mono', monospace; margin-bottom: 6px;
}
.hero-subject {
    font-size: 40px; font-weight: 800; line-height: 1; margin-bottom: 4px;
}
.hero-sub {
    font-family: 'DM Mono', monospace; font-size: 11px; color: #3A3A55; margin-top: 8px;
}
.hero-icon {
    font-size: 72px; position: absolute; right: 32px; top: 50%;
    transform: translateY(-50%); opacity: 0.08; line-height: 1;
}

/* Metric cards */
.stat-card {
    background: #0F0F1A;
    border: 1px solid #1E1E30;
    border-radius: 14px;
    padding: 18px 20px;
    height: 100%;
}
.stat-val {
    font-size: 32px; font-weight: 800;
    font-family: 'DM Mono', monospace; line-height: 1;
}
.stat-lbl {
    font-size: 10px; color: #44445A; letter-spacing: 2px;
    text-transform: uppercase; margin-top: 4px;
}
.stat-sub { font-size: 11px; color: #33334A; margin-top: 2px; font-family: 'DM Mono', monospace; }

/* Progress bar */
.prog-wrap { margin: 8px 0 16px; }
.prog-label { display: flex; justify-content: space-between; font-size: 11px; color: #44445A; margin-bottom: 4px; font-family: 'DM Mono', monospace; }
.prog-bar { height: 6px; background: #1A1A2E; border-radius: 3px; overflow: hidden; }
.prog-fill { height: 100%; border-radius: 3px; transition: width 0.5s ease; }

/* Dots */
.cycle-dots { display: flex; gap: 5px; margin-bottom: 24px; flex-wrap: wrap; }
.dot { width: 24px; height: 5px; border-radius: 3px; background: #1A1A2E; }
.dot.active { background: var(--accent, #6C63FF); }
.dot.done   { background: #252535; }

/* Buttons */
[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(135deg, #6C63FF, #9B59B6) !important;
    border: none !important; border-radius: 10px !important;
    padding: 12px 28px !important; font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important; font-size: 14px !important;
    letter-spacing: 0.5px !important; color: #fff !important; width: 100%;
    transition: opacity 0.2s !important;
}
[data-testid="stButton"] > button[kind="primary"]:hover { opacity: 0.82 !important; }
[data-testid="stButton"] > button[kind="secondary"] {
    background: #0F0F1A !important; border: 1px solid #2A2A45 !important;
    border-radius: 10px !important; color: #777 !important;
    font-family: 'Syne', sans-serif !important; font-size: 13px !important; width: 100%;
}

/* Inputs */
[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input,
textarea {
    background: #0F0F1A !important; border: 1px solid #2A2A45 !important;
    border-radius: 8px !important; color: #E8E8F0 !important;
    font-family: 'DM Mono', monospace !important;
}
[data-testid="stNumberInput"] input:focus,
[data-testid="stTextInput"] input:focus,
textarea:focus {
    border-color: #6C63FF !important;
    box-shadow: 0 0 0 2px rgba(108,99,255,0.15) !important;
}
[data-testid="stSelectbox"] > div > div {
    background: #0F0F1A !important; border: 1px solid #2A2A45 !important;
    border-radius: 8px !important; color: #E8E8F0 !important;
}

/* Alerts */
.alert-red {
    background: rgba(255,60,60,0.07); border: 1px solid rgba(255,60,60,0.35);
    border-radius: 10px; padding: 12px 16px; color: #FF6B6B;
    font-size: 13px; font-weight: 600; margin: 10px 0;
}
.alert-green {
    background: rgba(67,217,173,0.06); border: 1px solid rgba(67,217,173,0.2);
    border-radius: 10px; padding: 12px 16px; color: #43D9AD;
    font-size: 13px; margin: 10px 0;
}
.alert-yellow {
    background: rgba(255,179,71,0.07); border: 1px solid rgba(255,179,71,0.3);
    border-radius: 10px; padding: 12px 16px; color: #FFB347;
    font-size: 13px; margin: 10px 0;
}

/* Section title */
.section-title {
    font-size: 10px; letter-spacing: 4px; text-transform: uppercase;
    color: #33334A; font-family: 'DM Mono', monospace;
    margin: 24px 0 14px; border-bottom: 1px solid #141420; padding-bottom: 8px;
}

/* Frase */
.frase-card {
    background: linear-gradient(135deg, #0C0C1A, #12122A);
    border: 1px solid #1E1E35; border-radius: 12px;
    padding: 16px 20px; margin-bottom: 20px; text-align: center;
    font-style: italic; color: #6060A0; font-size: 13px; line-height: 1.6;
}

/* Pomodoro */
.pomo-display {
    font-family: 'DM Mono', monospace; font-size: 64px; font-weight: 500;
    text-align: center; line-height: 1; padding: 20px 0;
    background: #0F0F1A; border: 1px solid #2A2A45;
    border-radius: 16px; margin: 16px 0;
}
.pomo-phase {
    text-align: center; font-size: 11px; letter-spacing: 3px;
    text-transform: uppercase; font-family: 'DM Mono', monospace;
    margin-bottom: 8px;
}

/* Streak */
.streak-num {
    font-size: 52px; font-weight: 800; font-family: 'DM Mono', monospace;
    line-height: 1; color: #FFB347;
}

/* XP bar */
.xp-wrap { margin: 12px 0; }
.xp-label { font-size: 10px; color: #44445A; letter-spacing: 2px; font-family: 'DM Mono', monospace; margin-bottom: 4px; }
.xp-bar { height: 8px; background: #1A1A2E; border-radius: 4px; overflow: hidden; }
.xp-fill { height: 100%; border-radius: 4px; background: linear-gradient(90deg, #6C63FF, #FF6584); }

/* Sidebar section */
.sb-section {
    font-size: 9px; letter-spacing: 3px; text-transform: uppercase;
    color: #33334A; font-family: 'DM Mono', monospace; margin: 18px 0 8px;
}

/* Erros card */
.erro-card {
    background: #0F0F1A; border: 1px solid #2A2A45;
    border-left: 3px solid; border-radius: 8px;
    padding: 10px 14px; margin-bottom: 8px; font-size: 13px;
}

/* Sticker badges */
.badge {
    display: inline-block; padding: 3px 10px; border-radius: 20px;
    font-size: 10px; font-family: 'DM Mono', monospace; letter-spacing: 1px;
    font-weight: 600; margin-right: 4px; margin-bottom: 4px;
}
</style>
"""

# ── Supabase ──────────────────────────────────────────────────────────────────

@st.cache_resource
def get_supabase() -> Client:
    url = os.environ.get("SUPABASE_URL") or st.secrets["SUPABASE_URL"]
    key = os.environ.get("SUPABASE_KEY") or st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

# ── Session helpers ───────────────────────────────────────────────────────────

def load_cycle() -> list[str]:
    if "custom_cycle" not in st.session_state:
        st.session_state.custom_cycle = DEFAULT_CYCLE.copy()
    return st.session_state.custom_cycle

def save_cycle(cycle: list[str]) -> None:
    st.session_state.custom_cycle = cycle

def init_pomodoro() -> None:
    if "pomo_running"   not in st.session_state: st.session_state.pomo_running   = False
    if "pomo_phase"     not in st.session_state: st.session_state.pomo_phase     = "work"
    if "pomo_remaining" not in st.session_state: st.session_state.pomo_remaining = POMODORO_WORK
    if "pomo_cycles"    not in st.session_state: st.session_state.pomo_cycles    = 0
    if "pomo_last_tick" not in st.session_state: st.session_state.pomo_last_tick = None

# ── DB helpers ────────────────────────────────────────────────────────────────

def fetch_current_index(client: Client) -> int:
    try:
        res = client.table("estado_sistema").select("indice_bloco_atual").eq("id", 1).single().execute()
        return res.data["indice_bloco_atual"]
    except Exception as e:
        st.error(f"Erro ao buscar estado: {e}"); return 0

def set_index(client: Client, idx: int) -> bool:
    cycle = load_cycle()
    try:
        client.table("estado_sistema").update({"indice_bloco_atual": idx % len(cycle)}).eq("id", 1).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao definir bloco: {e}"); return False

def advance_index(client: Client, current: int) -> int:
    cycle = load_cycle()
    next_idx = (current + 1) % len(cycle)
    try:
        client.table("estado_sistema").update({"indice_bloco_atual": next_idx}).eq("id", 1).execute()
    except Exception as e:
        st.error(f"Erro ao avançar: {e}")
    return next_idx

def save_questoes(client: Client, materia: str, quantidade: int, acertos: int) -> bool:
    try:
        client.table("progresso_questoes").insert({
            "materia": materia, "quantidade": quantidade,
            "acertos": acertos,
            "data_registro": datetime.utcnow().isoformat(),
        }).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar questões: {e}"); return False

def delete_last_registro(client: Client) -> bool:
    try:
        res = (client.table("progresso_questoes").select("id")
               .order("data_registro", desc=True).limit(1).execute())
        if not res.data: return False
        client.table("progresso_questoes").delete().eq("id", res.data[0]["id"]).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao desfazer: {e}"); return False

def fetch_weekly_data(client: Client) -> list[dict]:
    since = (date.today() - timedelta(days=6)).isoformat()
    try:
        res = (client.table("progresso_questoes")
               .select("materia, quantidade, acertos, data_registro")
               .gte("data_registro", since).execute())
        return res.data or []
    except Exception as e:
        st.error(f"Erro ao buscar dados: {e}"); return []

def fetch_all_data(client: Client) -> list[dict]:
    try:
        res = (client.table("progresso_questoes")
               .select("materia, quantidade, acertos, data_registro")
               .order("data_registro", desc=False).execute())
        return res.data or []
    except Exception as e:
        st.error(f"Erro ao buscar histórico: {e}"); return []

def fetch_daily_minutes(client: Client) -> int:
    today = date.today().isoformat()
    try:
        res = (client.table("log_tempo").select("minutos_estudados")
               .eq("data_registro", today).execute())
        return sum(r["minutos_estudados"] for r in res.data)
    except Exception as e:
        st.error(f"Erro ao buscar tempo: {e}"); return 0

def save_tempo(client: Client, minutos: int) -> bool:
    try:
        client.table("log_tempo").insert({
            "data_registro": date.today().isoformat(),
            "minutos_estudados": minutos,
        }).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar tempo: {e}"); return False

def save_erro(client: Client, materia: str, topico: str, descricao: str) -> bool:
    try:
        client.table("caderno_erros").insert({
            "materia": materia, "topico": topico, "descricao": descricao,
            "revisado": False, "data_registro": datetime.utcnow().isoformat(),
        }).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar: {e}"); return False

def fetch_erros(client: Client, apenas_pendentes: bool = False) -> list[dict]:
    try:
        q = client.table("caderno_erros").select("*").order("data_registro", desc=True)
        if apenas_pendentes:
            q = q.eq("revisado", False)
        return q.execute().data or []
    except Exception as e:
        st.error(f"Erro ao buscar caderno: {e}"); return []

def marcar_revisado(client: Client, erro_id: int) -> None:
    try:
        client.table("caderno_erros").update({"revisado": True}).eq("id", erro_id).execute()
    except Exception as e:
        st.error(f"Erro: {e}")

def fetch_metas(client: Client) -> dict:
    try:
        res = client.table("metas").select("*").eq("id", 1).single().execute()
        return res.data or {}
    except:
        return {}

def save_meta(client: Client, meta_q: int, meta_h: int, nota_alvo: float) -> None:
    try:
        client.table("metas").upsert({
            "id": 1, "meta_questoes_dia": meta_q,
            "meta_horas_semana": meta_h, "nota_alvo": nota_alvo,
        }).execute()
    except Exception as e:
        st.error(f"Erro ao salvar meta: {e}")

# ── Analytics helpers ─────────────────────────────────────────────────────────

def compute_streak(data: list[dict]) -> int:
    if not data: return 0
    dias = sorted({r["data_registro"][:10] for r in data}, reverse=True)
    streak = 0
    cur = date.today()
    for d in dias:
        if date.fromisoformat(d) == cur:
            streak += 1
            cur -= timedelta(days=1)
        elif date.fromisoformat(d) == cur - timedelta(days=1):
            cur -= timedelta(days=1)
            streak += 1
        else:
            break
    return streak

def compute_xp(data: list[dict]) -> int:
    xp = 0
    for r in data:
        xp += r.get("quantidade", 0) * 2
        acertos = r.get("acertos") or 0
        xp += acertos * 3
    return xp

def xp_level(xp: int) -> tuple[int, int, int]:
    level = 1
    threshold = 100
    while xp >= threshold:
        xp -= threshold
        level += 1
        threshold = int(threshold * 1.4)
    return level, xp, threshold

def taxa_acerto(data: list[dict]) -> dict[str, float]:
    totais = defaultdict(int)
    acertos_map = defaultdict(int)
    for r in data:
        totais[r["materia"]]   += r.get("quantidade", 0)
        acertos_map[r["materia"]] += r.get("acertos") or 0
    result = {}
    for s in SUBJECTS:
        t = totais[s]
        result[s] = round(acertos_map[s] / t * 100, 1) if t > 0 else 0.0
    return result

def questoes_por_dia(data: list[dict]) -> dict[str, int]:
    by_day: dict[str, int] = defaultdict(int)
    for r in data:
        by_day[r["data_registro"][:10]] += r.get("quantidade", 0)
    return dict(by_day)

def nota_estimada(taxa: dict[str, float]) -> float:
    pesos = {"Matemática": 4, "Redação": 2, "Linguagens": 2, "Humanas": 1, "Natureza": 1}
    total_peso = sum(pesos.values())
    nota = sum((taxa.get(s, 0) / 100) * 1000 * pesos[s] / total_peso for s in SUBJECTS)
    return round(nota, 1)

# ── UI components ─────────────────────────────────────────────────────────────

def render_block_card(idx: int, cycle: list[str]) -> str:
    s     = cycle[idx]
    color = SUBJECT_COLORS[s]
    icon  = SUBJECT_ICONS[s]
    next_s = cycle[(idx + 1) % len(cycle)]
    return f"""
<div class="hero-card" style="--accent:{color};">
    <div class="hero-label">Bloco Atual · {idx+1} de {len(cycle)}</div>
    <div class="hero-subject" style="color:{color};">{s}</div>
    <div class="hero-sub">CICLO #{idx+1:02d} — próximo: {next_s}</div>
    <div class="hero-icon">{icon}</div>
</div>"""

def render_dots(idx: int, cycle: list[str]) -> str:
    dots = ""
    for i, s in enumerate(cycle):
        color = SUBJECT_COLORS[s]
        if i == idx:
            style = f"background:{color};"
            cls = "dot active"
        elif i < idx:
            cls = "dot done"; style = ""
        else:
            cls = "dot"; style = ""
        dots += f'<div class="{cls}" style="{style}" title="{i+1}. {s}"></div>'
    return f'<div class="cycle-dots">{dots}</div>'

def render_progress_bar(label: str, value: float, max_val: float, color: str) -> str:
    pct = min(value / max_val * 100, 100) if max_val > 0 else 0
    return f"""
<div class="prog-wrap">
  <div class="prog-label"><span>{label}</span><span>{value:.0f} / {max_val:.0f}</span></div>
  <div class="prog-bar"><div class="prog-fill" style="width:{pct:.1f}%;background:{color};"></div></div>
</div>"""

def render_stat_card(val, label: str, sub: str, color: str) -> str:
    return f"""
<div class="stat-card">
  <div class="stat-val" style="color:{color};">{val}</div>
  <div class="stat-lbl">{label}</div>
  <div class="stat-sub">{sub}</div>
</div>"""

def render_kill_status(total_min: int) -> str:
    h, m = divmod(total_min, 60)
    label = f"{h}h {m:02d}m"
    if total_min >= KILL_SWITCH_MINUTES:
        return f'<div class="alert-red">⚠ KILL SWITCH — {label} hoje. Limite atingido. Descanse!</div>'
    rem_h, rem_m = divmod(KILL_SWITCH_MINUTES - total_min, 60)
    return f'<div class="alert-green">✓ {label} estudados — {rem_h}h {rem_m:02d}m restantes</div>'

def render_taxa_badge(taxa: float) -> str:
    if taxa >= 80:   return f'<span class="badge" style="background:rgba(67,217,173,0.15);color:#43D9AD;">✓ {taxa}%</span>'
    elif taxa >= 60: return f'<span class="badge" style="background:rgba(255,179,71,0.15);color:#FFB347;">◎ {taxa}%</span>'
    else:            return f'<span class="badge" style="background:rgba(255,101,132,0.15);color:#FF6584;">✗ {taxa}%</span>'

# ── Pomodoro ──────────────────────────────────────────────────────────────────

def render_pomodoro() -> None:
    init_pomodoro()

    # Tick
    if st.session_state.pomo_running and st.session_state.pomo_last_tick:
        elapsed = (datetime.now() - st.session_state.pomo_last_tick).seconds
        st.session_state.pomo_remaining = max(0, st.session_state.pomo_remaining - elapsed)

    if st.session_state.pomo_remaining == 0:
        if st.session_state.pomo_phase == "work":
            st.session_state.pomo_cycles    += 1
            st.session_state.pomo_phase      = "break"
            st.session_state.pomo_remaining  = POMODORO_BREAK
        else:
            st.session_state.pomo_phase     = "work"
            st.session_state.pomo_remaining = POMODORO_WORK
        st.session_state.pomo_running = False

    st.session_state.pomo_last_tick = datetime.now()

    rem  = st.session_state.pomo_remaining
    mins = rem // 60
    secs = rem % 60

    phase_label = "🔴 FOCO" if st.session_state.pomo_phase == "work" else "🟢 DESCANSO"
    phase_color = "#6C63FF" if st.session_state.pomo_phase == "work" else "#43D9AD"

    st.markdown(f'<div class="pomo-phase" style="color:{phase_color};">{phase_label}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="pomo-display" style="color:{phase_color};">{mins:02d}:{secs:02d}</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("▶ Start" if not st.session_state.pomo_running else "⏸ Pause", key="pomo_start"):
            st.session_state.pomo_running = not st.session_state.pomo_running
            st.rerun()
    with col2:
        if st.button("⏹ Reset", key="pomo_reset"):
            st.session_state.pomo_running   = False
            st.session_state.pomo_phase     = "work"
            st.session_state.pomo_remaining = POMODORO_WORK
            st.rerun()
    with col3:
        st.markdown(f'<div style="text-align:center;font-family:\'DM Mono\',monospace;font-size:12px;color:#44445A;padding-top:10px;">🍅 {st.session_state.pomo_cycles} ciclos</div>', unsafe_allow_html=True)

    if st.session_state.pomo_running:
        import time; time.sleep(1); st.rerun()

# ── Cycle builder ─────────────────────────────────────────────────────────────

def render_cycle_builder(cycle: list[str]) -> None:
    with st.expander("🛠 Personalizar Ciclo", expanded=False):
        for i, s in enumerate(cycle):
            color = SUBJECT_COLORS[s]
            st.markdown(
                f'<div class="erro-card" style="border-left-color:{color};">'
                f'<span style="color:{color};font-family:\'DM Mono\',monospace;font-size:12px;">'
                f'{i+1:02d} · {SUBJECT_ICONS[s]} {s}</span></div>',
                unsafe_allow_html=True,
            )
        st.markdown("---")
        col_s, col_a = st.columns([2,1])
        with col_s:
            nm = st.selectbox("Matéria:", SUBJECTS, key="sb_nm", label_visibility="collapsed")
        with col_a:
            if st.button("＋ Add", key="btn_add"):
                save_cycle(cycle + [nm]); st.rerun()
        c1, c2 = st.columns(2)
        with c1:
            if st.button("－ Último", key="btn_rem"):
                if len(cycle) > 1: save_cycle(cycle[:-1]); st.rerun()
        with c2:
            if st.button("↺ Padrão", key="btn_rst"):
                save_cycle(DEFAULT_CYCLE.copy()); st.rerun()
        bi = st.number_input("Bloco nº:", min_value=1, max_value=len(cycle), step=1, key="bi", label_visibility="collapsed")
        cu, cd = st.columns(2)
        with cu:
            if st.button("↑ Subir", key="btn_up"):
                i = int(bi)-1
                if i > 0:
                    c = cycle.copy(); c[i], c[i-1] = c[i-1], c[i]; save_cycle(c); st.rerun()
        with cd:
            if st.button("↓ Descer", key="btn_dn"):
                i = int(bi)-1
                if i < len(cycle)-1:
                    c = cycle.copy(); c[i], c[i+1] = c[i+1], c[i]; save_cycle(c); st.rerun()

# ── TABS ──────────────────────────────────────────────────────────────────────

def tab_execucao(client: Client, cycle: list[str]) -> None:
    idx      = fetch_current_index(client)
    safe_idx = idx % len(cycle)
    subject  = cycle[safe_idx]

    # Frase motivacional
    frase = random.choice(FRASES_FOCO)
    st.markdown(f'<div class="frase-card">"{frase}"</div>', unsafe_allow_html=True)

    # Block card + dots
    st.markdown(render_block_card(safe_idx, cycle), unsafe_allow_html=True)
    st.markdown(render_dots(safe_idx, cycle), unsafe_allow_html=True)

    # Input de questões + acertos
    col1, col2 = st.columns(2)
    with col1:
        quantidade = st.number_input("Questões resolvidas", min_value=1, max_value=500, value=10, step=1)
    with col2:
        acertos = st.number_input("Acertos", min_value=0, max_value=500, value=7, step=1)

    if acertos > quantidade:
        st.markdown('<div class="alert-yellow">⚠ Acertos não pode ser maior que questões resolvidas.</div>', unsafe_allow_html=True)
        acertos = quantidade

    taxa_atual = round(acertos / quantidade * 100, 1) if quantidade > 0 else 0
    color_taxa = "#43D9AD" if taxa_atual >= 70 else "#FFB347" if taxa_atual >= 50 else "#FF6584"
    st.markdown(
        f'<div style="font-family:\'DM Mono\',monospace;font-size:12px;color:{color_taxa};">'
        f'Taxa de acerto neste bloco: <strong>{taxa_atual}%</strong></div>',
        unsafe_allow_html=True,
    )

    col_btn, col_ctrl = st.columns([2, 1])
    with col_btn:
        st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)
        if st.button("Registrar e Avançar →", type="primary", key="btn_avancar"):
            if save_questoes(client, subject, int(quantidade), int(acertos)):
                new_idx = advance_index(client, safe_idx)
                st.success(f"✓ {int(quantidade)} questões de **{subject}** salvas ({taxa_atual}% de acerto). Próximo: **{cycle[new_idx]}**.")
                st.cache_data.clear()
                st.rerun()

    st.markdown('<div class="section-title">Pomodoro Timer</div>', unsafe_allow_html=True)
    render_pomodoro()


def tab_dashboard(client: Client) -> None:
    all_data  = fetch_all_data(client)
    week_data = [r for r in all_data if r["data_registro"][:10] >= (date.today() - timedelta(days=6)).isoformat()]

    metas   = fetch_metas(client)
    meta_q  = metas.get("meta_questoes_dia", META_DIARIA_QUESTOES)
    meta_h  = metas.get("meta_horas_semana", META_SEMANAL_HORAS)
    nota_alvo = metas.get("nota_alvo", 750.0)

    streak     = compute_streak(all_data)
    total_xp   = compute_xp(all_data)
    level, xp_cur, xp_next = xp_level(total_xp)
    taxa       = taxa_acerto(all_data)
    nota_est   = nota_estimada(taxa)
    total_q_semana = sum(r.get("quantidade",0) for r in week_data)
    daily_min  = fetch_daily_minutes(client)

    # Top stats
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(render_stat_card(
            f"🔥 {streak}", "Streak de dias", f"{'Incrível!' if streak>=7 else 'Continue!'}", "#FFB347"
        ), unsafe_allow_html=True)
    with c2:
        st.markdown(render_stat_card(
            f"Nv {level}", "Seu nível", f"{total_xp} XP total", "#6C63FF"
        ), unsafe_allow_html=True)
    with c3:
        st.markdown(render_stat_card(
            f"{nota_est}", "Nota estimada", f"Alvo: {nota_alvo}", "#43D9AD"
        ), unsafe_allow_html=True)
    with c4:
        h, m = divmod(daily_min, 60)
        st.markdown(render_stat_card(
            f"{h}h{m:02d}", "Hoje estudado", f"Meta: 4h/dia", "#FF6584"
        ), unsafe_allow_html=True)

    # XP bar
    st.markdown(f"""
<div class="xp-wrap">
  <div class="xp-label">XP — Nível {level} → {level+1}</div>
  <div class="xp-bar"><div class="xp-fill" style="width:{min(xp_cur/xp_next*100,100):.1f}%;"></div></div>
</div>""", unsafe_allow_html=True)

    # Metas da semana
    st.markdown('<div class="section-title">Metas da Semana</div>', unsafe_allow_html=True)
    meta_q_total = meta_q * 7
    st.markdown(render_progress_bar("Questões esta semana", total_q_semana, meta_q_total, "#6C63FF"), unsafe_allow_html=True)

    # Taxa de acerto por matéria
    st.markdown('<div class="section-title">Taxa de Acerto por Matéria</div>', unsafe_allow_html=True)
    cols = st.columns(len(SUBJECTS))
    for col, s in zip(cols, SUBJECTS):
        with col:
            color = SUBJECT_COLORS[s]
            t = taxa[s]
            st.markdown(
                f'<div class="stat-card" style="border-top:2px solid {color};">'
                f'<div class="stat-val" style="color:{color};">{t}%</div>'
                f'<div class="stat-lbl">{SUBJECT_ICONS[s]} {s}</div>'
                f'<div class="stat-sub">{"✓ OK" if t>=70 else "⚠ Reforçar"}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # Gráficos
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        st.markdown('<div class="section-title">Questões por Matéria — 7 dias</div>', unsafe_allow_html=True)
        totais_s = defaultdict(int)
        for r in week_data: totais_s[r["materia"]] += r.get("quantidade", 0)

        fig1 = go.Figure(go.Bar(
            x=SUBJECTS,
            y=[totais_s[s] for s in SUBJECTS],
            marker_color=[SUBJECT_COLORS[s] for s in SUBJECTS],
            marker_line_width=0,
            text=[str(totais_s[s]) for s in SUBJECTS],
            textposition="outside",
            textfont=dict(family="DM Mono", size=12, color="#E8E8F0"),
        ))
        fig1.update_layout(
            plot_bgcolor="#07070F", paper_bgcolor="#07070F",
            font=dict(family="Syne", color="#666680"),
            xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#1A1A2E", zeroline=False),
            margin=dict(l=0, r=0, t=12, b=0), height=220,
        )
        st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False})

        # Evolução diária
        st.markdown('<div class="section-title">Evolução Diária — 7 dias</div>', unsafe_allow_html=True)
        by_day = questoes_por_dia(week_data)
        dias = [(date.today() - timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
        vals = [by_day.get(d, 0) for d in dias]
        labels = [d[5:] for d in dias]

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=labels, y=vals, mode="lines+markers",
            line=dict(color="#6C63FF", width=2),
            marker=dict(size=6, color="#6C63FF"),
            fill="tozeroy", fillcolor="rgba(108,99,255,0.08)",
        ))
        fig2.add_hline(y=meta_q, line_dash="dot", line_color="#FFB347",
                       annotation_text="meta/dia", annotation_font_color="#FFB347")
        fig2.update_layout(
            plot_bgcolor="#07070F", paper_bgcolor="#07070F",
            font=dict(family="Syne", color="#666680"),
            xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#1A1A2E", zeroline=False),
            margin=dict(l=0, r=0, t=12, b=0), height=200,
        )
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

        # Radar de taxa de acerto
        st.markdown('<div class="section-title">Radar de Domínio por Matéria</div>', unsafe_allow_html=True)
        fig3 = go.Figure(go.Scatterpolar(
            r=[taxa[s] for s in SUBJECTS] + [taxa[SUBJECTS[0]]],
            theta=SUBJECTS + [SUBJECTS[0]],
            fill="toself",
            fillcolor="rgba(108,99,255,0.1)",
            line=dict(color="#6C63FF", width=2),
            marker=dict(size=5),
        ))
        fig3.update_layout(
            polar=dict(
                bgcolor="#07070F",
                radialaxis=dict(visible=True, range=[0, 100], gridcolor="#1A1A2E", color="#33334A"),
                angularaxis=dict(gridcolor="#1A1A2E", color="#666680"),
            ),
            paper_bgcolor="#07070F",
            font=dict(family="Syne", color="#666680"),
            margin=dict(l=20, r=20, t=20, b=20), height=300,
            showlegend=False,
        )
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

    except ImportError:
        import pandas as pd
        totais_s = defaultdict(int)
        for r in week_data: totais_s[r["materia"]] += r.get("quantidade", 0)
        st.bar_chart(pd.DataFrame({s: [totais_s[s]] for s in SUBJECTS}))


def tab_caderno_erros(client: Client) -> None:
    st.markdown('<div class="section-title">Registrar Novo Erro</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        materia_err = st.selectbox("Matéria", SUBJECTS, key="err_mat")
    with col2:
        topico = st.text_input("Tópico / Assunto", placeholder="ex: Geometria plana", key="err_top")

    descricao = st.text_area("Descrição do erro ou dúvida", placeholder="O que você errou e por quê...", key="err_desc", height=100)

    if st.button("Salvar no Caderno de Erros", type="primary", key="btn_salvar_erro"):
        if topico and descricao:
            if save_erro(client, materia_err, topico, descricao):
                st.success("✓ Erro registrado no caderno.")
                st.rerun()
        else:
            st.warning("Preencha o tópico e a descrição.")

    st.markdown('<div class="section-title">Pendentes para Revisão</div>', unsafe_allow_html=True)

    pendentes = fetch_erros(client, apenas_pendentes=True)
    if not pendentes:
        st.markdown('<div class="alert-green">✓ Nenhum erro pendente. Você está em dia!</div>', unsafe_allow_html=True)
    else:
        for e in pendentes:
            color = SUBJECT_COLORS.get(e["materia"], "#888")
            with st.container():
                st.markdown(
                    f'<div class="erro-card" style="border-left-color:{color};">'
                    f'<span style="color:{color};font-size:11px;font-family:\'DM Mono\',monospace;">'
                    f'{e["materia"]} · {e["topico"]}</span><br>'
                    f'<span style="color:#88889A;font-size:12px;">{e["descricao"]}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                if st.button(f"✓ Marcar revisado", key=f"rev_{e['id']}"):
                    marcar_revisado(client, e["id"])
                    st.rerun()

    with st.expander("Ver todos os registros"):
        todos = fetch_erros(client, apenas_pendentes=False)
        for e in todos:
            color  = SUBJECT_COLORS.get(e["materia"], "#888")
            status = "✓" if e.get("revisado") else "○"
            st.markdown(
                f'<div class="erro-card" style="border-left-color:{color};opacity:{"0.5" if e.get("revisado") else "1"};">'
                f'{status} <span style="color:{color};font-size:11px;font-family:\'DM Mono\',monospace;">'
                f'{e["materia"]} · {e["topico"]}</span><br>'
                f'<span style="color:#55556A;font-size:12px;">{e["descricao"]}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )


def tab_metas(client: Client) -> None:
    metas = fetch_metas(client)

    st.markdown('<div class="section-title">Definir Metas</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        meta_q = st.number_input("Meta de questões/dia", min_value=5, max_value=200,
                                  value=int(metas.get("meta_questoes_dia", 30)), step=5)
    with col2:
        meta_h = st.number_input("Meta de horas/semana", min_value=1, max_value=50,
                                  value=int(metas.get("meta_horas_semana", 20)), step=1)
    with col3:
        nota_alvo = st.number_input("Nota alvo (0-1000)", min_value=400.0, max_value=1000.0,
                                     value=float(metas.get("nota_alvo", 750)), step=10.0)

    if st.button("Salvar Metas", type="primary", key="btn_save_meta"):
        save_meta(client, int(meta_q), int(meta_h), float(nota_alvo))
        st.success("✓ Metas salvas!")

    st.markdown('<div class="section-title">O que você precisa para sua nota alvo</div>', unsafe_allow_html=True)

    pesos = {"Matemática": 4, "Redação": 2, "Linguagens": 2, "Humanas": 1, "Natureza": 1}
    total_peso = sum(pesos.values())
    taxa_necessaria = (float(nota_alvo) / 1000) * 100

    for s in SUBJECTS:
        color = SUBJECT_COLORS[s]
        st.markdown(render_progress_bar(
            f"{SUBJECT_ICONS[s]} {s} (peso {pesos[s]})",
            taxa_necessaria, 100, color
        ), unsafe_allow_html=True)

    st.markdown(
        f'<div class="alert-yellow">Para atingir <strong>{nota_alvo:.0f} pontos</strong>, '
        f'você precisa de aproximadamente <strong>{taxa_necessaria:.0f}% de acerto</strong> em todas as áreas.</div>',
        unsafe_allow_html=True,
    )

# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    st.set_page_config(
        page_title="ENEM Ultimate Dashboard",
        page_icon="∑",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    client = get_supabase()
    cycle  = load_cycle()

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("## ∑ ENEM")
        st.markdown('<div style="font-size:10px;color:#33334A;font-family:\'DM Mono\',monospace;letter-spacing:2px;">ULTIMATE DASHBOARD</div>', unsafe_allow_html=True)

        st.markdown('<div class="sb-section">Kill Switch · Tempo Diário</div>', unsafe_allow_html=True)
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
            else:
                st.warning("Insira um tempo maior que zero.")
        daily_minutes = fetch_daily_minutes(client)
        st.markdown(render_kill_status(daily_minutes), unsafe_allow_html=True)

        st.markdown("---")
        st.markdown('<div class="sb-section">Controles do Ciclo</div>', unsafe_allow_html=True)

        if st.button("← Voltar um bloco", key="btn_voltar"):
            cur = fetch_current_index(client)
            if set_index(client, (cur - 1) % len(cycle)):
                st.rerun()

        if st.button("↩ Desfazer último registro", key="btn_undo"):
            cur = fetch_current_index(client)
            if delete_last_registro(client):
                set_index(client, (cur - 1) % len(cycle))
                st.rerun()
            else:
                st.warning("Nenhum registro encontrado.")

        bloco_escolhido = st.selectbox(
            "Ir para bloco:",
            options=list(range(len(cycle))),
            format_func=lambda i: f"{i+1:02d} · {cycle[i]}",
            key="select_bloco",
        )
        if st.button("→ Ir para este bloco", key="btn_goto"):
            if set_index(client, bloco_escolhido): st.rerun()

        st.markdown("---")
        render_cycle_builder(cycle)

        st.markdown('<div class="sb-section">Ciclo Atual</div>', unsafe_allow_html=True)
        cur_preview = fetch_current_index(client) % len(cycle)
        for i, s in enumerate(cycle):
            color   = SUBJECT_COLORS[s]
            is_curr = i == cur_preview
            bg      = f"background:rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.1);border-radius:6px;" if is_curr else ""
            fw      = "700" if is_curr else "400"
            st.markdown(
                f'<div style="font-family:\'DM Mono\',monospace;font-size:11px;color:#44445A;'
                f'padding:3px 6px;margin-bottom:1px;{bg}">'
                f'<span style="color:{color};font-weight:{fw};">{i+1:02d}</span> · '
                f'<span style="color:{"#D0D0E8" if is_curr else "#666680"};font-weight:{fw};">{s}</span>'
                f'{"  ◀" if is_curr else ""}</div>',
                unsafe_allow_html=True,
            )

    # ── Tabs ──────────────────────────────────────────────────────────────────
    t1, t2, t3, t4 = st.tabs(["⚡ Execução", "📊 Dashboard", "📓 Caderno de Erros", "🎯 Metas"])

    with t1: tab_execucao(client, cycle)
    with t2: tab_dashboard(client)
    with t3: tab_caderno_erros(client)
    with t4: tab_metas(client)


if __name__ == "__main__":
    main()
