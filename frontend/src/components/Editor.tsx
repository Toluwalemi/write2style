import { useState } from "react";

import { streamGenerate } from "../api";

type Props = {
  personaId: string;
  token: () => Promise<string | null>;
};

export function Editor({ personaId, token }: Props) {
  const [prompt, setPrompt] = useState("");
  const [output, setOutput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async () => {
    if (!prompt.trim()) return;
    setBusy(true);
    setError(null);
    setOutput("");
    try {
      await streamGenerate(token, personaId, prompt, (delta) => {
        setOutput((prev) => prev + delta);
      });
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <div className="editor">
        <div className="stack">
          <textarea
            placeholder="What should we write? A prompt, a rough draft, or bullet points…"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
          />
          <div className="row">
            <button onClick={run} disabled={busy || !prompt.trim()}>
              {busy ? "Writing…" : "Generate"}
            </button>
            {output && (
              <button className="secondary" onClick={() => navigator.clipboard.writeText(output)}>
                Copy
              </button>
            )}
          </div>
        </div>
        <div className="output">{output || <span className="empty">Output appears here.</span>}</div>
      </div>
      {error && <div className="error">{error}</div>}
    </>
  );
}
