import { useState } from 'react';

const API_BASE = import.meta.env.DEV ? 'http://localhost:8000' : '';
const API_KEY = import.meta.env.VITE_API_KEY || 'dev-secret-key';

export function useChat() {
    const [messages, setMessages] = useState([]);
    const [history, setHistory] = useState([]); // For API context
    const [loading, setLoading] = useState(false);

    const sendMessage = async (text) => {
        // Optimistic UI
        const userMsg = { role: 'user', content: text };
        setMessages((prev) => [...prev, userMsg]);
        setHistory((prev) => [...prev, userMsg]);
        setLoading(true);

        try {
            const response = await fetch(`${API_BASE}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': API_KEY,
                },
                body: JSON.stringify({
                    query: text,
                    history: history, // Send accumulated history
                }),
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();

            // Update state with answer AND debug info attached to the message
            const botMsg = {
                role: 'assistant',
                content: data.answer,
                debug: data // Store full response (variant, standalone_query, sources)
            };

            setMessages((prev) => [...prev, botMsg]);
            setHistory((prev) => [...prev, { role: 'assistant', content: data.answer }]); // History only needs content

        } catch (error) {
            console.error("Chat error:", error);
            setMessages((prev) => [...prev, { role: 'error', content: "Sorry, I couldn't connect to the rulebook." }]);
        } finally {
            setLoading(false);
        }
    };

    return { messages, loading, sendMessage };
}
