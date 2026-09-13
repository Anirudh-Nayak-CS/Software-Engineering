import { StrictMode, useState } from "react";
import { createRoot } from "react-dom/client";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import "./styles.css";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [prompt, setPrompt] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
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

  function handlePromptKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      event.currentTarget.form.requestSubmit();
    }
  }

  return (
    <main className="shell">
      <header>
        <p className="eyebrow">Requirement Engineering</p>
        <h1>Turn a project idea into a plan.</h1>
        <p className="subtext">Describe the system. The local workflow retrieves evidence, then asks the remote GPU model for requirements and an SDLC recommendation.</p>
      </header>

      <form onSubmit={submit} className="prompt-box">
        <label htmlFor="prompt">Project requirement</label>
        <textarea id="prompt" value={prompt} onChange={(event) => setPrompt(event.target.value)} onKeyDown={handlePromptKeyDown} placeholder="Build an AI-powered Hospital Management System..." rows="7" />
        <button disabled={loading || !prompt.trim()}>{loading ? "Generating..." : "Generate specification"}</button>
      </form>

      {error && <p className="error">{error}</p>}
      {result && <section className="results">
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
      </section>}
    </main>
  );
}

createRoot(document.getElementById("root")).render(<StrictMode><App /></StrictMode>);