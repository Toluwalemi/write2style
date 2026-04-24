import { useCallback, useEffect, useRef, useState } from "react";

import { listSamples, Sample, uploadSample } from "../api";

type Props = {
  personaId: string;
  token: () => Promise<string | null>;
  onUploaded: () => Promise<void>;
};

export function SamplesPanel({ personaId, token, onUploaded }: Props) {
  const [samples, setSamples] = useState<Sample[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);

  const refresh = useCallback(async () => {
    try {
      setSamples(await listSamples(token, personaId));
    } catch (err) {
      setError((err as Error).message);
    }
  }, [token, personaId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const handleFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      await uploadSample(token, personaId, file);
      await refresh();
      await onUploaded();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
      if (fileInput.current) fileInput.current.value = "";
    }
  };

  return (
    <div>
      <div className="uploader">
        <input
          ref={fileInput}
          type="file"
          accept=".txt,.md,.pdf,text/plain,text/markdown,application/pdf"
          onChange={handleFile}
          disabled={busy}
        />
        {busy && <span className="empty">Analyzing…</span>}
      </div>
      {error && <div className="error">{error}</div>}
      <div className="samples" style={{ marginTop: 16 }}>
        {samples.length === 0 ? (
          <p className="empty">No samples yet. Upload a .txt, .md, or .pdf.</p>
        ) : (
          samples.map((s) => (
            <div key={s.id} className="sample-row">
              <span>{s.filename}</span>
              <span className="meta">
                {s.chunk_count} chunk{s.chunk_count === 1 ? "" : "s"} ·{" "}
                {Math.round(s.char_count / 1000)}k chars
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
