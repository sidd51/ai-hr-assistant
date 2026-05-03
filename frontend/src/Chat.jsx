import { useState, useRef, useEffect } from 'react';
import Message from './Message';
import { sendMessage, resetSession } from './api';
import styles from './Chat.module.css';

const SUGGESTIONS = [
  'How many leave days do I have left?',
  'What is the maternity leave policy?',
  'I want to apply for annual leave next week.',
  'How do I submit an expense claim?',
];

export default function Chat({ employee, onLogout }) {
  const [messages, setMessages]   = useState([]);
  const [input, setInput]         = useState('');
  const [loading, setLoading]     = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [error, setError]         = useState(null);
  const bottomRef                 = useRef(null);
  const inputRef                  = useRef(null);

  // Greet on mount
  useEffect(() => {
    setMessages([{
      role: 'assistant',
      content: `Hello ${employee.name.split(' ')[0]} 👋  I'm your HR Assistant. I can help you with leave balances, company policies, submitting requests, and expense claims. How can I help you today?`,
    }]);
    inputRef.current?.focus();
  }, [employee]);

  // Auto-scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const send = async (text) => {
    const msg = (text || input).trim();
    if (!msg || loading) return;

    setInput('');
    setError(null);
    setMessages(prev => [...prev, { role: 'user', content: msg }]);
    setLoading(true);

    try {
      const data = await sendMessage({
        message:     msg,
        session_id:  sessionId,
        employee_id: employee.id,
      });
      setSessionId(data.session_id);
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleReset = async () => {
    if (sessionId) await resetSession(sessionId);
    setSessionId(null);
    setMessages([{
      role: 'assistant',
      content: `New conversation started. How can I help you, ${employee.name.split(' ')[0]}?`,
    }]);
    setError(null);
  };

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  const isEmpty = messages.length <= 1;

  return (
    <div className={styles.layout}>

      {/* ── Sidebar ── */}
      <aside className={styles.sidebar}>
        <div className={styles.sideTop}>
          <div className={styles.brand}>
            
            <span className={styles.brandName}>HarborHR</span>
          </div>

          <div className={styles.profile}>
            <div className={styles.avatar}>
              {employee.name.split(' ').map(n => n[0]).join('')}
            </div>
            <div className={styles.profileInfo}>
              <span className={styles.profileName}>{employee.name}</span>
              <span className={styles.profileMeta}>ID #{employee.id} · {employee.dept}</span>
            </div>
          </div>

          <div className={styles.sideSection}>
            <span className={styles.sideLabel}>Quick actions</span>
            {SUGGESTIONS.map((s, i) => (
              <button
                key={i}
                className={styles.suggestion}
                onClick={() => send(s)}
                disabled={loading}
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        <div className={styles.sideBottom}>
          <button className={styles.newChat} onClick={handleReset}>
            <span>+</span> New conversation
          </button>
          <button className={styles.logout} onClick={onLogout}>
            Sign out
          </button>
        </div>
      </aside>

      {/* ── Main chat area ── */}
      <main className={styles.main}>

        {/* Header */}
        <header className={styles.header}>
          <div className={styles.headerLeft}>
            <div className={styles.statusDot} />
            <span className={styles.headerTitle}>Assistant</span>
          </div>
          <div className={styles.headerRight}>
            {sessionId && (
              <span className={styles.sessionTag}>
                session {sessionId.slice(0, 8)}
              </span>
            )}
          </div>
        </header>

        {/* Messages */}
        <div className={styles.feed}>
          {isEmpty && (
            <div className={styles.empty}>
              <div className={styles.emptyIcon}>?</div>
              <p>Ask me anything about your HR matters</p>
            </div>
          )}

          {messages.map((m, i) => (
            <Message key={i} role={m.role} content={m.content} />
          ))}

          {loading && <Message isLoading />}

          {error && (
            <div className={styles.error}>
              ⚠ {error}
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className={styles.inputWrap}>
          <textarea
            ref={inputRef}
            className={styles.input}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Ask about leave, policies, expenses..."
            rows={1}
            disabled={loading}
          />
          <button
            className={styles.send}
            onClick={() => send()}
            disabled={!input.trim() || loading}
          >
            ↑
          </button>
        </div>
        <p className={styles.hint}>Enter to send · Shift+Enter for new line</p>
      </main>

    </div>
  );
}