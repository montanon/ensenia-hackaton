import React, { useEffect, useState } from 'react';
import { useBubbleStore } from '../../stores/bubbleStore';
import { useSessionStore } from '../../stores/sessionStore';
import { useChatStore } from '../../stores/chatStore';
import { useAudioStore } from '../../stores/audioStore';
import { websocketService } from '../../services/websocket';
import { API_URL } from '../../utils/constants';
import { MessageList } from '../chat/MessageList';
import { ChatInput } from '../chat/ChatInput';
import { cn } from '../../utils/helpers';
import './bubble-chat-window.css';

export const BubbleChatWindow: React.FC = () => {
  const { isChatOpen, closeChat } = useBubbleStore();
  const { currentSession, outputMode } = useSessionStore();
  const {
    addMessage,
    appendStreamChunk,
    completeStream,
    startStreaming,
  } = useChatStore();
  const { setCurrentAudio, setSpeaking, setPlaying } = useAudioStore();
  const [isConnected, setIsConnected] = useState(false);
  const audioRef = React.useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    if (!currentSession || !isChatOpen) return;

    // Connect WebSocket when chat opens
    websocketService.connect(currentSession.id, {
      onConnected: () => {
        setIsConnected(true);
      },

      onTextChunk: (msg) => {
        appendStreamChunk(msg.content);
      },

      onMessageComplete: (msg) => {
        completeStream(msg.message_id);
      },

      onAudioReady: (msg) => {
        const audioUrl = `${API_URL}${msg.url}`;
        setCurrentAudio(audioUrl);

        // Auto-play if output mode is voice
        if (outputMode === 'voice') {
          if (audioRef.current) {
            audioRef.current.pause();
            audioRef.current = null;
          }

          const audio = new Audio(audioUrl);
          audioRef.current = audio;
          setSpeaking(true);
          setPlaying(true);

          audio.onplay = () => setSpeaking(true);
          audio.onended = () => {
            setSpeaking(false);
            setPlaying(false);
            audioRef.current = null;
          };
          audio.onerror = () => {
            setSpeaking(false);
            setPlaying(false);
            audioRef.current = null;
          };

          audio.play().catch(err => {
            console.error('[BubbleChat] Audio playback failed:', err);
            setSpeaking(false);
            setPlaying(false);
            audioRef.current = null;
          });
        }
      },

      onModeChanged: () => {
        // Mode changed
      },

      onError: (msg) => {
        console.error('[BubbleChat] WebSocket error:', msg.message);
      },

      onDisconnect: () => {
        setIsConnected(false);
      },
    });

    return () => {
      // Don't disconnect on unmount, keep connection alive
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, [currentSession, isChatOpen, outputMode, appendStreamChunk, completeStream, setCurrentAudio, setSpeaking, setPlaying]);

  // Update WebSocket mode when output mode changes
  useEffect(() => {
    if (isConnected && currentSession) {
      const wsMode = outputMode === 'voice' ? 'audio' : 'text';
      websocketService.setMode(wsMode);
    }
  }, [outputMode, isConnected, currentSession]);

  const handleSendMessage = (message: string) => {
    if (!currentSession || !isConnected) return;

    addMessage({
      role: 'user',
      content: message,
      timestamp: new Date().toISOString(),
    });

    startStreaming();
    websocketService.sendMessage(message);
  };

  if (!isChatOpen) return null;

  return (
    <div className={cn(
      'fixed bottom-24 right-6 z-40',
      'w-96 h-[500px]',
      'bubble-chat-window',
      isChatOpen ? 'bubble-chat-window-open' : ''
    )}>
      <div className="h-full bg-white rounded-lg shadow-2xl border border-gray-200 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-500 to-blue-600 text-white px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xl">🤖</span>
            <div>
              <h3 className="font-semibold text-sm">Asistente Ensenia</h3>
              {currentSession && (
                <p className="text-xs text-blue-100">
                  {currentSession.subject} - {currentSession.grade}° Básico
                </p>
              )}
            </div>
          </div>
          <button
            onClick={closeChat}
            className="text-white hover:text-blue-100 transition-colors text-xl"
            aria-label="Cerrar chat"
          >
            ✕
          </button>
        </div>

        {/* Connection Status */}
        {currentSession && (
          <div className="px-4 py-2 bg-gray-50 border-b border-gray-200 flex items-center justify-between text-xs">
            <span className="flex items-center gap-1">
              {isConnected ? (
                <>
                  <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                  <span className="text-gray-700">Conectado</span>
                </>
              ) : (
                <>
                  <span className="w-2 h-2 bg-red-500 rounded-full"></span>
                  <span className="text-gray-700">Desconectado</span>
                </>
              )}
            </span>
            <span className="text-gray-600">
              {outputMode === 'voice' ? '🔊 Audio' : '📖 Texto'}
            </span>
          </div>
        )}

        {/* No Session State */}
        {!currentSession && (
          <div className="flex-1 flex items-center justify-center p-6">
            <div className="text-center">
              <div className="text-4xl mb-3">🎓</div>
              <p className="text-gray-600 text-sm">
                Crea una sesión para comenzar
              </p>
            </div>
          </div>
        )}

        {/* Messages */}
        {currentSession && (
          <>
            <div className="flex-1 overflow-hidden">
              <MessageList />
            </div>

            {/* Input */}
            <div className="border-t border-gray-200">
              <ChatInput
                onSendMessage={handleSendMessage}
                disabled={!isConnected}
              />
            </div>
          </>
        )}
      </div>
    </div>
  );
};
