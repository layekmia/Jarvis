/**
 * Global Zustand store for Jarvis UI state.
 * Extended for Phase 1: system stats, memory, conversation.
 */
import { create } from 'zustand';

// ─── Types ───────────────────────────────────────────────────────────────────

export type JarvisBrainState =
  | 'idle'
  | 'listening'
  | 'thinking'
  | 'executing'
  | 'speaking'
  | 'error';

export interface ConversationMessage {
  id: string;
  role: 'user' | 'jarvis';
  text: string;
  timestamp: string;
}

export interface SystemStats {
  cpu: number;      // 0-100
  ram: number;      // 0-100
  network: 'online' | 'offline' | 'slow';
  uptime: string;   // e.g. "2h 14m"
}

export interface MemoryEntry {
  id: string;
  label: string;
  value: string;
  category: 'context' | 'preference' | 'task' | 'fact';
  timestamp: string;
}

export type TaskStepStatus = 'pending' | 'running' | 'done' | 'failed' | 'awaiting_confirmation';

export interface TaskStep {
  id: number;
  description: string;
  status: TaskStepStatus;
}

export interface ActiveTask {
  total: number;
  current: number;
  completed: number;
  done: boolean;
  phase?: 'planning' | 'executing' | 'verifying' | 'complete' | 'failed';
  steps: TaskStep[];
}

export interface VisionData {
  image_base64: string;
  action: string;
  details: string;
  result?: string;
  timestamp: string;
}

export interface SystemLog {
  id: string;
  timestamp: string;
  message: string;
  type: 'info' | 'error' | 'success';
}

export interface JarvisSettings {
  wakeWord: string;
  voiceId: string;
  language: string;
}

// ─── Store Interface ──────────────────────────────────────────────────────────

interface JarvisStore {
  // === Connection ===
  isConnected: boolean;
  connectionError: string | null;

  // === Brain state ===
  brainState: JarvisBrainState;
  statusText: string;

  // === Conversation ===
  messages: ConversationMessage[];

  // === System stats ===
  systemStats: SystemStats;

  // === Active memory ===
  memoryEntries: MemoryEntry[];

  // === Phase 8: Agentic task progress ===
  activeTask: ActiveTask | null;

  // === Phase 9: Vision data ===
  visionData: VisionData | null;

  // === Phase 10: Settings & Logs ===
  settings: JarvisSettings;
  systemLogs: SystemLog[];

  // === Actions ===
  setConnected: (connected: boolean, error?: string) => void;
  setBrainState: (state: JarvisBrainState, statusText?: string) => void;
  addMessage: (role: 'user' | 'jarvis', text: string) => void;
  clearMessages: () => void;
  updateSystemStats: (stats: Partial<SystemStats>) => void;
  setMemoryEntries: (entries: MemoryEntry[]) => void;
  addMemoryEntry: (entry: Omit<MemoryEntry, 'id' | 'timestamp'>) => void;
  setTaskProgress: (task: ActiveTask | null) => void;
  setVisionData: (data: Partial<VisionData> | null) => void;
  updateSettings: (newSettings: Partial<JarvisSettings>) => void;
  addSystemLog: (message: string, type?: 'info' | 'error' | 'success') => void;
  clearSystemLogs: () => void;
}

// ─── Store Implementation ─────────────────────────────────────────────────────

export const useJarvisStore = create<JarvisStore>((set) => ({
  // === Initial state ===
  isConnected: false,
  connectionError: null,
  brainState: 'idle',
  statusText: 'Initializing...',
  messages: [],

  systemStats: {
    cpu: 0,
    ram: 0,
    network: 'online',
    uptime: '0m',
  },

  // Start with empty memory (fetched from backend)
  memoryEntries: [],

  // Phase 8: no active task initially
  activeTask: null,

  // Phase 9: no vision data initially
  visionData: null,

  // Phase 10: Settings and Logs
  settings: {
    wakeWord: 'Hey Jarvis',
    voiceId: 'eleven_v3_default',
    language: 'en-US'
  },
  systemLogs: [],

  // === Actions ===
  setConnected: (connected, error) =>
    set({
      isConnected: connected,
      connectionError: error ?? null,
      statusText: connected
        ? 'Connected to Jarvis backend'
        : `Disconnected${error ? `: ${error}` : ''}`,
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

  updateSystemStats: (stats) =>
    set((prev) => ({
      systemStats: { ...prev.systemStats, ...stats },
    })),

  setMemoryEntries: (entries) => set({ memoryEntries: entries }),

  addMemoryEntry: (entry) =>
    set((prev) => ({
      memoryEntries: [
        ...prev.memoryEntries,
        {
          ...entry,
          id: `mem-${Date.now()}-${Math.random().toString(36).slice(2)}`,
          timestamp: new Date().toISOString(),
        },
      ],
    })),

  setTaskProgress: (task) => set({ activeTask: task }),

  // Phase 9
  setVisionData: (data) =>
    set((state) => {
      if (!data) return { visionData: null };
      return {
        visionData: {
          ...(state.visionData || {
            image_base64: '',
            action: '',
            details: '',
            timestamp: new Date().toISOString(),
          }),
          ...data,
        },
      };
    }),

  // Phase 10
  updateSettings: (newSettings) =>
    set((state) => ({
      settings: { ...state.settings, ...newSettings }
    })),
    
  addSystemLog: (message, type = 'info') =>
    set((state) => {
      const newLog: SystemLog = {
        id: Math.random().toString(36).substr(2, 9),
        timestamp: new Date().toISOString(),
        message,
        type,
      };
      // Keep last 50 logs
      return { systemLogs: [newLog, ...state.systemLogs].slice(0, 50) };
    }),
    
  clearSystemLogs: () => set({ systemLogs: [] }),
}));

// ─── Helpers ──────────────────────────────────────────────────────────────────

function getBrainStateText(state: JarvisBrainState): string {
  const texts: Record<JarvisBrainState, string> = {
    idle: 'Ready — waiting for wake word',
    listening: 'Listening...',
    thinking: 'Processing your request...',
    executing: 'Executing command...',
    speaking: 'Speaking response...',
    error: 'Error — check backend connection',
  };
  return texts[state];
}
