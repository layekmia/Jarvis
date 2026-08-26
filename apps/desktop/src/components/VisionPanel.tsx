import React from 'react';
import { useJarvisStore } from '../stores/jarvisStore';
import { Eye, Target, Sparkles, CheckCircle2 } from 'lucide-react';

export const VisionPanel: React.FC = () => {
  const visionData = useJarvisStore((state) => state.visionData);

  if (!visionData) return null;

  return (
    <div className="glass-panel w-72 flex flex-col pointer-events-auto shadow-2xl overflow-hidden mt-4 animate-in slide-in-from-left duration-500 relative">
      {/* Decorative scanline specific to vision panel */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-cyan-500/10 to-transparent h-[200%] animate-[scan_3s_ease-in-out_infinite] pointer-events-none" />

      {/* Header */}
      <div className="bg-black/40 p-3 border-b border-white/5 flex items-center justify-between relative z-10">
        <div className="flex items-center space-x-2">
          <Eye className="w-4 h-4 text-cyan-400" />
          <h2 className="text-sm font-medium text-white/90">Visual Intelligence</h2>
        </div>
        <div className="flex space-x-1">
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-500/50 animate-pulse delay-75" />
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-600/50 animate-pulse delay-150" />
        </div>
      </div>

      <div className="p-4 space-y-4 relative z-10 bg-black/20">
        {/* Action Description */}
        <div className="flex items-start space-x-3">
          <div className="p-1.5 rounded-md bg-white/5 mt-0.5">
            {visionData.action === 'Find & Click' ? (
              <Target className="w-4 h-4 text-cyan-300" />
            ) : (
              <Sparkles className="w-4 h-4 text-purple-300" />
            )}
          </div>
          <div>
            <div className="text-xs text-white/50 uppercase tracking-wider mb-1">
              {visionData.action}
            </div>
            <div className="text-sm text-white/90">
              {visionData.details}
            </div>
          </div>
        </div>

        {/* Image Preview */}
        <div className="relative rounded-lg overflow-hidden border border-white/10 aspect-video bg-black/50 group">
          <img 
            src={visionData.image_base64} 
            alt="Vision capture" 
            className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-opacity"
          />
          {/* Overlay grid for tech feel */}
          <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.05)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.05)_1px,transparent_1px)] bg-[size:10px_10px] pointer-events-none" />
          
          {!visionData.result && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/40 backdrop-blur-sm">
              <div className="flex items-center space-x-2 text-xs font-mono text-cyan-300">
                <span className="animate-spin rounded-full h-3 w-3 border-b-2 border-cyan-300" />
                <span>PROCESSING...</span>
              </div>
            </div>
          )}
        </div>

        {/* Result */}
        {visionData.result && (
          <div className="pt-3 border-t border-white/5 animate-in fade-in slide-in-from-bottom-2">
            <div className="flex items-start space-x-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
              <p className="text-xs text-white/70 leading-relaxed">
                {visionData.result}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
