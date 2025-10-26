import React, { useEffect, useState, useRef } from 'react';
import { useBubbleStore } from '../../stores/bubbleStore';
import { useSessionStore } from '../../stores/sessionStore';
import { useChatStore } from '../../stores/chatStore';
import { useAudioStore } from '../../stores/audioStore';
import { websocketService } from '../../services/websocket';
import { API_URL } from '../../utils/constants';
import { MessageList } from '../chat/MessageList';
import { TypingIndicator } from './TypingIndicator';
import { SoundWaveVisualization } from './SoundWaveVisualization';
import { BubbleChatInput } from './BubbleChatInput';
import { cn } from '../../utils/helpers';
import './bubble-chat-window.css';

export const BubbleChatWindow: React.FC = () => {
  const { isChatOpen, closeChat } = useBubbleStore();
  const { currentSession, isInitializing, outputMode } = useSessionStore();
  const {
    appendStreamChunk,
    completeStream,
    isStreaming,
  } = useChatStore();
  const { setCurrentAudio, setSpeaking, setPlaying, isSpeaking } = useAudioStore();
  const [isConnected, setIsConnected] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const resizeRef = useRef<HTMLDivElement>(null);
  const [panelWidth, setPanelWidth] = useState(384);
  const [isResizing, setIsResizing] = useState(false);
  const resizeStartRef = useRef({ x: 0, width: 0 });

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

  // Handle resize from left edge
  const handleResizeStart = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
    resizeStartRef.current = {
      x: e.clientX,
      width: panelWidth,
    };
  };

  useEffect(() => {
    if (!isResizing) return;

    const handleResizeMove = (e: MouseEvent) => {
      const deltaX = resizeStartRef.current.x - e.clientX;
      const newWidth = Math.max(320, Math.min(800, resizeStartRef.current.width + deltaX));
      setPanelWidth(newWidth);
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

  // Don't render chat window if no session or still initializing
  if (!currentSession || isInitializing) {
    return null;
  }

  return (
    <div
      ref={resizeRef}
      className={cn(
        'h-screen z-40 flex-shrink-0',
        isChatOpen ? 'bubble-chat-panel-open' : 'bubble-chat-panel'
      )}
      style={{
        width: isChatOpen ? `${panelWidth}px` : '0px',
      }}
    >
      <div
        className="h-full bg-white shadow-[-20px_0_60px_-15px_rgba(59,130,246,0.5)] border-l border-blue-100 flex flex-col overflow-hidden backdrop-blur-sm relative"
        style={{ width: `${panelWidth}px` }}
      >
        {/* Resize Handle - Left Edge */}
        <div
          onMouseDown={handleResizeStart}
          className="absolute top-0 left-0 w-2 h-full cursor-ew-resize z-50 group hover:bg-blue-500/10 transition-colors"
        >
          <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-12 bg-blue-300/50 group-hover:bg-blue-500 rounded-r-full transition-colors" />
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

        {/* Messages Area */}
        <div className="flex-1 overflow-auto bg-gradient-to-b from-gray-50 to-white p-4">
          <MessageList />

          {/* Typing Indicator */}
          {isStreaming && (
            <div className="px-4 pb-4">
              <TypingIndicator />
            </div>
          )}
        </div>

        {/* Chat Input */}
        <BubbleChatInput />
      </div>
    </div>
  );
};
