import { StrictMode, useState } from "react";
import { createRoot } from "react-dom/client";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import "./styles.css";

const API_URL = import.meta.env.VITE_API_URL.replace(/\/$/, "");

function App() {
  const [prompt, setPrompt] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState("");

  async function submit(event) {
    event.preventDefault();
    if (!prompt.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const response = await fetch(`${API_URL}/requirements`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_requirement: prompt }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Request failed");
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function downloadPdf() {
    if (!result || downloading) return;
    setDownloading(true);
    setError("");
    try {
      const response = await fetch(`${API_URL}/requirements/pdf`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(result),
      });
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || "Could not create the PDF report.");
      }
      const pdf = await response.blob();
      const objectUrl = URL.createObjectURL(pdf);
      const link = document.createElement("a");
      link.href = objectUrl;
      link.download = "requirement-report.pdf";
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
    } catch (err) {
      setError(err.message);
    } finally {
      setDownloading(false);
    }
  }

  function handlePromptKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      event.currentTarget.form.requestSubmit();
    }
  }

  return (
    <main className="shell">
      <header>
        <p className="eyebrow"><span className="eyebrow-mark" aria-hidden="true" />Requirement Engineering</p>
        <h1>Turn a project idea into a plan.</h1>
        <p className="subtext">Describe the system you want to build. Get a structured requirement specification and a tailored SDLC recommendation, grounded in healthcare references.</p>
        <div className="workflow-badges" aria-label="Workflow features">
          <span className="workflow-badge badge-evidence"><span aria-hidden="true">◆</span> Evidence-backed</span>
          <span className="workflow-badge badge-model"><span aria-hidden="true">◉</span> Qwen-powered</span>
          <span className="workflow-badge badge-export"><span aria-hidden="true">↓</span> PDF export</span>
        </div>
      </header>

      <form onSubmit={submit} className="prompt-box">
        <div className="prompt-label-row">
          <label htmlFor="prompt">Project requirement</label>
          <span className="input-hint">Be as specific as you like</span>
        </div>
        <textarea id="prompt" value={prompt} onChange={(event) => setPrompt(event.target.value)} onKeyDown={handlePromptKeyDown} placeholder="Describe the users, key features, constraints, and goals for your project..." rows="7" />
        <div className="form-actions">
          <span className="keyboard-hint">Press <kbd>Enter</kbd> to generate · <kbd>Shift + Enter</kbd> for a new line</span>
          <button className="generate-button" disabled={loading || !prompt.trim()}>
            {loading ? <><span className="spinner" aria-hidden="true" />Generating your report</> : <>Generate specification <span className="button-arrow" aria-hidden="true">↗</span></>}
          </button>
        </div>
      </form>

      {error && <p className="error" role="alert"><span className="error-mark" aria-hidden="true">!</span>{error}</p>}
      {result && <>
        <div className="results-heading">
          <div>
            <p className="eyebrow">Your generated report</p>
            <h2>Review the results</h2>
          </div>
          <button className="download-button" onClick={downloadPdf} disabled={downloading}>
            {downloading ? <><span className="spinner" aria-hidden="true" />Preparing PDF</> : <><span className="download-icon" aria-hidden="true">↓</span>Download PDF</>}
          </button>
        </div>
        <section className="results">
        <article>
          <h2>Requirement specification</h2>
          <div className="markdown-body">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {result.requirement_specification}
            </ReactMarkdown>
          </div>
        </article>
        <article>
          <h2>SDLC recommendation</h2>
          <div className="markdown-body">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {result.sdlc_recommendation}
            </ReactMarkdown>
          </div>
        </article>
        </section>
      </>}
    </main>
  );
}

createRoot(document.getElementById("root")).render(<StrictMode><App /></StrictMode>);
