import { useState, useRef, useEffect } from 'react'
import { useChat } from './hooks/useChat'
import { Message } from './components/Message'

const THEMES = ["light", "dark", "corporate", "bumblebee", "cyberpunk", "retro", "valentine"];

function App() {
  const { messages, loading, sendMessage } = useChat();
  const [input, setInput] = useState("");
  const [theme, setTheme] = useState("dark");
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll to bottom of list logic
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  // Focus input on load
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    sendMessage(input);
    setInput("");
  };

  return (
    <div className="h-screen w-full flex flex-col bg-base-100 text-base-content font-sans antialiased" data-theme={theme}>

      {/* 1. Fixed Top Bar (Minimal) */}
      <div className="sticky top-0 z-20 bg-base-100/80 backdrop-blur border-b border-base-200">
        <div className="flex items-center justify-between px-4 py-2 max-w-3xl mx-auto w-full">
          <div className="font-bold text-lg opacity-80">FIH Rules AI</div>

          {/* Theme Picker */}
          <div className="dropdown dropdown-end">
            <div tabIndex={0} role="button" className="btn btn-xs btn-ghost font-normal opacity-50 hover:opacity-100">
              {theme}
            </div>
            <ul tabIndex={0} className="dropdown-content z-[1] menu p-2 shadow-lg bg-base-100 rounded-box w-32 border border-base-200">
              {THEMES.map(t => (
                <li key={t}><a onClick={() => setTheme(t)} className={theme === t ? "active" : ""}>{t}</a></li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* 2. Scrollable Chat Area */}
      <div className="flex-1 overflow-y-auto">
        <div className="flex flex-col pb-32">

          {/* Empty State / Welcome */}
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center min-h-[60vh] px-4 text-center">
              <div className="w-16 h-16 bg-primary text-primary-content rounded-xl flex items-center justify-center mb-6 text-3xl shadow-lg shadow-primary/20">
                🏑
              </div>
              <h1 className="text-2xl font-bold mb-2">FIH Rules Expert</h1>
              <p className="opacity-60 max-w-md mb-8">
                I can answer any question about International Hockey Rules (Indoor, Outdoor, Hockey5s). I cite official documents.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 w-full max-w-lg">
                <button onClick={() => sendMessage("How long is a yellow card?")} className="btn btn-outline btn-sm normal-case justify-start">
                  ⏱️ Duration of a yellow card?
                </button>
                <button onClick={() => sendMessage("Can I play the ball with my hand?")} className="btn btn-outline btn-sm normal-case justify-start">
                  ✋ Use of hands / body?
                </button>
                <button onClick={() => sendMessage("What happens with a deliberate foul in circle?")} className="btn btn-outline btn-sm normal-case justify-start">
                  ⭕ Foul in the circle?
                </button>
                <button onClick={() => sendMessage("Explain the danger rule")} className="btn btn-outline btn-sm normal-case justify-start">
                  ⚠️ Danger rule explained
                </button>
              </div>
            </div>
          )}

          {/* Message List */}
          {messages.map((msg, idx) => (
            <Message
              key={idx}
              role={msg.role}
              content={msg.content}
              debug={msg.debug}
              animate={idx === messages.length - 1} // Only animate the newest message
            />
          ))}

          {/* Loading Indicator (as a skeleton message) */}
          {loading && (
            <Message role="assistant" content="" />
          )}

          <div ref={bottomRef} />
        </div>
      </div>

      {/* 3. Fixed Bottom Input Area */}
      <div className="fixed bottom-0 left-0 w-full bg-gradient-to-t from-base-100 via-base-100 to-transparent pt-10 pb-6 px-4 z-10">
        <div className="max-w-3xl mx-auto">
          <form onSubmit={handleSubmit} className="relative">
            <input
              ref={inputRef}
              type="text"
              placeholder="Ask a question..."
              className="input input-lg input-bordered w-full pr-12 shadow-lg bg-base-100 focus:outline-none focus:ring-2 focus:ring-primary/20 text-base"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={loading}
            />
            <button
              type="submit"
              className={`absolute right-2 top-2 btn btn-square btn-sm btn-primary ${!input.trim() ? 'btn-disabled opacity-50' : ''}`}
              disabled={loading || !input.trim()}
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4">
                <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 10.5 12 3m0 0 7.5 7.5M12 3v18" />
              </svg>
            </button>
          </form>
          <div className="text-center mt-2 text-xs opacity-40">
            AI can make mistakes. Always check official FIH documents.
          </div>
        </div>
      </div>

    </div>
  )
}

export default App
