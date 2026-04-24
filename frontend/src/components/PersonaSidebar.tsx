import { useState } from "react";

import { Persona } from "../api";

type Props = {
  personas: Persona[];
  active: Persona | null;
  onSelect: (p: Persona) => void;
  onCreate: (name: string, description: string) => Promise<void>;
  onDelete: (p: Persona) => Promise<void>;
};

export function PersonaSidebar({ personas, active, onSelect, onCreate, onDelete }: Props) {
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    if (!name.trim()) return;
    setBusy(true);
    try {
      await onCreate(name.trim(), description.trim());
      setName("");
      setDescription("");
      setShowForm(false);
    } finally {
      setBusy(false);
    }
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <span className="brand">Write2Style</span>
        <button className="ghost" onClick={() => setShowForm((v) => !v)}>
          {showForm ? "Cancel" : "New"}
        </button>
      </div>

      {showForm && (
        <div className="inline-form">
          <input
            placeholder="Persona name (e.g. Professional)"
            value={name}
            onChange={(e) => setName(e.target.value)}
            autoFocus
          />
          <input
            placeholder="Short description (optional)"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
          <button onClick={submit} disabled={busy || !name.trim()}>
            {busy ? "Creating…" : "Create persona"}
          </button>
        </div>
      )}

      <div className="persona-list">
        {personas.length === 0 && !showForm && (
          <p className="empty">No personas yet.</p>
        )}
        {personas.map((p) => (
          <div
            key={p.id}
            className={`persona-item ${active?.id === p.id ? "active" : ""}`}
            onClick={() => onSelect(p)}
          >
            <div>{p.name}</div>
            <div className="meta">
              {p.sample_count} sample{p.sample_count === 1 ? "" : "s"}
            </div>
          </div>
        ))}
      </div>

      {active && (
        <div className="sidebar-footer">
          <span className="meta" style={{ color: "var(--muted)", fontSize: 12 }}>
            {active.name}
          </span>
          <button className="ghost" onClick={() => onDelete(active)}>
            Delete
          </button>
        </div>
      )}
    </aside>
  );
}
