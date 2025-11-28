import { useState, useRef, useEffect, FormEvent, ChangeEvent } from "react";
import ReactMarkdown from "react-markdown";
import "./ChatAssistant.css";

// Use relative path for production (nginx proxy) or localhost for development
const API_BASE_URL = import.meta.env.PROD
  ? "/api"
  : "http://localhost:8000/api";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface ChatResponse {
  response: string;
}

interface ChatAssistantProps {
  memberId?: number;
}

function ChatAssistant({ memberId }: ChatAssistantProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (isOpen) {
      // Small delay to ensure the modal is rendered before focusing
      setTimeout(() => {
        inputRef.current?.focus();
      }, 0);
    }
  }, [isOpen]);

  const toggleChat = () => {
    setIsOpen(!isOpen);
  };

  const closeChat = () => {
    setIsOpen(false);
  };

  const sendMessage = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: input,
          user_id: memberId || null,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to get response");
      }

      const data: ChatResponse = await response.json();
      const assistantMessage: Message = {
        role: "assistant",
        content: data.response,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: Message = {
        role: "assistant",
        content: "Sorry, I encountered an error. Please try again.",
      };
      setMessages((prev) => [...prev, errorMessage]);
      console.error("Chat error:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    setInput(e.target.value);
  };

  return (
    <>
      {/* Floating Chat Button */}
      <button
        className="chat-assistant-button"
        onClick={toggleChat}
        aria-label="Open chat assistant"
      >
        {isOpen ? (
          <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" />
          </svg>
        ) : (
          <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z" />
          </svg>
        )}
      </button>

      {/* Chat Modal */}
      {isOpen && (
        <>
          <div className="chat-assistant-overlay" onClick={closeChat} />
          <div className="chat-assistant-modal">
            <div className="chat-assistant-header">
              <div className="chat-assistant-header-info">
                <h2>Chat Assistant</h2>
                <p>Powered by CrewAI & AWS Bedrock</p>
              </div>
              <button
                className="chat-assistant-close"
                onClick={closeChat}
                aria-label="Close chat"
              >
                <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path
                    d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"
                    fill="currentColor"
                  />
                </svg>
              </button>
            </div>

            <div className="chat-assistant-messages">
              {messages.length === 0 && (
                <div className="chat-assistant-welcome">
                  <p>👋 Hello! I'm your AI assistant.</p>
                  <p>How can I help you today?</p>
                  {memberId ? (
                    <p className="chat-assistant-personalized-note">
                      ✓ You're logged in! I can help you with your profile,
                      benefits, and coverage details.
                    </p>
                  ) : (
                    <p className="chat-assistant-login-note">
                      💡 Log in to ask about your personal profile and benefits.
                    </p>
                  )}
                </div>
              )}
              {messages.map((msg, index) => (
                <div
                  key={index}
                  className={`chat-assistant-message ${msg.role}`}
                >
                  <div className="chat-assistant-message-content">
                    {msg.role === "assistant" ? (
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    ) : (
                      msg.content
                    )}
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="chat-assistant-message assistant">
                  <div className="chat-assistant-message-content chat-assistant-loading">
                    <span className="dot"></span>
                    <span className="dot"></span>
                    <span className="dot"></span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            <form className="chat-assistant-input" onSubmit={sendMessage}>
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={handleInputChange}
                placeholder="Type your message..."
                disabled={isLoading}
              />
              <button type="submit" disabled={isLoading || !input.trim()}>
                Send
              </button>
            </form>
          </div>
        </>
      )}
    </>
  );
}

export default ChatAssistant;
