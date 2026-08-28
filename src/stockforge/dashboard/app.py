"""Stochastix Streamlit dashboard - midnight research desk edition."""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

    st.set_page_config(page_title="Stochastix", layout="wide")

ARTIFACTS = Path(os.environ.get("STOCKFORGE_ARTIFACTS_DIR", "artifacts"))
CACHE = Path(os.environ.get("STOCKFORGE_DATA_CACHE_DIR", "data/cache"))

INK_0, INK_1, INK_2, LINE = "#0B0E14", "#11151F", "#1A2030", "#263043"
AMBER, CYAN = "#F5B84B", "#5FD4E8"
UP, DOWN = "#35D07F", "#F0564C"
TEXT, MUTED = "#E8ECF4", "#93A0B8"

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Inter:wght@400;500;600;700&display=swap');

.stApp {{
  background:
    radial-gradient(1200px 500px at 80% -10%, rgba(245,184,75,.06), transparent 60%),
    radial-gradient(900px 400px at 10% 110%, rgba(95,212,232,.05), transparent 60%),
    {INK_0};
  color: {TEXT};
}}
#MainMenu, footer {{visibility: hidden;}}
[data-testid="stHeader"] {{background: transparent;}}
section[data-testid="stSidebar"] {{
  background: {INK_1};
  border-right: 1px solid {LINE};
}}
h1, h2, h3, .stMarkdown p {{font-family: 'Inter', sans-serif;}}
h1 {{font-weight: 700; letter-spacing: -.02em;}}
.sf-mono, code, [data-testid="stMetricValue"] {{
  font-family: 'IBM Plex Mono', monospace !important;
}}
div[data-testid="stMetric"] {{
  background: linear-gradient(180deg, {INK_2}, {INK_1});
  border: 1px solid {LINE};
  border-radius: 12px;
  padding: 14px 18px 10px 18px;
}}
div[data-testid="stMetric"] label {{color: {MUTED} !important;}}
div[data-testid="stMetric"] [data-testid="stMetricDelta"] svg {{vertical-align: middle;}}
hr {{border-color: {LINE};}}
.block-container {{padding-top: 1.6rem;}}

.sf-eyebrow {{
  font-family:'IBM Plex Mono',monospace; font-size:.72rem; letter-spacing:.28em;
  text-transform:uppercase; color:{AMBER}; margin-bottom:.15em;
}}
.sf-hero {{
  border-bottom: 1px solid {LINE}; padding-bottom:.9rem; margin-bottom:1.1rem;
}}
.sf-hero h1 {{margin:0; font-size:2.5rem;}}
.sf-hero p {{color:{MUTED}; margin:.25em 0 0 0;}}

.sf-tape {{
  overflow:hidden; white-space:nowrap; border-block:1px solid {LINE};
  background:{INK_1}; margin:0 -1rem 1.2rem -1rem; padding:.45rem 0;
}}
.sf-tape-track {{
  display:inline-block; animation:sf-scroll 38s linear infinite;
}}
.sf-chip {{
  font-family:'IBM Plex Mono',monospace; font-size:.85rem; margin:0 .35rem;
  padding:.18rem .7rem; border-radius:999px; border:1px solid {LINE};
  background:{INK_2}; color:{MUTED};
}}
.sf-chip b {{color:{TEXT}; font-weight:600;}}
.sf-up {{color:{UP};}} .sf-down {{color:{DOWN};}} .sf-flat {{color:{AMBER};}}
@keyframes sf-scroll {{from{{transform:translateX(0)}}to{{transform:translateX(-50%)}}}}
@media (prefers-reduced-motion: reduce) {{
  .sf-tape-track {{animation:none;}}
}}

