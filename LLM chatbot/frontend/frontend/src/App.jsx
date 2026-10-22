
import { useState, useEffect } from "react";
import "./App.css";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [message, setMessage] = useState("");
  const [chat, setChat] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const [conversationId, setConversationId] = useState(() => {
    const savedId = localStorage.getItem("conversation_id");
    return savedId ? Number(savedId) : null;
  });

  const [conversations, setConversations] = useState([]);

  // Load the list of saved conversations.
  async function loadConversations() {
    try {
      const response = await fetch(`${API_URL}/conversations`);

      if (!response.ok) {
        throw new Error("Could not load conversations.");
      }

      const data = await response.json();
      setConversations(data);
    } catch (error) {
      console.error("Failed to load conversations:", error);
    }
  }

  useEffect(() => {
    loadConversations();
  }, []);

  // Restore the selected conversation's messages.
  useEffect(() => {
    if (!conversationId) {
      setChat([]);
      return;
    }

    let cancelled = false;

    async function loadHistory() {
      try {
        const response = await fetch(
          `${API_URL}/conversations/${conversationId}`
        );

        if (!response.ok) {
          throw new Error("Could not load conversation history.");
        }

        const data = await response.json();

        if (!cancelled) {
          setChat(data.messages);
        }
      } catch (error) {
        if (!cancelled) {
          console.error("Failed to restore conversation:", error);
        }
      }
    }

    loadHistory();

    return () => {
      cancelled = true;
    };
  }, [conversationId]);

  // Start a separate conversation without deleting old chats.
  function newChat() {
    setConversationId(null);
    localStorage.removeItem("conversation_id");
    setChat([]);
    setMessage("");
  }

  // Switch to a saved conversation.
  function selectConversation(id) {
    setConversationId(id);
    localStorage.setItem("conversation_id", String(id));
    setMessage("");
  }

  async function sendMessage(e) {
    e.preventDefault();

    const text = message.trim();

    if (!text || loading) return;

    setChat((prev) => [...prev, { role: "user", text }]);
    setMessage("");
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: text,
          conversation_id: conversationId,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail || "The server could not answer your request."
        );
      }

      const data = await response.json();

      // Remember which conversation is active.
      setConversationId(data.conversation_id);
      localStorage.setItem(
        "conversation_id",
        String(data.conversation_id)
      );

      setChat((prev) => [
        ...prev,
        { role: "assistant", text: data.reply },
      ]);

      // Refresh the sidebar to include newly created conversations.
      await loadConversations();
    } catch (error) {
      setChat((prev) => [
        ...prev,
        {
          role: "assistant",
          text: `Error: ${error.message}. Check that your backend is running.`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className={`app ${sidebarOpen ? "" : "sidebar-collapsed"}`}>
      <aside className="sidebar">
        <div className="sidebar-header">
          {sidebarOpen && <h2>My Chats</h2>}

          <button
            type="button"
            className="icon-button"
            onClick={() => setSidebarOpen((open) => !open)}
            title={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
            aria-label={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
          >
            ☰
          </button>
        </div>

        {sidebarOpen && (
          <>
            <button
              type="button"
              className="new-chat-button"
              onClick={newChat}
            >
              + New Chat
            </button>

            <div className="conversation-list">
              {conversations.length === 0 && (
                <p className="sidebar-empty">No saved conversations yet.</p>
              )}

              {conversations.map((conversation) => (
                <button
                  type="button"
                  key={conversation.id}
                  className={`conversation-item ${
                    conversation.id === conversationId ? "active" : ""
                  }`}
                  onClick={() => selectConversation(conversation.id)}
                  title={conversation.title}
                >
                  {conversation.title || "New conversation"}
                </button>
              ))}
            </div>
          </>
        )}
      </aside>

      <section className="chat-panel">
        <header className="header">
          <h1>My AI Chat</h1>
          <p>Powered by Gemini</p>
        </header>

        <section className="messages">
          {chat.length === 0 && (
            <p className="empty">
              Ask me anything to get started.
            </p>
          )}

          {chat.map((item, index) => (
            <div
              key={index}
              className={`message ${item.role}`}
            >
              <strong>
                {item.role === "user" ? "You" : "Gemini"}
              </strong>
              <div className="message-content">
  {item.role === "assistant" ? (
    <ReactMarkdown remarkPlugins={[remarkGfm]}>
      {item.text}
    </ReactMarkdown>
  ) : (
    <p>{item.text}</p>
  )}
</div>
            </div>
          ))}

          {loading && (
            <p className="loading">Gemini is thinking...</p>
          )}
        </section>

        <form className="input-area" onSubmit={sendMessage}>
          <input
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Type your message..."
            disabled={loading}
          />

          <button
            type="submit"
            disabled={loading || !message.trim()}
          >
            {loading ? "Sending..." : "Send"}
          </button>
        </form>
      </section>
    </main>
  );
}

export default App;
