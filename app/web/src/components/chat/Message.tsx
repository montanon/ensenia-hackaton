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
    <div className={cn('flex', isUser ? 'justify-end' : 'justify-start')}>
      <div className={cn(
        'max-w-[70%] rounded-lg px-4 py-2 shadow-sm',
        isUser
          ? 'bg-blue-600 text-white'
          : 'bg-white text-gray-900 border border-gray-200'
      )}>
        {/* Message Content */}
        <div className="whitespace-pre-wrap break-words">
          {message.content}
        </div>

        {/* Audio Player */}
        {message.audio_url && onPlayAudio && (
          <button
            onClick={() => onPlayAudio(message.audio_url!)}
            className={cn(
              'mt-2 flex items-center gap-1 text-sm px-2 py-1 rounded',
              isUser
                ? 'bg-blue-700 hover:bg-blue-800'
                : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
            )}
          >
            <span>▶️</span>
            <span>Reproducir audio</span>
          </button>
        )}

        {/* Timestamp */}
        {message.timestamp && (
          <div className={cn(
            'mt-1 text-xs',
            isUser ? 'text-blue-100' : 'text-gray-500'
          )}>
            {formatDate(message.timestamp)}
          </div>
        )}
      </div>
    </div>
  );
};
