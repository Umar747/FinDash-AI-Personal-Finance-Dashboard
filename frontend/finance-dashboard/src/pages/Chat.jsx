import React, { useState, useEffect, useRef } from 'react';
import { agentAPI } from '../services/api';
import './Chat.css';

const Chat = () => {
    const [messages, setMessages] = useState([
        { role: 'assistant', content: 'Hello! I am your AI Finance Assistant. How can I help you manage your transactions today?' }
    ]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(scrollToBottom, [messages]);

    const handleSend = async (e) => {
        e.preventDefault();
        if (!input.trim()) return;

        const userMessage = { role: 'user', content: input };
        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            const response = await agentAPI.ask(input);
            
            setMessages(prev => [...prev, { 
                role: 'assistant', 
                content: response.data.response 
            }]);
        } catch (error) {
            console.error("Agent Error:", error);
            setMessages(prev => [...prev, { 
                role: 'assistant', 
                content: 'Sorry, I encountered an error communicating with the local Llama agent. Make sure the Flask server and Ollama are running.' 
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="chat-container">
            <div className="messages-list">
                {messages.map((msg, index) => (
                    <div key={index} className={`message-bubble ${msg.role}`}>
                        <div className="message-content">
                            <strong>{msg.role === 'user' ? 'You' : 'Llama Agent'}:</strong>
                            <p>{msg.content}</p>
                        </div>
                    </div>
                ))}
                {isLoading && (
                    <div className="message-bubble assistant loading">
                        <div className="dot-typing"></div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>
            <form className="chat-input-area" onSubmit={handleSend}>
                <input 
                    type="text" 
                    value={input} 
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="e.g., 'What were my last 5 transactions?'"
                    disabled={isLoading}
                />
                <button type="submit" disabled={isLoading || !input.trim()}>
                    {isLoading ? 'Thinking...' : 'Send'}
                </button>
            </form>
        </div>
    );
};

export default Chat;