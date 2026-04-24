const API_URL = import.meta.env.VITE_API_URL;

if (!API_URL) {
  throw new Error("Missing VITE_API_URL");
}

export type Persona = {
  id: string;
  name: string;
  description: string;
  style_dna: Record<string, unknown> | null;
  sample_count: number;
};

export type Sample = {
  id: string;
  filename: string;
  content_type: string;
  chunk_count: number;
  char_count: number;
};

type GetToken = () => Promise<string | null>;

async function authed(getToken: GetToken, path: string, init: RequestInit = {}): Promise<Response> {
  const token = await getToken();
  const headers = new Headers(init.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const res = await fetch(`${API_URL}${path}`, { ...init, headers });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  return res;
}

export async function listPersonas(getToken: GetToken): Promise<Persona[]> {
  const res = await authed(getToken, "/api/personas");
  return res.json();
}

export async function createPersona(
  getToken: GetToken,
  name: string,
  description: string
): Promise<Persona> {
  const res = await authed(getToken, "/api/personas", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, description }),
  });
  return res.json();
}

export async function getPersona(getToken: GetToken, personaId: string): Promise<Persona> {
  const res = await authed(getToken, `/api/personas/${personaId}`);
  return res.json();
}

export async function deletePersona(getToken: GetToken, personaId: string): Promise<void> {
  await authed(getToken, `/api/personas/${personaId}`, { method: "DELETE" });
}

export async function listSamples(getToken: GetToken, personaId: string): Promise<Sample[]> {
  const res = await authed(getToken, `/api/personas/${personaId}/samples`);
  return res.json();
}

export async function uploadSample(
  getToken: GetToken,
  personaId: string,
  file: File
): Promise<Sample> {
  const form = new FormData();
  form.append("file", file);
  const res = await authed(getToken, `/api/personas/${personaId}/samples`, {
    method: "POST",
    body: form,
  });
  return res.json();
}

export async function streamGenerate(
  getToken: GetToken,
  personaId: string,
  prompt: string,
  onChunk: (delta: string) => void
): Promise<void> {
  const res = await authed(getToken, `/api/personas/${personaId}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });
  if (!res.body) throw new Error("No response body");

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    if (value) onChunk(decoder.decode(value, { stream: true }));
  }
}
