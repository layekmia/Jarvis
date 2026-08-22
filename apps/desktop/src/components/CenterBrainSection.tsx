/**
 * CenterBrainSection — Central focal point: animated 3D brain + state info ring.
 */
import { motion, AnimatePresence } from 'framer-motion';
import { JarvisBrain } from './JarvisBrain';
import { useJarvisStore, type JarvisBrainState } from '../../stores/jarvisStore';

const STATE_MESSAGES: Record<JarvisBrainState, string> = {
  idle:      'Waiting for wake word...',
  listening: 'Listening to your voice...',
  thinking:  'Processing your request...',
  executing: 'Executing command...',
  speaking:  'Generating response...',
  error:     'Connection error — retrying...',
};

const STATE_COLORS: Record<JarvisBrainState, string> = {
  idle:      'text-cyan-400',
  listening: 'text-green-400',
  thinking:  'text-purple-400',
  executing: 'text-amber-400',
  speaking:  'text-blue-400',
  error:     'text-red-400',
};

const RING_COLORS: Record<JarvisBrainState, string> = {
  idle:      'border-cyan-500/20',
  listening: 'border-green-500/30',
  thinking:  'border-purple-500/30',
  executing: 'border-amber-500/30',
  speaking:  'border-blue-500/30',
  error:     'border-red-500/30',
};

export function CenterBrainSection() {
  const { brainState, statusText } = useJarvisStore();

  return (
    <div className="flex flex-col items-center justify-center gap-6">
      {/* Outer decorative ring */}
      <div className="relative">
        <motion.div
          className={`absolute inset-0 rounded-full border-2 ${RING_COLORS[brainState]}`}
          style={{ margin: -20 }}
          animate={{ rotate: 360 }}
          transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
        />
        {/* Dash-ring overlay */}
        <motion.div
          className={`absolute inset-0 rounded-full border ${RING_COLORS[brainState]}`}
          style={{
            margin: -36,
            borderStyle: 'dashed',
            opacity: 0.4,
          }}
          animate={{ rotate: -360 }}
          transition={{ duration: 30, repeat: Infinity, ease: 'linear' }}
        />

        {/* The 3D brain */}
        <JarvisBrain brainState={brainState} size={260} />
      </div>

      {/* State label + status */}
      <div className="text-center space-y-2">
        <AnimatePresence mode="wait">
          <motion.p
            key={`state-${brainState}`}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.25 }}
            className={`text-xs font-mono font-semibold uppercase tracking-[0.2em] ${STATE_COLORS[brainState]}`}
          >
            {STATE_MESSAGES[brainState]}
          </motion.p>
        </AnimatePresence>

        <AnimatePresence mode="wait">
          <motion.p
            key={`status-${statusText}`}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="text-[10px] text-slate-600 font-mono max-w-[220px] text-center"
          >
            {statusText}
          </motion.p>
        </AnimatePresence>
      </div>
    </div>
  );
}
