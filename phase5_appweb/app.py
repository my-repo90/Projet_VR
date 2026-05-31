import streamlit as st
import plotly.graph_objects as go
import numpy as np
import random
import time

# ─────────────────────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="DATA-DIVE v2.0", page_icon="🔷",
                   layout="wide", initial_sidebar_state="collapsed")

# ─────────────────────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────────────────────
def _init(k, v):
    if k not in st.session_state: st.session_state[k] = v

_init("anomalies", 14); _init("fps", 89.4); _init("compute", 42)
_init("active_tab", "network"); _init("cypher_result", None)
_init("cypher_query", "MATCH\n  (n:Transaction)-[r:SENT_TO]->(m)\nWHERE\n  r.amount > 50000\nRETURN\n  n, r, m")
_init("log_lines", [
    ("INFO","UnityEngine.XR: Session started (OpenXR)"),
    ("INFO","NeoGraph: 428,092 nodes loaded into ECS"),
    ("WARN","ClusterID-8821: anomaly threshold exceeded"),
    ("INFO","UMAP projection synced to VR world space"),
    ("ERROR","NodeGroup-42 desynced from main graph"),
    ("INFO","DL Anomaly model: batch inference 42ms"),
    ("OK","Neo4j Graph write confirmed — 3,201 edges"),
])

# ─────────────────────────────────────────────────────────────
#  READ TAB FROM QUERY PARAMS
# ─────────────────────────────────────────────────────────────
qp = st.query_params
if "tab" in qp and qp["tab"] in ("network","anomaly","unity"):
    st.session_state.active_tab = qp["tab"]

# ─────────────────────────────────────────────────────────────
#  THEME & CSS
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Orbitron:wght@400;700;900&family=Rajdhani:wght@400;500;600;700&display=swap');

:root {
  --bg0:#020a12; --bg1:#050e18; --bg2:#071420; --bg3:#091828;
  --cyan:#00e5ff; --cyan2:#00b4cc; --cyanglow:rgba(0,229,255,.15);
  --pink:#ff006e; --green:#00ff88; --greeng:rgba(0,255,136,.10);
  --amber:#ffb300; --purple:#a259ff;
  --t1:#c8eaf2; --t2:#4a7a8a; --t3:#1e3a4a;
  --border:rgba(0,229,255,.14); --border2:rgba(0,229,255,.38);
}

/* ── RESET ── */
*, *::before, *::after { box-sizing: border-box; }
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
  background: var(--bg0) !important;
  color: var(--t1) !important;
  font-family: 'Rajdhani', sans-serif !important;
}
#MainMenu, footer, header,
[data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stStatusWidget"], .stDeployButton, .stAppDeployButton {
  display: none !important;
}
::-webkit-scrollbar { width: 3px; }
::-webkit-scrollbar-thumb { background: var(--cyan2); border-radius: 2px; }

/* ── LAYOUT ── */
.block-container { padding: 78px 1.4rem 2rem !important; max-width: 100% !important; }

/* ══════════════════════════════════════════════
   NAVBAR
══════════════════════════════════════════════ */
.navbar {
  position: fixed; top: 0; left: 0; right: 0; z-index: 9999;
  height: 62px;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 24px;
  background: rgba(2,6,14,.97);
  border-bottom: 1px solid var(--border2);
  backdrop-filter: blur(24px);
  box-shadow: 0 2px 40px rgba(0,0,0,.8), 0 0 1px var(--cyan2);
}

/* Logo */
.logo-wrap { display: flex; align-items: center; gap: 12px; flex-shrink: 0; }
.logo-hex {
  width: 34px; height: 34px; flex-shrink: 0;
  background: linear-gradient(135deg, var(--cyan), #007acc);
  clip-path: polygon(50% 0%,100% 25%,100% 75%,50% 100%,0% 75%,0% 25%);
  box-shadow: 0 0 12px var(--cyan);
  animation: hexPulse 3s ease-in-out infinite;
}
@keyframes hexPulse {
  0%,100% { box-shadow: 0 0 8px var(--cyan); }
  50%     { box-shadow: 0 0 22px var(--cyan), 0 0 44px rgba(0,229,255,.35); }
}
.logo-txt {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.15rem; font-weight: 900;
  color: #fff; letter-spacing: 3px; white-space: nowrap;
}
.logo-ver { color: var(--cyan); font-weight: 400; }

/* Nav links */
.nav-links { display: flex; align-items: center; gap: 6px; }
.nav-link {
  display: inline-flex; align-items: center;
  padding: 7px 20px;
  border: 1px solid transparent; border-radius: 28px;
  color: var(--t2);
  font-family: 'Share Tech Mono', monospace;
  font-size: .76rem; letter-spacing: 1.5px; text-transform: uppercase;
  text-decoration: none !important;
  white-space: nowrap; cursor: pointer;
  transition: color .18s, border-color .18s, background .18s;
}
.nav-link:hover {
  color: var(--cyan);
  border-color: rgba(0,229,255,.35);
  background: rgba(0,229,255,.05);
  text-decoration: none !important;
}
.nav-link.act {
  color: var(--cyan);
  border-color: var(--cyan);
  background: rgba(0,229,255,.06);
  box-shadow: 0 0 0 1px rgba(0,229,255,.25), 0 0 16px rgba(0,229,255,.1);
  text-decoration: none !important;
}

/* VR pill */
.vr-pill {
  display: flex; align-items: center; gap: 7px;
  padding: 6px 16px; border-radius: 22px;
  background: var(--greeng);
  border: 1px solid rgba(0,255,136,.32);
  font-family: 'Share Tech Mono', monospace;
  font-size: .72rem; color: var(--green); letter-spacing: 1.5px;
  white-space: nowrap; flex-shrink: 0;
}
.blink {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--green);
  animation: blink 1.5s ease-in-out infinite;
}
@keyframes blink {
  0%,100% { opacity:1; box-shadow: 0 0 6px var(--green); }
  50%     { opacity: .2; box-shadow: none; }
}

