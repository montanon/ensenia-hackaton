import React, { useEffect, useState, useRef } from 'react';
import { useBubbleStore } from '../../stores/bubbleStore';
import { useSessionStore } from '../../stores/sessionStore';
import { useChatStore } from '../../stores/chatStore';
import { useAudioStore } from '../../stores/audioStore';
import { websocketService } from '../../services/websocket';
import { API_URL } from '../../utils/constants';
import { MessageList } from '../chat/MessageList';
import { ChatInput } from '../chat/ChatInput';
import { TypingIndicator } from './TypingIndicator';
import { SoundWaveVisualization } from './SoundWaveVisualization';
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
    isStreaming,
  } = useChatStore();
  const { setCurrentAudio, setSpeaking, setPlaying, isSpeaking } = useAudioStore();
  const [isConnected, setIsConnected] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const resizeRef = useRef<HTMLDivElement>(null);
  const [windowSize, setWindowSize] = useState({ width: 384, height: 500 });
  const [isResizing, setIsResizing] = useState(false);
  const resizeStartRef = useRef({ x: 0, y: 0, width: 0, height: 0 });

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

  // Handle resize from top-left corner
  const handleResizeStart = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
    resizeStartRef.current = {
      x: e.clientX,
      y: e.clientY,
      width: windowSize.width,
      height: windowSize.height,
    };
  };

  useEffect(() => {
    if (!isResizing) return;

    const handleResizeMove = (e: MouseEvent) => {
      const deltaX = resizeStartRef.current.x - e.clientX;
      const deltaY = resizeStartRef.current.y - e.clientY;

      const newWidth = Math.max(320, Math.min(600, resizeStartRef.current.width + deltaX));
      const newHeight = Math.max(400, Math.min(700, resizeStartRef.current.height + deltaY));

      setWindowSize({ width: newWidth, height: newHeight });
    };

    const handleResizeEnd = () => {
      setIsResizing(false);
    };

    document.addEventListener('mousemove', handleResizeMove);
    document.addEventListener('mouseup', handleResizeEnd);

    return () => {
      document.removeEventListener('mousemove', handleResizeMove);
      document.removeEventListener('mouseup', handleResizeEnd);
    };
  }, [isResizing]);

  if (!isChatOpen) return null;

  return (
    <div
      ref={resizeRef}
      className={cn(
        'fixed bottom-24 right-12 z-40',
        'bubble-chat-window resize overflow-auto',
        isChatOpen ? 'bubble-chat-window-open' : ''
      )}
      style={{
        width: `${windowSize.width}px`,
        height: `${windowSize.height}px`,
        minWidth: '320px',
        maxWidth: '600px',
        minHeight: '400px',
        maxHeight: '700px',
      }}
    >
      <div className="h-full bg-white rounded-2xl shadow-[0_20px_60px_-15px_rgba(59,130,246,0.5)] border border-blue-100 flex flex-col overflow-hidden backdrop-blur-sm relative">
        {/* Resize Handle - Top Left */}
        <div
          onMouseDown={handleResizeStart}
          className="absolute top-0 left-0 w-8 h-8 cursor-nwse-resize z-50 group"
        >
          <div className="absolute top-2 left-2 w-4 h-4 flex flex-col gap-0.5 items-start pointer-events-none">
            <div className="w-3 h-0.5 bg-white/40 group-hover:bg-white/60 rounded-full transition-colors" />
            <div className="w-2 h-0.5 bg-white/40 group-hover:bg-white/60 rounded-full transition-colors" />
            <div className="w-1 h-0.5 bg-white/40 group-hover:bg-white/60 rounded-full transition-colors" />
          </div>
        </div>

        {/* Header */}
        <div className="bg-gradient-to-r from-blue-500 via-blue-600 to-blue-700 text-white px-5 py-3 flex items-center justify-between relative">
          <div>
            <h3 className="font-semibold text-sm">Asistente</h3>
            {currentSession && (
              <p className="text-xs text-blue-100">
                {currentSession.subject} - {currentSession.grade}° Básico
              </p>
            )}
          </div>
          <button
            onClick={closeChat}
            className="w-7 h-7 hover:bg-white/20 rounded-full transition-colors flex items-center justify-center"
            aria-label="Cerrar chat"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Sound Wave Visualization for Voice Mode */}
        {currentSession && outputMode === 'voice' && isSpeaking && (
          <div className="px-4 py-2 bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-blue-100">
            <SoundWaveVisualization />
          </div>
        )}

        {/* No Session State */}
        {!currentSession && (
          <div className="flex-1 flex items-center justify-center p-6">
            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 bg-blue-100 rounded-full flex items-center justify-center animate-pulse">
                <div className="w-8 h-8 bg-blue-500 rounded-full animate-ping-slow" />
              </div>
              <p className="text-gray-600 text-sm">
                Crea una sesión para comenzar
              </p>
            </div>
          </div>
        )}

        {/* Messages */}
        {currentSession && (
          <>
            <div className="flex-1 overflow-hidden bg-gradient-to-b from-gray-50 to-white">
              <MessageList />

              {/* Typing Indicator */}
              {isStreaming && (
                <div className="px-4 pb-4">
                  <TypingIndicator />
                </div>
              )}
            </div>

            {/* Input */}
            <div className="border-t border-blue-100 bg-white">
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
