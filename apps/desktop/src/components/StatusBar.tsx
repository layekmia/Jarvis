/**
 * StatusBar — Top header with Jarvis name, brain state badge, and connection status.
 */
import { motion, AnimatePresence } from 'framer-motion';
import { useJarvisStore, type JarvisBrainState } from '../stores/jarvisStore.js';

const STATE_ICONS: Record<JarvisBrainState, string> = {
  idle: '◉',
  listening: '◎',
  thinking: '◈',
  executing: '▶',
  speaking: '♫',
  error: '✕',
};

export function StatusBar() {
  const { brainState, statusText, isConnected } = useJarvisStore();

  return (
    <div className="flex items-center justify-between px-6 py-3 border-b border-white/5">
      {/* Logo / Name */}
      <div className="flex items-center gap-3">
        <div className="relative">
          <span className="text-lg font-bold tracking-[0.3em] gradient-text-cyan">JARVIS</span>
          <span className="absolute -top-0.5 -right-4 text-[8px] text-cyan-500/60 font-mono">v1</span>
        </div>
        <span className="text-[10px] text-slate-700 font-mono hidden sm:block">AI DESKTOP ASSISTANT</span>
      </div>

      {/* Brain state badge */}
      <AnimatePresence mode="wait">
        <motion.div
          key={brainState}
          initial={{ opacity: 0, y: -4 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 4 }}
          transition={{ duration: 0.2 }}
          className={`state-badge state-${brainState}`}
          aria-live="polite"
          aria-label={`Jarvis state: ${brainState}`}
        >
          <span>{STATE_ICONS[brainState]}</span>
          <span>{brainState.toUpperCase()}</span>
        </motion.div>
      </AnimatePresence>

      {/* Connection indicator + status */}
      <div className="flex items-center gap-2">
        <div className="hidden md:block text-right">
          <p className="text-[9px] text-slate-600 font-mono">{statusText}</p>
        </div>
        <div className="flex items-center gap-1.5">
          <motion.div
            animate={isConnected ? { scale: [1, 1.3, 1] } : { scale: 1 }}
            transition={{ repeat: Infinity, duration: 2, ease: 'easeInOut' }}
            className={`w-2 h-2 rounded-full ${
              isConnected ? 'bg-green-400 shadow-[0_0_8px_rgba(74,222,128,0.8)]' : 'bg-red-400'
            }`}
          />
          <span className={`text-[10px] font-mono ${isConnected ? 'text-green-400' : 'text-red-400'}`}>
            {isConnected ? 'LIVE' : 'DISC'}
          </span>
        </div>
      </div>
    </div>
  );
}