/* ══════════════════════════════════════════════
   SECTION LABELS
══════════════════════════════════════════════ */
.slabel {
  display: flex; align-items: center; gap: 7px;
  font-family: 'Share Tech Mono', monospace;
  font-size: .62rem; color: var(--cyan);
  letter-spacing: 2.5px; text-transform: uppercase;
  margin-bottom: 9px;
}
.slabel::before {
  content: '';
  width: 7px; height: 7px; border-radius: 50%;
  background: var(--cyan); box-shadow: 0 0 7px var(--cyan);
  flex-shrink: 0;
}

/* ══════════════════════════════════════════════
   CYPHER EDITOR
══════════════════════════════════════════════ */
.stTextArea > label { display: none !important; }
.stTextArea textarea {
  background: #010810 !important;
  color: var(--cyan) !important;
  border: 1px solid var(--border2) !important;
  border-radius: 4px !important;
  font-family: 'Share Tech Mono', monospace !important;
  font-size: .8rem !important;
  line-height: 1.9 !important;
  caret-color: var(--cyan) !important;
  resize: vertical !important;
  padding: 11px 13px !important;
  transition: border-color .2s, box-shadow .2s !important;
}
.stTextArea textarea:focus {
  border-color: var(--cyan) !important;
  box-shadow: 0 0 12px rgba(0,229,255,.18) !important;
  outline: none !important;
}
.cypher-result {
  background: rgba(0,229,255,.03);
  border: 1px solid rgba(0,229,255,.22);
  border-radius: 4px; padding: 9px 12px;
  font-family: 'Share Tech Mono', monospace;
  font-size: .7rem; color: var(--t1);
  line-height: 1.7; margin-top: 7px;
}
.cypher-result .ck { color: var(--cyan); font-weight: bold; }
.cypher-result .cv { color: #ff9f43; }

/* ══════════════════════════════════════════════
   BUTTONS
══════════════════════════════════════════════ */
.stButton > button {
  background: transparent !important;
  color: var(--cyan) !important;
  border: 1px solid var(--border2) !important;
  font-family: 'Share Tech Mono', monospace !important;
  font-size: .72rem !important;
  letter-spacing: 1.5px !important;
  border-radius: 4px !important;
  box-shadow: none !important;
  width: 100% !important;
  transition: all .18s !important;
}
.stButton > button:hover {
  border-color: var(--cyan) !important;
  background: rgba(0,229,255,.07) !important;
  box-shadow: 0 0 12px rgba(0,229,255,.2) !important;
}
/* Primary action button */
.stButton > button[data-testid="baseButton-primary"] {
  background: var(--cyan) !important;
  color: #000 !important;
  border: none !important;
  font-family: 'Orbitron', sans-serif !important;
  font-weight: 700 !important;
  letter-spacing: 2px !important;
  box-shadow: 0 0 14px rgba(0,229,255,.35) !important;
}
.stButton > button[data-testid="baseButton-primary"]:hover {
  box-shadow: 0 0 26px rgba(0,229,255,.65) !important;
}

/* ══════════════════════════════════════════════
   TEXT INPUT
══════════════════════════════════════════════ */
.stTextInput > div > div > input {
  background: var(--bg3) !important; color: var(--cyan) !important;
  border: 1px solid var(--border2) !important; border-radius: 4px !important;
  font-family: 'Share Tech Mono', monospace !important; font-size: .74rem !important;
}
.stTextInput label {
  font-family: 'Share Tech Mono', monospace !important;
  font-size: .61rem !important; color: var(--t2) !important; letter-spacing: 1.5px !important;
}

/* ══════════════════════════════════════════════
   PANEL / CARD
══════════════════════════════════════════════ */
.panel {
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: 6px; padding: 14px;
  margin-bottom: 12px; position: relative; overflow: hidden;
}
.panel::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(0,229,255,.4), transparent);
}

/* ══════════════════════════════════════════════
   PIPELINE
══════════════════════════════════════════════ */
.prow {
  display: flex; justify-content: space-between; align-items: center;
  padding: 6px 0; border-bottom: 1px solid rgba(0,229,255,.05);
  font-family: 'Share Tech Mono', monospace; font-size: .71rem; color: var(--t1);
}
.prow:last-child { border-bottom: none; }
.sok  { color: var(--green); }
.srun { color: var(--amber); animation: flash .9s ease-in-out infinite; }
@keyframes flash { 0%,100%{opacity:1} 50%{opacity:.3} }

/* ══════════════════════════════════════════════
   VR PANEL / TOOLBAR
══════════════════════════════════════════════ */
.vrpanel {
  background: #010810;
  border: 1px solid var(--border2); border-radius: 6px; overflow: hidden;
  margin-bottom: 8px;
}
.vrtoolbar {
  display: flex; justify-content: space-between; align-items: center;
  padding: 5px 12px;
  background: rgba(0,229,255,.04);
  border-bottom: 1px solid rgba(0,229,255,.12);
  font-family: 'Share Tech Mono', monospace; font-size: .61rem; color: var(--t2);
}
.vrtoolbar .hi { color: var(--cyan); }

