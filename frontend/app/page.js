"use client";

import { useEffect, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
const TIMEFRAMES = ["5m", "1h", "1d"];

function formatNumber(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "N/A";
  }
  return Number(value).toFixed(digits);
}

function formatPercent(value) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "N/A";
  }
  return `${Number(value).toFixed(1)}%`;
}

export default function Home() {
  const [assets, setAssets] = useState([]);
  const [ideas, setIdeas] = useState([]);
  const [llmSummary, setLlmSummary] = useState("");
  const [generatedBy, setGeneratedBy] = useState("rules");
  const [dataNotice, setDataNotice] = useState("");
  const [timeframe, setTimeframe] = useState("1d");
  const [symbol, setSymbol] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function safeFetch(url, options) {
    const response = await fetch(url, options);
    if (!response.ok) {
      const text = await response.text();
      throw new Error(`${response.status} ${text}`);
    }
    return response.json();
  }

  async function refreshAll() {
    setLoading(true);
    setError("");
    try {
      const [assetPayload, tradePayload] = await Promise.all([
        safeFetch(`${API_BASE}/assets`),
        safeFetch(`${API_BASE}/trade-ideas?timeframe=${timeframe}`),
      ]);
      setAssets(assetPayload.assets || []);
      setIdeas(tradePayload.items || []);
      setLlmSummary(tradePayload.llm_summary || "");
      setGeneratedBy(tradePayload.generated_by || "rules");
      setDataNotice(tradePayload.data_notice || "");
    } catch (err) {
      setError(`Could not refresh the scanner. ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refreshAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [timeframe]);

  async function addAsset(event) {
    event.preventDefault();
    if (!symbol.trim()) {
      return;
    }
    try {
      await safeFetch(`${API_BASE}/assets`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          symbol: symbol.trim().toUpperCase(),
          type: "stock",
        }),
      });
      setSymbol("");
      refreshAll();
    } catch (err) {
      setError(`Failed to add symbol. ${err.message}`);
    }
  }

  async function removeAsset(assetSymbol) {
    try {
      await safeFetch(`${API_BASE}/assets/${encodeURIComponent(assetSymbol)}`, {
        method: "DELETE",
      });
      refreshAll();
    } catch (err) {
      setError(`Failed to remove symbol. ${err.message}`);
    }
  }

  return (
    <main className="page-shell">
      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">Finviz Copy For Render</p>
          <h1>AI Trade Radar</h1>
          <p className="hero-text">
            Scan Finviz snapshots, recent headlines, analyst targets, and price structure in one
            place. The ranking engine is built for research and idea generation, not live
            execution.
          </p>
        </div>
        <div className="hero-badge">
          <span>Scanner Mode</span>
          <strong>{generatedBy === "rules+openai" ? "Rules + OpenAI" : "Rules Engine"}</strong>
        </div>
      </section>

      <section className="toolbar-panel">
        <form onSubmit={addAsset} className="asset-form">
          <label className="field">
            <span>Ticker</span>
            <input
              placeholder="AAPL, NVDA, TSLA"
              value={symbol}
              onChange={(event) => setSymbol(event.target.value)}
            />
          </label>
          <button type="submit">Add stock</button>
        </form>

        <div className="toolbar-row">
          <label className="field small">
            <span>Timeframe</span>
            <select value={timeframe} onChange={(event) => setTimeframe(event.target.value)}>
              {TIMEFRAMES.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>
          <button onClick={refreshAll} disabled={loading}>
            {loading ? "Refreshing..." : "Refresh scan"}
          </button>
        </div>
      </section>

      <section className="notice-strip">
        <p>{dataNotice || "This scanner uses delayed data and should be treated as research only."}</p>
      </section>

      {error ? <section className="error-banner">{error}</section> : null}

      <section className="summary-panel">
        <div>
          <p className="section-label">Tracked Symbols</p>
          <div className="chips">
            {assets.length === 0 ? (
              <span className="empty-chip">Add a few stocks to start the scan.</span>
            ) : (
              assets.map((asset) => (
                <button
                  key={asset.symbol}
                  className="chip"
                  onClick={() => removeAsset(asset.symbol)}
                >
                  {asset.symbol} remove
                </button>
              ))
            )}
          </div>
        </div>

        <div className="llm-panel">
          <p className="section-label">AI Desk Note</p>
          <p>{llmSummary || "Set OPENAI_API_KEY and OPENAI_MODEL on the backend to add a model-written desk summary on top of the rule-based scanner."}</p>
        </div>
      </section>

      <section className="ideas-grid">
        {ideas.length === 0 ? (
          <article className="empty-state">
            <h2>No trade ideas yet</h2>
            <p>Add stock tickers above to generate ranked Finviz-backed setups.</p>
          </article>
        ) : (
          ideas.map((idea) => (
            <article className="idea-card" key={idea.symbol}>
              <div className="card-top">
                <div>
                  <p className="section-label">{idea.company || "Equity"}</p>
                  <h2>{idea.symbol}</h2>
                </div>
                <div className={`pill pill-${idea.direction}`}>{idea.direction}</div>
              </div>

              <div className="score-row">
                <div>
                  <span>Score</span>
                  <strong>{idea.score}</strong>
                </div>
                <div>
                  <span>Confidence</span>
                  <strong>{idea.confidence}%</strong>
                </div>
                <div>
                  <span>Trend</span>
                  <strong>{idea.trend}</strong>
                </div>
              </div>

              <p className="setup">{idea.setup}</p>
              <p className="rationale">{idea.rationale}</p>
              <p className="ai-summary">{idea.ai_summary}</p>

              <div className="stat-grid">
                <div className="stat-box">
                  <span>Spot</span>
                  <strong>{formatNumber(idea.current_price)}</strong>
                </div>
                <div className="stat-box">
                  <span>RSI 14</span>
                  <strong>{formatNumber(idea.rsi_14)}</strong>
                </div>
                <div className="stat-box">
                  <span>Sentiment</span>
                  <strong>{idea.sentiment_label}</strong>
                </div>
                <div className="stat-box">
                  <span>Target Gap</span>
                  <strong>{formatPercent(idea.analyst_target_delta_pct)}</strong>
                </div>
              </div>

              <div className="metric-list">
                {(idea.finviz_metrics || []).slice(0, 8).map((metric) => (
                  <div className="metric-row" key={`${idea.symbol}-${metric.label}`}>
                    <span>{metric.label}</span>
                    <strong>{metric.value}</strong>
                  </div>
                ))}
              </div>

              <div className="risk-block">
                <p className="section-label">Risk Flags</p>
                <ul>
                  {(idea.risks || []).length === 0 ? (
                    <li>No major scanner warnings.</li>
                  ) : (
                    idea.risks.map((risk, index) => <li key={`${idea.symbol}-risk-${index}`}>{risk}</li>)
                  )}
                </ul>
              </div>

              <div className="news-block">
                <p className="section-label">Latest Headlines</p>
                <ul>
                  {(idea.latest_news || []).map((item, index) => (
                    <li key={`${idea.symbol}-news-${index}`}>
                      {item.url ? (
                        <a href={item.url} target="_blank" rel="noreferrer">
                          {item.headline}
                        </a>
                      ) : (
                        item.headline
                      )}
                      <span>{item.timestamp}{item.source ? ` · ${item.source}` : ""}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </article>
          ))
        )}
      </section>
    </main>
  );
}