.sf-callout {{
  background:{INK_1}; border:1px solid {LINE}; border-radius:14px; padding:18px;
}}
.stTabs [data-baseweb="tab-list"] {{gap:6px;}}
.stTabs [data-baseweb="tab"] {{
  background:{INK_1}; border:1px solid {LINE}; border-radius:8px 8px 0 0;
}}
.stTabs [aria-selected="true"] {{border-color:{AMBER};}}
</style>
"""

PALETTE = [CYAN, AMBER, UP, "#B78CFF", DOWN, "#FFB3C7", "#8FA5FF", "#FFD98A", "#7BE0C8", "#C9A66F"]


def dark(fig, height=460, title=None):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=INK_1,
        font_family="IBM Plex Mono",
        font_color=MUTED,
        height=height,
        margin=dict(l=10, r=10, t=52 if title else 24, b=10),
        title_text=title,
        title_font_color=TEXT,
        hovermode="x unified",
        xaxis_gridcolor=LINE,
        yaxis_gridcolor=LINE,
    )
    fig.update_xaxes(showline=True, linecolor=LINE)
    fig.update_yaxes(showline=True, linecolor=LINE)
    return fig


def load_json_safe(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return default


def load_parquet_safe(path: Path):
    if not path.exists():
        return None
    try:
        return pd.read_parquet(path)
    except Exception as exc:  # noqa: BLE001
        st.warning(f"`{path}` unreadable ({exc}). Run `python run.py` to regenerate.")
        return None


@st.cache_data(show_spinner=False)
def load_panel():
    try:
        from stockforge.config import load_config
        from stockforge.data.ingestion import load_panel_from_cache

        cfg = load_config()
        return load_panel_from_cache(cfg.universe.tickers, CACHE)
    except Exception:  # noqa: BLE001
        from stockforge.config import load_config
        from stockforge.data.synthetic import generate_synthetic_panel

        return generate_synthetic_panel(load_config().universe.tickers)


@st.cache_data(show_spinner=False)
def load_forecasts() -> dict[int, pd.DataFrame]:
    raw = load_parquet_safe(ARTIFACTS / "forecasts" / "latest.parquet")
    if raw is None:
        return {}
    return {int(h): sub.droplevel("horizon") for h, sub in raw.groupby(level="horizon")}


@st.cache_data(show_spinner=False)
def load_metadata() -> dict:
    models_root = ARTIFACTS / "models"
    if not models_root.exists():
        return {}
    runs = sorted(d for d in models_root.iterdir() if d.is_dir())
    for run in reversed(runs):
        meta = load_json_safe(run / "metadata.json", {})
        if meta:
            meta["_run_id"] = run.name
            return meta
    return {}


@st.cache_data(show_spinner=False)
def load_backtest():
    equity = load_parquet_safe(ARTIFACTS / "backtest" / "equity.csv")
    bench = load_parquet_safe(ARTIFACTS / "backtest" / "benchmark.csv")
    if equity is not None:
        equity.index = pd.to_datetime(equity.index)
    if bench is not None:
        bench.index = pd.to_datetime(bench.index)
    metrics = load_json_safe(ARTIFACTS / "backtest" / "metrics.json", {})
    return equity, bench, metrics


panel = load_panel()
metadata = load_metadata()
forecasts = load_forecasts()

st.markdown(CSS, unsafe_allow_html=True)

st.markdown(
    f"""
<div class="sf-hero">
  <div class="sf-eyebrow">stochastix // research desk</div>
  <h1>Forecasts &amp; Portfolio Lab</h1>
  <p>{len(panel.tickers)} tickers &middot; {len(panel.dates)} sessions &middot;
     model run <span class="sf-mono" style="color:{CYAN}">{metadata.get("_run_id", "none")}</span>
     &nbsp;&mdash;&nbsp; educational demo, not investment advice</p>