/* ══════════════════════════════════════════════
   METRICS GRID
══════════════════════════════════════════════ */
.mgrid { display: grid; grid-template-columns: repeat(3,1fr); gap: 8px; margin: 10px 0; }
.mcard {
  background: var(--bg3); border: 1px solid var(--border);
  border-radius: 5px; padding: 11px; text-align: center;
}
.mlabel {
  font-family: 'Share Tech Mono', monospace; font-size: .56rem;
  color: var(--t2); letter-spacing: 2px; text-transform: uppercase; margin-bottom: 4px;
}
.mval { font-family: 'Orbitron', sans-serif; font-size: 1.65rem; font-weight: 700; }
.mval.pink  { color: var(--pink); }
.mval.cyan  { color: var(--cyan); }
.mval.green { color: var(--green); font-size: 1rem; letter-spacing: 1px; }

/* ══════════════════════════════════════════════
   TELEMETRY
══════════════════════════════════════════════ */
.tgrid { display: grid; grid-template-columns: repeat(4,1fr); gap: 5px; margin-top: 8px; }
.titem { text-align: center; }
.tlabel { font-family: 'Share Tech Mono', monospace; font-size: .55rem; color: var(--t2); letter-spacing: 1px; margin-bottom: 3px; }
.tval   { font-family: 'Orbitron', monospace; font-size: .95rem; color: var(--cyan); }

/* ══════════════════════════════════════════════
   ANOMALY BADGE
══════════════════════════════════════════════ */
.abadge {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 4px 10px; background: rgba(255,0,110,.1);
  border: 1px solid var(--pink); border-radius: 3px;
  font-family: 'Share Tech Mono', monospace; font-size: .58rem; color: var(--pink);
  letter-spacing: 1px; animation: flash 1.2s ease-in-out infinite; margin-top: 5px;
}

/* ══════════════════════════════════════════════
   ALERTS
══════════════════════════════════════════════ */
.alert {
  border-radius: 4px; padding: 9px 11px; margin-bottom: 6px;
  font-size: .74rem; border-left: 3px solid transparent;
}
.alert.fraud { border-left-color: var(--pink);  background: rgba(255,0,110,.04); }
.alert.manip { border-left-color: var(--amber); background: rgba(255,179,0,.04); }
.alert.query { border-left-color: var(--cyan2); background: rgba(0,180,200,.05); }
.atype { font-family: 'Share Tech Mono', monospace; font-size: .56rem; letter-spacing: 2px; margin-bottom: 3px; }
.fraud .atype{color:var(--pink)} .manip .atype{color:var(--amber)} .query .atype{color:var(--cyan2)}
.atime { float: right; color: var(--t2); font-size: .6rem; font-family: 'Share Tech Mono', monospace; }
.amsg  { color: var(--t1); line-height: 1.4; clear: both; }

/* ══════════════════════════════════════════════
   CLUSTER STATUS
══════════════════════════════════════════════ */
.cstat {
  display: flex; justify-content: space-between;
  font-family: 'Share Tech Mono', monospace; font-size: .6rem; color: var(--t2); margin-top: 4px;
}
.cstat .g{color:var(--green)} .cstat .c{color:var(--cyan)} .cstat .a{color:var(--amber)}
.cfooter {
  display: flex; justify-content: space-between;
  font-family: 'Share Tech Mono', monospace; font-size: .59rem; color: var(--t2); margin-top: 5px;
}
.cfooter span { color: var(--cyan2); }

/* ══════════════════════════════════════════════
   PEERS
══════════════════════════════════════════════ */
.peer {
  display: flex; justify-content: space-between; align-items: center;
  padding: 7px 0; border-bottom: 1px solid rgba(0,229,255,.05);
  font-family: 'Share Tech Mono', monospace; font-size: .7rem;
}
.peer:last-child { border-bottom: none; }
.pname { display: flex; align-items: center; gap: 7px; }
.pdot  { width: 7px; height: 7px; border-radius: 50%; animation: blink 1.8s ease-in-out infinite; flex-shrink: 0; }
.pdot.c{background:var(--cyan);box-shadow:0 0 5px var(--cyan)}
.pdot.a{background:var(--amber);box-shadow:0 0 5px var(--amber)}
.pdot.r{background:var(--t3)}
.prole { color: var(--t2); font-size: .6rem; letter-spacing: 1px; }

/* ══════════════════════════════════════════════
   COLLAB
══════════════════════════════════════════════ */
.collabfoot { font-family: 'Share Tech Mono', monospace; font-size: .58rem; color: var(--t2); font-style: italic; margin-top: 6px; }
.sessid { float: right; color: var(--t2); font-family: 'Share Tech Mono', monospace; font-size: .58rem; }

