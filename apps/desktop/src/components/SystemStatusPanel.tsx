/**
 * SystemStatusPanel — Live system stats (CPU, RAM, Network, Uptime).
 * Shows animated progress bars and connection status.
 * Phase 1: dummy/simulated data. Phase 2+: real data from backend.
 */
import { useEffect } from 'react';
import { motion } from 'framer-motion';
import { useJarvisStore } from '../stores/jarvisStore';

// ─── Helpers ───────────────────────────────────────────────────────────────

function getBarColor(value: number): string {
  if (value < 50) return 'bg-green-500';
  if (value < 75) return 'bg-amber-500';
  return 'bg-red-500';
}

function getBarGlow(value: number): string {
  if (value < 50) return 'shadow-[0_0_8px_rgba(16,185,129,0.6)]';
  if (value < 75) return 'shadow-[0_0_8px_rgba(245,158,11,0.6)]';
  return 'shadow-[0_0_8px_rgba(239,68,68,0.6)]';
}

// ─── Stat Row ──────────────────────────────────────────────────────────────

interface StatRowProps {
  label: string;
  value: number;
  unit?: string;
}

function StatRow({ label, value, unit = '%' }: StatRowProps) {
  return (
    <div className="space-y-1.5">
      <div className="flex justify-between items-center">
        <span className="text-[10px] text-slate-500 font-mono uppercase tracking-widest">{label}</span>
        <span className="text-xs text-slate-300 font-mono font-semibold tabular-nums">
          {value.toFixed(0)}{unit}
        </span>
      </div>
      <div className="progress-bar">
        <motion.div
          className={`progress-fill ${getBarColor(value)} ${getBarGlow(value)}`}
          initial={{ width: 0 }}
          animate={{ width: `${value}%` }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
        />
      </div>
    </div>
  );
}

// ─── Network Badge ─────────────────────────────────────────────────────────

function NetworkBadge({ status }: { status: 'online' | 'offline' | 'slow' }) {
  const config = {
    online: { dot: 'bg-green-400', text: 'text-green-400', label: 'ONLINE' },
    offline: { dot: 'bg-red-400', text: 'text-red-400', label: 'OFFLINE' },
    slow: { dot: 'bg-amber-400', text: 'text-amber-400', label: 'SLOW' },
  }[status];

  return (
    <div className="flex items-center gap-1.5">
      <div className={`w-1.5 h-1.5 rounded-full ${config.dot} animate-pulse`} />
      <span className={`text-[10px] font-mono font-semibold ${config.text}`}>{config.label}</span>
    </div>
  );
}

// ─── Panel ─────────────────────────────────────────────────────────────────

export function SystemStatusPanel() {
  const { systemStats, updateSystemStats, isConnected } = useJarvisStore();

  // Simulate live CPU/RAM fluctuation in Phase 1
  useEffect(() => {
    const tick = () => {
      updateSystemStats({
        cpu: Math.max(5, Math.min(95, systemStats.cpu + (Math.random() - 0.5) * 12)),
        ram: Math.max(20, Math.min(90, systemStats.ram + (Math.random() - 0.5) * 5)),
      });
    };
    const interval = setInterval(tick, 2000);
    return () => clearInterval(interval);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Simulate uptime counter
  useEffect(() => {
    const startTime = Date.now();
    const tick = () => {
      const elapsed = Math.floor((Date.now() - startTime) / 1000);
      const h = Math.floor(elapsed / 3600);
      const m = Math.floor((elapsed % 3600) / 60);
      const s = elapsed % 60;
      const label = h > 0 ? `${h}h ${m}m` : m > 0 ? `${m}m ${s}s` : `${s}s`;
      updateSystemStats({ uptime: label });
    };
    const interval = setInterval(tick, 1000);
    return () => clearInterval(interval);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="glass-panel p-4 space-y-4">
      {/* Header */}
      <div className="flex items-center gap-2">
        <div className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-widest font-mono">
          System Status
        </span>
      </div>

      {/* Stats */}
      <div className="space-y-3">
        <StatRow label="CPU" value={systemStats.cpu} />
        <StatRow label="RAM" value={systemStats.ram} />
      </div>

      {/* Divider */}
      <div className="border-t border-white/5" />

      {/* Info grid */}
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-0.5">
          <p className="text-[10px] text-slate-600 font-mono uppercase">Network</p>
          <NetworkBadge status={isConnected ? 'online' : 'offline'} />
        </div>
        <div className="space-y-0.5">
          <p className="text-[10px] text-slate-600 font-mono uppercase">Uptime</p>
          <p className="text-xs text-slate-300 font-mono font-semibold">{systemStats.uptime}</p>
        </div>
        <div className="space-y-0.5">
          <p className="text-[10px] text-slate-600 font-mono uppercase">Backend</p>
          <div className="flex items-center gap-1.5">
            <div className={`w-1.5 h-1.5 rounded-full ${isConnected ? 'bg-cyan-400' : 'bg-red-400'}`} />
            <span className={`text-[10px] font-mono font-semibold ${isConnected ? 'text-cyan-400' : 'text-red-400'}`}>
              {isConnected ? 'WS LIVE' : 'OFFLINE'}
            </span>
          </div>
        </div>
        <div className="space-y-0.5">
          <p className="text-[10px] text-slate-600 font-mono uppercase">Port</p>
          <p className="text-[10px] text-slate-500 font-mono">:8765</p>
        </div>
      </div>
    </div>
  );
}
