/**
 * App.tsx — Phase 1 Jarvis UI
 *
 * Layout (3-column, full-screen):
 *   LEFT  : System Status + Active Memory
 *   CENTER: Animated Brain + State Info
 *   RIGHT : Conversation Panel
 *   BOTTOM: Dev State Controls (Phase 1 only)
 */
import { useEffect, useCallback } from 'react';
import { jarvisWS } from './lib/websocket';
import { useJarvisStore, type ActiveTask } from './stores/jarvisStore';
import { StatusBar } from './components/StatusBar';
import { CenterBrainSection } from './components/CenterBrainSection';
import { ConversationPanel } from './components/ConversationPanel';
import { SystemStatusPanel } from './components/SystemStatusPanel';
import { ActiveMemoryPanel } from './components/ActiveMemoryPanel';
import { BrainStateControls } from './components/BrainStateControls';
import { TaskProgressPanel } from './components/TaskProgressPanel';

// Demo messages to simulate a conversation
const DEMO_MESSAGES = [
  { role: 'user' as const, text: 'Jarvis, আজকের আবহাওয়া কেমন?' },
  { role: 'jarvis' as const, text: 'আজকের ঢাকার তাপমাত্রা ৩২°C। আংশিক মেঘলা আকাশ, সন্ধ্যায় বৃষ্টির সম্ভাবনা আছে।' },
  { role: 'user' as const, text: 'Open Chrome and go to YouTube' },
  { role: 'jarvis' as const, text: 'Opening Chrome and navigating to YouTube. Done!' },
];

let demoIndex = 0;

function App() {
  const { setConnected, addMessage, setMemoryEntries, setTaskProgress } = useJarvisStore();

  // WebSocket connection management
  useEffect(() => {
    jarvisWS.connect();

    const unsubConnected = jarvisWS.on('_connected', () => {
      setConnected(true);
    });

    const unsubDisconnected = jarvisWS.on('_disconnected', (msg: unknown) => {
      const m = msg as { code?: number };
      setConnected(false, `Code: ${m?.code ?? 'unknown'}`);
    });

    const unsubError = jarvisWS.on('_error', (msg: unknown) => {
      const m = msg as { error?: string };
      setConnected(false, m?.error ?? 'WebSocket error');
    });

    // Handle brain state changes from backend
    const unsubBrainState = jarvisWS.on('brain_state', (data: unknown) => {
      const d = data as { state?: string; status?: string };
      if (d?.state) {
        useJarvisStore.getState().setBrainState(
          d.state as ReturnType<typeof useJarvisStore.getState>['brainState'],
          d.status
        );
      }
    });

    // Handle conversation messages from backend
    const unsubMessage = jarvisWS.on('message', (data: unknown) => {
      const d = data as { role?: string; text?: string };
      if (d?.role && d?.text) {
        addMessage(d.role as 'user' | 'jarvis', d.text);
      }
    });

    // Handle active memory sync from backend
    const unsubMemory = jarvisWS.on('set_memory', (data: unknown) => {
      const d = data as { entries?: any[] };
      if (d?.entries && Array.isArray(d.entries)) {
        setMemoryEntries(d.entries);
      }
    });

    // Handle Phase 8 agentic task progress events
    const unsubTaskProgress = jarvisWS.on('task_progress', (data: unknown) => {
      const d = data as ActiveTask & { done?: boolean };
      if (d) {
        if (d.done) {
          // Keep showing completed state briefly then clear
          setTaskProgress({ ...d, done: true });
          setTimeout(() => setTaskProgress(null), 4000);
        } else {
          setTaskProgress(d);
        }
      }
    });

    return () => {
      unsubConnected();
      unsubDisconnected();
      unsubError();
      unsubBrainState();
      unsubMessage();
      unsubMemory();
      unsubTaskProgress();
      jarvisWS.disconnect();
    };
  }, [setConnected, addMessage, setMemoryEntries, setTaskProgress]);

  // Add demo messages for Phase 1 UI testing
  const handleAddDemoMessage = useCallback(() => {
    const msg = DEMO_MESSAGES[demoIndex % DEMO_MESSAGES.length];
    addMessage(msg.role, msg.text);
    demoIndex++;
  }, [addMessage]);

  return (
    <div className="h-screen w-screen overflow-hidden grid-bg flex flex-col">
      {/* Scanline overlay */}
      <div className="scanline-overlay" />

      {/* Top status bar */}
      <StatusBar />

      {/* Main 3-column layout */}
      <div className="flex-1 grid grid-cols-[260px_1fr_280px] gap-4 p-4 min-h-0">

        {/* LEFT COLUMN: System + Memory */}
        <div className="flex flex-col gap-4 min-h-0">
          <SystemStatusPanel />
          <div className="flex-1 min-h-0">
            <ActiveMemoryPanel />
          </div>
        </div>

        {/* CENTER COLUMN: Brain + Task Progress */}
        <div className="flex flex-col items-center justify-center gap-4">
          <CenterBrainSection />

          {/* Phase 8: Task Progress Panel — appears during multi-step tasks */}
          <div className="w-full max-w-sm">
            <TaskProgressPanel />
          </div>

          {/* Dev Controls — Phase 1 only */}
          <div className="w-full max-w-xs">
            <BrainStateControls onAddDemoMessage={handleAddDemoMessage} />
          </div>
        </div>

        {/* RIGHT COLUMN: Conversation */}
        <div className="min-h-0">
          <ConversationPanel />
        </div>

      </div>

      {/* Bottom status strip */}
      <div className="px-6 py-1.5 border-t border-white/5 flex items-center justify-between">
        <span className="text-[9px] text-slate-700 font-mono">JARVIS AI SYSTEM — PHASE 1 BUILD</span>
        <span className="text-[9px] text-slate-700 font-mono">WS ws://127.0.0.1:8765</span>
      </div>
    </div>
  );
}

export default App;
