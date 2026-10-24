
import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import "./App.css";

const API_URL = "";

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "end",
    });
  }, [messages, loading]);

  async function sendMessage(event) {
    event?.preventDefault();

    const text = input.trim();

    if (!text || loading) return;

    setInput("");
    setError("");

    setMessages((previous) => [
      ...previous,
      { role: "user", content: text },
    ]);

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

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Something went wrong. Please try again."
        );
      }

      if (!data.reply) {
        throw new Error("The AI returned an empty response.");
      }

      setConversationId(data.conversation_id);

      setMessages((previous) => [
        ...previous,
        { role: "assistant", content: data.reply },
      ]);
    } catch (err) {
      setError(
        err.message ||
        "Could not connect to the server. Check that FastAPI is running."
      );
    } finally {
      setLoading(false);
      textareaRef.current?.focus();
    }
  }

  function startNewChat() {
    setMessages([]);
    setConversationId(null);
    setInput("");
    setError("");
    setLoading(false);
    textareaRef.current?.focus();
  }

  function handleKeyDown(event) {
    if (
      event.key === "Enter" &&
      !event.shiftKey &&
      !event.nativeEvent.isComposing
    ) {
      event.preventDefault();
      sendMessage();
    }
  }

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">C</div>
          <div>
            <h2>Context AI</h2>
            <p>Think. Explore. Create.</p>
          </div>
        </div>

        <button
          className="new-chat-button"
          onClick={startNewChat}
          type="button"
        >
          <span>＋</span> New conversation
        </button>

        <p className="workspace-label">YOUR WORKSPACE</p>

        <div className="sidebar-note">
          <div className="sidebar-note-icon">✦</div>
          <div>
            <strong>AI Assistant</strong>
            <p>Context-aware chat</p>
          </div>
          <span className="status-dot" />
        </div>

        <div className="sidebar-bottom">
          <div className="provider-card">
            <div className="provider-icon">G</div>
            <div>
              <strong>Powered by Gemini</strong>
              <p>AI responses enabled</p>
            </div>
          </div>

          <div className="sidebar-footer">
            <span>●</span> Your conversations stay in context
          </div>
        </div>
      </aside>

      <main className="chat-panel">
        <header className="topbar">
          <div>
            <h1>Chat Assistant</h1>
            <p>Your ideas, connected.</p>
          </div>

          <div className="model-label">
            <span className="status-dot" />
            <span>Gemini</span>
            <span className="model-divider">/</span>
            <strong>3.8 Flash</strong>
          </div>
        </header>

        <section className="messages">
          {messages.length === 0 && (
            <div className="welcome">
              <div className="welcome-icon">✦</div>
              <p className="eyebrow">YOUR AI ASSISTANT</p>
              <h2>What would you like to explore?</h2>
              <p className="welcome-description">
                Start a conversation. Your assistant can use
                earlier messages to keep the discussion in context.
              </p>

              <div className="suggestions">
                <button
                  type="button"
                  onClick={() =>
                    setInput("Explain context-aware chatbots simply.")
                  }
                >
                  <span className="suggestion-icon">✧</span>
                  <strong>Learn something</strong>
                  <span>Understand context-aware AI</span>
                </button>

                <button
                  type="button"
                  onClick={() =>
                    setInput("Help me plan my next programming project.")
                  }
                >
                  <span className="suggestion-icon">⌘</span>
                  <strong>Build a project</strong>
                  <span>Explore ideas and solutions</span>
                </button>
              </div>
            </div>
          )}

          {messages.map((message, index) => (
            <article
              className={`message-row ${message.role}`}
              key={`${index}-${message.role}`}
            >
              <div className="avatar">
                {message.role === "user" ? "Y" : "✦"}
              </div>

              <div className="message-content">
                <div className="message-author">
                  {message.role === "user" ? "You" : "Context AI"}
                </div>

                <div className="message-text">
                  {message.role === "assistant" ? (
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        a: ({ children, ...props }) => (
                          <a
                            {...props}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            {children}
                          </a>
                        ),
                        pre: ({ children }) => (
                          <pre className="markdown-code-block">
                            {children}
                          </pre>
                        ),
                        code: ({ children, className, ...props }) => (
                          <code
                            className={
                              className
                                ? `markdown-inline-code ${className}`
                                : "markdown-inline-code"
                            }
                            {...props}
                          >
                            {children}
                          </code>
                        ),
                      }}
                    >
                      {message.content}
                    </ReactMarkdown>
                  ) : (
                    message.content
                  )}
                </div>
              </div>
            </article>
          ))}

          {loading && (
            <article className="message-row assistant">
              <div className="avatar">✦</div>

              <div className="message-content">
                <div className="message-author">Context AI</div>
                <div className="typing">
                  <span />
                  <span />
                  <span />
                </div>
              </div>
            </article>
          )}

          <div ref={messagesEndRef} />
        </section>

        <footer className="composer-area">
          {error && (
            <div className="error-message" role="alert">
              {error}
            </div>
          )}

          <form className="composer" onSubmit={sendMessage}>
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Message Context AI..."
              rows={1}
              maxLength={4000}
              disabled={loading}
            />

            <button
              className="send-button"
              type="submit"
              disabled={!input.trim() || loading}
              aria-label="Send message"
              title="Send message"
            >
              {loading ? "···" : "➤"}
            </button>
          </form>

          <p className="composer-hint">
            Enter to send · Shift + Enter for a new line
            <span>AI can make mistakes. Check important information.</span>
          </p>
        </footer>
      </main>
    </div>
  );
}

export default App;