</div>
""",
    unsafe_allow_html=True,
)

if forecasts:
    chips = []
    frame = forecasts[min(forecasts)]
    for ticker, row in frame.iterrows():
        pct = float(row["expected_return_pct"])
        cls = "sf-up" if pct > 0 else ("sf-down" if pct < 0 else "sf-flat")
        arrow = "&#9650;" if pct > 0 else ("&#9660;" if pct < 0 else "&#9679;")
        chip = f'<span class="sf-chip"><b>{ticker}</b> '
        chips.append(f'{chip}<span class="{cls}">{pct:+.2f}% {arrow}</span></span>')
    half = len(chips) // 2 or 1
    track = "".join(chips + chips[:half])
    st.markdown(
        f'<div class="sf-tape"><div class="sf-tape-track">{track}</div></div>',
        unsafe_allow_html=True,
    )

page = st.sidebar.radio(
    "Desk", ["Market Overview", "Forecasts", "Portfolio Lab", "Backtest", "Correlations"]
)

if page == "Market Overview":
    tickers = st.sidebar.multiselect("Tickers", panel.tickers, default=panel.tickers[:5])

    c1, c2, c3, c4 = st.columns(4)
    rets_all = panel.simple_returns()
    spy_ret = rets_all["SPY"].iloc[-1] if "SPY" in rets_all else rets_all.iloc[:, -1].iloc[-1]
    best_day = rets_all.iloc[-1].idxmax()
    c1.metric("Sessions tracked", f"{len(panel.dates):,}")
    c2.metric("Last session move (SPY)", f"{spy_ret:+.2%}", spy_ret, delta_color="off")
    c3.metric(
        "Best mover today", str(best_day), float(rets_all.iloc[-1][best_day]), delta_color="off"
    )
    avg_vol = rets_all.std().mean() * np.sqrt(252)
    c4.metric("Universe avg vol (ann.)", f"{avg_vol:.1%}")

    closes = panel.close[tickers]
    normalized = closes / closes.iloc[0] * 100.0
    fig = go.Figure()
    for i, ticker in enumerate(tickers):
        fig.add_trace(
            go.Scatter(
                x=normalized.index,
                y=normalized[ticker],
                name=ticker,
                line=dict(color=PALETTE[i % len(PALETTE)], width=1.8),
            )
        )
    fig.add_hline(y=100, line_dash="dot", line_color=LINE, opacity=0.6)
    st.plotly_chart(dark(fig, 520, "Normalized performance (start = 100)"), width="stretch")

    with st.expander("Raw closes", expanded=False):
        st.dataframe(closes.tail().style.format("${:,.2f}"), width="stretch")

elif page == "Forecasts":
    if not forecasts:
        st.info("No forecasts yet.")
        st.code("python run.py", language="bash")
    else:
        horizon = st.sidebar.selectbox(
            "Horizon (days)", sorted(forecasts), index=len(forecasts) - 1
        )
        frame = forecasts[horizon]
        price_col = next(c for c in frame.columns if c.startswith("predicted_price"))
        span = (frame["expected_return_pct"].abs().max() or 1.0) / 100.0

        st.subheader(f"{horizon}-day outlook")
        st.dataframe(
            frame.reset_index(),
            hide_index=True,
            width="stretch",
            column_config={
                "last_close": st.column_config.NumberColumn("Last close", format="$ %.2f"),
                price_col: st.column_config.NumberColumn("Target price", format="$ %.2f"),
                "expected_return_pct": st.column_config.ProgressColumn(
                    "Expected move",
                    format="%+.2f%%",
                    min_value=float(-span * 100),
                    max_value=float(span * 100),
                ),
                "lower_95": st.column_config.NumberColumn("95% low", format="$ %.2f"),
                "upper_95": st.column_config.NumberColumn("95% high", format="$ %.2f"),
            },
        )

        left, right = st.columns([3, 2])
        with left:
            ticker = st.selectbox("Simulate", frame.index.tolist())
            resid_std = float(
                (metadata.get("per_horizon", {}).get(str(horizon), {}) or {}).get(
                    "residual_std", 0.05
                )
                or 0.05
            )
            s0 = float(frame.loc[ticker, "last_close"])
            rng = np.random.default_rng(7)
            steps = min(horizon, 21)
            sims = s0 * np.exp(
                np.cumsum(rng.normal(0.0, resid_std / np.sqrt(horizon), size=(600, steps)), axis=1)
            )
            x_axis = np.arange(1, steps + 1)
            med = np.percentile(sims, 50, axis=0)
            hi90, lo90 = np.percentile(sims, 95, axis=0), np.percentile(sims, 5, axis=0)
            hi60, lo60 = np.percentile(sims, 80, axis=0), np.percentile(sims, 20, axis=0)

            fan = go.Figure()
            fan.add_trace(
                go.Scatter(
                    x=x_axis, y=hi90, line=dict(width=0), hoverinfo="skip", fill=None, name="_90"
                )
            )
            fan.add_trace(
                go.Scatter(
                    x=x_axis,
                    y=lo90,
                    fill="tonexty",
                    mode="none",
                    fillcolor="rgba(95,212,232,.12)",
                    hoverinfo="skip",
                    name="90% band",
                )
            )
            fan.add_trace(
                go.Scatter(x=x_axis, y=hi60, line=dict(width=0), hoverinfo="skip", name="_60")
            )
            fan.add_trace(
                go.Scatter(
                    x=x_axis,
                    y=lo60,
                    fill="tonexty",
                    mode="none",
                    fillcolor="rgba(245,184,75,.22)",
                    hoverinfo="skip",
                    name="60% band",
                )
            )
            fan.add_trace(
                go.Scatter(
                    x=x_axis,
                    y=med,
                    line=dict(color=AMBER, width=3),
                    name="Median path",
                    hovertemplate="day %{x}: $%{y:,.0f}<extra>median</extra>",
                )
            )
            fan.add_hline(
                y=s0,
                line_dash="dot",
                line_color=MUTED,
                annotation_text=f"last close ${s0:,.0f}",
                annotation_font_color=MUTED,
            )
            st.plotly_chart(
                dark(
                    fan,
                    480,
                    f"{ticker}: simulated paths from out-of-sample residuals (std {resid_std:.4f})",
                ),
                width="stretch",
            )
        with right:
            target = frame.loc[ticker]
            drift_pct = float(target["expected_return_pct"])
            tone = UP if drift_pct > 0 else (DOWN if drift_pct < 0 else AMBER)
            band_lo, band_hi = float(target["lower_95"]), float(target["upper_95"])
            st.markdown(
                f"""
                <div class="sf-callout">
                  <div class="sf-eyebrow">{ticker} &middot; {horizon}d call</div>
                  <div class="sf-mono" style="font-size:2rem;color:{tone}">
                    {drift_pct:+.2f}% {"" if drift_pct > 0 else ""}
                  </div>
                  <div style="color:{MUTED};font-size:.85rem;margin-top:6px">
                    ${float(target["last_close"]):,.2f} &rarr; ${float(target[price_col]):,.2f}
                    &nbsp;(band ${band_lo:,.0f}&ndash;${band_hi:,.0f})
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.caption("Bands are residual-bootstrap percentiles, not guarantees.")

