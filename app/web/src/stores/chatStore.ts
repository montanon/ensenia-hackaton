import { create } from 'zustand';
import type { Message } from '../types/message';

interface ChatStore {
  messages: Message[];
  isStreaming: boolean;
  streamingContent: string;
  currentMessageId: number | null;

  addMessage: (message: Message) => void;
  updateMessage: (id: number, updates: Partial<Message>) => void;
  appendStreamChunk: (chunk: string) => void;
  completeStream: (messageId?: number) => void;
  startStreaming: () => void;
  clearMessages: () => void;
  setMessages: (messages: Message[]) => void;
}

export const useChatStore = create<ChatStore>((set) => ({
  messages: [],
  isStreaming: false,
  streamingContent: '',
  currentMessageId: null,

  addMessage: (message) => set((state) => ({
    messages: [...state.messages, message]
  })),

  updateMessage: (id, updates) => set((state) => ({
    messages: state.messages.map(msg =>
      msg.id === id ? { ...msg, ...updates } : msg
    )
  })),

  appendStreamChunk: (chunk) => set((state) => ({
    streamingContent: state.streamingContent + chunk,
    isStreaming: true
  })),

  completeStream: (messageId) => set((state) => {
    const newMessage: Message = {
      id: messageId,
      role: 'assistant',
      content: state.streamingContent,
      timestamp: new Date().toISOString()
    };

    return {
      messages: [...state.messages, newMessage],
      streamingContent: '',
      isStreaming: false,
      currentMessageId: messageId ?? null
    };
  }),

  startStreaming: () => set({
    isStreaming: true,
    streamingContent: ''
  }),

  clearMessages: () => set({
    messages: [],
    streamingContent: '',
    isStreaming: false
  }),

  setMessages: (messages) => set({ messages }),
}));
