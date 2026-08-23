/**
 * BrainStateControls — Dev/debug panel to manually trigger brain states.
 * Used in Phase 1 to demo all UI states. Will be hidden/removed in production.
 */
import { motion } from 'framer-motion';
import { useJarvisStore, type JarvisBrainState } from '../stores/jarvisStore';

const STATES: { state: JarvisBrainState; label: string; color: string }[] = [
  { state: 'idle',      label: 'IDLE',      color: 'border-cyan-500/40 text-cyan-400   hover:bg-cyan-500/10' },
  { state: 'listening', label: 'LISTEN',    color: 'border-green-500/40 text-green-400 hover:bg-green-500/10' },
  { state: 'thinking',  label: 'THINK',     color: 'border-purple-500/40 text-purple-400 hover:bg-purple-500/10' },
  { state: 'executing', label: 'EXECUTE',   color: 'border-amber-500/40 text-amber-400 hover:bg-amber-500/10' },
  { state: 'speaking',  label: 'SPEAK',     color: 'border-blue-500/40 text-blue-400   hover:bg-blue-500/10' },
  { state: 'error',     label: 'ERROR',     color: 'border-red-500/40 text-red-400     hover:bg-red-500/10' },
];

interface BrainStateControlsProps {
  onAddDemoMessage?: () => void;
}

export function BrainStateControls({ onAddDemoMessage }: BrainStateControlsProps) {
  const { brainState, setBrainState } = useJarvisStore();

  return (
    <div className="glass-panel p-3 space-y-2">
      <div className="flex items-center gap-2 mb-1">
        <div className="w-1.5 h-1.5 rounded-full bg-amber-400" />
        <span className="text-[10px] font-mono text-slate-500 uppercase tracking-widest">Dev Controls</span>
      </div>

      {/* State buttons */}
      <div className="grid grid-cols-3 gap-1.5">
        {STATES.map(({ state, label, color }) => (
          <motion.button
            key={state}
            whileTap={{ scale: 0.95 }}
            onClick={() => setBrainState(state)}
            id={`btn-state-${state}`}
            className={`px-2 py-1.5 rounded-lg border text-[9px] font-mono font-bold uppercase transition-all ${color} ${
              brainState === state ? 'brightness-125 ring-1 ring-current/30' : ''
            }`}
          >
            {label}
          </motion.button>
        ))}
      </div>

      {/* Add demo message */}
      {onAddDemoMessage && (
        <motion.button
          whileTap={{ scale: 0.97 }}
          onClick={onAddDemoMessage}
          id="btn-demo-message"
          className="w-full px-2 py-1.5 rounded-lg border border-slate-600/40 text-[9px] font-mono text-slate-500 hover:text-slate-300 hover:bg-slate-700/30 transition-all uppercase"
        >
          + Add Demo Message
        </motion.button>
      )}
    </div>
  );
}