/* ══════════════════════════════════════════════
   UNITY / VR CONSOLE
══════════════════════════════════════════════ */
.vcgrid { display: grid; grid-template-columns: 1fr 1fr; gap: 7px; margin-bottom: 10px; }
.vcbtn {
  background: var(--bg3); border: 1px solid var(--border); border-radius: 4px;
  padding: 10px; text-align: center; font-family: 'Share Tech Mono', monospace; font-size: .68rem; cursor: pointer;
}
.vcbtn.g{color:var(--green)} .vcbtn.c{color:var(--cyan)} .vcbtn.a{color:var(--amber)} .vcbtn.p{color:var(--pink)}
.vmrow {
  display: flex; justify-content: space-between; padding: 6px 0;
  border-bottom: 1px solid rgba(0,229,255,.05);
  font-family: 'Share Tech Mono', monospace; font-size: .69rem;
}
.vmrow:last-child { border-bottom: none; }
.vmrow .lbl{color:var(--t2)} .vmrow .val{color:var(--cyan)} .vmrow .val.g{color:var(--green)}
.logbox {
  background: #010810; border: 1px solid var(--border); border-radius: 4px; padding: 11px;
  font-family: 'Share Tech Mono', monospace; font-size: .65rem;
  line-height: 2; max-height: 210px; overflow-y: auto;
}
.log-info{color:var(--cyan)} .log-warn{color:var(--amber)} .log-err{color:var(--pink)} .log-ok{color:var(--green)}
.log-msg{color:#6ecadb}

/* ══════════════════════════════════════════════
   ANOMALY FEED / ENGINE
══════════════════════════════════════════════ */
.afeed {
  display: flex; justify-content: space-between; align-items: center;
  padding: 8px 11px; margin-bottom: 5px;
  background: var(--bg3); border-radius: 4px; border-left: 3px solid transparent;
  font-family: 'Share Tech Mono', monospace; font-size: .69rem;
}
.afeed .ts { color: var(--t2); font-size: .6rem; }

/* ══════════════════════════════════════════════
   INTEGRATION STATUS
══════════════════════════════════════════════ */
.intstatus {
  background: rgba(0,255,136,.03); border: 1px solid rgba(0,255,136,.18);
  border-radius: 4px; padding: 11px; font-family: 'Share Tech Mono', monospace; font-size: .68rem;
}
.isrow { display: flex; justify-content: space-between; padding: 3px 0; font-size: .67rem; }
.isrow .k{color:var(--t2)} .isrow .ok{color:var(--green)} .isrow .vc{color:var(--cyan)}

hr { border-color: var(--border) !important; margin: 7px 0 !important; }
div[data-testid="stVerticalBlock"] > div { gap: 0 !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  CHART BUILDERS
# ─────────────────────────────────────────────────────────────
def cluster_density_fig():
    rng = np.random.default_rng(42)
    vals = rng.integers(18, 100, 28).tolist()
    colors = ['#ff006e' if i in [4,9,14,19] else '#00e5ff' for i in range(28)]
    fig = go.Figure(go.Bar(y=vals, marker_color=colors, marker_line_width=0))
    fig.update_layout(height=100, margin=dict(l=0,r=0,t=0,b=0),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False,showticklabels=False,zeroline=False),
        yaxis=dict(showgrid=False,showticklabels=False,zeroline=False), bargap=0.1)
    return fig

def network_graph_fig():
    rng = np.random.default_rng(7)
    n = 90
    x = rng.uniform(-1.1,1.1,n); y = rng.uniform(-1.1,1.1,n)
    hx = rng.normal(0.1,0.2,14); hy = rng.normal(-0.1,0.2,14)
    ex,ey = [],[]
    for _ in range(140):
        i,j = rng.integers(0,n,2); ex+=[x[i],x[j],None]; ey+=[y[i],y[j],None]
    for _ in range(30):
        i,j = rng.integers(0,14,2); ex+=[hx[i],hx[j],None]; ey+=[hy[i],hy[j],None]
    sizes = rng.uniform(4,15,n)
    colors = ['rgba(255,0,110,.9)' if rng.random()<.07 else 'rgba(0,229,255,.82)' for _ in range(n)]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ex,y=ey,mode='lines',
        line=dict(color='rgba(0,180,200,.1)',width=.6),hoverinfo='none',showlegend=False))
    fig.add_trace(go.Scatter(x=x,y=y,mode='markers',
        marker=dict(size=sizes,color=colors,line=dict(width=0),opacity=.82),
        hovertemplate='<b>Node</b><extra></extra>',showlegend=False))
    fig.add_trace(go.Scatter(x=hx,y=hy,mode='markers',
        marker=dict(size=18,color='rgba(255,0,110,.5)',line=dict(color='#ff006e',width=1.2)),
        hovertemplate='<b>ANOMALY CLUSTER-8821</b><extra></extra>',showlegend=False))
    fig.update_layout(height=340, margin=dict(l=0,r=0,t=0,b=0),
        paper_bgcolor='rgba(1,8,16,1)', plot_bgcolor='rgba(1,8,16,1)',
        xaxis=dict(showgrid=False,zeroline=False,showticklabels=False,range=[-1.3,1.3]),
        yaxis=dict(showgrid=False,zeroline=False,showticklabels=False,range=[-1.3,1.3]),
        dragmode='pan', showlegend=False)
    return fig

def collab_focus_fig():
    rng = np.random.default_rng(3)
    n = 22
    x = rng.normal(0,.5,n); y = rng.normal(0,.5,n)
    palette=['rgba(255,0,110,.9)','rgba(0,229,255,.7)','rgba(162,89,255,.75)']
    colors=[random.choice(palette) for _ in range(n)]
    ex,ey=[],[]
    for _ in range(26):
        i,j=rng.integers(0,n,2); ex+=[x[i],x[j],None]; ey+=[y[i],y[j],None]
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=ex,y=ey,mode='lines',
        line=dict(color='rgba(120,0,200,.2)',width=1),hoverinfo='none',showlegend=False))
    fig.add_trace(go.Scatter(x=x,y=y,mode='markers',
        marker=dict(size=rng.uniform(6,22,n).tolist(),color=colors,line=dict(width=0)),
        hoverinfo='none',showlegend=False))
    fig.update_layout(height=150,margin=dict(l=0,r=0,t=0,b=0),
        paper_bgcolor='rgba(5,10,20,1)',plot_bgcolor='rgba(5,10,20,1)',
        xaxis=dict(showgrid=False,zeroline=False,showticklabels=False),
        yaxis=dict(showgrid=False,zeroline=False,showticklabels=False),dragmode='pan')
    return fig

