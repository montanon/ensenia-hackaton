import React, { useEffect, useRef } from 'react';
import { useChatStore } from '../../stores/chatStore';
import { useAudioStore } from '../../stores/audioStore';
import { Message } from './Message';

export const MessageList: React.FC = () => {
  const { messages, isStreaming, streamingContent } = useChatStore();
  const { isSpeaking } = useAudioStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingContent]);

  const handlePlayAudio = (url: string) => {
    const audio = new Audio(url);
    audio.play();
  };

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {/* Empty State */}
      {messages.length === 0 && !isStreaming && (
        <div className="h-full flex items-center justify-center">
          <div className="text-center text-gray-500">
            <div className="text-5xl mb-3">💬</div>
            <p className="text-lg">Comienza la conversación</p>
            <p className="text-sm">Envía un mensaje para empezar</p>
          </div>
        </div>
      )}

      {/* Messages */}
      {messages.map((message, index) => (
        <Message
          key={message.id || index}
          message={message}
          onPlayAudio={handlePlayAudio}
        />
      ))}

      {/* Streaming Message */}
      {isStreaming && streamingContent && (
        <div className="flex justify-start">
          <div className="max-w-[70%] rounded-lg px-4 py-2 bg-white border border-gray-200 shadow-sm">
            <div className="whitespace-pre-wrap break-words text-gray-900">
              {streamingContent}
              <span className="inline-block w-2 h-4 bg-blue-600 ml-1 animate-pulse" />
            </div>
          </div>
        </div>
      )}

      {/* Speaking Indicator */}
      {isSpeaking && (
        <div className="flex justify-start">
          <div className="px-4 py-2 bg-purple-100 border border-purple-200 rounded-lg flex items-center gap-2">
            <span className="text-2xl animate-pulse">🎙️</span>
            <span className="text-sm text-purple-900 font-medium">Hablando...</span>
          </div>
        </div>
      )}

      <div ref={messagesEndRef} />
    </div>
  );
};
