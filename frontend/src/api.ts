const BASE_URL = "http://localhost:8000"

export type AnswerMap = Record<string, string>;

interface VoteRequest {
  question: string;
  answers: AnswerMap;
  winner: string;
  feedback: string;
}

export async function askQuestion(question: string): Promise<AnswerMap> {
  const res = await fetch(`${BASE_URL}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) throw new Error(`ask failed: ${res.status}`);
  return res.json() as Promise<AnswerMap>;
}

export async function submitVote(question: string, answers: AnswerMap, winner: string, feedback: string): Promise<{ status: string }> {
  const body: VoteRequest = { question, answers, winner, feedback }
  const res = await fetch(`${BASE_URL}/vote`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`vote failed: ${res.status}`);
  return res.json();
}