def anomaly_dist_fig():
    rng=np.random.default_rng(11)
    x2=np.linspace(0,24,250)
    y2=(rng.uniform(3,15,250)+28*np.exp(-((x2-8)**2)/4)
        +48*np.exp(-((x2-14)**2)/3)+18*np.exp(-((x2-20)**2)/5))
    pi=int(np.argmax(y2))
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=x2,y=y2,mode='lines',
        line=dict(color='#00e5ff',width=1.5),fill='tozeroy',fillcolor='rgba(0,229,255,.06)'))
    fig.add_trace(go.Scatter(x=[x2[pi]],y=[y2[pi]],mode='markers',
        marker=dict(size=10,color='#ff006e',line=dict(color='#fff',width=1)),
        hoverinfo='none',showlegend=False))
    fig.update_layout(height=220,margin=dict(l=35,r=8,t=8,b=28),
        paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,dragmode='zoom',
        xaxis=dict(showgrid=False,color='#2a4a5a',tickfont=dict(family='Share Tech Mono',size=8)),
        yaxis=dict(showgrid=True,gridcolor='rgba(0,229,255,.05)',color='#2a4a5a',
                   tickfont=dict(family='Share Tech Mono',size=8)))
    return fig

def tsne_scatter_fig():
    rng=np.random.default_rng(99)
    gdata=[(rng.normal(-0.5,.15,80),rng.normal(-0.4,.15,80),'rgba(0,229,255,.75)'),
           (rng.normal(.5,.18,90),rng.normal(.4,.18,90),'rgba(0,255,136,.70)'),
           (rng.normal(0,.12,70),rng.normal(.6,.12,70),'rgba(255,0,110,.85)'),
           (rng.normal(-.3,.10,60),rng.normal(.1,.10,60),'rgba(255,179,0,.75)')]
    cx=np.concatenate([g[0] for g in gdata]); cy=np.concatenate([g[1] for g in gdata])
    cc=[c for g in gdata for c in [g[2]]*len(g[0])]
    fig=go.Figure(go.Scatter(x=cx,y=cy,mode='markers',
        marker=dict(size=5,color=cc,line=dict(width=0),opacity=.85),
        hoverinfo='none',showlegend=False))
    fig.update_layout(height=195,margin=dict(l=0,r=0,t=0,b=0),
        paper_bgcolor='rgba(1,8,16,1)',plot_bgcolor='rgba(1,8,16,1)',
        xaxis=dict(showgrid=False,zeroline=False,showticklabels=False),
        yaxis=dict(showgrid=False,zeroline=False,showticklabels=False),dragmode='pan')
    return fig

ZOOMABLE = dict(scrollZoom=True,displayModeBar=True,
    modeBarButtonsToRemove=['toImage','lasso2d','select2d','autoScale2d'],displaylogo=False)
STATIC = dict(displayModeBar=False)

# ─────────────────────────────────────────────────────────────
#  NAVBAR  (pure HTML anchor links → query_params)
# ─────────────────────────────────────────────────────────────
active = st.session_state.active_tab
n1 = "act" if active=="network" else ""
n2 = "act" if active=="anomaly" else ""
n3 = "act" if active=="unity"   else ""

