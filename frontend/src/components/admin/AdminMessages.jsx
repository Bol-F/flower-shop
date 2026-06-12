import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { getAdminMessages, replyToMessage, markMessageRead } from '../../api/contact';
import LoadingSpinner from '../common/LoadingSpinner';

const POLL_MS = 15000;
const MAX_PAGES = 5;

function groupConversations(messages) {
  const byUser = new Map();
  for (const msg of messages) {
    if (!byUser.has(msg.user_email)) {
      byUser.set(msg.user_email, {
        email: msg.user_email,
        username: msg.user_username,
        messages: [],
      });
    }
    byUser.get(msg.user_email).messages.push(msg);
  }
  const conversations = [...byUser.values()];
  for (const convo of conversations) {
    convo.messages.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
    convo.last = convo.messages[convo.messages.length - 1];
    convo.unread = convo.messages.filter((m) => !m.is_read).length;
  }
  conversations.sort((a, b) => new Date(b.last.created_at) - new Date(a.last.created_at));
  return conversations;
}

function AdminMessages() {
  const { t, i18n } = useTranslation();
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [replyText, setReplyText] = useState('');
  const [sending, setSending] = useState(false);
  const threadRef = useRef(null);

  const loadMessages = useCallback(async () => {
    try {
      const all = [];
      for (let page = 1; page <= MAX_PAGES; page++) {
        const { data } = await getAdminMessages(page);
        all.push(...(data.results || data));
        if (!data.next) break;
      }
      setMessages(all);
    } catch {
      // keep last known state; next poll retries
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadMessages();
    const timer = setInterval(loadMessages, POLL_MS);
    return () => clearInterval(timer);
  }, [loadMessages]);

  const conversations = groupConversations(messages);
  const selected = conversations.find((c) => c.email === selectedEmail) || null;

  // Opening a conversation marks its unread messages as read
  const handleSelect = (convo) => {
    setSelectedEmail(convo.email);
    setReplyText('');
    convo.messages
      .filter((m) => !m.is_read)
      .forEach((m) => markMessageRead(m.id).catch(() => {}));
    setMessages((prev) =>
      prev.map((m) => (m.user_email === convo.email ? { ...m, is_read: true } : m)));
  };

  useEffect(() => {
    if (threadRef.current) {
      threadRef.current.scrollTop = threadRef.current.scrollHeight;
    }
  }, [selectedEmail, messages]);

  // One reply slot per message: answer the newest message that has no reply yet
  const replyTarget = selected
    ? [...selected.messages].reverse().find((m) => !m.admin_reply)
    : null;

  const handleSend = async (e) => {
    e.preventDefault();
    const body = replyText.trim();
    if (!body || !replyTarget || sending) return;
    setSending(true);
    try {
      await replyToMessage(replyTarget.id, body);
      setReplyText('');
      await loadMessages();
    } finally {
      setSending(false);
    }
  };

  const formatTime = (iso) =>
    new Date(iso).toLocaleString(i18n.language, {
      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
    });

  if (loading) return <LoadingSpinner />;

  if (conversations.length === 0) {
    return (
      <div className="empty-state" style={{ background: '#fff', borderRadius: '16px', padding: '60px 20px' }}>
        <div style={{ fontSize: '4rem', marginBottom: '16px' }}>💬</div>
        <h3>{t('adminChat.empty')}</h3>
      </div>
    );
  }

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '280px 1fr',
      height: '560px',
      background: '#fff',
      borderRadius: '16px',
      overflow: 'hidden',
      boxShadow: '0 2px 12px rgba(233,30,140,0.06)',
    }}>
      {/* Conversation list */}
      <div style={{ borderRight: '1px solid #f0e0e6', overflowY: 'auto' }}>
        {conversations.map((convo) => (
          <button
            key={convo.email}
            onClick={() => handleSelect(convo)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              width: '100%',
              padding: '12px 14px',
              border: 'none',
              borderBottom: '1px solid #faf0f4',
              cursor: 'pointer',
              textAlign: 'left',
              fontFamily: 'inherit',
              background: selectedEmail === convo.email ? '#fff0f7' : '#fff',
            }}
          >
            <div style={{
              width: '40px',
              height: '40px',
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #e91e8c, #c2185b)',
              color: '#fff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: '700',
              flexShrink: 0,
            }}>
              {(convo.username || convo.email)[0].toUpperCase()}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: '6px' }}>
                <span style={{ fontWeight: '600', fontSize: '0.85rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {convo.username || convo.email}
                </span>
                <span style={{ color: '#9e9e9e', fontSize: '0.7rem', flexShrink: 0 }}>
                  {formatTime(convo.last.created_at)}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: '6px', marginTop: '2px' }}>
                <span style={{ color: '#757575', fontSize: '0.78rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {convo.last.body}
                </span>
                {convo.unread > 0 && (
                  <span style={{
                    background: '#e91e8c',
                    color: '#fff',
                    borderRadius: '10px',
                    minWidth: '20px',
                    height: '20px',
                    fontSize: '0.7rem',
                    fontWeight: '700',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '0 6px',
                    flexShrink: 0,
                  }}>
                    {convo.unread}
                  </span>
                )}
              </div>
            </div>
          </button>
        ))}
      </div>

      {/* Thread */}
      {selected ? (
        <div style={{ display: 'flex', flexDirection: 'column', minWidth: 0 }}>
          <div style={{ padding: '12px 16px', borderBottom: '1px solid #f0e0e6' }}>
            <div style={{ fontWeight: '700', fontSize: '0.95rem' }}>{selected.username || selected.email}</div>
            <div style={{ color: '#757575', fontSize: '0.78rem' }}>{selected.email}</div>
          </div>

          <div ref={threadRef} style={{ flex: 1, overflowY: 'auto', padding: '16px', background: '#fff8f9' }}>
            {selected.messages.map((msg) => (
              <div key={msg.id} style={{ marginBottom: '12px' }}>
                {/* Customer bubble */}
                <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                  <div style={{
                    maxWidth: '70%',
                    background: '#fff',
                    border: '1px solid #f0e0e6',
                    borderRadius: '14px 14px 14px 4px',
                    padding: '8px 12px',
                    fontSize: '0.85rem',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                  }}>
                    {msg.body}
                    <div style={{ fontSize: '0.65rem', color: '#9e9e9e', marginTop: '2px' }}>
                      {formatTime(msg.created_at)}
                    </div>
                  </div>
                </div>
                {/* Admin reply bubble */}
                {msg.admin_reply && (
                  <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '6px' }}>
                    <div style={{
                      maxWidth: '70%',
                      background: 'linear-gradient(135deg, #e91e8c, #c2185b)',
                      color: '#fff',
                      borderRadius: '14px 14px 4px 14px',
                      padding: '8px 12px',
                      fontSize: '0.85rem',
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word',
                    }}>
                      {msg.admin_reply}
                      {msg.replied_at && (
                        <div style={{ fontSize: '0.65rem', opacity: 0.8, textAlign: 'right', marginTop: '2px' }}>
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
              value={replyText}
              onChange={(e) => setReplyText(e.target.value)}
              placeholder={replyTarget ? t('adminChat.replyPlaceholder') : t('adminChat.waitHint')}
              disabled={!replyTarget}
              maxLength={2000}
              style={{
                flex: 1,
                border: '1.5px solid #f0e0e6',
                borderRadius: '20px',
                padding: '9px 14px',
                fontSize: '0.85rem',
                outline: 'none',
                fontFamily: 'inherit',
                background: replyTarget ? '#fff' : '#faf5f7',
              }}
            />
            <button
              type="submit"
              disabled={sending || !replyTarget || !replyText.trim()}
              style={{
                background: 'linear-gradient(135deg, #e91e8c, #c2185b)',
                color: '#fff',
                border: 'none',
                borderRadius: '50%',
                width: '38px',
                height: '38px',
                cursor: sending ? 'wait' : 'pointer',
                fontSize: '1rem',
                opacity: replyTarget && replyText.trim() ? 1 : 0.5,
              }}
              title={t('chat.send')}
            >
              ➤
            </button>
          </form>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: '#9e9e9e', background: '#fff8f9' }}>
          <div style={{ fontSize: '3rem', marginBottom: '10px' }}>💬</div>
          <p style={{ fontSize: '0.9rem' }}>{t('adminChat.select')}</p>
        </div>
      )}
    </div>
  );
}

export default AdminMessages;
