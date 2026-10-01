import { useState, useEffect, type ChangeEvent } from 'react';
import ReactMarkdown from "react-markdown";
import remarkGfm from 'remark-gfm';
import Sidebar from './Sidebar';
import { type Thread, type Round, type AnswerMap, listThreads, createThread, getMessages, askQuestion, submitVote  } from './api';
import './App.css';

function App() {
  const [threads, setThreads] = useState<Thread[]>([]);
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Round[]>([]);

  const [question, setQuestion] = useState<string>("");
  const [answers, setAnswers] = useState<AnswerMap | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [winner, setWinner] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string>("");

  useEffect(() => {
    listThreads().then((t) => {
      setThreads(t);
      if (t.length > 0) setActiveThreadId(t[0].id);
    });
  }, []);

  async function handleSelectThread(thread_id: string): Promise<void> {
    setActiveThreadId(thread_id);
    const messages = await getMessages(thread_id);
    setMessages(messages);
  }

  async function handleNewThread(): Promise<void> {
    const thread = await createThread();
    setThreads((prev) => [thread, ...prev]);
    setActiveThreadId(thread.id);
  }

  async function handleAsk(e: ChangeEvent<HTMLFormElement>): Promise<void> {
    e.preventDefault();
    if (!activeThreadId) return;
    setLoading(true);
    setAnswers(null);
    setWinner(null);
    try {
      const result = await askQuestion(activeThreadId, question);
      setAnswers(result);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
      setQuestion("");
    }
  }

  async function handleVote(): Promise<void> {
    if (!activeThreadId || !winner || !answers) return;
    await submitVote(question, answers, winner, activeThreadId, feedback);
    const updated = await getMessages(activeThreadId);
    setMessages(updated);
    setWinner(null);
    setAnswers(null);
    setQuestion("");
    setFeedback("");
  }

  return ( 
    <div style={{ display: "flex" }}>
      <Sidebar
        threads={threads}
        numMessages={messages.length}
        activeThreadId={activeThreadId}
        onSelectThread={handleSelectThread}
        onNewThread={handleNewThread}
      />

      <div style={{ display: "flex", maxWidth: 900, margin: "1rem", fontFamily: "sans-serif", justifyContent: "start", flexDirection: "column" }}>
        <h1>PrimeAIT</h1>

        {!activeThreadId ? (
          <p>Start a new conversation to begin.</p>
        ) : (
          <>
            {messages.map((r, i) => (
              <div key={i} style={{ marginBottom: "1.5rem", paddingBottom: "1rem", borderBottom: "1px solid #eee" }}>
                <p style={{ fontWeight: 600 }}>{r.question}</p>
                <div style={{ display: "flex", gap: "1rem" }}>
                  {Object.entries(r.answers).map(([model, text]) => (
                    <div
                      key={model}
                      style={{
                        flex: 1,
                        padding: "0.75rem",
                        border: model === r.winner ? "2px solid #4caf50" : "1px solid #eee",
                        borderRadius: 8,
                      }}
                    >
                      <strong>{model}{model === r.winner ? " 🏆" : ""}</strong>
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{text}</ReactMarkdown>
                    </div>
                  ))}
                </div>
                {r.feedback && <p style={{ fontStyle: "italic", marginTop: "0.5rem" }}>Feedback: {r.feedback}</p>}
              </div>
            ))}

            {answers && (
              <>
                <div style={{ display: "flex", gap: "1rem", marginTop: "1rem" }}>
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

                {winner && (
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
              </>
            )
            }
          </>
        )}
        <form onSubmit={handleAsk}>
          <input
            value={question}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setQuestion(e.target.value)}
            placeholder="Ask something..."
            style={{ width: "500px", padding: "0.5rem" }}
          />
          <button type="submit" disabled={loading || !question.trim()}>
            {loading ? "Asking..." : "Ask"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default App
