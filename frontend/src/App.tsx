import { useState } from "react";
import "./App.css";

type Message = {
  role: "user" | "assistant";
  content: string;
};

type Source = {
  filename: string;
  page: number;
};

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState("");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [sources, setSources] = useState<Source[]>([]);
  const [chatHistory, setChatHistory] = useState<Message[]>([]);

  const API_URL =
    import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

  const handleUpload = async () => {
    if (!file) {
      setMessage("Please select a PDF first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      setMessage("Uploading...");

      const response = await fetch(`${API_URL}/upload`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Upload failed");
      }

      setMessage(
        `${data.filename} uploaded successfully! ${data.chunks} chunks created.`
      );

      setChatHistory([]);
      setAnswer("");
      setSources([]);
    } catch (error) {
      console.error(error);
      setMessage("Upload failed. Make sure the backend is running.");
    }
  };

  const handleChat = async () => {
    if (!question.trim() || loading) return;

    const currentQuestion = question.trim();

    try {
      setLoading(true);
      setAnswer("");

      const response = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: currentQuestion,
          history: chatHistory,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Chat request failed");
      }

      setAnswer(data.answer);
      setSources(data.sources || []);

      setChatHistory((previousHistory) => [
        ...previousHistory,
        {
          role: "user",
          content: currentQuestion,
        },
        {
          role: "assistant",
          content: data.answer,
        },
      ]);

      setQuestion("");
    } catch (error) {
      console.error(error);
      setAnswer(
        "Something went wrong. Please make sure the backend is running."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <h1>DocuChat</h1>
        <p>Chat with your PDF documents using AI</p>
      </header>

      <main className="main-content">
        <section className="upload-panel">
          <h2>Upload Document</h2>

          <p>Select a PDF file to begin.</p>

          <input
            type="file"
            accept=".pdf"
            onChange={(e) => {
              setFile(e.target.files?.[0] || null);
              setMessage("");
            }}
          />

          <button onClick={handleUpload}>Upload PDF</button>

          {message && <p>{message}</p>}
        </section>

        <section className="chat-panel">
          <h2>Chat</h2>

          <div className="chat-box">
            {chatHistory.length === 0 && !loading && (
              <p className="welcome-message">
                Upload a PDF and ask a question about it.
              </p>
            )}

            {chatHistory.map((chat, index) => (
              <div
                key={index}
                className={
                  chat.role === "user"
                    ? "user-message"
                    : "assistant-message"
                }
              >
                <strong>
                  {chat.role === "user" ? "You" : "DocuChat"}
                </strong>

                <p>{chat.content}</p>
              </div>
            ))}

            {loading && <p>Thinking...</p>}

            {answer && chatHistory.length === 0 && (
              <div className="assistant-message">
                <strong>DocuChat</strong>
                <p>{answer}</p>
              </div>
            )}

            {sources.length > 0 && (
              <div className="sources">
                <strong>Sources</strong>

                <ul>
                  {sources.map((source, index) => (
                    <li key={index}>
                      {source.filename} — Page {source.page}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          <div className="chat-input">
            <input
              type="text"
              value={question}
              placeholder="Ask a question about your document..."
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  handleChat();
                }
              }}
            />

            <button onClick={handleChat} disabled={loading}>
              {loading ? "Thinking..." : "Send"}
            </button>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;