elif page == "Portfolio Lab":
    payload = load_json_safe(ARTIFACTS / "portfolios" / "latest.json", {})
    if not payload:
        st.info("No optimized portfolios yet.")
        st.code("python run.py", language="bash")
    else:
        schemes = list(payload["schemes"].keys())
        scheme = st.sidebar.selectbox("Scheme", schemes)
        entry = payload["schemes"][scheme]
        weights = pd.Series(entry["weights"]).sort_values(ascending=False)
        weights = weights[weights >= 1e-4]

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Scheme", scheme.replace("_", " "))
        k2.metric(
            "Exp. return", f"{entry['exp_return']:+.1%}" if entry["exp_return"] is not None else "-"
        )
        k3.metric(
            "Exp. volatility", f"{entry['exp_vol']:.1%}" if entry["exp_vol"] is not None else "-"
        )
        k4.metric("Sharpe", f"{entry['sharpe']:.2f}" if entry["sharpe"] is not None else "-")

        tab_alloc, tab_frontier = st.tabs(["Allocation", "Efficient frontier"])

        with tab_alloc:
            lc, rc = st.columns([3, 2])
            with lc:
                tree = px.treemap(
                    names=weights.index,
                    values=weights.values,
                    color=weights.values,
                    color_continuous_scale=[INK_2, CYAN, AMBER],
                )
                tree.update_traces(textinfo="label+percent entry", textfont_size=16)
                tree.update_layout(coloraxis_showscale=False)
                st.plotly_chart(dark(tree, 420, "Where the money goes"), width="stretch")
            with rc:
                sharpe_val = entry["sharpe"]
                if sharpe_val is not None:
                    gauge = go.Figure(
                        go.Indicator(
                            mode="gauge+number",
                            value=float(sharpe_val),
                            number={"font": {"color": TEXT, "family": "IBM Plex Mono"}},
                            gauge={
                                "axis": {"range": [0, 2.5], "tickcolor": MUTED},
                                "bar": {"color": AMBER},
                                "bgcolor": INK_1,
                                "steps": [
                                    {"range": [0, 0.7], "color": "rgba(240,86,76,.25)"},
                                    {"range": [0.7, 1.2], "color": "rgba(245,184,75,.18)"},
                                    {"range": [1.2, 2.5], "color": "rgba(53,208,127,.20)"},
                                ],
                                "bordercolor": LINE,
                            },
                        )
                    )
                    st.plotly_chart(
                        dark(gauge, 300, "Risk-adjusted quality (Sharpe)"), width="stretch"
                    )
            dollar = weights.rename("weight").reset_index()
            dollar.columns = ["Ticker", "Weight"]
            st.dataframe(
                dollar,
                hide_index=True,
                width="stretch",
                column_config={
                    "Weight": st.column_config.ProgressColumn(
                        "",
                        format="%.1f%%",
                        min_value=0.0,
                        max_value=float(weights.max() * 100) * 1.05,
                    ),
                },
            )

        with tab_frontier:
            try:
                from stockforge.portfolio.optimizer import PortfolioOptimizer, shrunk_covariance

                returns_hist = panel.simple_returns().tail(252)
                cov = shrunk_covariance(returns_hist) * 252.0
                mu_hist = returns_hist.mean() * 252.0
                blend_mu = (
                    mu_hist + pd.Series(entry["weights"], index=cov.columns).fillna(0)
                ) / 2.0
                opt = PortfolioOptimizer(blend_mu.clip(-1, 3), cov, max_weight=0.35)
                frontier = opt.efficient_frontier(n_points=40)

                rng = np.random.default_rng(1)
                n_a = len(cov.columns)
                rand_w = rng.dirichlet(np.ones(n_a), size=900)
                mus, vols = [], []
                cov_np, mu_np = cov.to_numpy(), blend_mu.reindex(cov.columns).fillna(0).to_numpy()
                for w in rand_w:
                    mus.append(float(w @ mu_np))
                    vols.append(float(np.sqrt(w @ cov_np @ w)))

                front = go.Figure()
                front.add_trace(
                    go.Scatter(
                        x=vols,
                        y=mus,
                        mode="markers",
                        name="random portfolios",
                        marker=dict(color="rgba(147,160,184,.30)", size=5),
                        hovertemplate="vol %{x:.1%}<br>ret %{y:.1%}<extra></extra>",
                    )
                )
                front.add_trace(
                    go.Scatter(
                        x=frontier["volatility"],
                        y=frontier["return"],
                        mode="lines",
                        line=dict(color=CYAN, width=3),
                        name="efficient frontier",
                    )
                )
                ms = opt.max_sharpe()
                ms_r = float(ms.weights @ blend_mu.reindex(cov.columns).fillna(0))
                ms_v = float(np.sqrt(ms.weights.to_numpy() @ cov_np @ ms.weights.to_numpy()))
                front.add_trace(
                    go.Scatter(
                        x=[ms_v],
                        y=[ms_r],
                        mode="markers+text",
                        marker=dict(
                            size=18, symbol="star", color=AMBER, line=dict(width=1, color=INK_0)
                        ),
                        text=["max Sharpe"],
                        textposition="top center",
                        textfont=dict(color=AMBER),
                        name="max Sharpe",
                    )
                )
                front.add_trace(
                    go.Scatter(
                        x=[entry["exp_vol"]],
                        y=[entry["exp_return"]],
                        mode="markers",
                        marker=dict(size=13, color=UP, symbol="diamond"),
                        name=f"{scheme}",
                        hovertemplate=f"{scheme}: %{{x:.1%}} / %{{y:.1%}}<extra></extra>",
                    )
                )
                rf = 0.02
                cal_x = np.linspace(0, ms_v * 1.5, 10)
                front.add_trace(
                    go.Scatter(
                        x=cal_x,
                        y=rf + (ms_r - rf) / ms_v * cal_x,
                        mode="lines",
                        line=dict(color="rgba(245,184,75,.45)", dash="dot"),
                        name="capital market line",
                    )
                )
                st.plotly_chart(
                    dark(front, 500, "The frontier, the cloud, and where you sit"), width="stretch"
                )
            except Exception as exc:  # noqa: BLE001
                st.warning(f"Frontier unavailable: {exc}")

