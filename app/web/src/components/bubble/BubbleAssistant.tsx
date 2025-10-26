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
  const holdTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isHoldingRef = useRef(false);

  // Initialize WebSocket when component mounts (if session exists)
  useEffect(() => {
    console.log('[Bubble] useEffect triggered - currentSession:', currentSession?.id, 'isInitializing:', isInitializing, 'isConnected:', websocketService.isConnected());

    if (currentSession && !isInitializing && !websocketService.isConnected()) {
      console.log('[Bubble] Connecting WebSocket for session:', currentSession.id);
      websocketService.connect(currentSession.id, {
        onConnected: () => {
          console.log('[Bubble] WebSocket connected successfully');
        },
        onError: (msg) => {
          console.error('[Bubble] WebSocket error:', msg.message);
        },
        onDisconnect: () => {
          console.log('[Bubble] WebSocket disconnected');
        },
      });
    } else if (currentSession && websocketService.isConnected()) {
      console.log('[Bubble] WebSocket already connected, skipping');
    }

    return () => {
      // Keep connection alive, don't disconnect
    };
  }, [currentSession, isInitializing]);

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
    console.log('[Bubble] startVoiceInput called');
    if (!currentSession || !speechRecognitionService.isAvailable()) {
      console.log('[Bubble] Cannot start voice input - session:', !!currentSession, 'speechAvailable:', speechRecognitionService.isAvailable());
      return;
    }

    console.log('[Bubble] Starting voice input');
    setListening(true);
    setTranscript('');

    speechRecognitionService.start(
      (text, isFinal) => {
        console.log('[Bubble] Transcript received:', { text, isFinal });
        setTranscript(text);
        if (isFinal && text.trim()) {
          console.log('[Bubble] Final transcript, sending via WebSocket:', text);
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
        console.log('[Bubble] Speech recognition ended');
        setListening(false);
      }
    );
  };

  const stopVoiceInput = () => {
    console.log('[Bubble] stopVoiceInput called, transcript:', transcript);
    if (transcript.trim()) {
      console.log('[Bubble] Stopping voice input and sending message:', transcript);
      websocketService.sendMessage(transcript);
    }
    speechRecognitionService.stop();
    setListening(false);
    setTranscript('');
  };

  const handleMouseDown = () => {
    console.log('[Bubble] handleMouseDown');
    isHoldingRef.current = true;
    holdTimerRef.current = setTimeout(() => {
      console.log('[Bubble] Hold timer fired (300ms)');
      if (isHoldingRef.current) {
        startVoiceInput();
      }
    }, 300); // 300ms hold to activate voice
  };

  const handleMouseUp = () => {
    console.log('[Bubble] handleMouseUp, isListening:', isListening);
    isHoldingRef.current = false;

    if (holdTimerRef.current) {
      clearTimeout(holdTimerRef.current);
      holdTimerRef.current = null;
    }

    if (isListening) {
      console.log('[Bubble] User released, stopping voice input');
      stopVoiceInput();
    } else {
      console.log('[Bubble] Quick tap detected, toggling chat');
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
    <div className="fixed bottom-12 right-12 z-50">
      {/* Bubble - Fixed size and position to prevent layout shifts */}
      <button
        type="button"
        onMouseDown={handleMouseDown}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseLeave}
        onTouchStart={handleMouseDown}
        onTouchEnd={handleMouseUp}
        className={cn(
          'bubble-assistant',
          'w-20 h-20 bg-gradient-to-br from-blue-500 to-blue-600',
          'shadow-lg hover:shadow-xl cursor-pointer',
          'flex items-center justify-center',
          'focus:outline-none focus:ring-4 focus:ring-blue-300',
          'relative overflow-visible',
          'transition-shadow duration-200 ease-in-out',
          isChatOpen && 'opacity-0 pointer-events-none'
        )}
        aria-label={isChatOpen ? 'Close assistant' : 'Open assistant'}
        style={{
          willChange: 'transform',
          transformOrigin: 'center center',
          transition: isChatOpen ? 'opacity 300ms ease-in-out' : 'none'
        }}
      >
        {/* Glow effect for listening */}
        {isListening && (
          <div className="absolute inset-0 bg-red-400 opacity-30 animate-pulse rounded-full" />
        )}

        {/* Icon */}
        <img
          src={microphoneIcon}
          alt="Microphone"
          className={cn(
            'w-10 h-10 relative z-10 transition-transform duration-200',
            isListening && 'scale-110',
            isSpeaking && 'scale-105'
          )}
        />
      </button>

      {/* Transcript - Absolute positioned to not affect bubble */}
      {transcript && (
        <div className="absolute bottom-24 left-1/2 -translate-x-1/2 mb-2 whitespace-nowrap pointer-events-none">
          <div className="max-w-xs p-3 bg-white border border-gray-200 rounded-lg shadow-lg">
            <p className="text-sm text-gray-900">{transcript}</p>
          </div>
        </div>
      )}

      {/* Status indicator - Absolute positioned to not affect bubble */}
      {!isChatOpen && (
        <div className="absolute top-24 left-1/2 -translate-x-1/2 mt-2 whitespace-nowrap pointer-events-none">
          <div className="text-xs text-gray-600 bg-white px-3 py-1.5 rounded-full shadow-sm">
            {isListening
              ? 'Escuchando...'
              : isSpeaking
              ? 'Hablando...'
              : 'Click o mantén presionado'}
          </div>
        </div>
      )}
    </div>
  );
};
