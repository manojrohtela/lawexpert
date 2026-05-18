const BASE_URL = "http://localhost:8001";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatResponse {
  intent: { needs_section: boolean; needs_case: boolean };
  answer: string;
  law_hits: Array<{ score: number; payload: Record<string, unknown> }>;
  case_hits: Array<{ score: number; payload: Record<string, unknown> }>;
}

export interface StatsResponse {
  total_cases_processed: number;
  total_laws_indexed: number;
  trending_topics: string[];
  top_laws: string[];
  updated_at: string;
}

export async function sendChat(
  query: string,
  history: ChatMessage[],
  top_k = 5
): Promise<ChatResponse> {
  const res = await fetch(`${BASE_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, history, top_k }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function fetchStats(): Promise<StatsResponse> {
  const res = await fetch(`${BASE_URL}/stats`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function fetchSuggestions(): Promise<string[]> {
  const res = await fetch(`${BASE_URL}/suggestions`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();
  return data.suggestions ?? [];
}
