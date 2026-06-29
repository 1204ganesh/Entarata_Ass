
import { useMemo, useState } from "react";
import { Code2, Loader2, Wand2, Clock, BarChart2, CheckCircle2 } from "lucide-react";
import { explainCode } from "./api.js";
import CodePanel from "./components/CodePanel.jsx";
import DiffView from "./components/DiffView.jsx";
import HistoryList from "./components/HistoryList.jsx";

const examples = {
  python: `def find_even_numbers(values):
    evens = []
    for value in values:
        if value % 2 == 0:
            evens.append(value)
    return evens`,
  javascript: `function totalCart(items) {
  let total = 0;
  for (const item of items) {
    total += item.price * item.quantity;
  }
  return total;
}`
};

export default function App() {
  const [language, setLanguage] = useState("python");
  const [code, setCode] = useState(examples.python);
  const [includeOptimization, setIncludeOptimization] = useState(true);
  const [history, setHistory] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const activeResult = useMemo(
    () => history.find((item) => item.id === activeId) || history[0],
    [activeId, history]
  );

  function handleLanguageChange(nextLanguage) {
    setLanguage(nextLanguage);
    setCode(examples[nextLanguage]);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const result = await explainCode({ language, code, includeOptimization });
      const saved = { ...result, originalCode: code, createdAt: new Date().toISOString() };
      setHistory((items) => [saved, ...items]);
      setActiveId(saved.id);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      {/* Top bar */}
      <header className="topbar">
        <div className="topbar-brand">
          <div className="brand-icon">
            <Code2 size={16} />
          </div>
          <span className="brand-name">Code Explainer</span>
          <span className="brand-sep" />
          <span className="brand-sub">AI-powered</span>
        </div>
        <div className="topbar-controls">
          <div className="lang-switcher">
            {["python", "javascript"].map((lang) => (
              <button
                key={lang}
                type="button"
                className={`lang-btn ${language === lang ? "lang-btn--active" : ""}`}
                onClick={() => handleLanguageChange(lang)}
              >
                {lang === "python" ? "Python" : "JavaScript"}
              </button>
            ))}
          </div>
          <label className="opt-toggle">
            <input
              type="checkbox"
              checked={includeOptimization}
              onChange={(e) => setIncludeOptimization(e.target.checked)}
            />
            <span>Optimize</span>
          </label>
        </div>
      </header>

      {/* Main editor + sidebar */}
      <div className="main-grid">
        <form className="editor-pane" onSubmit={handleSubmit}>
          <div className="editor-header">
            <span className="editor-lang-badge">{language}</span>
            <span className="editor-line-count">{code.split("\n").length} lines</span>
          </div>
          <textarea
            className="code-textarea"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            spellCheck="false"
            aria-label="Code snippet"
          />
          <div className="editor-footer">
            <button className="run-btn" type="submit" disabled={loading || !code.trim()}>
              {loading ? <Loader2 size={15} className="spin" /> : <Wand2 size={15} />}
              Explain code
            </button>
            {error && <p className="error-text">{error}</p>}
          </div>
        </form>

        <aside className="sidebar">
          <HistoryList items={history} activeId={activeId} onSelect={setActiveId} />
          {history.length > 0 && (
            <div className="sidebar-stats">
              <div className="stat-card">
                <span>Snippets</span>
                <strong>{history.length}</strong>
              </div>
              <div className="stat-card">
                <span>Languages</span>
                <strong>{new Set(history.map((h) => h.language)).size}</strong>
              </div>
            </div>
          )}
        </aside>
      </div>

      {/* Results */}
      {activeResult && (
        <section className="results">
          <div className="results-grid">
            {/* Explanation */}
            <article className="result-card">
              <div className="card-title">
                <BarChart2 size={14} />
                Explanation
              </div>
              <p className="explanation-text">{activeResult.explanation}</p>
              <div className="metrics-row">
                <div className="metric">
                  <span>Time</span>
                  <strong>{activeResult.complexity.time}</strong>
                </div>
                <div className="metric">
                  <span>Space</span>
                  <strong>{activeResult.complexity.space}</strong>
                </div>
                <div className="metric">
                  <span>Provider</span>
                  <strong>{activeResult.provider}</strong>
                </div>
              </div>
              <p className="complexity-reason">{activeResult.complexity.reason}</p>
              <div className="provider-chip">
                <CheckCircle2 size={12} />
                {activeResult.provider}
              </div>
            </article>

            {/* Annotated code */}
            <CodePanel
              code={activeResult.originalCode}
              annotations={activeResult.annotations}
            />

            {/* Diff */}
            {activeResult.optimizedCode && (
              <DiffView
                original={activeResult.originalCode}
                optimized={activeResult.optimizedCode}
                summary={activeResult.optimizationSummary}
              />
            )}
          </div>
        </section>
      )}
    </div>
  );
}