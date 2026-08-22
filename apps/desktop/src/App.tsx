import { useEffect } from 'react';
import { jarvisWS } from './lib/websocket';
import { useJarvisStore } from './stores/jarvisStore';
import './App.css';

function App() {
  const { isConnected, statusText, brainState } = useJarvisStore();

  useEffect(() => {
    // Connect to WebSocket on mount
    jarvisWS.connect();

    // Listen to WS connection events to update Zustand state
    const unsubConnected = jarvisWS.on('_connected', () => {
      useJarvisStore.getState().setConnected(true);
    });

    const unsubDisconnected = jarvisWS.on('_disconnected', (msg: any) => {
      useJarvisStore.getState().setConnected(false, `Code: ${msg.code}`);
    });

    const unsubError = jarvisWS.on('_error', (msg: any) => {
      useJarvisStore.getState().setConnected(false, msg.error);
    });

    return () => {
      // Cleanup subscriptions
      unsubConnected();
      unsubDisconnected();
      unsubError();
      jarvisWS.disconnect();
    };
  }, []);

  return (
    <div className="min-h-screen bg-gray-900 text-white flex flex-col items-center justify-center font-sans">
      <div className="text-center p-8 bg-gray-800 rounded-xl shadow-2xl border border-gray-700 max-w-md w-full">
        <h1 className="text-3xl font-bold mb-6 text-blue-400">JARVIS</h1>
        
        <div className="mb-8">
          <div className="relative inline-block">
            {/* Simple static brain placeholder for Phase 0 */}
            <div className={`w-32 h-32 rounded-full flex items-center justify-center transition-all duration-500
              ${isConnected ? 'bg-blue-900 shadow-[0_0_30px_rgba(59,130,246,0.5)]' : 'bg-red-900 shadow-[0_0_30px_rgba(239,68,68,0.3)]'}
            `}>
              <span className="text-4xl">🧠</span>
            </div>
            
            {/* Status indicator dot */}
            <div className={`absolute bottom-2 right-2 w-4 h-4 rounded-full border-2 border-gray-800
              ${isConnected ? 'bg-green-500 shadow-[0_0_10px_rgba(34,197,94,0.8)]' : 'bg-red-500'}
            `} />
          </div>
        </div>

        <div className="space-y-3">
          <div className="p-3 bg-gray-900 rounded-lg">
            <p className="text-sm text-gray-400 uppercase tracking-wider mb-1">Connection Status</p>
            <p className={`font-mono text-sm ${isConnected ? 'text-green-400' : 'text-red-400'}`}>
              {isConnected ? 'CONNECTED' : 'DISCONNECTED'}
            </p>
          </div>
          
          <div className="p-3 bg-gray-900 rounded-lg">
            <p className="text-sm text-gray-400 uppercase tracking-wider mb-1">System State</p>
            <p className="font-mono text-sm text-blue-300">
              {statusText}
            </p>
          </div>
          
          <div className="p-3 bg-gray-900 rounded-lg">
            <p className="text-sm text-gray-400 uppercase tracking-wider mb-1">Brain State</p>
            <p className="font-mono text-sm text-purple-300 capitalize">
              {brainState}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
