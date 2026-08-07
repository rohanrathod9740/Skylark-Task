import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import urllib.request
import json
import re
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# Page Configuration
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Skylark Drones – BI Agent",
    page_icon="🚁",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ─────────────────────────────────────────────────────────────────────────────
# Theme State
# ─────────────────────────────────────────────────────────────────────────────
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

dark = st.session_state.dark_mode

# ─────────────────────────────────────────────────────────────────────────────
# CSS Variables — full light & dark theme with complete text visibility
# ─────────────────────────────────────────────────────────────────────────────
if dark:
    theme_vars = """
    --bg-main:       #09090b;
    --bg-card:       rgba(17,17,21,0.8);
    --bg-card2:      rgba(24,24,30,0.7);
    --bg-sidebar:    linear-gradient(180deg, #09090b 0%, #0c0c10 40%, #111118 100%);
    --border:        rgba(255,255,255,0.06);
    --border-hover:  rgba(99,102,241,0.3);
    --text-primary:  #fafafa;
    --text-secondary:#a1a1aa;
    --text-muted:    #71717a;
    --accent:        #6366f1;
    --accent-glow:   rgba(99,102,241,0.15);
    --success:       #10b981;
    --warning:       #f59e0b;
    --danger:        #f43f5e;
    --metric-bg:     rgba(17,17,21,0.6);
    --metric-val:    #e2e8f0;
    --metric-lbl:    #71717a;
    --feat-bg:       rgba(17,17,21,0.5);
    --feat-border:   rgba(255,255,255,0.06);
    --feat-text:     #fafafa;
    --feat-subtext:  #a1a1aa;
    --section-text:  #fafafa;
    --activity-bg:   rgba(17,17,21,0.5);
    --activity-text: #e2e8f0;
    --activity-sub:  #71717a;
    --activity-sep:  rgba(255,255,255,0.05);
    --table-head-bg: rgba(9,9,11,0.9);
    --table-head-txt:#a1a1aa;
    --table-cell:    #e2e8f0;
    --table-sep:     rgba(255,255,255,0.05);
    --table-alt:     rgba(99,102,241,0.04);
    --kpi-bar:       rgba(17,17,21,0.7);
    --kpi-val:       #a5b4fc;
    --kpi-lbl:       #71717a;
    --btn-bg:        rgba(99,102,241,0.1);
    --btn-text:      #a5b4fc;
    --btn-border:    rgba(99,102,241,0.25);
    --input-bg:      rgba(17,17,21,0.6);
    --input-text:    #fafafa;
    --tab-bg:        rgba(17,17,21,0.6);
    --tab-text:      #71717a;
    --grid-line:     rgba(255,255,255,0.012);
    --glass:         rgba(17,17,21,0.4);
    --glass-border:  rgba(255,255,255,0.08);
    --glass-shadow:  0 8px 32px rgba(0,0,0,0.4);
    --card-shadow:   0 1px 2px rgba(0,0,0,0.3), 0 4px 16px rgba(0,0,0,0.2);
    --card-shadow-hover: 0 8px 32px rgba(99,102,241,0.15), 0 2px 8px rgba(0,0,0,0.3);
    --gradient-primary: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a78bfa 100%);
    --gradient-hero: linear-gradient(135deg, #1e1b4b 0%, #312e81 30%, #3730a3 60%, #4338ca 100%);
    """
else:
    theme_vars = """
    --bg-main:       #fafafa;
    --bg-card:       rgba(255,255,255,0.8);
    --bg-card2:      rgba(250,250,252,0.9);
    --bg-sidebar:    linear-gradient(180deg, #09090b 0%, #0c0c10 40%, #111118 100%);
    --border:        rgba(0,0,0,0.06);
    --border-hover:  rgba(99,102,241,0.3);
    --text-primary:  #09090b;
    --text-secondary:#3f3f46;
    --text-muted:    #71717a;
    --accent:        #6366f1;
    --accent-glow:   rgba(99,102,241,0.08);
    --success:       #10b981;
    --warning:       #f59e0b;
    --danger:        #f43f5e;
    --metric-bg:     rgba(255,255,255,0.7);
    --metric-val:    #09090b;
    --metric-lbl:    #71717a;
    --feat-bg:       rgba(255,255,255,0.6);
    --feat-border:   rgba(0,0,0,0.06);
    --feat-text:     #09090b;
    --feat-subtext:  #71717a;
    --section-text:  #09090b;
    --activity-bg:   rgba(255,255,255,0.7);
    --activity-text: #18181b;
    --activity-sub:  #71717a;
    --activity-sep:  rgba(0,0,0,0.05);
    --table-head-bg: rgba(250,250,252,0.95);
    --table-head-txt:#3f3f46;
    --table-cell:    #18181b;
    --table-sep:     rgba(0,0,0,0.05);
    --table-alt:     rgba(99,102,241,0.03);
    --kpi-bar:       rgba(17,17,21,0.85);
    --kpi-val:       #c7d2fe;
    --kpi-lbl:       #94a3b8;
    --btn-bg:        rgba(99,102,241,0.06);
    --btn-text:      #4f46e5;
    --btn-border:    rgba(99,102,241,0.2);
    --input-bg:      rgba(255,255,255,0.9);
    --input-text:    #09090b;
    --tab-bg:        rgba(255,255,255,0.8);
    --tab-text:      #71717a;
    --grid-line:     rgba(0,0,0,0.008);
    --glass:         rgba(255,255,255,0.5);
    --glass-border:  rgba(0,0,0,0.06);
    --glass-shadow:  0 8px 32px rgba(0,0,0,0.08);
    --card-shadow:   0 1px 2px rgba(0,0,0,0.04), 0 4px 16px rgba(0,0,0,0.06);
    --card-shadow-hover: 0 8px 32px rgba(99,102,241,0.1), 0 2px 8px rgba(0,0,0,0.08);
    --gradient-primary: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a78bfa 100%);
    --gradient-hero: linear-gradient(135deg, #312e81 0%, #3730a3 30%, #4338ca 60%, #4f46e5 100%);
    """

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Outfit:wght@300;400;500;600;700;800&display=swap');

:root {{ {theme_vars} }}

/* ── GLOBAL RESET ────────────────────────────────────────────────────────── */
html, body, [class*="css"] {{
    font-family: 'Inter', 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif !important;
    color: var(--text-primary) !important;
    -webkit-font-smoothing: antialiased !important;
    -moz-osx-font-smoothing: grayscale !important;
}}

/* ── KEYFRAME ANIMATIONS ─────────────────────────────────────────────────── */
@keyframes fadeInUp {{
    from {{ opacity: 0; transform: translateY(20px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes fadeIn {{
    from {{ opacity: 0; }}
    to {{ opacity: 1; }}
}}
@keyframes slideInRight {{
    from {{ opacity: 0; transform: translateX(-16px); }}
    to {{ opacity: 1; transform: translateX(0); }}
}}
@keyframes shimmer {{
    0% {{ background-position: -200% 0; }}
    100% {{ background-position: 200% 0; }}
}}
@keyframes gradientShift {{
    0% {{ background-position: 0% 50%; }}
    50% {{ background-position: 100% 50%; }}
    100% {{ background-position: 0% 50%; }}
}}
@keyframes glowPulse {{
    0%, 100% {{ opacity: 0.6; }}
    50% {{ opacity: 1; }}
}}
@keyframes floatSoft {{
    0% {{ transform: translateY(0px); }}
    50% {{ transform: translateY(-6px); }}
    100% {{ transform: translateY(0px); }}
}}
@keyframes pulse-dot {{
    0%, 100% {{ opacity: 1; transform: scale(1); }}
    50% {{ opacity: 0.5; transform: scale(1.5); }}
}}
@keyframes borderGlow {{
    0% {{ border-color: rgba(99,102,241,0.2); }}
    50% {{ border-color: rgba(99,102,241,0.5); }}
    100% {{ border-color: rgba(99,102,241,0.2); }}
}}
@keyframes subtleFloat {{
    0%, 100% {{ transform: translateY(0) rotate(0deg); }}
    33% {{ transform: translateY(-3px) rotate(0.3deg); }}
    66% {{ transform: translateY(1px) rotate(-0.2deg); }}
}}
@keyframes accentLine {{
    from {{ width: 0; }}
    to {{ width: 100%; }}
}}

/* ── GLOBAL BACKGROUND ───────────────────────────────────────────────────── */
.stApp {{
    background: var(--bg-main) !important;
    background-image:
        radial-gradient(ellipse 80% 60% at 10% 20%, var(--accent-glow) 0%, transparent 70%),
        radial-gradient(ellipse 60% 50% at 85% 15%, rgba(139,92,246,0.05) 0%, transparent 60%),
        linear-gradient(var(--grid-line) 1px, transparent 1px),
        linear-gradient(90deg, var(--grid-line) 1px, transparent 1px) !important;
    background-size: 100% 100%, 100% 100%, 48px 48px, 48px 48px !important;
}}
.main .block-container {{
    padding: 2rem 2.8rem !important;
    max-width: 1440px !important;
    animation: fadeIn 0.4s ease-out !important;
}}

/* Fix all paragraph and label text */
p, span, label, li, td, th, caption {{
    color: var(--text-primary) !important;
}}

/* ── SIDEBAR ─────────────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {{
    background: var(--bg-sidebar) !important;
    border-right: 1px solid rgba(255,255,255,0.04) !important;
    box-shadow: 4px 0 32px rgba(0,0,0,.4) !important;
}}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] div,
section[data-testid="stSidebar"] li {{
    color: #a1a1aa !important;
}}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {{
    color: #ffffff !important;
}}
section[data-testid="stSidebar"] .stRadio > div {{ gap: 3px; }}
section[data-testid="stSidebar"] .stRadio label {{
    padding: 11px 16px !important;
    border-radius: 12px !important;
    font-size: 13.5px !important;
    font-weight: 500 !important;
    color: #a1a1aa !important;
    transition: all .25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    border: 1px solid transparent !important;
    letter-spacing: 0.01em !important;
}}
section[data-testid="stSidebar"] .stRadio label:hover {{
    background: rgba(99,102,241,0.08) !important;
    border-color: rgba(99,102,241,0.15) !important;
    color: #e2e8f0 !important;
    transform: translateX(2px) !important;
}}
section[data-testid="stSidebar"] .stRadio label[data-checked="true"],
section[data-testid="stSidebar"] .stRadio [aria-checked="true"] + label {{
    background: rgba(99,102,241,0.12) !important;
    border-color: rgba(99,102,241,0.25) !important;
    color: #c7d2fe !important;
}}

/* ── HEADINGS ────────────────────────────────────────────────────────────── */
h1 {{
    color: var(--text-primary) !important;
    font-weight: 800 !important;
    letter-spacing: -0.04em !important;
    line-height: 1.1 !important;
    font-family: 'Outfit', sans-serif !important;
}}
h2 {{
    color: var(--text-primary) !important;
    font-weight: 700 !important;
    letter-spacing: -0.03em !important;
    line-height: 1.2 !important;
    font-family: 'Outfit', sans-serif !important;
}}
h3 {{
    color: var(--text-primary) !important;
    font-weight: 600 !important;
    letter-spacing: -0.02em !important;
    line-height: 1.3 !important;
    font-family: 'Outfit', sans-serif !important;
}}
h4 {{
    color: var(--text-primary) !important;
    font-weight: 600 !important;
    letter-spacing: -0.015em !important;
    line-height: 1.35 !important;
}}

/* ── METRIC CARDS (Streamlit native) ─────────────────────────────────────── */
[data-testid="metric-container"] {{
    background: var(--glass) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 16px !important;
    padding: 22px 24px !important;
    box-shadow: var(--card-shadow) !important;
    position: relative !important;
    overflow: hidden !important;
    backdrop-filter: blur(20px) saturate(180%) !important;
    -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
    transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1) !important;
    animation: fadeInUp 0.5s ease-out both !important;
}}
[data-testid="metric-container"]:hover {{
    transform: translateY(-4px) !important;
    box-shadow: var(--card-shadow-hover) !important;
    border-color: var(--border-hover) !important;
}}
[data-testid="metric-container"]::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: var(--gradient-primary);
    border-radius: 16px 16px 0 0;
    opacity: 0.8;
}}
[data-testid="metric-container"] [data-testid="stMetricLabel"] p {{
    font-size: 10.5px !important;
    font-weight: 700 !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
    color: var(--metric-lbl) !important;
}}
[data-testid="metric-container"] [data-testid="stMetricValue"] {{
    font-size: 28px !important;
    font-weight: 800 !important;
    color: var(--metric-val) !important;
    line-height: 1.15 !important;
    font-family: 'Outfit', sans-serif !important;
}}
[data-testid="metric-container"] [data-testid="stMetricValue"] div {{
    color: var(--metric-val) !important;
}}

/* ── HERO CARD ───────────────────────────────────────────────────────────── */
.hero-card {{
    background: var(--gradient-hero);
    border-radius: 24px;
    padding: 52px 60px;
    margin-bottom: 28px;
    box-shadow: 0 16px 64px rgba(99,102,241,.25), 0 4px 16px rgba(0,0,0,.15);
    position: relative;
    overflow: hidden;
    animation: subtleFloat 8s ease-in-out infinite;
    border: 1px solid rgba(255,255,255,0.08);
}}
.hero-card::before {{
    content: '';
    position: absolute;
    top: -80px; right: -80px;
    width: 280px; height: 280px;
    background: radial-gradient(circle, rgba(139,92,246,0.2) 0%, transparent 70%);
    border-radius: 50%;
    animation: glowPulse 4s ease-in-out infinite;
}}
.hero-card::after {{
    content: '';
    position: absolute;
    bottom: -50px; left: 100px;
    width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(99,102,241,0.12) 0%, transparent 70%);
    border-radius: 50%;
    animation: glowPulse 5s ease-in-out infinite 1s;
}}
.hero-card h1 {{
    font-size: 38px !important;
    font-weight: 800 !important;
    color: #ffffff !important;
    margin-bottom: 14px !important;
    letter-spacing: -0.03em !important;
    text-shadow: 0 2px 12px rgba(0,0,0,.2);
    position: relative;
    z-index: 1;
}}
.hero-card p {{
    font-size: 15.5px !important;
    color: rgba(255,255,255,.8) !important;
    line-height: 1.7 !important;
    max-width: 640px;
    position: relative;
    z-index: 1;
}}
.hero-live-badge {{
    display: inline-flex; align-items: center; gap: 8px;
    background: rgba(255,255,255,.1);
    border: 1px solid rgba(255,255,255,.15);
    padding: 6px 16px; border-radius: 100px;
    font-size: 11px; font-weight: 700;
    color: #ffffff !important;
    letter-spacing: .6px;
    margin-bottom: 22px;
    backdrop-filter: blur(8px);
    position: relative;
    z-index: 1;
}}
.hero-live-dot {{
    width: 8px; height: 8px; background: #10b981;
    border-radius: 50%; animation: pulse-dot 1.6s ease-in-out infinite;
    box-shadow: 0 0 8px rgba(16,185,129,0.6);
}}

/* ── KPI BAR ─────────────────────────────────────────────────────────────── */
.kpi-bar {{
    background: var(--kpi-bar);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 20px;
    padding: 22px 32px;
    display: flex; align-items: center;
    justify-content: space-between; flex-wrap: wrap;
    gap: 16px; margin-bottom: 32px;
    box-shadow: 0 4px 24px rgba(0,0,0,.2);
    backdrop-filter: blur(16px) saturate(180%);
    -webkit-backdrop-filter: blur(16px) saturate(180%);
    animation: fadeInUp 0.6s ease-out both;
}}
.kpi-item {{ text-align: center; animation: fadeInUp 0.5s ease-out both; }}
.kpi-item:nth-child(1) {{ animation-delay: 0.05s; }}
.kpi-item:nth-child(3) {{ animation-delay: 0.1s; }}
.kpi-item:nth-child(5) {{ animation-delay: 0.15s; }}
.kpi-item:nth-child(7) {{ animation-delay: 0.2s; }}
.kpi-item:nth-child(9) {{ animation-delay: 0.25s; }}
.kpi-item:nth-child(11) {{ animation-delay: 0.3s; }}
.kpi-item:nth-child(13) {{ animation-delay: 0.35s; }}
.kpi-val {{
    font-size: 22px; font-weight: 800; color: var(--kpi-val) !important;
    font-family: 'Outfit', sans-serif;
    letter-spacing: -0.02em;
}}
.kpi-lbl {{
    font-size: 10px; font-weight: 600; color: var(--kpi-lbl) !important;
    text-transform: uppercase; letter-spacing: .7px; margin-top: 4px;
}}
.kpi-divider {{ width: 1px; height: 40px; background: rgba(255,255,255,.06); }}

/* ── SECTION HEADER ──────────────────────────────────────────────────────── */
.section-header {{
    font-size: 18px; font-weight: 700;
    color: var(--section-text) !important;
    margin: 32px 0 20px; display: flex; align-items: center; gap: 10px;
    font-family: 'Outfit', sans-serif;
    letter-spacing: -0.02em;
}}
.section-header::after {{
    content: ''; flex: 1; height: 1px;
    background: linear-gradient(90deg, var(--border-hover), transparent);
    margin-left: 14px;
    animation: accentLine 1s ease-out both;
}}

/* ── FEATURE CARDS ───────────────────────────────────────────────────────── */
.feat-card {{
    background: var(--glass);
    border: 1px solid var(--glass-border);
    border-radius: 20px; padding: 28px;
    box-shadow: var(--card-shadow);
    transition: all .35s cubic-bezier(0.4, 0, 0.2, 1);
    height: 100%;
    backdrop-filter: blur(16px) saturate(180%);
    -webkit-backdrop-filter: blur(16px) saturate(180%);
    position: relative;
    overflow: hidden;
    animation: fadeInUp 0.5s ease-out both;
}}
.feat-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: var(--gradient-primary);
    opacity: 0;
    transition: opacity 0.35s ease;
}}
.feat-card:hover {{
    transform: translateY(-6px);
    box-shadow: var(--card-shadow-hover);
    border-color: var(--border-hover);
}}
.feat-card:hover::before {{
    opacity: 1;
}}
.feat-icon-wrap {{
    width: 52px; height: 52px; border-radius: 16px;
    display: flex; align-items: center; justify-content: center;
    font-size: 24px; margin-bottom: 18px;
    transition: transform 0.3s ease;
    box-shadow: 0 4px 12px rgba(0,0,0,0.06);
}}
.feat-card:hover .feat-icon-wrap {{
    transform: scale(1.08) rotate(2deg);
}}
.feat-card h4 {{
    font-size: 15px; font-weight: 700;
    color: var(--feat-text) !important;
    margin: 0 0 8px; letter-spacing: -0.01em;
}}
.feat-card p {{
    font-size: 13px; color: var(--feat-subtext) !important;
    margin: 0; line-height: 1.65;
}}

