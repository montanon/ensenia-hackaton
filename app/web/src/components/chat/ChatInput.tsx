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
    <div className="border-t border-gray-200 bg-white p-4">
      {inputMode === 'text' ? (
        <>
          <div className="flex gap-2 items-end">
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Escribe tu mensaje..."
              disabled={disabled}
              rows={1}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
              style={{ minHeight: '44px', maxHeight: '120px' }}
            />
            <Button
              onClick={handleSend}
              disabled={disabled || !message.trim()}
              variant="primary"
              className="px-6"
            >
              Enviar
            </Button>
          </div>
          <div className="mt-2 text-xs text-gray-500">
            Presiona Enter para enviar, Shift+Enter para nueva línea
          </div>
        </>
      ) : (
        <VoiceButton onTranscript={handleVoiceTranscript} disabled={disabled} />
      )}
    </div>
  );
};
