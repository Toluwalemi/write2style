import {
  SignedIn,
  SignedOut,
  SignInButton,
  UserButton,
  useAuth,
} from "@clerk/clerk-react";
import { useCallback, useEffect, useState } from "react";

import {
  createPersona,
  deletePersona,
  getPersona,
  listPersonas,
  Persona,
} from "./api";
import { Editor } from "./components/Editor";
import { PersonaSidebar } from "./components/PersonaSidebar";
import { SamplesPanel } from "./components/SamplesPanel";
import { StyleDnaView } from "./components/StyleDnaView";

function Landing() {
  return (
    <div className="landing">
      <h1>Write2Style</h1>
      <p>
        Clone your writing voice from samples. Build multiple style personas. Draft new
        content that actually sounds like you.
      </p>
      <SignInButton mode="modal">
        <button>Sign in to get started</button>
      </SignInButton>
    </div>
  );
}

function Workspace() {
  const { getToken } = useAuth();
  const token = useCallback(() => getToken(), [getToken]);

  const [personas, setPersonas] = useState<Persona[]>([]);
  const [active, setActive] = useState<Persona | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshPersonas = useCallback(async () => {
    try {
      const list = await listPersonas(token);
      setPersonas(list);
      return list;
    } catch (err) {
      setError((err as Error).message);
      return [];
    }
  }, [token]);

  const refreshActive = useCallback(async () => {
    if (!active) return;
    try {
      const fresh = await getPersona(token, active.id);
      setActive(fresh);
      setPersonas((prev) => prev.map((p) => (p.id === fresh.id ? fresh : p)));
    } catch (err) {
      setError((err as Error).message);
    }
  }, [active, token]);

  useEffect(() => {
    (async () => {
      setLoading(true);
      const list = await refreshPersonas();
      if (list.length > 0) setActive(list[0]);
      setLoading(false);
    })();
  }, [refreshPersonas]);

  const handleCreate = async (name: string, description: string) => {
    try {
      const p = await createPersona(token, name, description);
      setPersonas((prev) => [...prev, p]);
      setActive(p);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const handleDelete = async (persona: Persona) => {
    if (!confirm(`Delete "${persona.name}" and all its samples?`)) return;
    try {
      await deletePersona(token, persona.id);
      const next = personas.filter((p) => p.id !== persona.id);
      setPersonas(next);
      setActive(next[0] ?? null);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return (
    <div className="app-shell">
      <PersonaSidebar
        personas={personas}
        active={active}
        onSelect={setActive}
        onCreate={handleCreate}
        onDelete={handleDelete}
      />
      <main className="main">
        {error && <div className="error">{error}</div>}
        {loading ? (
          <p className="empty">Loading…</p>
        ) : !active ? (
          <div className="panel">
            <h2>Create your first persona</h2>
            <p className="empty">
              A persona is a silo for one voice. Upload a handful of samples and Write2Style
              will learn to write like you.
            </p>
          </div>
        ) : (
          <>
            <div className="panel">
              <h2>{active.name}</h2>
              {active.description && <p className="empty">{active.description}</p>}
            </div>
            <div className="panel">
              <h3>Samples</h3>
              <SamplesPanel
                personaId={active.id}
                token={token}
                onUploaded={refreshActive}
              />
            </div>
            <div className="panel">
              <h3>Style DNA</h3>
              <StyleDnaView dna={active.style_dna} />
            </div>
            <div className="panel">
              <h3>Draft</h3>
              <Editor personaId={active.id} token={token} />
            </div>
          </>
        )}
      </main>
    </div>
  );
}

export default function App() {
  return (
    <>
      <SignedOut>
        <Landing />
      </SignedOut>
      <SignedIn>
        <Workspace />
      </SignedIn>
      <div style={{ position: "fixed", top: 16, right: 16 }}>
        <SignedIn>
          <UserButton />
        </SignedIn>
      </div>
    </>
  );
}