elif page == "Backtest":
    equity, bench, metrics = load_backtest()
    if equity is None:
        st.info("No backtest yet.")
        st.code("python run.py", language="bash")
    else:
        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            row_heights=[0.72, 0.28],
            vertical_spacing=0.03,
        )
        for i, col in enumerate(equity.columns):
            fig.add_trace(
                go.Scatter(
                    x=equity.index,
                    y=equity[col],
                    name=col,
                    line=dict(color=PALETTE[i % len(PALETTE)], width=2),
                ),
                row=1,
                col=1,
            )
        if bench is not None:
            for col in bench.columns:
                fig.add_trace(
                    go.Scatter(
                        x=bench.index,
                        y=bench[col],
                        name=col,
                        line=dict(color=MUTED, width=1.4, dash="dash"),
                    ),
                    row=1,
                    col=1,
                )
        for i, col in enumerate(equity.columns):
            dd = equity[col] / equity[col].cummax() - 1.0
            fig.add_trace(
                go.Scatter(
                    x=equity.index,
                    y=dd,
                    name=f"{col} dd",
                    showlegend=False,
                    stackgroup=f"dd{i}",
                    line=dict(width=0.6, color=PALETTE[i % len(PALETTE)]),
                    fillcolor="rgba(240,86,76,.08)",
                    hoverinfo="x+y",
                ),
                row=2,
                col=1,
            )
        fig.update_yaxes(title_text="Equity ($)", row=1, col=1)
        fig.update_yaxes(title_text="Drawdown", tickformat=".0%", row=2, col=1)
        st.plotly_chart(dark(fig, 640, "Out-of-sample equity & underwater curve"), width="stretch")

        if metrics:
            rows = []
            for scheme_name, m in metrics.items():
                rows.append(
                    {
                        "Scheme": scheme_name,
                        "CAGR": m.get("cagr") or np.nan,
                        "Volatility": m.get("volatility") or np.nan,
                        "Sharpe": m.get("sharpe") or np.nan,
                        "Max DD": m.get("max_drawdown") or np.nan,
                        "Calmar": m.get("calmar") or np.nan,
                        "Excess CAGR": m.get("excess_cagr") or np.nan,
                    }
                )
            stats_df = pd.DataFrame(rows).set_index("Scheme")
            st.dataframe(
                stats_df.reset_index(),
                hide_index=True,
                width="stretch",
                column_config={
                    "CAGR": st.column_config.NumberColumn(format="%+.1f%%"),
                    "Volatility": st.column_config.NumberColumn(format="%.1f%%"),
                    "Sharpe": st.column_config.NumberColumn(format="%.2f"),
                    "Max DD": st.column_config.NumberColumn(format="%.1f%%"),
                    "Calmar": st.column_config.NumberColumn(format="%.2f"),
                    "Excess CAGR": st.column_config.NumberColumn(format="%+.1f%%"),
                },
            )

