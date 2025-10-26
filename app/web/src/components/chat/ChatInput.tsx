import React, { useState, type KeyboardEvent } from 'react';
import { useSessionStore } from '../../stores/sessionStore';
import { Button } from '../ui/Button';
import { VoiceButton } from './VoiceButton';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, disabled }) => {
  const [message, setMessage] = useState('');
  const { inputMode } = useSessionStore();

  const handleSend = () => {
    if (message.trim() && !disabled) {
      onSendMessage(message.trim());
      setMessage('');
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleVoiceTranscript = (text: string) => {
    if (text.trim() && !disabled) {
      onSendMessage(text.trim());
    }
  };

  return (
    <div className="border-t border-gray-200 bg-white">
      {inputMode === 'text' ? (
        <div className="relative">
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Escribe tu mensaje..."
            aria-label="Mensaje de chat"
            disabled={disabled}
            className="w-full px-4 py-3 pr-16 resize-none focus:outline-none focus:ring-0 disabled:bg-gray-50 disabled:text-gray-400"
            style={{ minHeight: '120px', maxHeight: '200px' }}
          />
          <button
            onClick={handleSend}
            disabled={disabled || !message.trim()}
            className="absolute bottom-3 right-3 w-10 h-10 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed text-white rounded-full flex items-center justify-center transition-colors shadow-sm"
            aria-label="Enviar mensaje"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
      ) : (
        <div className="p-4">
          <VoiceButton onTranscript={handleVoiceTranscript} disabled={disabled} />
        </div>
      )}
    </div>
  );
};