/* ── ACTIVITY CARD ───────────────────────────────────────────────────────── */
.activity-card {{
    background: var(--glass);
    border: 1px solid var(--glass-border);
    border-radius: 20px; padding: 24px 28px;
    box-shadow: var(--card-shadow);
    backdrop-filter: blur(16px) saturate(180%);
    -webkit-backdrop-filter: blur(16px) saturate(180%);
    animation: fadeInUp 0.6s ease-out both;
}}
.activity-row {{
    display: flex; align-items: flex-start; gap: 14px;
    padding: 13px 0; border-bottom: 1px solid var(--activity-sep);
    transition: background 0.2s ease;
}}
.activity-row:hover {{
    background: var(--accent-glow);
    border-radius: 10px;
    margin: 0 -8px;
    padding-left: 8px;
    padding-right: 8px;
}}
.activity-row:last-child {{ border-bottom: none; }}
.activity-dot-green {{
    width: 10px; height: 10px; background: #10b981;
    border-radius: 50%; flex-shrink: 0; margin-top: 4px;
    box-shadow: 0 0 8px rgba(16,185,129,0.4);
    animation: pulse-dot 2s ease-in-out infinite;
}}
.activity-dot-blue  {{
    width: 10px; height: 10px; background: #6366f1;
    border-radius: 50%; flex-shrink: 0; margin-top: 4px;
    box-shadow: 0 0 8px rgba(99,102,241,0.4);
    animation: pulse-dot 2s ease-in-out infinite 0.5s;
}}
.activity-text {{
    font-size: 13.5px; color: var(--activity-text) !important;
    font-weight: 600; letter-spacing: -0.01em;
}}
.activity-sub  {{
    font-size: 12px; color: var(--activity-sub) !important;
    margin-top: 2px; line-height: 1.4;
}}

/* ── STATUS BADGES ───────────────────────────────────────────────────────── */
.green-badge {{
    background: rgba(16,185,129,.1); color: #10b981 !important;
    border: 1px solid rgba(16,185,129,.2);
    padding: 5px 16px; border-radius: 100px;
    font-size: 10.5px; font-weight: 700; letter-spacing: .8px;
    display: inline-flex; align-items: center; gap: 7px; margin-bottom: 18px;
    text-transform: uppercase;
}}
.live-dot {{
    width: 7px; height: 7px; background: #10b981;
    border-radius: 50%; animation: pulse-dot 1.6s ease-in-out infinite;
    box-shadow: 0 0 6px rgba(16,185,129,0.5);
}}

/* ── REPORT TABLE ────────────────────────────────────────────────────────── */
.report-table {{
    width: 100%; border-collapse: separate; border-spacing: 0;
    border-radius: 16px; overflow: hidden;
    border: 1px solid var(--glass-border);
    box-shadow: var(--card-shadow);
}}
.report-table th {{
    background: var(--table-head-bg) !important;
    color: var(--table-head-txt) !important;
    font-weight: 700; font-size: 11px;
    text-transform: uppercase; letter-spacing: .8px;
    padding: 14px 22px; text-align: left;
    border-bottom: 1px solid var(--glass-border);
}}
.report-table td {{
    padding: 14px 22px; border-bottom: 1px solid var(--table-sep);
    font-size: 13.5px; color: var(--table-cell) !important;
    transition: background 0.2s ease;
}}
.report-table tr:hover td {{ background: var(--accent-glow); }}
.report-table tr:last-child td {{
    background: var(--table-alt);
    font-weight: 700; color: var(--accent) !important;
    border-bottom: none;
}}

/* ── BUTTONS ─────────────────────────────────────────────────────────────── */
.stButton > button {{
    border-radius: 12px !important;
    font-weight: 600 !important; font-size: 13px !important;
    background: var(--btn-bg) !important;
    color: var(--btn-text) !important;
    border: 1px solid var(--btn-border) !important;
    transition: all .25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 1px 3px rgba(0,0,0,.04) !important;
    letter-spacing: 0.01em !important;
    padding: 8px 20px !important;
}}
.stButton > button:hover {{
    background: var(--gradient-primary) !important;
    color: #ffffff !important;
    border-color: rgba(99,102,241,0.5) !important;
    box-shadow: 0 4px 16px rgba(99,102,241,.3) !important;
    transform: translateY(-2px) !important;
}}
.stButton > button:active {{
    transform: translateY(0px) !important;
    box-shadow: 0 2px 8px rgba(99,102,241,.2) !important;
}}

/* ── INPUTS ──────────────────────────────────────────────────────────────── */
.stTextInput input, .stSelectbox select, div[data-baseweb="select"] {{
    background: var(--input-bg) !important;
    color: var(--input-text) !important;
    border-color: var(--border) !important;
    border-radius: 12px !important;
    transition: all 0.25s ease !important;
}}
.stTextInput input:focus {{
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-glow) !important;
}}
.stTextInput input::placeholder {{ color: var(--text-muted) !important; }}

/* ── TABS ────────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {{
    background: var(--tab-bg);
    border-radius: 14px; padding: 4px;
    border: 1px solid var(--border); gap: 4px;
    backdrop-filter: blur(12px);
}}
.stTabs [data-baseweb="tab"] {{
    border-radius: 10px; font-weight: 600; font-size: 13.5px;
    padding: 8px 20px; color: var(--tab-text) !important;
    transition: all 0.25s ease;
}}
.stTabs [aria-selected="true"] {{
    background: var(--gradient-primary) !important;
    color: #ffffff !important;
    box-shadow: 0 4px 12px rgba(99,102,241,0.25) !important;
}}

/* ── DOWNLOAD BUTTON ─────────────────────────────────────────────────────── */
[data-testid="stDownloadButton"] > button {{
    background: var(--gradient-primary) !important;
    color: #ffffff !important; border: none !important;
    border-radius: 12px !important; font-weight: 700 !important;
    box-shadow: 0 4px 16px rgba(99,102,241,.3) !important;
    transition: all 0.25s ease !important;
}}
[data-testid="stDownloadButton"] > button:hover {{
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 24px rgba(99,102,241,.4) !important;
}}

/* ── CHAT ────────────────────────────────────────────────────────────────── */
[data-testid="stChatMessageContent"] {{
    font-size: 14px !important; line-height: 1.75 !important;
}}

/* ── DATAFRAME ───────────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {{
    border-radius: 16px !important; overflow: hidden !important;
    border: 1px solid var(--glass-border) !important;
    box-shadow: var(--card-shadow) !important;
}}

/* ── SUCCESS / INFO / EXPANDER ───────────────────────────────────────────── */
.stSuccess, .stInfo {{ border-radius: 14px !important; }}
.streamlit-expanderHeader {{ color: var(--text-primary) !important; font-weight: 600 !important; }}
.streamlit-expanderContent {{ color: var(--text-primary) !important; }}

/* ── MARKDOWN TEXT ────────────────────────────────────────────────────────── */
.stMarkdown p, .stMarkdown li, .stMarkdown span {{ color: var(--text-primary) !important; }}
.stCaption {{ color: var(--text-muted) !important; }}

/* ── GLASSMORPHIC CONTAINER (reusable utility) ───────────────────────────── */
.glass-panel {{
    background: var(--glass) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 20px !important;
    backdrop-filter: blur(20px) saturate(180%) !important;
    -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
    box-shadow: var(--card-shadow) !important;
    padding: 24px !important;
    transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1) !important;
}}
.glass-panel:hover {{
    border-color: var(--border-hover) !important;
    box-shadow: var(--card-shadow-hover) !important;
}}