else:
    returns_hist = panel.simple_returns().dropna()
    corr = returns_hist.corr()
    heat = px.imshow(
        corr,
        text_auto=".2f",
        aspect="auto",
        color_continuous_scale=[DOWN, INK_1, UP],
        zmin=-1,
        zmax=1,
        labels=dict(color="corr"),
    )
    heat.update_traces(textfont_size=11)
    st.plotly_chart(dark(heat, 560, "Who moves together (trailing daily returns)"), width="stretch")
    offdiag = corr.values[~np.eye(len(corr), dtype=bool)]
    tight = corr.where(~np.eye(len(corr), dtype=bool)).stack().sort_values()
    c1, c2 = st.columns(2)
    c1.metric(
        "Most correlated pair",
        f"{tight.index[-1][0]} × {tight.index[-1][1]}",
        round(float(tight.iloc[-1]), 2),
        delta_color="off",
    )
    c2.metric(
        "Best diversifier pair",
        f"{tight.index[0][0]} × {tight.index[0][1]}",
        round(float(tight.iloc[0]), 2),
        delta_color="off",
    )
    _ = offdiag

st.sidebar.markdown("---")
if metadata:
    st.sidebar.caption(f"Model run `{metadata.get('_run_id', '?')}`")
st.sidebar.caption("Not investment advice. Educational demo.")
