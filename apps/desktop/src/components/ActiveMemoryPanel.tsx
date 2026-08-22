/**
 * ActiveMemoryPanel — Shows Jarvis's active working memory entries.
 * Phase 1: static/dummy data. Phase 7+: connected to SQLite backend.
 */
import { motion, AnimatePresence } from 'framer-motion';
import { useJarvisStore, type MemoryEntry } from '../stores/jarvisStore.js';

// ─── Category Config ───────────────────────────────────────────────────────

const CATEGORY_CONFIG: Record<MemoryEntry['category'], { color: string; bg: string; label: string; icon: string }> = {
  context:    { color: 'text-cyan-400',   bg: 'bg-cyan-500/10 border-cyan-500/20',   label: 'CTX',  icon: '◈' },
  preference: { color: 'text-purple-400', bg: 'bg-purple-500/10 border-purple-500/20', label: 'PREF', icon: '◉' },
  task:       { color: 'text-amber-400',  bg: 'bg-amber-500/10 border-amber-500/20',  label: 'TASK', icon: '▸' },
  fact:       { color: 'text-blue-400',   bg: 'bg-blue-500/10 border-blue-500/20',    label: 'FACT', icon: '◆' },
};

// ─── Memory Card ───────────────────────────────────────────────────────────

function MemoryCard({ entry }: { entry: MemoryEntry }) {
  const cat = CATEGORY_CONFIG[entry.category];

  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 8 }}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      className={`flex items-start gap-2.5 px-3 py-2.5 rounded-lg border ${cat.bg} glass-panel-hover`}
    >
      {/* Category badge */}
      <div className={`flex-shrink-0 mt-0.5 text-[10px] font-mono font-bold ${cat.color}`}>
        {cat.icon}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0 space-y-0.5">
        <div className="flex items-center gap-1.5">
          <p className="text-[10px] text-slate-600 font-mono uppercase tracking-wide">{cat.label}</p>
          <p className={`text-[10px] font-mono font-semibold ${cat.color}`}>{entry.label}</p>
        </div>
        <p className="text-xs text-slate-300 truncate">{entry.value}</p>
      </div>
    </motion.div>
  );
}

// ─── Panel ─────────────────────────────────────────────────────────────────

export function ActiveMemoryPanel() {
  const memoryEntries = useJarvisStore((s) => s.memoryEntries);

  return (
    <div className="glass-panel flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/5">
        <div className="flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-pulse" />
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-widest font-mono">
            Active Memory
          </span>
        </div>
        <span className="text-[10px] text-slate-600 font-mono">{memoryEntries.length} entries</span>
      </div>

      {/* Category legend */}
      <div className="flex gap-2 px-4 py-2 border-b border-white/5 flex-wrap">
        {Object.entries(CATEGORY_CONFIG).map(([key, cfg]) => (
          <div key={key} className={`flex items-center gap-1 text-[9px] font-mono px-1.5 py-0.5 rounded border ${cfg.bg}`}>
            <span className={cfg.color}>{cfg.icon}</span>
            <span className={cfg.color}>{cfg.label}</span>
          </div>
        ))}
      </div>

      {/* Memory list */}
      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-2">
        <AnimatePresence initial={false}>
          {memoryEntries.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <p className="text-[10px] text-slate-700 font-mono">NO ACTIVE MEMORY</p>
            </div>
          ) : (
            memoryEntries.map((entry) => <MemoryCard key={entry.id} entry={entry} />)
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
