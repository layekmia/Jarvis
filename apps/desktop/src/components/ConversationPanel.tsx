/**
 * ConversationPanel — Scrollable chat thread between User & Jarvis.
 * Renders "You" and "Jarvis" message bubbles with animated entry.
 */
import { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useJarvisStore, type ConversationMessage } from '../stores/jarvisStore.js';

// ─── Message Bubble ────────────────────────────────────────────────────────

function MessageBubble({ msg }: { msg: ConversationMessage }) {
  const isJarvis = msg.role === 'jarvis';
  const time = new Date(msg.timestamp).toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  });

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 12, scale: 0.96 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ type: 'spring', stiffness: 300, damping: 28 }}
      className={`flex gap-2 ${isJarvis ? 'flex-row' : 'flex-row-reverse'}`}
    >
      {/* Avatar */}
      <div
        className={`flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold mt-0.5 ${
          isJarvis
            ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
            : 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
        }`}
      >
        {isJarvis ? 'J' : 'U'}
      </div>

      {/* Bubble */}
      <div className={`flex flex-col gap-1 max-w-[80%] ${isJarvis ? 'items-start' : 'items-end'}`}>
        <div
          className={`px-3 py-2 rounded-xl text-sm leading-relaxed ${
            isJarvis
              ? 'bg-cyan-500/10 border border-cyan-500/20 text-cyan-50 rounded-tl-sm'
              : 'bg-blue-600/20 border border-blue-500/20 text-blue-100 rounded-tr-sm'
          }`}
        >
          {msg.text}
        </div>
        <span className="text-[10px] text-slate-600 font-mono px-1">{time}</span>
      </div>
    </motion.div>
  );
}

// ─── Empty State ───────────────────────────────────────────────────────────

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-3 py-8 text-center">
      <div className="w-10 h-10 rounded-full bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
        <svg className="w-5 h-5 text-cyan-500/60" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
            d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
      </div>
      <div>
        <p className="text-xs text-slate-500 font-mono">NO CONVERSATION YET</p>
        <p className="text-[10px] text-slate-700 mt-1">Say the wake word to start</p>
      </div>
    </div>
  );
}

// ─── Panel ─────────────────────────────────────────────────────────────────

export function ConversationPanel() {
  const messages = useJarvisStore((s) => s.messages);
  const clearMessages = useJarvisStore((s) => s.clearMessages);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to newest message
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div className="glass-panel flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/5">
        <div className="flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-widest font-mono">
            Conversation
          </span>
        </div>
        {messages.length > 0 && (
          <button
            onClick={clearMessages}
            className="text-[10px] text-slate-600 hover:text-red-400 transition-colors font-mono uppercase tracking-wide"
            title="Clear conversation"
          >
            Clear
          </button>
        )}
      </div>

      {/* Message list */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-3 py-3 space-y-3"
        id="conversation-scroll"
      >
        {messages.length === 0 ? (
          <EmptyState />
        ) : (
          <AnimatePresence initial={false}>
            {messages.map((msg) => (
              <MessageBubble key={msg.id} msg={msg} />
            ))}
          </AnimatePresence>
        )}
      </div>
    </div>
  );
}
