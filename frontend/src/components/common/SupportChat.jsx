import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../hooks/useAuth';
import { sendMessage, getMyMessages } from '../../api/contact';

const TELEGRAM_USER = 'Bol_F';
const POLL_MS = 20000;

function SupportChat() {
  const { t, i18n } = useTranslation();
  const { isAuthenticated, isAdmin } = useAuth();
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState('');
  const [sending, setSending] = useState(false);
  const bodyRef = useRef(null);

  const loadMessages = useCallback(() => {
    if (!isAuthenticated) return;
    getMyMessages()
      .then(({ data }) => {
        const list = data.results || data;
        // API returns newest first; chat reads oldest -> newest
        setMessages([...list].reverse());
      })
      .catch(() => {});
  }, [isAuthenticated]);

  // Fetch on open, then poll for admin replies while the panel stays open
  useEffect(() => {
    if (!open) return undefined;
    loadMessages();
    const timer = setInterval(loadMessages, POLL_MS);
    return () => clearInterval(timer);
  }, [open, loadMessages]);

  // Stick to the newest message
  useEffect(() => {
    if (bodyRef.current) {
      bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
    }
  }, [messages, open]);

  const handleSend = async (e) => {
    e.preventDefault();
    const body = text.trim();
    if (!body || sending) return;
    setSending(true);
    try {
      const subject = body.length > 60 ? `${body.slice(0, 60)}…` : body;
      await sendMessage(subject, body);
      setText('');
      loadMessages();
    } catch {
      // keep the text so the user can retry
    } finally {
      setSending(false);
    }
  };

  const formatTime = (iso) =>
    new Date(iso).toLocaleTimeString(i18n.language, { hour: '2-digit', minute: '2-digit' });

  // Admins answer from the dashboard's Messages tab — they ARE support,
  // so don't show them the customer chat.
  if (isAdmin) return null;

  return (
    <>
      {/* Telegram — bottom-left corner */}
      <a
        href={`https://t.me/${TELEGRAM_USER}`}
        target="_blank"
        rel="noopener noreferrer"
        title={t('chat.telegramTitle')}
        style={{
          position: 'fixed',
          bottom: '20px',
          left: '20px',
          zIndex: 998,
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          background: '#fff',
          color: '#2AABEE',
          border: '1.5px solid #2AABEE',
          borderRadius: '22px',
          padding: '8px 14px',
          fontSize: '0.85rem',
          fontWeight: '600',
          boxShadow: '0 2px 12px rgba(0,0,0,0.12)',
          textDecoration: 'none',
        }}
      >
        ✈️ @{TELEGRAM_USER}
      </a>

      {/* Chat panel */}
      {open && (
        <div style={{
          position: 'fixed',
          bottom: '90px',
          right: '20px',
          zIndex: 999,
          width: 'min(340px, calc(100vw - 40px))',
          height: '440px',
          background: '#fff',
          borderRadius: '16px',
          boxShadow: '0 8px 40px rgba(0,0,0,0.18)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}>
          {/* Header */}
          <div style={{
            background: 'linear-gradient(135deg, #e91e8c, #c2185b)',
            color: '#fff',
            padding: '14px 16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}>
            <div>
              <div style={{ fontWeight: '700' }}>💬 {t('chat.title')}</div>
              <div style={{ fontSize: '0.75rem', opacity: 0.85 }}>{t('chat.subtitle')}</div>
            </div>
            <button
              onClick={() => setOpen(false)}
              style={{ background: 'none', border: 'none', color: '#fff', fontSize: '1.2rem', cursor: 'pointer' }}
            >
              ✕
            </button>
          </div>

          {/* Body */}
          {isAuthenticated ? (
            <>
              <div ref={bodyRef} style={{ flex: 1, overflowY: 'auto', padding: '14px', background: '#fff8f9' }}>
                {messages.length === 0 && (
                  <p style={{ color: '#757575', fontSize: '0.85rem', textAlign: 'center', marginTop: '20px' }}>
                    {t('chat.empty')}
                  </p>
                )}
                {messages.map((msg) => (
                  <div key={msg.id} style={{ marginBottom: '12px' }}>
                    {/* User bubble */}
                    <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                      <div style={{
                        maxWidth: '80%',
                        background: 'linear-gradient(135deg, #e91e8c, #c2185b)',
                        color: '#fff',
                        borderRadius: '14px 14px 4px 14px',
                        padding: '8px 12px',
                        fontSize: '0.85rem',
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word',
                      }}>
                        {msg.body}
                        <div style={{ fontSize: '0.65rem', opacity: 0.8, textAlign: 'right', marginTop: '2px' }}>
                          {formatTime(msg.created_at)}
                        </div>
                      </div>
                    </div>
                    {/* Admin reply bubble */}
                    {msg.admin_reply && (
                      <div style={{ display: 'flex', justifyContent: 'flex-start', marginTop: '6px' }}>
                        <div style={{
                          maxWidth: '80%',
                          background: '#fff',
                          border: '1px solid #f0e0e6',
                          color: '#2d2d2d',
                          borderRadius: '14px 14px 14px 4px',
                          padding: '8px 12px',
                          fontSize: '0.85rem',
                          whiteSpace: 'pre-wrap',
                          wordBreak: 'break-word',
                        }}>
                          <div style={{ fontSize: '0.7rem', fontWeight: '700', color: '#e91e8c', marginBottom: '2px' }}>
                            🌸 {t('chat.supportName')}
                          </div>
                          {msg.admin_reply}
                          {msg.replied_at && (
                            <div style={{ fontSize: '0.65rem', color: '#9e9e9e', marginTop: '2px' }}>
                              {formatTime(msg.replied_at)}
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Composer */}
              <form onSubmit={handleSend} style={{ display: 'flex', gap: '8px', padding: '10px', borderTop: '1px solid #f0e0e6' }}>
                <input
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder={t('chat.placeholder')}
                  maxLength={2000}
                  style={{
                    flex: 1,
                    border: '1.5px solid #f0e0e6',
                    borderRadius: '20px',
                    padding: '9px 14px',
                    fontSize: '0.85rem',
                    outline: 'none',
                    fontFamily: 'inherit',
                  }}
                />
                <button
                  type="submit"
                  disabled={sending || !text.trim()}
                  style={{
                    background: 'linear-gradient(135deg, #e91e8c, #c2185b)',
                    color: '#fff',
                    border: 'none',
                    borderRadius: '50%',
                    width: '38px',
                    height: '38px',
                    cursor: sending ? 'wait' : 'pointer',
                    fontSize: '1rem',
                    opacity: text.trim() ? 1 : 0.5,
                  }}
                  title={t('chat.send')}
                >
                  ➤
                </button>
              </form>
            </>
          ) : (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '24px', textAlign: 'center', background: '#fff8f9' }}>
              <div style={{ fontSize: '2.5rem', marginBottom: '12px' }}>🔐</div>
              <p style={{ color: '#4a4a4a', fontSize: '0.9rem', marginBottom: '16px' }}>{t('chat.loginPrompt')}</p>
              <Link
                to="/login"
                onClick={() => setOpen(false)}
                style={{
                  background: 'linear-gradient(135deg, #e91e8c, #c2185b)',
                  color: '#fff',
                  padding: '10px 24px',
                  borderRadius: '20px',
                  fontWeight: '600',
                  fontSize: '0.85rem',
                }}
              >
                {t('chat.loginCta')}
              </Link>
              <a
                href={`https://t.me/${TELEGRAM_USER}`}
                target="_blank"
                rel="noopener noreferrer"
                style={{ marginTop: '14px', color: '#2AABEE', fontSize: '0.8rem', fontWeight: '600' }}
              >
                {t('chat.orTelegram')} @{TELEGRAM_USER}
              </a>
            </div>
          )}
        </div>
      )}

      {/* Chat bubble — bottom-right corner */}
      <button
        onClick={() => setOpen(!open)}
        title={t('chat.title')}
        style={{
          position: 'fixed',
          bottom: '20px',
          right: '20px',
          zIndex: 999,
          width: '56px',
          height: '56px',
          borderRadius: '50%',
          border: 'none',
          background: 'linear-gradient(135deg, #e91e8c, #c2185b)',
          color: '#fff',
          fontSize: '1.5rem',
          cursor: 'pointer',
          boxShadow: '0 4px 20px rgba(233,30,140,0.4)',
        }}
      >
        {open ? '✕' : '💬'}
      </button>
    </>
  );
}

export default SupportChat;
