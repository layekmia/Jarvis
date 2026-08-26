import React from 'react';
import { useJarvisStore } from '../stores/jarvisStore';
import { Activity, X, Info, AlertTriangle, CheckCircle2 } from 'lucide-react';

interface LogsPanelProps {
  onClose: () => void;
}

export const LogsPanel: React.FC<LogsPanelProps> = ({ onClose }) => {
  const { systemLogs, clearSystemLogs } = useJarvisStore();

  return (
    <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="glass-panel w-[600px] max-h-[80vh] shadow-2xl flex flex-col border border-white/10 animate-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-white/10 bg-black/20">
          <div className="flex items-center space-x-2">
            <Activity className="w-5 h-5 text-purple-400" />
            <h2 className="text-lg font-medium text-white/90">System Activity Logs</h2>
          </div>
          <div className="flex items-center space-x-4">
            <button 
              onClick={clearSystemLogs}
              className="text-xs text-white/40 hover:text-white/80 transition-colors"
            >
              Clear Logs
            </button>
            <button 
              onClick={onClose}
              className="p-1 rounded-md hover:bg-white/10 text-white/50 hover:text-white transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="p-4 flex-1 overflow-y-auto custom-scrollbar bg-black/40 space-y-2">
          {systemLogs.length === 0 ? (
            <div className="h-40 flex items-center justify-center text-white/30 text-sm italic">
              No recent activity.
            </div>
          ) : (
            systemLogs.map((log) => (
              <div 
                key={log.id} 
                className="flex items-start space-x-3 p-3 rounded-md bg-white/5 border border-white/5 hover:bg-white/10 transition-colors"
              >
                <div className="mt-0.5">
                  {log.type === 'error' && <AlertTriangle className="w-4 h-4 text-red-400" />}
                  {log.type === 'success' && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
                  {log.type === 'info' && <Info className="w-4 h-4 text-cyan-400" />}
                </div>
                <div className="flex-1">
                  <div className="text-sm text-white/80 leading-relaxed">
                    {log.message}
                  </div>
                  <div className="text-[10px] font-mono text-white/30 mt-1 uppercase tracking-wider">
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
