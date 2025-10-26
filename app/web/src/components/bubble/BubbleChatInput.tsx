import React, { useState, type KeyboardEvent } from 'react';
import { useSessionStore } from '../../stores/sessionStore';
import { useChatStore } from '../../stores/chatStore';
import { websocketService } from '../../services/websocket';

export const BubbleChatInput: React.FC = () => {
  const [message, setMessage] = useState('');
  const { currentSession } = useSessionStore();
  const { addMessage, startStreaming } = useChatStore();

  const handleSend = () => {
    console.log('[ChatInput] handleSend called, message:', message, 'currentSession:', currentSession?.id);
    if (!message.trim() || !currentSession) {
      console.warn('[ChatInput] Cannot send - message empty or no session');
      return;
    }

    console.log('[ChatInput] Adding message to store:', message);
    addMessage({
      role: 'user',
      content: message.trim(),
      timestamp: new Date().toISOString(),
    });

    console.log('[ChatInput] Starting streaming');
    startStreaming();
    console.log('[ChatInput] Sending message via WebSocket:', message);
    websocketService.sendMessage(message.trim());
    setMessage('');
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="bg-white p-4">
      <div className="space-y-2">
        <textarea
          value={message}
          onChange={(e) => {
            setMessage(e.target.value);
            // Auto-resize based on content
            e.target.style.height = 'auto';
            e.target.style.height = `${Math.min(e.target.scrollHeight, 300)}px`;
          }}
          onKeyPress={handleKeyPress}
          placeholder={currentSession ? "Escribe tu mensaje..." : "Crea una sesión para comenzar"}
          aria-label="Mensaje de chat"
          disabled={!currentSession}
          className="w-full px-4 py-3 resize-none focus:outline-none focus:ring-2 focus:ring-blue-400 disabled:bg-gray-100 disabled:text-gray-400 bg-white rounded-lg border border-gray-200 shadow-sm overflow-y-auto"
          style={{ minHeight: '150px', maxHeight: '300px' }}
        />
        <div className="flex justify-end">
          <button
            onClick={handleSend}
            disabled={!currentSession || !message.trim()}
            className="px-3 py-1 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed text-white text-xs font-medium rounded-full flex items-center gap-1.5 transition-colors shadow-sm hover:shadow-md"
            aria-label="Enviar mensaje"
          >
            <span>Enviar</span>
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};
