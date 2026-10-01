const BASE_URL = "http://localhost:8000"

export type AnswerMap = Record<string, string>;

export interface Thread {
  id: string;
  title: string;
  created_at: string;
}

export interface Round {
  question: string;
  answers: AnswerMap;
  winner: string;
  feedback: string | null;
  created_at: string;
}

export async function listThreads(): Promise<Thread[]> {
  const res = await fetch(`${BASE_URL}/threads`);
  if (!res.ok) throw new Error(`listThreads failed: ${res.status}`);
  return res.json();
}

export async function createThread(title?: string): Promise<Thread> {
  const res = await fetch(`${BASE_URL}/threads`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({title: title ?? null}),
  });
  if (!res.ok) throw new Error(`createThread failed: ${res.status}`);
  return res.json();
} 

export async function getMessages(threadId: string): Promise<Round[]> {
  const res = await fetch(`${BASE_URL}/threads/${threadId}/messages`);
  if (!res.ok) throw new Error(`getMessages failed: ${res.status}`);
  return res.json();
}

export async function askQuestion(threadId: string, question: string): Promise<AnswerMap> {
  const res = await fetch(`${BASE_URL}/threads/${threadId}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) throw new Error (`ask failed: ${res.status}`);
  return res.json();
}

export async function submitVote(question: string, answers: AnswerMap, winner: string, threadId: string, feedback: string): Promise<{ status: string }> {
  const res = await fetch(`${BASE_URL}/threads/${threadId}/vote`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, answers, winner, feedback }),
  });
  if (!res.ok) throw new Error(`vote failed: ${res.status}`);
  return res.json();  
}