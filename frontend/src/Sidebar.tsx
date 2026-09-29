import { type Thread } from "./api";

interface SidebarProps {
  threads: Thread[],
  activeThreadId: string | null,
  onSelectThread: (id: string) => void;
  onNewThread: () => void;
}

export default function Sidebar({ threads, activeThreadId, onSelectThread, onNewThread }: SidebarProps) {
  return (
    <div style={{ width: 240, borderRight: "1px solid #ddd", padding: "1rem", height: "100vh", boxSizing: "border-box"}}>
      <button onClick={onNewThread} style={{ width: "100%", padding: "0.5rem", marginBottom: "1rem" }}>
        + New Conversation
      </button>
      {threads.map((t) => (
        <div
          key={t.id}
          onClick={() => onSelectThread(t.id)}
          style={{
            padding: "0.5rem",
            marginBottom: "0.25rem",
            borderRadius: 6,
            cursor: "pointer",
            background: t.id === activeThreadId ? "#e8f0fe" : "transparent",
            fontWeight: t.id === activeThreadId ? 600 : 400,
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
        >
          {t.title}
        </div>
      ))}
    </div>
  );
}