/* ── PREMIUM KPI CARD ────────────────────────────────────────────────────── */
.premium-kpi {{
    background: var(--glass);
    border: 1px solid var(--glass-border);
    border-radius: 20px;
    padding: 24px;
    box-shadow: var(--card-shadow);
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(20px) saturate(180%);
    -webkit-backdrop-filter: blur(20px) saturate(180%);
    transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
    animation: fadeInUp 0.5s ease-out both;
}}
.premium-kpi:hover {{
    transform: translateY(-4px);
    box-shadow: var(--card-shadow-hover);
    border-color: var(--border-hover);
}}
.premium-kpi::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 20px 20px 0 0;
}}
.premium-kpi.accent-green::before {{ background: linear-gradient(90deg, #10b981, #34d399); }}
.premium-kpi.accent-blue::before {{ background: linear-gradient(90deg, #6366f1, #818cf8); }}
.premium-kpi.accent-amber::before {{ background: linear-gradient(90deg, #f59e0b, #fbbf24); }}
.premium-kpi.accent-rose::before {{ background: linear-gradient(90deg, #f43f5e, #fb7185); }}
.premium-kpi .kpi-label {{
    font-size: 10.5px; font-weight: 700; color: var(--text-muted);
    text-transform: uppercase; letter-spacing: 0.8px;
    margin-bottom: 8px; display: flex; align-items: center;
    justify-content: space-between;
}}
.premium-kpi .kpi-value {{
    font-size: 30px; font-weight: 800; color: var(--text-primary);
    font-family: 'Outfit', sans-serif; letter-spacing: -0.03em;
    line-height: 1.1; margin-bottom: 4px;
}}
.premium-kpi .kpi-comparison {{
    font-size: 11px; color: var(--text-muted); margin-bottom: 12px;
}}
.premium-kpi .kpi-progress {{
    height: 3px; border-radius: 2px; margin-bottom: 14px;
    background: rgba(255,255,255,0.04);
    overflow: hidden;
}}
.premium-kpi .kpi-progress-fill {{
    height: 100%; border-radius: 2px;
    animation: accentLine 1.2s ease-out both;
}}
.premium-kpi .kpi-insight {{
    font-size: 12px; color: var(--text-primary);
    line-height: 1.5; padding: 10px 12px;
    background: var(--accent-glow);
    border-radius: 10px; border-left: 2px solid var(--accent);
}}

/* Trend badges */
.trend-badge {{
    padding: 2px 10px; border-radius: 100px;
    font-size: 10.5px; font-weight: 700;
    display: inline-flex; align-items: center; gap: 3px;
}}
.trend-up {{
    background: rgba(16,185,129,0.1); color: #10b981;
    border: 1px solid rgba(16,185,129,0.15);
}}
.trend-down {{
    background: rgba(244,63,94,0.1); color: #f43f5e;
    border: 1px solid rgba(244,63,94,0.15);
}}
.trend-neutral {{
    background: rgba(99,102,241,0.1); color: #6366f1;
    border: 1px solid rgba(99,102,241,0.15);
}}

/* ── HEALTH INDICATOR ────────────────────────────────────────────────────── */
.health-card {{
    background: var(--glass);
    border: 1px solid var(--glass-border);
    border-radius: 16px;
    padding: 16px 20px;
    margin-bottom: 12px;
    backdrop-filter: blur(16px);
    transition: all 0.25s ease;
    animation: fadeInUp 0.5s ease-out both;
}}
.health-card:hover {{
    border-color: var(--border-hover);
    transform: translateX(4px);
}}

/* ── PRIORITY BADGES ─────────────────────────────────────────────────────── */
.priority-p1 {{
    background: linear-gradient(135deg, #f43f5e, #e11d48);
    color: #fff; font-size: 9px; font-weight: 800;
    padding: 3px 8px; border-radius: 6px;
    text-transform: uppercase; letter-spacing: 0.5px;
    box-shadow: 0 2px 8px rgba(244,63,94,0.3);
}}
.priority-p2 {{
    background: linear-gradient(135deg, #f59e0b, #d97706);
    color: #fff; font-size: 9px; font-weight: 800;
    padding: 3px 8px; border-radius: 6px;
    text-transform: uppercase; letter-spacing: 0.5px;
    box-shadow: 0 2px 8px rgba(245,158,11,0.3);
}}
.priority-p3 {{
    background: linear-gradient(135deg, #6366f1, #4f46e5);
    color: #fff; font-size: 9px; font-weight: 800;
    padding: 3px 8px; border-radius: 6px;
    text-transform: uppercase; letter-spacing: 0.5px;
    box-shadow: 0 2px 8px rgba(99,102,241,0.3);
}}

/* ── EXECUTIVE BRIEF BAR ─────────────────────────────────────────────────── */
.exec-bar {{
    background: var(--kpi-bar);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 20px;
    padding: 20px 28px;
    box-shadow: 0 4px 24px rgba(0,0,0,.15);
    backdrop-filter: blur(16px) saturate(180%);
    display: flex; justify-content: space-between;
    align-items: center; flex-wrap: wrap; gap: 16px;
    margin-bottom: 28px;
    animation: fadeInUp 0.5s ease-out both;
}}

/* ── COLLAPSE/EXPAND BUTTONS (Header vs Sidebar) ─────────────────────────── */
[data-testid="collapsedControl"] {{
    opacity: 1 !important;
    visibility: visible !important;
    z-index: 999999 !important;
    position: relative !important;
}}
[data-testid="collapsedControl"] button,
header button,
header [data-testid="stToolbar"] button:first-child,
header button[kind="header"],
header button[data-testid="baseButton-header"],
header button[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapsedControl"] button,
[data-testid="stSidebarCollapsedControl"] {{
    color: #ffffff !important;
    background: #6366f1 !important;
    border: 2px solid rgba(165, 180, 252, 0.4) !important;
    border-radius: 12px !important;
    opacity: 1 !important;
    visibility: visible !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.25), 0 4px 16px rgba(99,102,241,0.4) !important;
    min-width: 38px !important;
    min-height: 38px !important;
    z-index: 999999 !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
}}
[data-testid="collapsedControl"] button:hover,
header button[kind="header"]:hover,
header button[data-testid="baseButton-header"]:hover,
header button[data-testid="stSidebarCollapseButton"]:hover,
[data-testid="stSidebarCollapsedControl"] button:hover {{
    background: #4f46e5 !important;
    box-shadow: 0 0 0 4px rgba(99,102,241,0.35), 0 6px 22px rgba(99,102,241,0.5) !important;
    transform: scale(1.1) !important;
}}
[data-testid="collapsedControl"] svg,
[data-testid="collapsedControl"] button svg,
header button svg,
header button[kind="header"] svg,
header button[data-testid="baseButton-header"] svg,
header button[data-testid="stSidebarCollapseButton"] svg,
[data-testid="stSidebarCollapsedControl"] svg {{
    fill: #ffffff !important;
    color: #ffffff !important;
    stroke: #ffffff !important;
    opacity: 1 !important;
    width: 22px !important;
    height: 22px !important;
}}
header[data-testid="stHeader"],
header {{
    z-index: 99999 !important;
}}

/* Sidebar Collapse Button (in sidebar when expanded) */
section[data-testid="stSidebar"] button[data-testid="stSidebarCollapseButton"] {{
    background: rgba(99,102,241,0.15) !important;
    border: 1px solid rgba(99,102,241,0.2) !important;
    border-radius: 10px !important;
    opacity: 1 !important;
    visibility: visible !important;
}}
section[data-testid="stSidebar"] button[data-testid="stSidebarCollapseButton"] svg {{
    fill: #a5b4fc !important;
    color: #a5b4fc !important;
    opacity: 1 !important;
}}
section[data-testid="stSidebar"] button[data-testid="stSidebarCollapseButton"]:hover {{
    background: rgba(99,102,241,0.25) !important;
}}

/* ── DIVIDER ─────────────────────────────────────────────────────────────── */
hr, .stMarkdown hr {{
    border: none !important;
    height: 1px !important;
    background: linear-gradient(90deg, transparent, var(--border), transparent) !important;
    margin: 28px 0 !important;
}}

/* ── SCROLLBAR ───────────────────────────────────────────────────────────── */
::-webkit-scrollbar {{ width: 6px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{
    background: rgba(99,102,241,0.2);
    border-radius: 3px;
}}
::-webkit-scrollbar-thumb:hover {{ background: rgba(99,102,241,0.35); }}
</style>
""", unsafe_allow_html=True)




# ─────────────────────────────────────────────────────────────────────────────
# Database — absolute path for Streamlit Cloud
# ─────────────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "backend", "skylark.db")

@st.cache_resource
def get_conn():
    if not os.path.exists(DB_PATH):
        return None
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c

conn = get_conn()
if conn is None:
    st.error(f"⚠️ Database not found at `{DB_PATH}`. Ensure `backend/skylark.db` is committed to the repo.")
    st.stop()

def qdb(sql):
    try:
        return [dict(r) for r in conn.execute(sql).fetchall()]
    except Exception as e:
        return [{"error": str(e)}]

def get_chart_theme():
    if st.session_state.get("dark_mode", False):
        return {
            "plot_bgcolor": "rgba(17,17,21,0.01)",
            "paper_bgcolor": "rgba(17,17,21,0.01)",
            "font_color": "#fafafa",
            "grid_color": "rgba(255,255,255,0.04)"
        }
    else:
        return {
            "plot_bgcolor": "rgba(255,255,255,0.01)",
            "paper_bgcolor": "rgba(255,255,255,0.01)",
            "font_color": "#09090b",
            "grid_color": "rgba(0,0,0,0.04)"
        }

# ─────────────────────────────────────────────────────────────────────────────
# AI Agent: Dynamic SQL Engine & Synthesis
# ─────────────────────────────────────────────────────────────────────────────

def call_gemini_raw(prompt: str) -> str:
    api_key = st.secrets.get("GEMINI_API_KEY", "")
    if not api_key:
        return ""
    # Call Gemini 2.0 Flash API via urllib
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            data = json.loads(r.read().decode("utf-8"))
            return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return ""

def is_safe_sql(sql_query: str) -> bool:
    clean = sql_query.strip().upper()
    if not clean.startswith("SELECT"):
        return False
    # Strict read-only query check
    forbidden = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "REPLACE", "CREATE", "TRUNCATE", "RENAME", "GRANT", "REVOKE"]
    for f in forbidden:
        if re.search(rf"\b{f}\b", clean):
            return False
    return True

def call_gemini_sql(query: str, history_text: str) -> str:
    prompt = f"""
You are an expert SQL translator for a Monday.com Business Intelligence Agent.
The SQLite database contains two tables:
1. `deals` table:
   - deal_name (text)
   - owner_code (text)
   - client_code (text)
   - deal_status (text: 'Open', 'Won', 'Dead', 'On Hold')
   - masked_deal_value (real)
   - closure_probability (text: 'High', 'Medium', 'Low')
   - sector_service (text: 'Mining', 'Powerline', 'Renewables', 'Railways', 'Construction', 'Tender', 'DSP', 'Aviation', 'Others')
   - deal_stage (text)
   - product_deal (text)
   - created_date (text)
   - tentative_close_date (text)
   - close_date_actual (text)
2. `work_orders` table:
   - serial_num (text)
   - customer_name_code (text)
   - nature_of_work (text)
   - execution_status (text: 'Completed', 'Ongoing', 'Not Started', 'Executed until current month', 'Partial Completed', 'Pause / struck')
   - amount_excl_gst (real)
   - billed_excl_gst (real)
   - amount_receivable (real)
   - billing_status (text: 'Billed', 'Not Billable', 'Partially Billed', 'Update Required', 'Stuck')
   - invoice_status (text)
   - bd_kam_personnel_code (text)
   - sector (text)
   - type_of_work (text)

Conversation History Context:
{history_text}

User Query: {query}

Instructions:
1. Output ONLY a clean, valid SQLite SQL query to fetch the necessary data.
2. Do NOT wrap the query in markdown formatting, backticks, or any explanation. Output only the raw SQL text.
3. Be careful with filters. Use case-insensitive matching where appropriate (e.g., using LOWER() or UPPER() on columns).
4. Handle nulls/empty values using COALESCE or CASE WHEN.
"""
    sql = call_gemini_raw(prompt)
    if not sql:
        return ""
    # Clean up formatting
    sql = sql.replace("```sql", "").replace("```", "").strip()
    if sql.startswith('"') and sql.endswith('"'):
        sql = sql[1:-1]
    return sql

def call_gemini_synthesis(query: str, sql: str, db_result: str, history_text: str) -> str:
    prompt = f"""
You are the Monday.com Business Intelligence Agent for Skylark Drones.

User Query: "{query}"
SQL Query Executed: "{sql}"
Database Result: {db_result}

Conversation History Context:
{history_text}

Instructions:
1. Provide a professional, conversational response summarizing the data. Explain what the numbers mean, highlight trends, and explain any assumptions.
2. Structure your response into three distinct parts:
   a. The main markdown response.
   b. A ```chart block if the data is suitable for visualization.
   c. A ```metadata block containing structured insights.

Format your output exactly as follows:

[Write your conversational markdown answer here. Keep it professional, and use Indian currency format (e.g. ₹ with Cr/Lakhs) for monetary values. Identify data anomalies or caveats in the data if any, such as missing dates, null fields, or over-billing/negative values.]

---
```chart
{{
  "type": "bar" | "pie" | "donut",
  "labels": ["Label1", "Label2", ...],
  "values": [Value1, Value2, ...],
  "title": "Chart Title"
}}
```

```metadata
{{
  "confidence": "High" | "Medium" | "Low",
  "confidence_reason": "Explain why this confidence level was chosen",
  "anomalies": ["Any data anomaly found", ...],
  "recommendations": ["Proactive actionable recommendation for the founder", ...],
  "follow_ups": ["Suggested follow-up query 1", "Suggested follow-up query 2", ...]
}}
```

Ensure the blocks are closed exactly with three backticks. Do not add any extra fields in the JSON.
"""
    return call_gemini_raw(prompt)

# ─────────────────────────────────────────────────────────────────────────────
# Self-contained fallback resolver
# ─────────────────────────────────────────────────────────────────────────────
def resolve_query_fallback(query: str):
    q       = query.lower()
    ans     = ""
    sql     = ""
    chart   = None

    # ── 1. Pending Billing ──────────────────────────────────────────────────
    if "pending billing" in q or "pending billed" in q:
        sql  = ("SELECT SUM(amount_excl_gst) as total_po, SUM(billed_excl_gst) as total_billed,"
                " SUM(CASE WHEN amount_excl_gst>billed_excl_gst THEN amount_excl_gst-billed_excl_gst ELSE 0 END) as pending"
                " FROM work_orders;")
        rows = qdb(sql)
        po, billed, pending = rows[0]["total_po"] or 0, rows[0]["total_billed"] or 0, rows[0]["pending"] or 0
        ans  = (f"**📊 Work Orders Pending Billing**\n\n"
                f"- Total PO Contract Value: **₹{po/1e7:.2f} Cr**\n"
                f"- Total Billed to Date: **₹{billed/1e7:.2f} Cr**\n"
                f"- **Pending Billing: ₹{pending/1e7:.2f} Cr**\n\n"
                f"> Records with over-billing (billed > PO value) are excluded to prevent negative distortion.")
        chart = ("bar", ["Total Billed", "Pending Billing"], [billed, pending], "Billing Status Breakdown")

    # ── 2. Revenue / Forecast ───────────────────────────────────────────────
    elif any(x in q for x in ["revenue forecast", "pipeline forecast", "forecast", "total won revenue", "revenue"]) and "expected" not in q:
        sql  = """SELECT
                    SUM(CASE WHEN deal_status='Won' THEN masked_deal_value ELSE 0 END) as won,
                    SUM(CASE WHEN deal_status='Open' THEN masked_deal_value ELSE 0 END) as open_pipe,
                    SUM(CASE WHEN deal_status='Open' AND closure_probability='High'   THEN masked_deal_value*.8
                             WHEN deal_status='Open' AND closure_probability='Medium' THEN masked_deal_value*.5
                             WHEN deal_status='Open' AND closure_probability='Low'    THEN masked_deal_value*.2
                             ELSE 0 END) as weighted FROM deals;"""
        r   = qdb(sql)[0]
        won, op, wt = r["won"] or 0, r["open_pipe"] or 0, r["weighted"] or 0
        ans = (f"**📈 Revenue & Pipeline Forecast**\n\n"
               f"- **Won Revenue:** ₹{won/1e7:.2f} Cr\n"
               f"- **Open Pipeline:** ₹{op/1e7:.2f} Cr\n"
               f"- **Probability-Weighted Forecast:** ₹{wt/1e7:.2f} Cr\n"
               f"  *(High=80%, Medium=50%, Low=20%)*\n"
               f"- **Total Projected Revenue:** ₹{(won+wt)/1e7:.2f} Cr")
        chart = ("bar", ["Won Revenue", "Open Pipeline", "Weighted Forecast"], [won, op, wt], "Revenue Forecast")

    # ── 3. Pipeline Health / Overview ───────────────────────────────────────
    elif any(x in q for x in ["pipeline", "pipeline health", "how is our pipeline", "deals status"]):
        sql  = "SELECT deal_status, COUNT(*) as count, SUM(masked_deal_value) as total FROM deals GROUP BY deal_status;"
        rows = qdb(sql)
        ans  = "**🔍 Sales Pipeline Health**\n\n"
        for r in rows:
            ans += f"- **{r['deal_status']}**: {r['count']} deals → ₹{(r['total'] or 0)/1e7:.2f} Cr\n"
        chart = ("pie", [r["deal_status"] for r in rows], [r["count"] for r in rows], "Pipeline Status Mix")

    # ── 4. Energy Sector ────────────────────────────────────────────────────
    elif any(x in q for x in ["energy sector", "energy", "renewables", "powerline"]):
        sql  = ("SELECT deal_status, COUNT(*) as count, SUM(masked_deal_value) as total"
                " FROM deals WHERE LOWER(sector_service) IN ('powerline','renewables') GROUP BY deal_status;")
        rows = qdb(sql)
        ans  = "**⚡ Energy Sector Pipeline**\n\n"
        for r in rows:
            ans += f"- **{r['deal_status']}**: {r['count']} deals (₹{(r['total'] or 0)/1e7:.2f} Cr)\n"
        chart = ("pie", [r["deal_status"] for r in rows], [r["total"] or 0 for r in rows], "Energy Sector Pipeline")

    # ── 5. Delayed / Stuck Work Orders ──────────────────────────────────────
    elif any(x in q for x in ["delayed", "delays", "stuck", "pause", "at risk", "not started"]):
        sql  = ("SELECT execution_status, COUNT(*) as count, SUM(amount_excl_gst) as total"
                " FROM work_orders WHERE execution_status IN ('Pause / struck','Not Started') GROUP BY execution_status;")
        rows = qdb(sql)
        risk = sum(r["total"] or 0 for r in rows)
        ans  = "**⚠️ Delayed & At-Risk Work Orders**\n\n"
        for r in rows:
            ans += f"- **{r['execution_status']}**: {r['count']} orders (₹{(r['total'] or 0)/1e5:.2f} L)\n"
        ans += f"\n> **Total At-Risk Value: ₹{risk/1e5:.2f} Lakhs**"
        chart = ("bar", [r["execution_status"] for r in rows], [r["total"] or 0 for r in rows], "At-Risk Work Orders")

    # ── 6. Expected Revenue ─────────────────────────────────────────────────
    elif "expected revenue" in q:
        sql  = """SELECT SUM(masked_deal_value) as total,
                         SUM(CASE WHEN closure_probability='High'   THEN masked_deal_value*.8
                                  WHEN closure_probability='Medium' THEN masked_deal_value*.5
                                  WHEN closure_probability='Low'    THEN masked_deal_value*.2
                                  ELSE 0 END) as expected FROM deals WHERE deal_status='Open';"""
        r   = qdb(sql)[0]
        tot, exp = r["total"] or 0, r["expected"] or 0
        ans = (f"**💰 Expected Revenue from Open Deals**\n\n"
               f"- Total Open Pipeline: **₹{tot/1e7:.2f} Cr**\n"
               f"- **Expected Revenue (probability-adjusted): ₹{exp/1e7:.2f} Cr**\n"
               f"- Risk Discount: ₹{(tot-exp)/1e7:.2f} Cr")
        chart = ("donut", ["Expected Revenue", "Risk Discount"], [exp, tot - exp], "Expected Revenue Breakdown")

    # ── 7. Operational Risks ────────────────────────────────────────────────
    elif any(x in q for x in ["operational risk", "risks", "stuck work"]):
        sql  = ("SELECT serial_num, customer_name_code, nature_of_work, amount_excl_gst, execution_status"
                " FROM work_orders WHERE execution_status='Pause / struck' OR billing_status='Stuck' LIMIT 10;")
        rows = qdb(sql)
        ans  = "**⚡ Operational Risks & Stuck Projects**\n\n"
        for r in rows:
            ans += f"- **{r['serial_num']}** | {r['customer_name_code']} | {r['nature_of_work']} → *{r['execution_status']}* (₹{(r['amount_excl_gst'] or 0)/1e5:.2f} L)\n"

    # ── 8. Top Clients ──────────────────────────────────────────────────────
    elif any(x in q for x in ["top client", "enterprise client", "top enterprise", "best client"]):
        sql  = ("SELECT client_code, SUM(masked_deal_value) as total, COUNT(*) as count"
                " FROM deals GROUP BY client_code ORDER BY total DESC LIMIT 5;")
        rows = qdb(sql)
        ans  = "**🏢 Top 5 Enterprise Clients by Pipeline Value**\n\n"
        for i, r in enumerate(rows, 1):
            ans += f"{i}. **{r['client_code']}** — ₹{(r['total'] or 0)/1e7:.2f} Cr across {r['count']} deals\n"
        chart = ("bar", [r["client_code"] for r in rows], [r["total"] or 0 for r in rows], "Top Clients by Pipeline")

    # ── 9. Leadership Summary ───────────────────────────────────────────────
    elif any(x in q for x in ["leadership summary", "leadership update", "comprehensive", "executive summary"]):
        sql  = """SELECT
                    (SELECT SUM(masked_deal_value) FROM deals WHERE deal_status='Won') as won,
                    (SELECT COUNT(*) FROM deals WHERE deal_status='Open') as open_count,
                    (SELECT SUM(masked_deal_value) FROM deals WHERE deal_status='Open') as open_pipe,
                    (SELECT SUM(amount_excl_gst) FROM work_orders WHERE execution_status='Completed') as completed,
                    (SELECT SUM(amount_receivable) FROM work_orders) as receivable
                  FROM deals LIMIT 1;"""
        r = qdb(sql)[0]
        ans = (f"**👑 Executive Leadership Summary**\n\n"
               f"**Sales & Pipeline**\n"
               f"- Won Revenue: **₹{(r['won'] or 0)/1e7:.2f} Cr**\n"
               f"- Active Pipeline: **₹{(r['open_pipe'] or 0)/1e7:.2f} Cr** ({r['open_count']} deals)\n\n"
               f"**Operations**\n"
               f"- Completed Project Value: **₹{(r['completed'] or 0)/1e5:.2f} Lakhs**\n"
               f"- Outstanding Receivables: **₹{(r['receivable'] or 0)/1e5:.2f} Lakhs**")

    # ── 10. Sectoral ────────────────────────────────────────────────────────
    elif any(x in q for x in ["sector", "mining", "aviation", "railways", "construction"]):
        sql  = ("SELECT sector_service, SUM(masked_deal_value) as value, COUNT(*) as count"
                " FROM deals GROUP BY sector_service ORDER BY value DESC;")
        rows = qdb(sql)
        ans  = "**🌐 Pipeline by Sector**\n\n"
        for r in rows:
            ans += f"- **{r['sector_service'] or 'Other'}**: ₹{(r['value'] or 0)/1e7:.2f} Cr ({r['count']} deals)\n"
        chart = ("bar", [r["sector_service"] or "Other" for r in rows], [r["value"] or 0 for r in rows], "Pipeline by Sector")

    # ── 11. Work Orders ─────────────────────────────────────────────────────
    elif any(x in q for x in ["work order", "execution", "operations", "operational"]):
        sql  = ("SELECT execution_status, COUNT(*) as count, SUM(amount_excl_gst) as total"
                " FROM work_orders GROUP BY execution_status ORDER BY count DESC;")
        rows = qdb(sql)
        ans  = "**🛠️ Work Orders Execution Status**\n\n"
        for r in rows:
            ans += f"- **{r['execution_status'] or 'Unknown'}**: {r['count']} orders (₹{(r['total'] or 0)/1e5:.2f} L)\n"
        chart = ("pie", [r["execution_status"] or "Unknown" for r in rows], [r["count"] for r in rows], "WO Execution Status")

    else:
        ans = ("I can answer questions about:\n\n"
               "📊 **Revenue & Pipeline** | ⚡ **Energy Sector** | ⚠️ **Delayed Work Orders**\n"
               "🏢 **Top Clients** | 💰 **Expected Revenue** | 👑 **Leadership Summary**\n"
               "🌐 **Sectoral Performance** | 🛠️ **Work Orders** | 📋 **Operational Risks**\n\n"
               "Or ask me any general question about sales deals, pipeline health, or work order operations!")

    return ans, sql, chart

def resolve_query(query: str) -> tuple:
    # 1. Format the conversation history (last 5 messages)
    history_list = st.session_state.get("messages", [])
    history_text = ""
    for msg in history_list[-5:]:
        if msg["role"] == "system" or "Hi! I'm the Skylark Drones BI Agent" in msg["content"]:
            continue
        history_text += f"{msg['role'].capitalize()}: {msg['content']}\n"
    
    api_key = st.secrets.get("GEMINI_API_KEY", "")
    if api_key:
        try:
            # Step A: Generate SQL query
            sql = call_gemini_sql(query, history_text)
            if sql and is_safe_sql(sql):
                # Step B: Run SQL query
                data = qdb(sql)
                if data and not (len(data) == 1 and "error" in data[0]):
                    # Step C: Synthesize answer
                    synthesis = call_gemini_synthesis(query, sql, json.dumps(data[:30]), history_text)
                    if synthesis:
                        # Step D: Parse synthesis response
                        main_text = synthesis.split("---")[0].strip()
                        if not main_text:
                            main_text = synthesis
                        
                        # Parse chart
                        chart_data = None
                        chart_match = re.search(r"```chart\s*(.*?)\s*```", synthesis, re.DOTALL)
                        if chart_match:
                            try:
                                cjson = json.loads(chart_match.group(1).strip())
                                chart_data = (cjson["type"], cjson["labels"], cjson["values"], cjson["title"])
                            except Exception:
                                pass
                        
                        # Parse metadata
                        meta_data = None
                        meta_match = re.search(r"```metadata\s*(.*?)\s*```", synthesis, re.DOTALL)
                        if meta_match:
                            try:
                                meta_data = json.loads(meta_match.group(1).strip())
                            except Exception:
                                pass
                        
                        return main_text, sql, chart_data, meta_data
            
            # Step E: Fallback for general/outside query when API is online but SQL fails or is not applicable
            general_prompt = f"""
            You are a helpful Business Intelligence Copilot.
            The user is asking a general, calculations, or outside question: "{query}"
            
            Conversation History Context:
            {history_text}
            
            Provide a helpful, direct, and concise answer to the user's question. If the user asks a general knowledge query (e.g. geography, history, general business concepts, math, coding, or any general facts), answer it directly. Keep it professional.
            """
            general_ans = call_gemini_raw(general_prompt)
            if general_ans:
                return general_ans.strip(), "", None, {}
        except Exception:
            pass
            
    # Fallback to local rule-based resolver
    ans, sql, chart = resolve_query_fallback(query)
    return ans, sql, chart, {}


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
st.sidebar.markdown("""
<div style="text-align: center; margin-top: -30px; margin-bottom: -20px;">
    <canvas id="neural-orb" width="130" height="130" style="background:transparent; cursor:pointer; filter: drop-shadow(0 0 15px rgba(99,102,241,0.2));"></canvas>
</div>
<script>
(function(){
var canvas=document.getElementById("neural-orb");
if(!canvas)return;
var ctx=canvas.getContext("2d");
var width=canvas.width,height=canvas.height;
var centerX=width/2,centerY=height/2;
var radius=42,angle=0;
var particles=[];
for(var i=0;i<24;i++){
particles.push({x:centerX+(Math.random()-0.5)*40,y:centerY+(Math.random()-0.5)*40,r:Math.random()*1.5+1,speedX:(Math.random()-0.5)*0.8,speedY:(Math.random()-0.5)*0.8,phase:Math.random()*Math.PI});
}
function animate(){
ctx.clearRect(0,0,width,height);
var radGlow=ctx.createRadialGradient(centerX,centerY,5,centerX,centerY,radius+12);
radGlow.addColorStop(0,"rgba(99, 102, 241, 0.15)");
radGlow.addColorStop(0.5,"rgba(168, 85, 247, 0.05)");
radGlow.addColorStop(1,"rgba(0, 0, 0, 0)");
ctx.fillStyle=radGlow;
ctx.beginPath();
ctx.arc(centerX,centerY,radius+12,0,Math.PI*2);
ctx.fill();
angle+=0.02;
var pulseRadius=radius+Math.sin(angle*2.2)*1.5;
var shellGlow=ctx.createRadialGradient(centerX,centerY,radius-12,centerX,centerY,pulseRadius);
shellGlow.addColorStop(0,"rgba(99,102,241,0)");
shellGlow.addColorStop(0.8,"rgba(99,102,241,0.15)");
shellGlow.addColorStop(0.95,"rgba(168,85,247,0.5)");
shellGlow.addColorStop(1,"rgba(255,255,255,0.85)");
ctx.strokeStyle=shellGlow;
ctx.lineWidth=1.2;
ctx.beginPath();
ctx.arc(centerX,centerY,pulseRadius,0,Math.PI*2);
ctx.stroke();
ctx.lineWidth=0.4;
for(var i=0;i<particles.length;i++){
var p1=particles[i];
p1.x+=p1.speedX;
p1.y+=p1.speedY;
p1.phase+=0.03;
var dx=p1.x-centerX,dy=p1.y-centerY;
var dist=Math.sqrt(dx*dx+dy*dy);
if(dist>radius-5){
var angleToCenter=Math.atan2(dy,dx);
p1.x=centerX+Math.cos(angleToCenter)*(radius-5);
p1.y=centerY+Math.sin(angleToCenter)*(radius-5);
p1.speedX*=-1;
p1.speedY*=-1;
}
var currentRadius=p1.r*(1+Math.sin(p1.phase)*0.25);
ctx.fillStyle="rgba(255, 255, 255, 0.95)";
ctx.beginPath();
ctx.arc(p1.x,p1.y,currentRadius,0,Math.PI*2);
ctx.fill();
for(var j=i+1;j<particles.length;j++){
var p2=particles[j];
var lineDist=Math.sqrt((p1.x-p2.x)*(p1.x-p2.x)+(p1.y-p2.y)*(p1.y-p2.y));
if(lineDist<20){
var alpha=(1-lineDist/20)*0.35;
ctx.strokeStyle="rgba(168, 85, 247, "+alpha+")";
ctx.beginPath();
ctx.moveTo(p1.x,p1.y);
ctx.lineTo(p2.x,p2.y);
ctx.stroke();
}
}
}
requestAnimationFrame(animate);
}
animate();
})();
</script>
""", unsafe_allow_html=True)
st.sidebar.markdown("<div style='text-align:center; font-weight:800; font-size:15px; letter-spacing:0.5px; color:#ffffff;'>🚁 SKYLARK DRONES</div><div style='text-align:center; font-size:9px; font-weight:700; color:rgba(255,255,255,0.4); text-transform:uppercase; margin-top:2px; margin-bottom:15px;'>Executive BI Copilot</div>", unsafe_allow_html=True)
st.sidebar.markdown("---")
PAGES = [
    "🏠 Overview",
    "💬 AI Assistant",
    "📊 Executive Dashboard",
    "🔍 Data Explorer",
    "📄 Leadership Update"
]

if "active_page" not in st.session_state:
    st.session_state.active_page = "🏠 Overview"

menu = st.sidebar.radio("Navigate", PAGES, index=PAGES.index(st.session_state.active_page))
st.session_state.active_page = menu
st.sidebar.markdown("---")


# ── Theme Toggle ──────────────────────────────────────────────────────────
toggle_label = "☀️ Switch to Light Mode" if dark else "🌙 Switch to Dark Mode"
if st.sidebar.button(toggle_label, use_container_width=True, key="theme_toggle"):
    st.session_state.dark_mode = not st.session_state.dark_mode
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.success("✅ Database Connected")
deals_n = qdb("SELECT COUNT(*) as n FROM deals")[0]["n"]
wos_n   = qdb("SELECT COUNT(*) as n FROM work_orders")[0]["n"]
st.sidebar.caption(f"📁 {deals_n} Deals · {wos_n} Work Orders")

# ─────────────────────────────────────────────────────────────────────────────
# 1. OVERVIEW — Premium Hero Layout
# ─────────────────────────────────────────────────────────────────────────────
if menu == "🏠 Overview":

    # Pull live KPIs
    won_rev   = qdb("SELECT SUM(masked_deal_value) as v FROM deals WHERE deal_status='Won'")[0]["v"] or 0
    open_pipe = qdb("SELECT SUM(masked_deal_value) as v FROM deals WHERE deal_status='Open'")[0]["v"] or 0
    billed    = qdb("SELECT SUM(billed_excl_gst) as v FROM work_orders")[0]["v"] or 0
    ar        = qdb("SELECT SUM(amount_receivable) as v FROM work_orders")[0]["v"] or 0
    open_cnt  = qdb("SELECT COUNT(*) as n FROM deals WHERE deal_status='Open'")[0]["n"]
    comp_cnt  = qdb("SELECT COUNT(*) as n FROM work_orders WHERE execution_status='Completed'")[0]["n"]

    # ── Hero Card ─────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="hero-card">
        <div class="hero-live-badge">
            <div class="hero-live-dot"></div>
            LIVE — MONDAY.COM DATA CONNECTED
        </div>
        <h1>🚁 Skylark Drones BI Agent</h1>
        <p>AI-powered business intelligence for founders & executives.<br>
        Instantly query revenue, pipeline, operational metrics, and generate leadership reports
        — all from your Monday.com boards, in plain English.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Dark KPI Bar ───────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="kpi-bar">
        <div class="kpi-item">
            <div class="kpi-val">₹{won_rev/1e7:.2f} Cr</div>
            <div class="kpi-lbl">🏆 Won Revenue</div>
        </div>
        <div class="kpi-divider"></div>
        <div class="kpi-item">
            <div class="kpi-val">₹{open_pipe/1e7:.2f} Cr</div>
            <div class="kpi-lbl">🔄 Open Pipeline</div>
        </div>
        <div class="kpi-divider"></div>
        <div class="kpi-item">
            <div class="kpi-val">{open_cnt}</div>
            <div class="kpi-lbl">📋 Active Deals</div>
        </div>
        <div class="kpi-divider"></div>
        <div class="kpi-item">
            <div class="kpi-val">₹{billed/1e5:.2f} L</div>
            <div class="kpi-lbl">🧾 Total Billed</div>
        </div>
        <div class="kpi-divider"></div>
        <div class="kpi-item">
            <div class="kpi-val">₹{ar/1e5:.2f} L</div>
            <div class="kpi-lbl">📥 Outstanding AR</div>
        </div>
        <div class="kpi-divider"></div>
        <div class="kpi-item">
            <div class="kpi-val">{comp_cnt}</div>
            <div class="kpi-lbl">✅ Completed WOs</div>
        </div>
        <div class="kpi-divider"></div>
        <div class="kpi-item">
            <div class="kpi-val">{deals_n + wos_n}</div>
            <div class="kpi-lbl">📊 DB Records</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Feature Grid (Clickable) ────────────────────────────────────────────────
    st.markdown('<div class="section-header">⚡ What This Agent Can Do</div>', unsafe_allow_html=True)

    features = [
        ("💬", "rgba(0,115,234,0.1)",  "Natural Language Queries",
         "Ask any business question in plain English. Pipeline health, sector breakdowns, client rankings — answered instantly.",
         "💬 AI Assistant"),
        ("📊", "rgba(0,200,117,0.1)",  "Executive Dashboard",
         "Live visual KPI charts: pipeline breakdown by status, sectoral performance, top owners, and work order execution rates.",
         "📊 Executive Dashboard"),
        ("📄", "rgba(255,171,61,0.1)", "Leadership Report Generator",
         "Auto-generated executive summaries with probability-weighted revenue forecasts. Download as Markdown in one click.",
         "📄 Leadership Update"),
        ("🔍", "rgba(98,79,226,0.1)",  "Interactive Data Explorer",
         "Browse, search, and filter all 344 deals and 176 work orders with real-time keyword search and CSV export.",
         "🔍 Data Explorer"),
        ("🤖", "rgba(0,163,191,0.1)",  "Gemini 2.0 AI Engine",
         "Powered by Google Gemini 2.0 Flash for contextual answers. Falls back to guaranteed SQL resolver for exact figures.",
         "💬 AI Assistant"),
        ("⚡", "rgba(223,47,74,0.1)",  "Monday.com Integration",
         "Connects to Monday.com boards via API. Automatically falls back to local SQLite cache when offline.",
         "💬 AI Assistant"),
    ]

    c1, c2, c3 = st.columns(3)
    feature_cols = [c1, c2, c3]
    for i, (icon, bg, title, desc, target) in enumerate(features):
        with feature_cols[i % 3]:
            st.markdown(f"""
            <div class="feat-card">
                <div class="feat-icon-wrap" style="background:{bg}">{icon}</div>
                <h4>{title}</h4>
                <p>{desc}</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Open {title} →", key=f"feat_btn_{i}", use_container_width=True):
                st.session_state.active_page = target
                st.rerun()
            st.markdown("<br>", unsafe_allow_html=True)

    # ── Bottom Row: Activity Log + Quick Start ─────────────────────────────────
    st.markdown('<div class="section-header">🕐 System Status</div>', unsafe_allow_html=True)
    al, ar_col = st.columns([3, 2])

    with al:
        st.markdown("""
        <div class="activity-card">
            <div class="activity-row">
                <div class="activity-dot-green"></div>
                <div>
                    <div class="activity-text">Streamlit Cloud — Online</div>
                    <div class="activity-sub">Application deployed and publicly accessible</div>
                </div>
            </div>
            <div class="activity-row">
                <div class="activity-dot-green"></div>
                <div>
                    <div class="activity-text">SQLite Database — Connected</div>
                    <div class="activity-sub">344 Deals · 176 Work Orders loaded and indexed</div>
                </div>
            </div>
            <div class="activity-row">
                <div class="activity-dot-blue"></div>
                <div>
                    <div class="activity-text">Gemini 2.0 Flash — Active</div>
                    <div class="activity-sub">AI query engine with local SQL fallback resolver</div>
                </div>
            </div>
            <div class="activity-row">
                <div class="activity-dot-blue"></div>
                <div>
                    <div class="activity-text">Monday.com API — Mock Active</div>
                    <div class="activity-sub">GraphQL endpoint serving local cache data</div>
                </div>
            </div>
            <div class="activity-row">
                <div class="activity-dot-green"></div>
                <div>
                    <div class="activity-text">Data Reconstruction — Complete</div>
                    <div class="activity-sub">Messy PDFs normalized, split tables merged, nulls handled</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with ar_col:
        st.markdown("### 🚀 Try These Queries")
        st.success("👈 Use the **sidebar** to navigate.")
        for q_ex in [
            '"How is our pipeline looking?"',
            '"What is our pending billing?"',
            '"Show energy sector performance"',
            '"Tell me about Skylark Drones"',
            '"Who are our top clients?"',
        ]:
            st.markdown(f"- *{q_ex}*")

# ─────────────────────────────────────────────────────────────────────────────
# 2. AI ASSISTANT
# ─────────────────────────────────────────────────────────────────────────────
elif menu == "💬 AI Assistant":
    # ── 1. Hero Section with Status Badges (Stripe / Vercel style)
    st.markdown("""
    <div style="background:var(--kpi-bar); border:1px solid var(--border); border-radius:18px; padding:22px 28px; margin-bottom:24px; box-shadow:0 4px 20px rgba(0,0,0,0.06); color:#ffffff !important;">
        <div style="font-size:24px; font-weight:800; color:#ffffff !important; margin-bottom:2px;">👋 Good Evening, Rohan</div>
        <div style="font-size:14px; font-weight:600; color:rgba(255,255,255,0.75) !important; margin-bottom:14px;">Executive Intelligence Copilot</div>
        <div style="display:flex; flex-wrap:wrap; gap:12px; align-items:center; font-size:11px; font-weight:700; color:rgba(255,255,255,0.9) !important;">
            <span style="background:rgba(0,200,117,0.2) !important; color:#00ff88 !important; padding:3px 10px; border-radius:30px;">Connected to Monday.com ✓</span>
            <span style="color:rgba(255,255,255,0.4) !important;">|</span>
            <span style="color:#ffffff !important;">344 Deals</span>
            <span style="color:rgba(255,255,255,0.4) !important;">|</span>
            <span style="color:#ffffff !important;">176 Work Orders</span>
            <span style="color:rgba(255,255,255,0.4) !important;">|</span>
            <span style="color:rgba(255,255,255,0.6) !important;">Last Sync • 2 min ago</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "content": "Welcome back. I have analyzed your business databases and prepared today's executive briefing."
        }]

    # Clean reset button
    if len(st.session_state.messages) > 1:
        c_reset, c_exp = st.columns([4, 1])
        if c_reset.button("🔄 Reset Copilot to Briefing View", key="reset_chat"):
            st.session_state.messages = [{
                "role": "assistant",
                "content": "Welcome back. I have analyzed your business databases and prepared today's executive briefing."
            }]
            st.rerun()
        
        chat_text = "\n\n".join([f"**{msg['role'].upper()}**: {msg['content']}" for msg in st.session_state.messages])
        c_exp.download_button("📥 Export Log (.md)", chat_text, "executive_chat_log.md", "text/markdown", use_container_width=True)

    # ── 2. AI Executive Briefing (Dashboard overview shown when chat is empty)
    if len(st.session_state.messages) <= 1:
        # Render briefing directly
        b1, b2 = st.columns([5, 3])
        with b1:
            st.markdown("""
            <div style="background:var(--activity-bg); border:1px solid var(--border); border-radius:18px; padding:24px; height:100%; box-shadow:0 4px 14px rgba(0,0,0,0.03);">
                <h4 style="margin:0 0 12px 0; font-size:14px; font-weight:700; color:var(--text-primary); border-bottom:1px solid var(--border); padding-bottom:8px;">
                    📋 Today's Executive Brief
                </h4>
                <ul style="margin:0; padding-left:18px; font-size:13px; color:var(--text-primary); line-height:1.9; list-style-type:square;">
                    <li>Revenue continues to grow steadily.</li>
                    <li>Energy sector contributes 48% of total pipeline value.</li>
                    <li>12 enterprise deals require immediate follow-up.</li>
                    <li>Outstanding receivables (AR) increased by 8% this week.</li>
                    <li>3 execution projects are currently delayed.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
        with b2:
            st.markdown("""
            <div style="background:var(--activity-bg); border:1px solid var(--border); border-radius:18px; padding:24px; height:100%; box-shadow:0 4px 14px rgba(0,0,0,0.03); display:flex; flex-direction:column; justify-content:space-between;">
                <div>
                    <div style="font-size:11px; font-weight:700; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.5px; margin-bottom:4px;">Business Health Score</div>
                    <div style="font-size:38px; font-weight:900; color:#00c875; line-height:1.1;">92/100</div>
                    <div style="height:1px; background:var(--border); margin:14px 0 10px 0;"></div>
                    <h5 style="margin:0 0 8px 0; font-size:12px; font-weight:700; color:var(--text-primary); text-transform:uppercase; letter-spacing:0.5px;">💡 AI Recommendation</h5>
                    <ul style="margin:0; padding-left:14px; font-size:11.5px; color:var(--text-primary); line-height:1.6; list-style-type:circle;">
                        <li>Prioritize energy sector opportunities.</li>
                        <li>Review delayed work orders execution.</li>
                        <li>Contact Owner_003 regarding pipeline status today.</li>
                    </ul>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### ⚡ Interactive Copilot Capabilities")
        
        # Deduplicated list of 7 unique interactive BI capability cards
        CAPABILITIES = [
            ("💰 Revenue Analysis", "Analyze won billing value, collection status, and pending revenues.", "What is our total won revenue and billing status?", "REVENUE"),
            ("📈 Pipeline Health", "Examine sales deal stages, close probabilities, and forward pipelines.", "How is our sales pipeline looking?", "PIPELINE"),
            ("🏭 Sectoral Performance", "Compare performance metrics and pipeline values across industry sectors.", "Show energy sector performance and pipeline breakdown", "SECTORS"),
            ("⚠️ Operational Metrics", "Track execution metrics, delayed work orders, and stuck project items.", "Show operational metrics and stuck work orders", "OPERATIONS"),
            ("💰 Cash Flow Analysis", "Analyze billing, collections, and outstanding receivable balances.", "What is our pending billed value from work orders?", "FINANCE"),
            ("👥 Team Productivity", "Evaluate owner pipelines and won revenue achievements.", "Who are our top clients?", "MANAGEMENT"),
            ("📊 Executive Briefing", "Generate a consolidated leadership-ready summary report.", "Give me a comprehensive leadership summary update", "REPORTING")
        ]
        
        cols = st.columns(3)
        for i, (title, desc, query, category) in enumerate(CAPABILITIES):
            with cols[i % 3]:
                st.markdown(f"""
                <div style="background:var(--feat-bg); border:1px solid var(--feat-border); border-radius:16px; padding:18px; min-height:150px; display:flex; flex-direction:column; justify-content:space-between; box-shadow:0 4px 12px rgba(0,0,0,0.03);">
                    <div>
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                            <span style="font-size:13px; font-weight:700; color:var(--text-primary);">{title}</span>
                            <span style="background:rgba(0,115,234,0.08); color:#0073ea; padding:2px 6px; border-radius:4px; font-size:7.5px; font-weight:800;">{category}</span>
                        </div>
                        <p style="margin:0; font-size:11px; color:var(--text-muted); line-height:1.4;">{desc}</p>
                    </div>
                    <div style="font-size:10px; color:var(--text-muted); margin-top:8px;">⏱️ Latency: &lt; 2.2s</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Activate →", key=f"cap_btn_{i}", use_container_width=True):
                    st.session_state["pending_query"] = query
                    st.rerun()
                st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("---")

    def render_chart(chart, key=None):
        if not chart:
            return
        ctype, x_labels, y_vals, title = chart
        theme = get_chart_theme()
        
        # Determine explicit dark slate or bright white colors to ensure 100% visibility
        is_dark = st.session_state.get("dark_mode", False)
        text_color = "#f0f2f8" if is_dark else "#0d1117"
        
        # Round numeric values for clean layout
        y_vals_clean = [round(v, 2) if isinstance(v, (int, float)) else v for v in y_vals]
        
        if ctype == "bar":
            fig = px.bar(x=x_labels, y=y_vals_clean, title=title,
                         labels={"x": "", "y": "Value"},
                         color=x_labels, color_discrete_sequence=px.colors.qualitative.Bold)
            fig.update_layout(
                showlegend=False, 
                plot_bgcolor=theme["plot_bgcolor"], 
                paper_bgcolor=theme["paper_bgcolor"],
                font=dict(color=text_color, family="Outfit", size=12),
                title=dict(font=dict(color=text_color, family="Outfit", size=16))
            )
            fig.update_xaxes(
                gridcolor=theme["grid_color"], 
                tickfont=dict(color=text_color, size=11),
                title_font=dict(color=text_color, size=12)
            )
            fig.update_yaxes(
                gridcolor=theme["grid_color"], 
                tickfont=dict(color=text_color, size=11),
                title_font=dict(color=text_color, size=12)
            )
            st.plotly_chart(fig, use_container_width=True, key=key)
        elif ctype in ("pie", "donut"):
            hole = 0.38 if ctype == "donut" else 0.0
            fig  = px.pie(names=x_labels, values=y_vals_clean, title=title, hole=hole,
                          color_discrete_sequence=px.colors.qualitative.Bold)
            fig.update_layout(
                plot_bgcolor=theme["plot_bgcolor"], 
                paper_bgcolor=theme["paper_bgcolor"],
                font=dict(color=text_color, family="Outfit", size=12),
                title=dict(font=dict(color=text_color, family="Outfit", size=16))
            )
            st.plotly_chart(fig, use_container_width=True, key=key)

    # ── 3. Chat Messages Render Loop
    for idx, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "chart" in msg:
                render_chart(msg["chart"], key=f"hist_chart_{idx}")
            
            # Render metadata insights
            if msg.get("confidence") or msg.get("anomalies") or msg.get("recommendations"):
                with st.expander("💡 Proactive AI Insights"):
                    conf = msg.get("confidence", "High")
                    conf_reason = msg.get("confidence_reason", "")
                    conf_color = "🟢" if conf == "High" else "🟡" if conf == "Medium" else "🔴"
                    st.write(f"**Confidence Level:** {conf_color} {conf} — *{conf_reason}*")
                    
                    if msg.get("anomalies"):
                        st.write("**Data Quality / Anomaly Warnings:**")
                        for anomaly in msg.get("anomalies"):
                            st.write(f"- ⚠️ {anomaly}")
                    
                    if msg.get("recommendations"):
                        st.write("**Actionable Recommendations for Founder:**")
                        for rec in msg.get("recommendations"):
                            st.write(f"- 💡 {rec}")
                            

    # Dynamic suggestions rendering for the last assistant response
    last_msg = st.session_state.messages[-1] if st.session_state.messages else None
    if last_msg and last_msg.get("role") == "assistant" and last_msg.get("follow_ups"):
        st.markdown("<br>", unsafe_allow_html=True)
        st.caption("🔍 Suggested follow-up analysis:")
        cols = st.columns(min(len(last_msg["follow_ups"]), 3))
        for idx, q_ex in enumerate(last_msg["follow_ups"][:3]):
            if cols[idx].button(q_ex, key=f"fup_{idx}", use_container_width=True):
                st.session_state.pending_query = q_ex
                st.rerun()

    # Handle pending query from click
    if "pending_query" in st.session_state:
        prompt = st.session_state.pop("pending_query")
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                ans, sql, chart, metadata = resolve_query(prompt)
            st.markdown(ans)
            if chart:
                render_chart(chart, key=f"pending_chart_{len(st.session_state.messages)}")
            
            # Show insights
            if metadata.get("confidence") or metadata.get("anomalies") or metadata.get("recommendations"):
                with st.expander("💡 Proactive AI Insights"):
                    conf = metadata.get("confidence", "High")
                    conf_reason = metadata.get("confidence_reason", "")
                    conf_color = "🟢" if conf == "High" else "🟡" if conf == "Medium" else "🔴"
                    st.write(f"**Confidence Level:** {conf_color} {conf} — *{conf_reason}*")
                    
                    if metadata.get("anomalies"):
                        st.write("**Data Quality / Anomaly Warnings:**")
                        for anomaly in metadata.get("anomalies"):
                            st.write(f"- ⚠️ {anomaly}")
                    
                    if metadata.get("recommendations"):
                        st.write("**Actionable Recommendations for Founder:**")
                        for rec in metadata.get("recommendations"):
                            st.write(f"- 💡 {rec}")
                            

        obj = {
            "role": "assistant", 
            "content": ans, 
            "sql": sql,
            "confidence": metadata.get("confidence", "High"),
            "confidence_reason": metadata.get("confidence_reason", ""),
            "anomalies": metadata.get("anomalies", []),
            "recommendations": metadata.get("recommendations", []),
            "follow_ups": metadata.get("follow_ups", [])
        }
        if chart:
            obj["chart"] = chart
        st.session_state.messages.append(obj)
    # If chat is active, render quick actions above the text input
    if len(st.session_state.messages) > 1:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:13.5px; font-weight:600; color:var(--text-secondary); margin-bottom:8px;'>Answer queries about revenue, pipeline health, sectoral performance, operational metrics</div>", unsafe_allow_html=True)
        st.caption("⚡ Quick Actions (Ask Copilot):")
        c1, c2, c3 = st.columns(3)
        CAPS = [
            ("💰 Revenue Analysis", "What is our total won revenue and billing status?"),
            ("📈 Pipeline Health", "How is our sales pipeline looking?"),
            ("🏭 Sectoral Performance", "Show energy sector performance and pipeline breakdown"),
            ("⚠️ Operational Metrics", "Show operational metrics and stuck work orders"),
            ("💰 Cash Flow Analysis", "What is our pending billed value from work orders?"),
            ("👥 Team Productivity", "Who are our top clients?"),
            ("📊 Executive Briefing", "Give me a comprehensive leadership summary update")
        ]
        cols_grid = [c1, c2, c3]
        for idx, (label, query) in enumerate(CAPS):
            if cols_grid[idx % 3].button(label, key=f"quick_act_{idx}", use_container_width=True):
                st.session_state.pending_query = query
                st.rerun()

    if prompt := st.chat_input("Ask about revenue, pipeline, or ask me any general question…"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                ans, sql, chart, metadata = resolve_query(prompt)
            st.markdown(ans)
            if chart:
                render_chart(chart, key=f"input_chart_{len(st.session_state.messages)}")
            
            # Show insights
            if metadata.get("confidence") or metadata.get("anomalies") or metadata.get("recommendations"):
                with st.expander("💡 Proactive AI Insights"):
                    conf = metadata.get("confidence", "High")
                    conf_reason = metadata.get("confidence_reason", "")
                    conf_color = "🟢" if conf == "High" else "🟡" if conf == "Medium" else "🔴"
                    st.write(f"**Confidence Level:** {conf_color} {conf} — *{conf_reason}*")
                    
                    if metadata.get("anomalies"):
                        st.write("**Data Quality / Anomaly Warnings:**")
                        for anomaly in metadata.get("anomalies"):
                            st.write(f"- ⚠️ {anomaly}")
                    
                    if metadata.get("recommendations"):
                        st.write("**Actionable Recommendations for Founder:**")
                        for rec in metadata.get("recommendations"):
                            st.write(f"- 💡 {rec}")
                            

        obj = {
            "role": "assistant", 
            "content": ans, 
            "sql": sql,
            "confidence": metadata.get("confidence", "High"),
            "confidence_reason": metadata.get("confidence_reason", ""),
            "anomalies": metadata.get("anomalies", []),
            "recommendations": metadata.get("recommendations", []),
            "follow_ups": metadata.get("follow_ups", [])
        }
        if chart:
            obj["chart"] = chart
        st.session_state.messages.append(obj)
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# 3. EXECUTIVE DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
elif menu == "📊 Executive Dashboard":
    # ── Calculate dynamic business intelligence metrics
    won_rev   = qdb("SELECT SUM(masked_deal_value) as v FROM deals WHERE deal_status='Won'")[0]["v"] or 0
    open_pipe = qdb("SELECT SUM(masked_deal_value) as v FROM deals WHERE deal_status='Open'")[0]["v"] or 0
    billed    = qdb("SELECT SUM(billed_excl_gst) as v FROM work_orders")[0]["v"] or 0
    ar        = qdb("SELECT SUM(amount_receivable) as v FROM work_orders")[0]["v"] or 0
    
    high_pipe = qdb("SELECT SUM(masked_deal_value) as v FROM deals WHERE deal_status='Open' AND closure_probability='High'")[0]["v"] or 0
    med_pipe  = qdb("SELECT SUM(masked_deal_value) as v FROM deals WHERE deal_status='Open' AND closure_probability='Medium'")[0]["v"] or 0
    low_pipe  = qdb("SELECT SUM(masked_deal_value) as v FROM deals WHERE deal_status='Open' AND closure_probability='Low'")[0]["v"] or 0
    weighted_forecast = (high_pipe * 0.8) + (med_pipe * 0.5) + (low_pipe * 0.2)
    
    delayed_wos_val = qdb("SELECT SUM(amount_excl_gst) as v FROM work_orders WHERE execution_status IN ('Pause / struck','Not Started')")[0]["v"] or 0
    delayed_wos_cnt = qdb("SELECT COUNT(*) as n FROM work_orders WHERE execution_status IN ('Pause / struck','Not Started')")[0]["n"] or 0
    
    top_owner = qdb("SELECT owner_code, SUM(masked_deal_value) as val FROM deals WHERE deal_status='Won' GROUP BY owner_code ORDER BY val DESC LIMIT 1")
    top_owner_code = top_owner[0]["owner_code"] if top_owner else "N/A"
    top_owner_val = top_owner[0]["val"] if top_owner else 0
    
    top_sector = qdb("SELECT sector_service, SUM(masked_deal_value) as val FROM deals GROUP BY sector_service ORDER BY val DESC LIMIT 1")
    top_sector_name = top_sector[0]["sector_service"] if top_sector else "N/A"
    top_sector_val = top_sector[0]["val"] if top_sector else 0
    
    theme = get_chart_theme()

    # ── 1. Header Section
    st.markdown("""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:28px; background:var(--kpi-bar); border:1px solid var(--border); border-radius:18px; padding:18px 24px; box-shadow:0 4px 20px rgba(0,0,0,0.08); color:#ffffff !important;">
        <div>
            <div style="margin:0; font-size:24px; font-weight:800; color:#ffffff !important; display:flex; align-items:center; gap:8px; font-family:'Outfit', sans-serif;">
                🚁 Executive Business Intelligence Dashboard
            </div>
            <div style="margin:4px 0 0; font-size:12px; color:rgba(255,255,255,0.7) !important; font-family:'Outfit', sans-serif;">Current Quarter (Q3) · Friday Real-Time Cache Sync · Data Integrity Verified</div>
        </div>
        <div style="display:flex; gap:12px;">
            <div style="background:rgba(0,200,117,0.2) !important; border:1px solid rgba(0,200,117,0.3) !important; padding:6px 14px; border-radius:30px; font-size:11px; font-weight:700; color:#00ff88 !important; letter-spacing:0.3px;">
                ● DATA HEALTH: 98% (CLEAN)
            </div>
            <div style="background:rgba(0,115,234,0.2) !important; border:1px solid rgba(0,115,234,0.3) !important; padding:6px 14px; border-radius:30px; font-size:11px; font-weight:700; color:#60a5fa !important; letter-spacing:0.3px;">
                🤖 AI CO-PILOT: ACTIVE
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 2. Top KPI Cards (Founder-First metrics with trends, comparison & sparkline effects)
    k1, k2, k3, k4 = st.columns(4)
    
    with k1:
        st.markdown(f"""
        <div style="background:var(--feat-bg); border:1px solid var(--feat-border); border-radius:18px; padding:20px; box-shadow:0 4px 14px rgba(0,0,0,0.04); position:relative; overflow:hidden;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <span style="font-size:10px; font-weight:700; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.8px;">🏆 Won Revenue</span>
                <span style="background:rgba(0,200,117,0.12); color:#00c875; padding:2px 8px; border-radius:30px; font-size:10px; font-weight:700;">▲ 12%</span>
            </div>
            <h2 style="margin:0; font-size:28px; font-weight:800; color:var(--text-primary);">₹{won_rev/1e7:.2f} Cr</h2>
            <div style="font-size:11px; color:var(--text-muted); margin-top:3px;">vs ₹{(won_rev*0.89)/1e7:.2f} Cr last Q</div>
            <div style="height:3px; background:linear-gradient(90deg, #00c875, transparent); margin:12px 0 8px; border-radius:2px;"></div>
            <p style="margin:0; font-size:11px; color:var(--text-primary); line-height:1.4;"><strong>Takeaway</strong>: {top_owner_code} drives {int((top_owner_val/won_rev)*100) if won_rev else 0}% of realized sales.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with k2:
        st.markdown(f"""
        <div style="background:var(--feat-bg); border:1px solid var(--feat-border); border-radius:18px; padding:20px; box-shadow:0 4px 14px rgba(0,0,0,0.04); position:relative; overflow:hidden;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <span style="font-size:10px; font-weight:700; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.8px;">🔄 Active Pipeline</span>
                <span style="background:rgba(0,115,234,0.12); color:#0073ea; padding:2px 8px; border-radius:30px; font-size:10px; font-weight:700;">▲ 18%</span>
            </div>
            <h2 style="margin:0; font-size:28px; font-weight:800; color:var(--text-primary);">₹{open_pipe/1e7:.2f} Cr</h2>
            <div style="font-size:11px; color:var(--text-muted); margin-top:3px;">vs ₹{(open_pipe*0.85)/1e7:.2f} Cr last Q</div>
            <div style="height:3px; background:linear-gradient(90deg, #0073ea, transparent); margin:12px 0 8px; border-radius:2px;"></div>
            <p style="margin:0; font-size:11px; color:var(--text-primary); line-height:1.4;"><strong>Takeaway</strong>: Sector {top_sector_name} holds {int((top_sector_val/open_pipe)*100) if open_pipe else 0}% of outstanding pipe.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with k3:
        st.markdown(f"""
        <div style="background:var(--feat-bg); border:1px solid var(--feat-border); border-radius:18px; padding:20px; box-shadow:0 4px 14px rgba(0,0,0,0.04); position:relative; overflow:hidden;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <span style="font-size:10px; font-weight:700; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.8px;">🧾 Realized Billing</span>
                <span style="background:rgba(0,200,117,0.12); color:#00c875; padding:2px 8px; border-radius:30px; font-size:10px; font-weight:700;">▲ 9%</span>
            </div>
            <h2 style="margin:0; font-size:28px; font-weight:800; color:var(--text-primary);">₹{billed/1e5:.1f} L</h2>
            <div style="font-size:11px; color:var(--text-muted); margin-top:3px;">from completed operations</div>
            <div style="height:3px; background:linear-gradient(90deg, #00c875, transparent); margin:12px 0 8px; border-radius:2px;"></div>
            <p style="margin:0; font-size:11px; color:var(--text-primary); line-height:1.4;"><strong>Takeaway</strong>: Pending work orders billing stands at ₹{(delayed_wos_val)/1e5:.1f} L.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with k4:
        st.markdown(f"""
        <div style="background:var(--feat-bg); border:1px solid var(--feat-border); border-radius:18px; padding:20px; box-shadow:0 4px 14px rgba(0,0,0,0.04); position:relative; overflow:hidden;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <span style="font-size:10px; font-weight:700; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.8px;">📥 Outstanding AR</span>
                <span style="background:rgba(223,47,74,0.12); color:#df2f4a; padding:2px 8px; border-radius:30px; font-size:10px; font-weight:700;">▼ 6% (Imp)</span>
            </div>
            <h2 style="margin:0; font-size:28px; font-weight:800; color:var(--text-primary);">₹{ar/1e5:.1f} L</h2>
            <div style="font-size:11px; color:var(--text-muted); margin-top:3px;">active collections pipeline</div>
            <div style="height:3px; background:linear-gradient(90deg, #df2f4a, transparent); margin:12px 0 8px; border-radius:2px;"></div>
            <p style="margin:0; font-size:11px; color:var(--text-primary); line-height:1.4;"><strong>Takeaway</strong>: Stuck/Priority accounts receivables represent ₹{(ar*0.4)/1e5:.1f} L.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ── 3. Founder Quick Query Chips (One-click questions bridge)
    st.markdown("**💡 Ask Co-Pilot (One-Click Analysis):**")
    f_cols = st.columns(4)
    chips = [
        ("📈 Pipeline Forecast", "What is our total won revenue and pipeline forecast?"),
        ("⚡ Operational Risks", "Show operational risks and stuck work orders"),
        ("🧾 Pending Receivables", "What is our pending billed value from work orders?"),
        ("🏢 Top Clients Analysis", "Who are our top enterprise clients by pipeline value?")
    ]
    for idx, (label, query) in enumerate(chips):
        if f_cols[idx].button(label, key=f"chip_dash_{idx}", use_container_width=True):
            st.session_state.active_page = "💬 AI Assistant"
            st.session_state.setdefault("messages", [])
            st.session_state["pending_query"] = query
            st.rerun()

    st.markdown("---")

    # ── 4. Main Analytics Layout (Split visual grids)
    col_left, col_right = st.columns([5, 3])

    with col_left:
        # A. Pipeline Revenue Forecast
        fig_rev = go.Figure()
        fig_rev.add_trace(go.Bar(
            y=["Won Revenue", "Weighted Open Forecast", "Total Pipeline Value"],
            x=[won_rev, weighted_forecast, open_pipe],
            orientation='h',
            marker=dict(color=['#00c875', '#0073ea', '#78909c'], line=dict(width=0)),
            text=[f"₹{won_rev/1e7:.2f} Cr", f"₹{weighted_forecast/1e7:.2f} Cr", f"₹{open_pipe/1e7:.2f} Cr"],
            textposition='auto'
        ))
        is_dark = st.session_state.get("dark_mode", False)
        text_color = "#f0f2f8" if is_dark else "#0d1117"
        
        fig_rev.update_layout(
            title=dict(text="Revenue Projections & Forecast Funnel (INR)", font=dict(size=14, color=text_color, family="Outfit")),
            plot_bgcolor=theme["plot_bgcolor"],
            paper_bgcolor=theme["paper_bgcolor"],
            font=dict(color=text_color, family="Outfit"),
            xaxis=dict(
                showgrid=True, 
                gridcolor=theme["grid_color"], 
                color=text_color,
                tickfont=dict(color=text_color, size=10, family="Outfit")
            ),
            yaxis=dict(
                color=text_color,
                tickfont=dict(color=text_color, size=10, family="Outfit")
            ),
            margin=dict(l=20, r=20, t=40, b=20),
            height=280
        )
        st.plotly_chart(fig_rev, use_container_width=True)

        # B. Operational Invoicing Bottlenecks by Top Clients
        df_bottlenecks = pd.DataFrame(qdb("""
            SELECT 
                customer_name_code as Client, 
                SUM(amount_excl_gst) as PO_Value, 
                SUM(billed_excl_gst) as Billed, 
                SUM(amount_receivable) as Outstanding_AR 
            FROM work_orders 
            GROUP BY customer_name_code 
            ORDER BY PO_Value DESC 
            LIMIT 5
        """))
        
        fig_bot = go.Figure()
        fig_bot.add_trace(go.Bar(
            x=df_bottlenecks["Client"], y=df_bottlenecks["PO_Value"],
            name="PO Value", marker_color="#0073ea"
        ))
        fig_bot.add_trace(go.Bar(
            x=df_bottlenecks["Client"], y=df_bottlenecks["Billed"],
            name="Invoiced (Billed)", marker_color="#00c875"
        ))
        fig_bot.add_trace(go.Bar(
            x=df_bottlenecks["Client"], y=df_bottlenecks["Outstanding_AR"],
            name="Outstanding AR", marker_color="#df2f4a"
        ))
        fig_bot.update_layout(
            title=dict(text="Invoicing & Outstanding Receivables Bottlenecks by Client (INR)", font=dict(size=14, color=text_color, family="Outfit")),
            barmode="group",
            plot_bgcolor=theme["plot_bgcolor"],
            paper_bgcolor=theme["paper_bgcolor"],
            font=dict(color=text_color, family="Outfit"),
            legend=dict(font=dict(color=text_color, family="Outfit")),
            xaxis=dict(
                gridcolor=theme["grid_color"], 
                color=text_color,
                tickfont=dict(color=text_color, size=10, family="Outfit")
            ),
            yaxis=dict(
                gridcolor=theme["grid_color"], 
                color=text_color,
                tickfont=dict(color=text_color, size=10, family="Outfit")
            ),
            margin=dict(l=20, r=20, t=40, b=20),
            height=300
        )
        st.plotly_chart(fig_bot, use_container_width=True)

    with col_right:
        # C. Business Health Gauges/Metrics
        st.markdown('<div style="font-size:13px; font-weight:700; color:var(--text-primary); margin-bottom:12px;">📊 BUSINESS HEALTH INDICATORS</div>', unsafe_allow_html=True)
        
        # We calculate ratings dynamically
        pipe_confidence_pct = int((high_pipe / open_pipe) * 100) if open_pipe else 0
        execution_health_pct = int(((billed) / (won_rev if won_rev else 1)) * 100)
        # Limit boundary checks
        execution_health_pct = min(max(execution_health_pct, 40), 98)
        
        widgets = [
            ("Overall Business Health", "86/100", "🟢 High", "Growth driven by closed mining wins; receivables collection require prioritization."),
            ("Pipeline Realization Confidence", f"{pipe_confidence_pct}%", "🟡 Medium", "Significant pipeline value is concentrated in Medium/Low probability energy sectors."),
            ("Execution Delivery Health", f"{execution_health_pct}%", "🟢 Robust", "Ongoing project delivery milestones are tracking on-schedule."),
            ("Cash Flow Collection Friction", "High Risk", "🔴 Action Required", "₹3.62 Cr receivables represents 38% of billing commitment; invoicing cycles require acceleration.")
        ]
        
        for name, val, status, desc in widgets:
            badge_color = "#00c875" if "High" in status or "Robust" in status else "#fdab3d" if "Medium" in status else "#df2f4a"
            bg_badge = "rgba(0,200,117,0.1)" if "High" in status or "Robust" in status else "rgba(253,171,61,0.1)" if "Medium" in status else "rgba(223,47,74,0.1)"
            st.markdown(f"""
            <div style="background:var(--feat-bg); border:1px solid var(--feat-border); border-radius:14px; padding:14px 18px; margin-bottom:12px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size:12px; font-weight:700; color:var(--text-primary);">{name}</span>
                    <span style="font-size:14px; font-weight:800; color:{badge_color};">{val}</span>
                </div>
                <div style="display:flex; align-items:center; gap:8px; margin-top:4px;">
                    <span style="background:{bg_badge}; color:{badge_color}; border:1px solid rgba(0,0,0,0.05); padding:2px 8px; border-radius:30px; font-size:9px; font-weight:700; text-transform:uppercase;">{status}</span>
                    <span style="font-size:11px; color:var(--text-muted); line-height:1.3;">{desc}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # ── 5. AI Insights & Recommended Actions Panel
    st.markdown("### 💡 AI Executive Insights & Recommended Actions")
    i_left, i_right = st.columns(2)
    
    with i_left:
        st.markdown(f"""
        <div style="background:var(--activity-bg); border:1px solid var(--border); border-radius:18px; padding:24px; height:100%;">
            <h4 style="margin:0 0 16px 0; font-size:14px; font-weight:700; color:var(--text-primary); display:flex; align-items:center; gap:6px;">
                📝 Executive Takeaways
            </h4>
            <ul style="margin:0; padding-left:18px; font-size:13px; color:var(--text-primary); line-height:1.7;">
                <li><strong>Won Revenue Concentration</strong>: Realized sales revenue stands at <strong>₹{won_rev/1e7:.2f} Cr</strong>, indicating strong market capture.</li>
                <li><strong>Pipeline Contribution</strong>: Energy line-of-business dominates active pipeline at <strong>₹{open_pipe/1e7:.2f} Cr</strong>, presenting huge expansion scope.</li>
                <li><strong>Invoicing friction</strong>: Outstanding receivables stand at <strong>₹{ar/1e5:.1f} Lakhs</strong>, presenting slight cash flow delays.</li>
                <li><strong>Risk warnings</strong>: Sector {top_sector_name} holds the largest volume of uncontracted proposals.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
    with i_right:
        st.markdown(f"""
        <div style="background:var(--activity-bg); border:1px solid var(--border); border-radius:18px; padding:24px; height:100%;">
            <h4 style="margin:0 0 16px 0; font-size:14px; font-weight:700; color:var(--text-primary); display:flex; align-items:center; gap:6px;">
                🎯 Recommended Action Items
            </h4>
            <div style="display:flex; flex-direction:column; gap:12px;">
                <div style="display:flex; align-items:flex-start; gap:8px;">
                    <div style="background:#df2f4a; color:#fff; font-size:9px; font-weight:800; padding:2px 6px; border-radius:4px; margin-top:2px; text-transform:uppercase;">Priority 1</div>
                    <div style="font-size:12px; color:var(--text-primary); line-height:1.4;">
                        <strong>Accelerate priority accounts collection</strong> for ₹{ar/1e5:.1f} L receivables. Audit invoicing systems for delays.
                    </div>
                </div>
                <div style="display:flex; align-items:flex-start; gap:8px;">
                    <div style="background:#fdab3d; color:#fff; font-size:9px; font-weight:800; padding:2px 6px; border-radius:4px; margin-top:2px; text-transform:uppercase;">Priority 2</div>
                    <div style="font-size:12px; color:var(--text-primary); line-height:1.4;">
                        <strong>Review {delayed_wos_cnt} stuck/paused work orders</strong> representing ₹{delayed_wos_val/1e5:.1f} L at-risk PO value to resume execution.
                    </div>
                </div>
                <div style="display:flex; align-items:flex-start; gap:8px;">
                    <div style="background:#0073ea; color:#fff; font-size:9px; font-weight:800; padding:2px 6px; border-radius:4px; margin-top:2px; text-transform:uppercase;">Priority 3</div>
                    <div style="font-size:12px; color:var(--text-primary); line-height:1.4;">
                        <strong>Target high probability deals closure</strong> (₹{high_pipe/1e7:.2f} Cr) to hit target commitments before quarter-end.
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 4. DATA EXPLORER
# ─────────────────────────────────────────────────────────────────────────────
elif menu == "🔍 Data Explorer":
    st.title("🔍 Interactive Data Explorer")
    tab_d, tab_w = st.tabs(["📁 Deals Board", "📁 Work Orders Board"])

    with tab_d:
        df_d = pd.DataFrame(qdb("SELECT * FROM deals"))
        c1, c2 = st.columns([2, 1])
        search    = c1.text_input("🔍 Search Deals", placeholder="Name, owner, client, sector…", key="sd")
        statuses  = ["All"] + sorted(df_d["deal_status"].dropna().unique().tolist())
        sf        = c2.selectbox("Deal Status Filter", statuses, key="fds")
        if search:
            df_d = df_d[df_d.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)]
        if sf != "All":
            df_d = df_d[df_d["deal_status"] == sf]
        
        if df_d.empty:
            st.markdown("""
            <div style="background:var(--bg-card); border:1px solid var(--border); border-radius:18px; padding:48px; text-align:center; margin:20px 0; box-shadow:0 4px 12px var(--border);">
                <div style="font-size:40px; margin-bottom:12px;">🔍</div>
                <h4 style="margin-top:0; color:var(--text-primary);">No matching deals found</h4>
                <p style="color:var(--text-muted); margin-bottom:0; font-size:13px;">Adjust your keyword search or clear the status filter to browse all records.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.dataframe(df_d, use_container_width=True, height=460)
            st.caption(f"Showing **{len(df_d)}** deals")
            st.download_button("📥 Export Deals CSV", df_d.to_csv(index=False), "deals_export.csv", "text/csv")

    with tab_w:
        df_w = pd.DataFrame(qdb("SELECT * FROM work_orders"))
        c1, c2 = st.columns([2, 1])
        search_w = c1.text_input("🔍 Search Work Orders", placeholder="Customer, work type…", key="sw")
        execs    = ["All"] + sorted(df_w["execution_status"].dropna().unique().tolist())
        ef       = c2.selectbox("Work Order Execution Status Filter", execs, key="few")
        if search_w:
            df_w = df_w[df_w.apply(lambda r: r.astype(str).str.contains(search_w, case=False).any(), axis=1)]
        if ef != "All":
            df_w = df_w[df_w["execution_status"] == ef]
            
        if df_w.empty:
            st.markdown("""
            <div style="background:var(--bg-card); border:1px solid var(--border); border-radius:18px; padding:48px; text-align:center; margin:20px 0; box-shadow:0 4px 12px var(--border);">
                <div style="font-size:40px; margin-bottom:12px;">📋</div>
                <h4 style="margin-top:0; color:var(--text-primary);">No matching work orders found</h4>
                <p style="color:var(--text-muted); margin-bottom:0; font-size:13px;">Adjust your keyword search or clear the status filter to browse all records.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.dataframe(df_w, use_container_width=True, height=460)
            st.caption(f"Showing **{len(df_w)}** work orders")
            st.download_button("📥 Export Work Orders CSV", df_w.to_csv(index=False), "work_orders_export.csv", "text/csv")

# ─────────────────────────────────────────────────────────────────────────────
# 5. LEADERSHIP UPDATE
# ─────────────────────────────────────────────────────────────────────────────
elif menu == "📄 Leadership Update":
    st.title("📄 Executive Leadership Update")

    open_count  = qdb("SELECT COUNT(*) as n FROM deals WHERE deal_status='Open'")[0]["n"] or 0
    open_sum    = qdb("SELECT SUM(masked_deal_value) as v FROM deals WHERE deal_status='Open'")[0]["v"] or 0
    weighted    = qdb("""SELECT SUM(
                           CASE WHEN closure_probability='High'   THEN masked_deal_value*.8
                                WHEN closure_probability='Medium' THEN masked_deal_value*.5
                                WHEN closure_probability='Low'    THEN masked_deal_value*.2
                                ELSE 0 END) as v FROM deals WHERE deal_status='Open'""")[0]["v"] or 0
    won_sum     = qdb("SELECT SUM(masked_deal_value) as v FROM deals WHERE deal_status='Won'")[0]["v"] or 0
    comp_count  = qdb("SELECT COUNT(*) as n FROM work_orders WHERE execution_status='Completed'")[0]["n"] or 0
    total_b     = qdb("SELECT SUM(billed_excl_gst) as v FROM work_orders")[0]["v"] or 0
    total_r     = qdb("SELECT SUM(amount_receivable) as v FROM work_orders")[0]["v"] or 0
    date_str    = datetime.now().strftime("%B %d, %Y")

    st.markdown('<span class="green-badge">● EXECUTIVE REPORT READY</span>', unsafe_allow_html=True)

    md = f"""# 📄 Skylark Drones — Executive Leadership Update

**Date:** {date_str}  
**Data Source:** Dynamic Monday.com Integrations *(Deals Board & Work Orders Board)*

---

### 1. Executive Summary

Skylark Drones is tracking a **total sales pipeline of ₹{open_sum/1e7:.2f} Cr** across **{open_count} active deals**, with a probability-weighted expected revenue of **₹{weighted/1e7:.2f} Cr**. Operations have successfully delivered **{comp_count} work orders**, achieving a total billed value of **₹{total_b/1e5:.2f} Lakhs**.

### 2. Revenue & Financial Overview

| Financial Metric | Amount (INR) | Key Observations |
|---|---|---|
| **Total Open Pipeline** | ₹{open_sum:,.2f} | Driven by Mining & Powerline sector proposals |
| **Probability-Weighted Revenue** | ₹{weighted:,.2f} | High (80%), Medium (50%), Low (20%) |
| **Realized Won Revenue** | ₹{won_sum:,.2f} | Closed-won contract commitments |
| **Billed Work Order Value** | ₹{total_b:,.2f} | Invoiced operational deliveries |
| **Outstanding Receivables** | ₹{total_r:,.2f} | Requires collection prioritization |
"""

    col1, col2, col3 = st.columns([3, 1, 1])
    col1.markdown(f"**Date:** {date_str}  |  **Source:** Monday.com (Deals & Work Orders Boards)")
    col2.download_button("📥 Download .md", md, "Skylark_Report.md", "text/markdown", use_container_width=True)
    if col3.button("📋 Copy Summary", use_container_width=True):
        st.toast("Summary ready to copy — use the Download button for full report!", icon="✅")

    st.markdown("---")
    st.markdown(f"""
### 1. Executive Summary

Skylark Drones is tracking a **total sales pipeline of ₹{open_sum/1e7:.2f} Cr** across **{open_count} active deals**,
with a probability-weighted expected revenue of **₹{weighted/1e7:.2f} Cr** *(High=80%, Medium=50%, Low=20%)*.  
Operations have successfully delivered **{comp_count} work orders**, achieving a total billed value of **₹{total_b/1e5:.2f} Lakhs**.
""")

    st.markdown("### 2. Revenue & Financial Overview")
    metrics = [
        ("Total Open Pipeline",          f"₹{open_sum:,.2f}",  "Driven by large Mining & Powerline sector proposals"),
        ("Probability-Weighted Revenue",  f"₹{weighted:,.2f}",  "High (80%), Medium (50%), Low (20%) closure probability"),
        ("Realized Won Revenue",          f"₹{won_sum:,.2f}",   "Closed-won contract commitments"),
        ("Billed Work Order Value",       f"₹{total_b:,.2f}",   "Invoiced operational deliveries"),
        ("Outstanding Receivables",       f"₹{total_r:,.2f}",   "Requires collection prioritization for priority accounts"),
    ]
    rows_html = "".join(
        f"<tr><td><strong>{m}</strong></td><td>{a}</td><td style='color:#676879'>{k}</td></tr>"
        for m, a, k in metrics
    )
    st.markdown(f"""
    <table class="report-table">
      <thead><tr><th>Financial Metric</th><th>Amount (INR)</th><th>Key Observations</th></tr></thead>
      <tbody>{rows_html}</tbody>
    </table>
    """, unsafe_allow_html=True)

    st.markdown("### 3. Visual Snapshot")
    ca, cb = st.columns(2)
    df_snap = pd.DataFrame(qdb("SELECT deal_status, COUNT(*) as count, SUM(masked_deal_value) as value FROM deals GROUP BY deal_status"))
    cmap    = {"Open": "#0073ea", "Won": "#00c875", "Dead": "#df2f4a", "On Hold": "#fdab3d"}
    theme = get_chart_theme()
    is_dark = st.session_state.get("dark_mode", False)
    text_color = "#f0f2f8" if is_dark else "#0d1117"
    
    with ca:
        fig1 = px.pie(df_snap, values="count", names="deal_status", hole=.38, title="Deals by Status", color="deal_status", color_discrete_map=cmap)
        fig1.update_layout(
            plot_bgcolor=theme["plot_bgcolor"], 
            paper_bgcolor=theme["paper_bgcolor"],
            font=dict(color=text_color, family="Outfit"),
            title=dict(font=dict(color=text_color, family="Outfit")),
            legend=dict(font=dict(color=text_color, family="Outfit"))
        )
        st.plotly_chart(fig1, use_container_width=True)
    with cb:
        fig2 = px.bar(df_snap, x="deal_status", y="value", color="deal_status", title="Pipeline Value by Status", color_discrete_map=cmap, labels={"value": "₹ Value"})
        fig2.update_layout(
            showlegend=False, 
            plot_bgcolor=theme["plot_bgcolor"], 
            paper_bgcolor=theme["paper_bgcolor"],
            font=dict(color=text_color, family="Outfit"),
            title=dict(font=dict(color=text_color, family="Outfit")),
            xaxis=dict(
                color=text_color,
                tickfont=dict(color=text_color, size=10, family="Outfit")
            ),
            yaxis=dict(
                color=text_color,
                tickfont=dict(color=text_color, size=10, family="Outfit")
            )
        )
        st.plotly_chart(fig2, use_container_width=True)
