import { useState, type ChangeEvent } from 'react';
import { askQuestion, submitVote, type AnswerMap } from './api';
import ReactMarkdown from "react-markdown";
import remarkGfm from 'remark-gfm';
import './App.css';

function App() {
  const [question, setQuestion] = useState<string>("");
  const [answers, setAnswers] = useState<AnswerMap | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [winner, setWinner] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string>("");
  const [submitted, setSubmitted] = useState<boolean>(false);

  async function handleAsk(e: ChangeEvent<HTMLFormElement>): Promise<void> {
    e.preventDefault();
    setLoading(true);
    setAnswers(null);
    setWinner(null);
    setSubmitted(false);
    try {
      const result = await askQuestion(question);
      setAnswers(result);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  async function handleVote(): Promise<void> {
    if (!winner || !answers) return;
    await submitVote(question, answers, winner, feedback);
    setSubmitted(true);
  }

  return (
    <div style={{ maxWidth: 900, margin: "2rem auto", fontFamily: "sans-serif" }}>
      <h1>PrimeAIT</h1>

      <form onSubmit={handleAsk}>
        <input 
          type="text"
          value={question}
          onChange={(e: ChangeEvent<HTMLInputElement>) => setQuestion(e.target.value)}
          placeholder="Ask something..."
          style={{ width: "70%", padding: "0.5rem", marginRight: "1rem" }} 
        />
        <button type="submit" disabled={loading || !question.trim()} style={{ height: 30, width: 50 }}>
          {loading ? "Asking..." : "Ask"}
        </button>
      </form>

      {answers && (
         <>
          <div style={{ display: "flex", gap: "1rem", marginTop: "1.5rem" }}>
            {Object.entries(answers).map(([model, text]) => (
              <div
                key={model}
                onClick={() => setWinner(model)}
                style={{
                  flex: 1,
                  padding: "1rem",
                  border: winner === model ? "2px solid #4caf50" : "1px solid #ccc",
                  borderRadius: 8,
                  cursor: "pointer",
                }}
              >
                <h3>{model}</h3>
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{text}</ReactMarkdown>
              </div>
            ))}
          </div>

          {winner && !submitted && (
            <div style={{ marginTop: "1rem" }}>
              <textarea
                value={feedback}
                onChange={(e: ChangeEvent<HTMLTextAreaElement>) => setFeedback(e.target.value)}
                placeholder="Why? (optional)"
                style={{ width: "100%", minHeight: 60 }}
              />
              <button onClick={handleVote}>Submit vote for {winner}</button>
            </div>
          )}

          {submitted && <p>Vote recorded.</p>}
        </>
      )}
    </div>
  )
}

export default App
