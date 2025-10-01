import React, { useState, useEffect, useRef } from 'react';
import './App.css';

const App = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState('');
  const [analytics, setAnalytics] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    // Generate session ID
    setSessionId('session_' + Math.random().toString(36).substr(2, 9));
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const sendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage = {
      id: Date.now(),
      text: inputMessage,
      sender: 'user',
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: inputMessage,
          session_id: sessionId
        })
      });

      const data = await response.json();
      
      const botMessage = {
        id: Date.now() + 1,
        text: data.response,
        sender: 'bot',
        timestamp: new Date().toLocaleTimeString(),
        metadata: {
          intent: data.intent,
          sentiment: data.sentiment,
          responseTime: data.response_time
        }
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        id: Date.now() + 1,
        text: 'Sorry, I encountered an error. Please try again.',
        sender: 'bot',
        timestamp: new Date().toLocaleTimeString(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const loadAnalytics = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/analytics/conversations');
      const data = await response.json();
      setAnalytics(data);
    } catch (error) {
      console.error('Error loading analytics:', error);
    }
  };

  return (
    <div className="app">
      <div className="chat-container">
        <div className="chat-header">
          <h1>Dynamic AI Chatbot</h1>
          <button onClick={loadAnalytics} className="analytics-btn">
            View Analytics
          </button>
        </div>

        <div className="messages-container">
          {messages.map((message) => (
            <div key={message.id} className={`message ${message.sender}`}>
              <div className="message-content">
                <p>{message.text}</p>
                <span className="timestamp">{message.timestamp}</span>
                {message.metadata && (
                  <div className="metadata">
                    <small>
                      Intent: {message.metadata.intent.intent} | 
                      Sentiment: {message.metadata.sentiment.label} | 
                      Response: {message.metadata.responseTime.toFixed(2)}s
                    </small>
                  </div>
                )}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="message bot">
              <div className="message-content">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-container">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message here..."
            rows="1"
            disabled={isLoading}
          />
          <button 
            onClick={sendMessage} 
            disabled={isLoading || !inputMessage.trim()}
          >
            Send
          </button>
        </div>
      </div>

      {analytics && (
        <div className="analytics-panel">
          <div className="analytics-content">
            <h3>Chatbot Analytics</h3>
            <div className="metrics">
              <div className="metric">
                <span className="metric-value">
                  {analytics.metrics.total_conversations}
                </span>
                <span className="metric-label">Total Conversations</span>
              </div>
              <div className="metric">
                <span className="metric-value">
                  {analytics.metrics.average_response_time.toFixed(2)}s
                </span>
                <span className="metric-label">Avg Response Time</span>
              </div>
            </div>
            <button 
              onClick={() => setAnalytics(null)}
              className="close-btn"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default App;