import React from 'react';
import type { Message as MessageType } from '../../types/message';
import { cn } from '../../utils/helpers';
import { formatDate } from '../../utils/helpers';

interface MessageProps {
  message: MessageType;
  onPlayAudio?: (url: string) => void;
}

export const Message: React.FC<MessageProps> = ({ message, onPlayAudio }) => {
  const isUser = message.role === 'user';

  return (
    <div
      className={cn(
        'flex mb-4 px-4 animate-in slide-in-from-bottom-2 duration-300',
        isUser ? 'justify-end' : 'justify-start'
      )}
    >
      <div className={cn(
        'max-w-[75%] rounded-2xl px-4 py-3 shadow-sm',
        isUser
          ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-br-md'
          : 'bg-white text-gray-900 border border-blue-100 rounded-bl-md'
      )}>
        {/* Message Content */}
        <div className="whitespace-pre-wrap break-words text-sm leading-relaxed">
          {message.content}
        </div>

        {/* Audio Player */}
        {message.audio_url && onPlayAudio && (
          <button
            onClick={() => onPlayAudio(message.audio_url!)}
            className={cn(
              'mt-2 flex items-center gap-2 text-xs px-3 py-1.5 rounded-full font-medium transition-colors',
              isUser
                ? 'bg-blue-700 hover:bg-blue-800'
                : 'bg-blue-50 hover:bg-blue-100 text-blue-700'
            )}
          >
            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
              <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
            </svg>
            <span>Reproducir</span>
          </button>
        )}

        {/* Timestamp */}
        {message.timestamp && (
          <div className={cn(
            'mt-1.5 text-xs font-medium',
            isUser ? 'text-blue-100' : 'text-gray-400'
          )}>
            {formatDate(message.timestamp)}
          </div>
        )}
      </div>
    </div>
  );
};
