import React from 'react';
import { useJarvisStore } from '../stores/jarvisStore';
import { Settings2, X, Mic, Globe, Volume2 } from 'lucide-react';

interface SettingsPanelProps {
  onClose: () => void;
}

export const SettingsPanel: React.FC<SettingsPanelProps> = ({ onClose }) => {
  const { settings, updateSettings } = useJarvisStore();

  return (
    <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="glass-panel w-[400px] shadow-2xl flex flex-col border border-white/10 animate-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-white/10 bg-black/20">
          <div className="flex items-center space-x-2">
            <Settings2 className="w-5 h-5 text-cyan-400" />
            <h2 className="text-lg font-medium text-white/90">Jarvis Configuration</h2>
          </div>
          <button 
            onClick={onClose}
            className="p-1 rounded-md hover:bg-white/10 text-white/50 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-6">
          
          {/* Wake Word */}
          <div className="space-y-2">
            <label className="flex items-center space-x-2 text-sm font-medium text-white/70">
              <Mic className="w-4 h-4 text-purple-400" />
              <span>Wake Word Phrase</span>
            </label>
            <select 
              value={settings.wakeWord}
              onChange={(e) => updateSettings({ wakeWord: e.target.value })}
              className="w-full bg-black/40 border border-white/10 rounded-md p-2.5 text-white text-sm outline-none focus:border-cyan-500/50 transition-colors"
            >
              <option value="Hey Jarvis">Hey Jarvis (Default ONNX)</option>
              <option value="Hello Jessica">Hello Jessica (Requires Custom ONNX)</option>
              <option value="Computer">Computer</option>
            </select>
            <p className="text-xs text-white/40">
              Note: Changing this requires the corresponding .onnx model in the backend models directory.
            </p>
          </div>

          {/* Voice ID */}
          <div className="space-y-2">
            <label className="flex items-center space-x-2 text-sm font-medium text-white/70">
              <Volume2 className="w-4 h-4 text-emerald-400" />
              <span>TTS Voice (ElevenLabs)</span>
            </label>
            <select 
              value={settings.voiceId}
              onChange={(e) => updateSettings({ voiceId: e.target.value })}
              className="w-full bg-black/40 border border-white/10 rounded-md p-2.5 text-white text-sm outline-none focus:border-cyan-500/50 transition-colors"
            >
              <option value="eleven_v3_default">Jarvis Default (Male, British)</option>
              <option value="jessica_v1">Jessica (Female, American)</option>
              <option value="nabanita_bn">Nabanita (Bengali)</option>
            </select>
          </div>

          {/* Language */}
          <div className="space-y-2">
            <label className="flex items-center space-x-2 text-sm font-medium text-white/70">
              <Globe className="w-4 h-4 text-blue-400" />
              <span>Language Preference</span>
            </label>
            <div className="flex space-x-2">
              <button 
                onClick={() => updateSettings({ language: 'en-US' })}
                className={`flex-1 py-2 rounded-md border text-sm transition-colors ${
                  settings.language === 'en-US' 
                    ? 'bg-cyan-500/20 border-cyan-500/50 text-cyan-300' 
                    : 'bg-black/20 border-white/10 text-white/50 hover:bg-white/5'
                }`}
              >
                English
              </button>
              <button 
                onClick={() => updateSettings({ language: 'bn-BD' })}
                className={`flex-1 py-2 rounded-md border text-sm transition-colors ${
                  settings.language === 'bn-BD' 
                    ? 'bg-cyan-500/20 border-cyan-500/50 text-cyan-300' 
                    : 'bg-black/20 border-white/10 text-white/50 hover:bg-white/5'
                }`}
              >
                বাংলা (Bengali)
              </button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-white/10 bg-black/20 flex justify-end">
          <button 
            onClick={onClose}
            className="px-4 py-2 bg-cyan-500 hover:bg-cyan-400 text-black font-medium rounded-md transition-colors text-sm"
          >
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
};
