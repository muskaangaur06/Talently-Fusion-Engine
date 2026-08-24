import { Loader2, Send } from "lucide-react";
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import api from "../services/api.js";

export default function ChatAssistant({ jobId, resumeSkills, experienceYears }) {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: resumeSkills?.length
        ? "Ask me anything about this role, required skills, salary, or why you're a fit based on your resume."
        : "Ask me anything about this role, required skills, or salary.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const send = async (e) => {
    e.preventDefault();
    const text = input.trim();
    if (!text) return;

    const nextMessages = [...messages, { role: "user", content: text }];
    setMessages(nextMessages);
    setInput("");
    setLoading(true);

    try {
      const data = await api.chat({
        message: text,
        job_id: jobId,
        history: nextMessages,
        resume_skills: resumeSkills || [],
        experience_years: experienceYears ?? null,
      });
      setMessages([...nextMessages, { role: "assistant", content: data.reply }]);
    } catch {
      setMessages([...nextMessages, { role: "assistant", content: "Something went wrong. Please try again." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-full flex-col rounded-2xl border border-line bg-card">
      <div className="border-b border-line px-4 py-3">
        <h3 className="text-sm font-semibold text-ink">Career Copilot</h3>
      </div>
      <div className="flex-1 space-y-3 overflow-y-auto p-4" style={{ maxHeight: 400 }}>
        {messages.map((m, i) => (
          <div key={i} className={`text-sm ${m.role === "user" ? "text-right" : ""}`}>
            <div
              className={`inline-block max-w-[85%] rounded-lg px-3 py-2 text-left ${
                m.role === "user" ? "bg-primary text-white" : "bg-paper text-ink"
              }`}
            >
              <ReactMarkdown>{m.content}</ReactMarkdown>
            </div>
          </div>
        ))}
        {loading && <Loader2 className="animate-spin text-primary" size={16} />}
      </div>
      <form onSubmit={send} className="flex gap-2 border-t border-line p-3">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question..."
          className="flex-1 rounded border border-line px-3 py-1.5 text-sm outline-none focus:border-primary"
        />
        <button type="submit" className="rounded bg-primary p-2 text-white hover:bg-primary-deep">
          <Send size={14} />
        </button>
      </form>
    </div>
  );
}