st.markdown(f"""
<div class="navbar">
  <div class="logo-wrap">
    <div class="logo-hex"></div>
    <span class="logo-txt">DATA&#8209;DIVE&nbsp;<span class="logo-ver">v2.0</span></span>
  </div>
  <div class="nav-links">
    <a class="nav-link {n1}" href="?tab=network">NETWORK EXPLORER</a>
    <a class="nav-link {n2}" href="?tab=anomaly">ANOMALY ENGINE</a>
    <a class="nav-link {n3}" href="?tab=unity">UNITY&#8209;LIVE CONSOLE</a>
  </div>
  <div class="vr-pill"><div class="blink"></div>VR PARTNER: ACTIVE</div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  TAB 1 — NETWORK EXPLORER
# ═══════════════════════════════════════════════════════════════
if active == "network":

    L, C, R = st.columns([2.4, 4.8, 3.1], gap="medium")

    # ── LEFT ────────────────────────────────────────────────
    with L:
        # CYPHER COMMAND
        st.markdown('<div class="slabel">CYPHER COMMAND</div>', unsafe_allow_html=True)
        cypher_input = st.text_area("q", value=st.session_state.cypher_query,
            height=175, key="cypher_ta", label_visibility="collapsed",
            placeholder="MATCH (n)-->(m) RETURN n, m LIMIT 25")
        st.session_state.cypher_query = cypher_input

        rc, cc2 = st.columns([3,1])
        with rc:
            if st.button("▶  EXECUTE QUERY", key="btn_run"):
                st.session_state.cypher_result = {
                    "nodes": random.randint(800,12000),
                    "edges": random.randint(1200,35000),
                    "time_ms": round(random.uniform(12,340),1),
                }; st.rerun()
        with cc2:
            if st.button("CLR", key="btn_clr"):
                st.session_state.cypher_query = ""; st.session_state.cypher_result = None; st.rerun()

        if st.session_state.cypher_result:
            r = st.session_state.cypher_result
            st.markdown(f"""<div class="cypher-result">
              <span class="ck">✓ OK</span> &nbsp;·&nbsp;<span class="cv">{r['time_ms']} ms</span><br>
              Nodes: <span class="ck">{r['nodes']:,}</span> &nbsp; Edges: <span class="ck">{r['edges']:,}</span>
            </div>""", unsafe_allow_html=True)

        if st.button("RESHAPE ENVIRONMENT", key="btn_reshape"):
            st.toast("⚡ Environment reshaped!", icon="🔷")

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        # CLUSTER DENSITY
        st.markdown('<div class="slabel">CLUSTER DENSITY (T‑SNE)</div>', unsafe_allow_html=True)
        st.plotly_chart(cluster_density_fig(), use_container_width=True, config=STATIC)
        st.markdown("""
        <div class="cstat">
          <span>NB04J:&nbsp;<span class="g">CONNECTED</span></span>
          <span>SPARK:&nbsp;<span class="a">IDLE</span></span>
          <span>STREAM:&nbsp;<span class="c">1.2 GB/S</span></span>
        </div>
        <div class="cfooter">
          <span>NODES:&nbsp;<span>428,092</span></span>
          <span>ITER:&nbsp;<span>2,500</span></span>
        </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        # PIPELINE
        st.markdown('<div class="slabel">PIPELINE</div>', unsafe_allow_html=True)
        for name, txt, cls in [
            ("Spark Ingest","OK","ok"),("Neo4j Graph","OK","ok"),
            ("UMAP Reduce","RUN","run"),("DL Anomaly","RUN","run"),("Unity ECS","OK","ok"),
        ]:
            st.markdown(f'<div class="prow"><span>{name}</span>'
                        f'<span class="s{cls}">{txt}</span></div>', unsafe_allow_html=True)

    # ── CENTER ──────────────────────────────────────────────
    with C:
        st.markdown("""<div class="vrpanel">
          <div class="vrtoolbar">
            <span>SYNC_LATENCY:&nbsp;<span class="hi">12MS</span></span>
            <span style="color:var(--t2);font-size:.58rem">🖱 scroll=zoom &nbsp;·&nbsp; drag=pan</span>
            <span>CAM:&nbsp;<span class="hi">XR_PLAYER_01</span></span>
          </div></div>""", unsafe_allow_html=True)

        st.plotly_chart(network_graph_fig(), use_container_width=True, config=ZOOMABLE)

        st.markdown('<div class="abadge">● &nbsp;ANOMALY DETECTED · CLUSTER-8821</div>',
                    unsafe_allow_html=True)
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        st.markdown(f"""<div class="mgrid">
          <div class="mcard"><div class="mlabel">ANOMALIES</div>
            <div class="mval pink">{st.session_state.anomalies}</div></div>
          <div class="mcard"><div class="mlabel">COMPUTE LOAD</div>
            <div class="mval cyan">{st.session_state.compute}%</div></div>
          <div class="mcard"><div class="mlabel">UNITY ECS</div>
            <div class="mval green">STABLE</div></div>
        </div>""", unsafe_allow_html=True)

        st.markdown('<div class="slabel">LIVE FRAME TELEMETRY</div>', unsafe_allow_html=True)
        st.markdown(f"""<div class="tgrid">
          <div class="titem"><div class="tlabel">FPS</div><div class="tval">{st.session_state.fps}</div></div>
          <div class="titem"><div class="tlabel">DRAW CALLS</div><div class="tval">1,204</div></div>
          <div class="titem"><div class="tlabel">NODES RENDERED</div><div class="tval">82,140</div></div>
          <div class="titem"><div class="tlabel">TRIS</div><div class="tval">241,883</div></div>
        </div>""", unsafe_allow_html=True)

    # ── RIGHT ────────────────────────────────────────────────
    with R:
        st.markdown('<div class="slabel">REAL-TIME ALERTS</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="alert fraud">
          <div class="atype">FRAUD ALERT<span class="atime">14:21:05</span></div>
          <div class="amsg">Cluster ID-8821 showing recursive transaction loops in VR sector 4.</div>
        </div>
        <div class="alert manip">
          <div class="atype">MANIPULATION<span class="atime">14:19:33</span></div>
          <div class="amsg">VR user separated NodeGroup-42 and isolated peripheral links.</div>
        </div>
        <div class="alert query">
          <div class="atype">QUERY SYNC<span class="atime">14:18:02</span></div>
          <div class="amsg">Dimensionality reduction UMAP update complete across all instances.</div>
        </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        st.markdown('<div class="slabel">COLLABORATIVE FOCUS</div>', unsafe_allow_html=True)
        st.plotly_chart(collab_focus_fig(), use_container_width=True, config=STATIC)
        st.markdown("""
        <div class="sessid">[ SESSION_ID: DIVE-992-K ]</div>
        <div class="collabfoot" style="margin-top:20px">
          * Highlighted areas indicate active VR player manipulation.</div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        st.markdown('<div class="slabel">SESSION PEERS</div>', unsafe_allow_html=True)
        for name, badge, dc in [
            ("XR_PLAYER_01","DIVER","c"),
            ("DESK_ANALYST_02","ANALYST","a"),
            ("OBSERVER_03","READ-ONLY","r"),
        ]:
            st.markdown(f"""<div class="peer">
              <div class="pname"><div class="pdot {dc}"></div>{name}</div>
              <div class="prole">{badge}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # bottom controls
    bc1,bc2,bc3,_ = st.columns([1.5,1.5,1.6,4.5])
    with bc1:
        if st.button("⟳  REFRESH", key="ref_m"):
            st.session_state.anomalies=random.randint(10,22)
            st.session_state.compute=random.randint(28,68)
            st.session_state.fps=round(random.uniform(72,95),1); st.rerun()
    with bc2:
        if st.button("+ ALERT", key="add_a"):
            st.toast("🔴 New anomaly: cluster-9934!", icon="⚠️")
    with bc3:
        if st.button("⬡  RESET SESSION", key="reset_s"):
            for k in ["anomalies","fps","compute","log_lines","cypher_result"]:
                if k in st.session_state: del st.session_state[k]
            st.rerun()

# ═══════════════════════════════════════════════════════════════
#  TAB 2 — ANOMALY ENGINE
# ═══════════════════════════════════════════════════════════════
elif active == "anomaly":
    AL, AR = st.columns([1.4,2.6], gap="medium")

    with AL:
        st.markdown('<div class="slabel">ANOMALY FEED</div>', unsafe_allow_html=True)
        for aid,atype,color,ts in [
            ("8821","RECURSIVE_LOOP","#ff006e","14:21"),
            ("3304","ISOLATED_NODE", "#ffb300","14:15"),
            ("1120","HIGH_VELOCITY", "#00e5ff","14:08"),
            ("6677","CIRCULAR_REF",  "#ff006e","13:55"),
            ("0042","ORPHAN_CLUSTER","#a259ff","13:40"),
            ("7711","RATE_SPIKE",    "#ffb300","13:28"),
            ("2293","BRIDGE_BREAK",  "#00e5ff","13:12"),
        ]:
            st.markdown(f"""<div class="afeed" style="border-left-color:{color}">
              <span style="color:{color};font-weight:bold">ID-{aid}</span>
              <span style="color:var(--t1)">{atype}</span>
              <span class="ts">{ts}</span></div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="slabel">SEVERITY BREAKDOWN</div>', unsafe_allow_html=True)
        sev=go.Figure(go.Bar(x=["CRITICAL","HIGH","MEDIUM","LOW"],y=[3,5,8,12],
            marker_color=['#ff006e','#ffb300','#00e5ff','#00ff88'],marker_line_width=0))
        sev.update_layout(height=130,margin=dict(l=0,r=0,t=0,b=28),
            paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False,color='#2a4a5a',tickfont=dict(family='Share Tech Mono',size=7)),
            yaxis=dict(showgrid=True,gridcolor='rgba(0,229,255,.05)',color='#2a4a5a',
                       tickfont=dict(family='Share Tech Mono',size=7)),bargap=0.22)
        st.plotly_chart(sev, use_container_width=True, config=STATIC)

    with AR:
        st.markdown("""<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:9px">
          <div class="slabel" style="margin-bottom:0">ANOMALY DISTRIBUTION — 24 H</div>
          <span style="font-family:'Share Tech Mono',monospace;font-size:.57rem;color:var(--t2)">🖱 scroll=zoom</span>
        </div>""", unsafe_allow_html=True)
        st.plotly_chart(anomaly_dist_fig(), use_container_width=True, config=ZOOMABLE)

        st.markdown("<div style='height:5px'></div>", unsafe_allow_html=True)
        st.markdown("""<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:9px">
          <div class="slabel" style="margin-bottom:0">CLUSTER MAP (T‑SNE)</div>
          <span style="font-family:'Share Tech Mono',monospace;font-size:.57rem;color:var(--t2)">🖱 scroll=zoom · drag=pan</span>
        </div>""", unsafe_allow_html=True)
        st.plotly_chart(tsne_scatter_fig(), use_container_width=True, config=ZOOMABLE)
        st.markdown("""<div style="display:flex;gap:14px;flex-wrap:wrap;margin-top:5px;
                    font-family:'Share Tech Mono',monospace;font-size:.6rem;">
          <span><span style="color:#00e5ff">■</span> CLUSTER-A (80)</span>
          <span><span style="color:#00ff88">■</span> CLUSTER-B (90)</span>
          <span><span style="color:#ff006e">■</span> ANOMALY (70)</span>
          <span><span style="color:#ffb300">■</span> PENDING (60)</span>
        </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  TAB 3 — UNITY-LIVE CONSOLE
# ═══════════════════════════════════════════════════════════════
elif active == "unity":
    VL, VR_col = st.columns([3.2,2.2], gap="medium")

    with VL:
        st.markdown('<div class="slabel">UNITY WebGL — VR EMBED</div>', unsafe_allow_html=True)
        unity_url = st.text_input("🔗 Unity WebGL Build URL",
            value="https://your-unity-webgl-build.netlify.app",
            help="Paste your Unity WebGL build URL")
        st.markdown(f"""<div class="vrpanel" style="margin-bottom:11px">
          <div class="vrtoolbar">
            <span>UNITY&#8209;LIVE &nbsp;|&nbsp;<span class="hi">WebGL 2.0 · OpenXR</span></span>
            <span style="color:var(--green)">● STREAM ACTIVE</span>
          </div>
          <div style="background:#010810;position:relative">
            <iframe src="{unity_url}" width="100%" height="450"
              style="border:none;display:block;"
              allow="fullscreen; xr-spatial-tracking; camera; microphone"
              allowfullscreen></iframe>
          </div>
          <div style="padding:5px 11px;font-family:'Share Tech Mono',monospace;
                      font-size:.58rem;color:var(--t2);text-align:center;border-top:1px solid var(--border)">
            ▸ XR SPATIAL TRACKING ENABLED &nbsp;·&nbsp; PASSTHROUGH MODE: ON
          </div></div>""", unsafe_allow_html=True)

        st.markdown('<div class="slabel">CONSOLE LOG — REAL TIME</div>', unsafe_allow_html=True)
        _, lc2 = st.columns([3,1])
        with lc2:
            if st.button("+ LOG", key="addlog"):
                st.session_state.log_lines.append(random.choice([
                    ("INFO","UMAP: new batch projection complete"),
                    ("WARN","High latency on WebSocket bridge (24ms)"),
                    ("OK","Anomaly model retrained — accuracy 97.3%"),
                    ("ERROR","Cluster-3304 isolation triggered"),
                    ("INFO","XR frame rendered in 11.2ms"),
                ]))
                if len(st.session_state.log_lines)>12: st.session_state.log_lines.pop(0)
                st.rerun()
        cmap={"INFO":"log-info","WARN":"log-warn","ERROR":"log-err","OK":"log-ok"}
        ts_list=[f"14:21:{str(i+1).zfill(2)}" for i in range(20)]
        lh='<div class="logbox">'
        for i,(lvl,msg) in enumerate(st.session_state.log_lines):
            ts=ts_list[i] if i<len(ts_list) else "14:21:20"
            lh+=f'<div><span class="{cmap.get(lvl,"log-info")}">[{ts}] {lvl}</span>&nbsp;<span class="log-msg">{msg}</span></div>'
        lh+='</div>'
        st.markdown(lh, unsafe_allow_html=True)

    with VR_col:
        st.markdown('<div class="slabel">VR CONTROLS</div>', unsafe_allow_html=True)
        st.markdown("""<div class="vcgrid">
          <div class="vcbtn g">▶ ENTER XR</div>
          <div class="vcbtn a">⏸ PAUSE SYNC</div>
          <div class="vcbtn p">✕ RESET SCENE</div>
          <div class="vcbtn c">⤴ EXPORT DATA</div>
        </div>""", unsafe_allow_html=True)
        vc1,vc2=st.columns(2)
        with vc1:
            if st.button("ENTER XR MODE", key="xr_e"): st.toast("🥽 XR Session started!", icon="🔷")
        with vc2:
            if st.button("RESET SCENE", key="xr_r"): st.toast("♻️ Scene reset complete", icon="⚙️")

        st.markdown("<div style='height:5px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="slabel">VR SESSION METRICS</div>', unsafe_allow_html=True)
        for label,val,vc in [
            ("XR FRAME RATE","89.4 fps",""),("HAND TRACKING","ACTIVE","g"),
            ("SYNC LATENCY","12 ms",""),("PASS-THROUGH","ON","g"),
            ("ECS ENTITIES","241,883",""),("PHYSICS BODIES","3,201",""),
            ("DRAW CALLS","1,204",""),("RENDER BUDGET","11.2 ms","g"),
        ]:
            st.markdown(f'<div class="vmrow"><span class="lbl">{label}</span>'
                        f'<span class="val {vc}">{val}</span></div>', unsafe_allow_html=True)

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="slabel">INTEGRATION STATUS</div>', unsafe_allow_html=True)
        st.markdown("""<div class="intstatus">
          <div style="color:var(--green);margin-bottom:7px;font-size:.7rem">● &nbsp;UNITY ↔ DATA-DIVE BRIDGE</div>
          <div class="isrow"><span class="k">Neo4j Graph</span><span class="ok">SYNCED</span></div>
          <div class="isrow"><span class="k">UMAP Space</span><span class="ok">MAPPED</span></div>
          <div class="isrow"><span class="k">ECS Mirror</span><span class="ok">ACTIVE</span></div>
          <div class="isrow"><span class="k">WebSocket</span><span class="ok">CONNECTED</span></div>
          <div class="isrow"><span class="k">OpenXR Runtime</span><span class="vc">v1.0.28</span></div>
          <div class="isrow"><span class="k">DL Anomaly</span><span class="ok">RUNNING</span></div>
        </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="slabel">BRIDGE CONFIG</div>', unsafe_allow_html=True)
        ws_url=st.text_input("ws","ws://localhost:9090/unity-bridge",label_visibility="collapsed")
        st.markdown(f"""<div style="background:var(--bg3);border:1px solid var(--border);border-radius:4px;
                    padding:9px 11px;font-family:'Share Tech Mono',monospace;font-size:.65rem;
                    color:var(--t2);margin-top:5px">
          <span style="color:var(--cyan2)">ENDPOINT:</span> {ws_url}<br>
          <span style="color:var(--cyan2)">PROTOCOL:</span> JSON / msgpack<br>
          <span style="color:var(--cyan2)">HEARTBEAT:</span> <span style="color:var(--green)">OK · 500ms</span>
        </div>""", unsafe_allow_html=True)
        if st.button("TEST CONNECTION", key="ws_t"):
            with st.spinner("Testing..."): time.sleep(0.7)
            st.success("✅  Bridge reachable — latency 8ms")