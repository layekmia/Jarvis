/**
 * Global Zustand store for Jarvis UI state.
 * Manages connection status, AI brain state, and conversation.
 */
import { create } from 'zustand';

// Brain states matching backend events
export type JarvisBrainState = 'idle' | 'listening' | 'thinking' | 'executing' | 'speaking' | 'error';

export interface ConversationMessage {
  id: string;
  role: 'user' | 'jarvis';
  text: string;
  timestamp: string;
}

interface JarvisStore {
  // === Connection ===
  isConnected: boolean;
  connectionError: string | null;

  // === Brain state ===
  brainState: JarvisBrainState;
  statusText: string;

  // === Conversation ===
  messages: ConversationMessage[];

  // === Actions ===
  setConnected: (connected: boolean, error?: string) => void;
  setBrainState: (state: JarvisBrainState, statusText?: string) => void;
  addMessage: (role: 'user' | 'jarvis', text: string) => void;
  clearMessages: () => void;
}

export const useJarvisStore = create<JarvisStore>((set) => ({
  // === Initial state ===
  isConnected: false,
  connectionError: null,
  brainState: 'idle',
  statusText: 'Initializing...',
  messages: [],

  // === Actions ===
  setConnected: (connected, error) =>
    set({
      isConnected: connected,
      connectionError: error ?? null,
      statusText: connected ? 'Connected to Jarvis backend' : `Disconnected${error ? `: ${error}` : ''}`,
      brainState: connected ? 'idle' : 'error',
    }),

  setBrainState: (state, statusText) =>
    set({
      brainState: state,
      statusText: statusText ?? getBrainStateText(state),
    }),

  addMessage: (role, text) =>
    set((prev) => ({
      messages: [
        ...prev.messages,
        {
          id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
          role,
          text,
          timestamp: new Date().toISOString(),
        },
      ],
    })),

  clearMessages: () => set({ messages: [] }),
}));

function getBrainStateText(state: JarvisBrainState): string {
  const texts: Record<JarvisBrainState, string> = {
    idle: 'Ready — waiting for wake word',
    listening: 'Listening...',
    thinking: 'Processing...',
    executing: 'Executing command...',
    speaking: 'Speaking...',
    error: 'Error — check backend connection',
  };
  return texts[state];
}
