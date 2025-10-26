import React, { useState, useRef, useEffect } from 'react';
import { useBubbleStore } from '../../stores/bubbleStore';
import { useAudioStore } from '../../stores/audioStore';
import { useSessionStore } from '../../stores/sessionStore';
import { speechRecognitionService } from '../../services/speech';
import { websocketService } from '../../services/websocket';
import { cn } from '../../utils/helpers';
import microphoneIcon from '../../assets/microphone.svg';
import './bubble-animations.css';

export const BubbleAssistant: React.FC = () => {
  const { isChatOpen, isListening, toggleChat, setListening } = useBubbleStore();
  const { isSpeaking } = useAudioStore();
  const { currentSession, isInitializing, setInputMode, setOutputMode } = useSessionStore();
  const [transcript, setTranscript] = useState('');
  const holdTimerRef = useRef<NodeJS.Timeout | null>(null);
  const isHoldingRef = useRef(false);

  // Auto-switch modes based on chat state
  useEffect(() => {
    if (isChatOpen) {
      // Chat open → text mode
      setInputMode('text');
      setOutputMode('text');
    } else {
      // Chat closed → voice mode
      setInputMode('voice');
      setOutputMode('voice');
    }
  }, [isChatOpen, setInputMode, setOutputMode]);

  const startVoiceInput = () => {
    if (!currentSession || !speechRecognitionService.isAvailable()) return;

    setListening(true);
    setTranscript('');

    speechRecognitionService.start(
      (text, isFinal) => {
        setTranscript(text);
        if (isFinal && text.trim()) {
          // Send message via WebSocket
          websocketService.sendMessage(text);
          setListening(false);
          setTranscript('');
        }
      },
      (err) => {
        console.error('[Bubble] Speech recognition error:', err);
        setListening(false);
        setTranscript('');
      },
      () => {
        setListening(false);
      }
    );
  };

  const stopVoiceInput = () => {
    if (transcript.trim()) {
      websocketService.sendMessage(transcript);
    }
    speechRecognitionService.stop();
    setListening(false);
    setTranscript('');
  };

  const handleMouseDown = () => {
    isHoldingRef.current = true;
    holdTimerRef.current = setTimeout(() => {
      if (isHoldingRef.current) {
        startVoiceInput();
      }
    }, 300); // 300ms hold to activate voice
  };

  const handleMouseUp = () => {
    isHoldingRef.current = false;

    if (holdTimerRef.current) {
      clearTimeout(holdTimerRef.current);
      holdTimerRef.current = null;
    }

    if (isListening) {
      stopVoiceInput();
    } else {
      // Quick tap → toggle chat
      toggleChat();
    }
  };

  const handleMouseLeave = () => {
    if (isListening) {
      stopVoiceInput();
    }
    isHoldingRef.current = false;
    if (holdTimerRef.current) {
      clearTimeout(holdTimerRef.current);
      holdTimerRef.current = null;
    }
  };

  // Determine bubble state for visual feedback
  const getBubbleState = () => {
    if (isListening) return 'listening';
    if (isSpeaking) return 'speaking';
    return 'idle';
  };

  const bubbleState = getBubbleState();

  // Don't show bubble if no session or still initializing
  if (!currentSession || isInitializing) {
    return null;
  }

  return (
    <div className="fixed bottom-12 right-12 z-50 flex flex-col items-center gap-2">
      {/* Live Transcript */}
      {transcript && (
        <div className="max-w-xs p-3 bg-white border border-gray-200 rounded-lg shadow-lg mb-2 bubble-transcript">
          <p className="text-sm text-gray-900">{transcript}</p>
        </div>
      )}

      {/* Bubble */}
      <button
        type="button"
        onMouseDown={handleMouseDown}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseLeave}
        onTouchStart={handleMouseDown}
        onTouchEnd={handleMouseUp}
        className={cn(
          'bubble-assistant',
          `bubble-${bubbleState}`,
          'w-20 h-20 bg-gradient-to-br from-blue-500 to-blue-600',
          'shadow-lg hover:shadow-xl cursor-pointer',
          'flex items-center justify-center',
          'focus:outline-none focus:ring-4 focus:ring-blue-300',
          'relative overflow-visible',
          'transition-all duration-300 ease-in-out',
          isChatOpen && 'scale-0 opacity-0'
        )}
        aria-label={isChatOpen ? 'Close assistant' : 'Open assistant'}
        style={{
          willChange: 'transform, border-radius',
          transformOrigin: 'center center'
        }}
      >
        {/* Glow effect for listening */}
        {isListening && (
          <div className="absolute inset-0 bg-red-400 opacity-30 animate-pulse" />
        )}

        {/* Icon */}
        <img
          src={microphoneIcon}
          alt="Microphone"
          className={cn(
            'w-10 h-10 relative z-10',
            isListening && 'scale-110 animate-pulse',
            isSpeaking && 'scale-105'
          )}
        />
      </button>

      {/* Status indicator */}
      {!isChatOpen && (
        <div className="text-xs text-gray-600 bg-white px-3 py-1.5 rounded-full shadow-sm text-center">
          {isListening
            ? 'Escuchando...'
            : isSpeaking
            ? 'Hablando...'
            : 'Click o mantén presionado'}
        </div>
      )}
    </div>
  );
};
