import React, { useState, useEffect, useRef, useCallback } from 'react';
import { speechRecognitionService } from '../../services/speech';
import { getAudioRecordingService, AudioRecordingService } from '../../services/audioRecording';
import { websocketService, type MessageHandler } from '../../services/websocket';
import { cn } from '../../utils/helpers';
import type { WSSTTResultMessage } from '../../types/websocket';

export type STTMode = 'browser' | 'backend';

interface VoiceButtonProps {
  onTranscript: (text: string) => void;
  disabled?: boolean;
  sttMode?: STTMode;
  onSTTModeChange?: (mode: STTMode) => void;
  onSTTResult?: (transcript: string) => void;
}

export const VoiceButton: React.FC<VoiceButtonProps> = ({
  onTranscript,
  disabled,
  sttMode = 'browser',
  onSTTModeChange,
  onSTTResult,
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSupported] = useState(speechRecognitionService.isAvailable());
  const [backendSTTSupported, setBackendSTTSupported] = useState(false);
  const [currentMode, setCurrentMode] = useState<STTMode>(sttMode);
  const [isConnected, setIsConnected] = useState(websocketService.isConnected());

  const audioRecorderRef = useRef<AudioRecordingService | null>(null);

  // Monitor WebSocket connection status for real-time updates
  useEffect(() => {
    const checkConnection = () => {
      const connected = websocketService.isConnected();
      setIsConnected(connected);
      setBackendSTTSupported(AudioRecordingService.isSupported() && connected);
    };

    // Check connection on mount
    checkConnection();

    // Check periodically in case connection changes
    const interval = setInterval(checkConnection, 1000);
    return () => clearInterval(interval);
  }, []);

  // Create STT result handler with proper typing
  const handleSTTResult = useCallback(
    (msg: WSSTTResultMessage) => {
      const resultTranscript = msg.transcript;
      setTranscript(resultTranscript);
      onSTTResult?.(resultTranscript);
      onTranscript(resultTranscript);
      setIsRecording(false);
      setTranscript('');
    },
    [onTranscript, onSTTResult]
  );

  // Initialize audio recorder for backend STT
  useEffect(() => {
    if (currentMode !== 'backend') {
      // Unregister handlers when switching away from backend mode
      websocketService.unregisterAdditionalHandlers();
      return;
    }

    // Create audio recorder with chunk callback
    audioRecorderRef.current = getAudioRecordingService({
      onChunkReceived: (chunk: string) => {
        // Send audio chunks to server in real-time
        websocketService.sendAudioChunk(chunk);
      },
      onError: (err: Error) => {
        console.error('Audio recording error:', err);
        setError(err.message);
        setIsRecording(false);
      },
    });

    // Register WebSocket handlers for STT results
    const sttHandlers: MessageHandler = {
      onSTTResult: handleSTTResult,
    };
    websocketService.registerAdditionalHandlers(sttHandlers);

    // Cleanup on unmount or mode change
    return () => {
      if (audioRecorderRef.current && isRecording) {
        audioRecorderRef.current.abort();
      }
      websocketService.unregisterAdditionalHandlers();
    };
  }, [currentMode, handleSTTResult, isRecording]);

  // Cleanup on component unmount
  useEffect(() => {
    return () => {
      if (isRecording) {
        if (currentMode === 'browser') {
          speechRecognitionService.abort();
        } else if (audioRecorderRef.current) {
          audioRecorderRef.current.abort();
        }
        websocketService.unregisterAdditionalHandlers();
      }
    };
  }, [isRecording, currentMode]);

  const startBrowserRecording = useCallback(() => {
    speechRecognitionService.start(
      (text, isFinal) => {
        setTranscript(text);
        if (isFinal) {
          onTranscript(text);
          setIsRecording(false);
          setTranscript('');
        }
      },
      (err) => {
        setError(err);
        setIsRecording(false);
        setTranscript('');
      },
      () => {
        setIsRecording(false);
      }
    );
  }, [onTranscript]);

  const startBackendRecording = useCallback(async () => {
    try {
      if (!audioRecorderRef.current) {
        throw new Error('Audio recorder not initialized');
      }
      await audioRecorderRef.current.startRecording();
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to start recording';
      setError(errorMsg);
      setIsRecording(false);
    }
  }, []);

  const startRecording = useCallback(async () => {
    if (disabled) return;

    if (currentMode === 'browser' && !isSupported) return;
    if (currentMode === 'backend' && !backendSTTSupported) return;

    setError(null);
    setTranscript('');
    setIsRecording(true);

    if (currentMode === 'browser') {
      startBrowserRecording();
    } else {
      await startBackendRecording();
    }
  }, [disabled, isSupported, currentMode, backendSTTSupported, startBrowserRecording, startBackendRecording]);

  const stopBrowserRecording = useCallback(() => {
    if (transcript) {
      onTranscript(transcript);
    }
    speechRecognitionService.stop();
    setIsRecording(false);
    setTranscript('');
  }, [transcript, onTranscript]);

  const stopBackendRecording = useCallback(async () => {
    try {
      if (!audioRecorderRef.current) return;

      await audioRecorderRef.current.stopRecording();

      // Add small delay to ensure all chunks are processed before signaling end
      await new Promise(resolve => setTimeout(resolve, 100));

      // Signal end of audio stream - triggers Deepgram transcription
      websocketService.sendAudioEnd();
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to stop recording';
      setError(errorMsg);
    }
  }, []);

  const stopRecording = useCallback(async () => {
    if (currentMode === 'browser') {
      stopBrowserRecording();
    } else {
      await stopBackendRecording();
    }
  }, [currentMode, stopBrowserRecording, stopBackendRecording]);

  const toggleSTTMode = useCallback(() => {
    const newMode: STTMode = currentMode === 'browser' ? 'backend' : 'browser';
    setCurrentMode(newMode);
    onSTTModeChange?.(newMode);
  }, [currentMode, onSTTModeChange]);

  // Determine which modes are available
  const browserAvailable = isSupported;
  const backendAvailable = AudioRecordingService.isSupported() && isConnected;
  const canToggleMode = browserAvailable && backendAvailable;

  // If no STT method is available at all
  if (!browserAvailable && !backendAvailable) {
    return (
      <div className="text-sm text-gray-500 px-4 py-2 bg-gray-100 rounded-lg">
        🎤 Micrófono no disponible en este navegador
      </div>
    );
  }

  return (
    <div className="w-full space-y-2">
      {/* STT Mode Toggle */}
      {canToggleMode && (
        <div className="flex gap-2">
          <button
            type="button"
            onClick={toggleSTTMode}
            disabled={disabled}
            className={cn(
              'flex-1 px-3 py-2 text-xs font-medium rounded-lg',
              'transition-colors duration-200',
              currentMode === 'browser'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300',
              disabled && 'opacity-50 cursor-not-allowed'
            )}
            title="Usar reconocimiento de voz del navegador"
          >
            🌐 Navegador
          </button>
          <button
            type="button"
            onClick={toggleSTTMode}
            disabled={disabled}
            className={cn(
              'flex-1 px-3 py-2 text-xs font-medium rounded-lg',
              'transition-colors duration-200',
              currentMode === 'backend'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300',
              disabled && 'opacity-50 cursor-not-allowed'
            )}
            title="Usar transcrición en servidor (más preciso)"
          >
            ☁️ Servidor
          </button>
        </div>
      )}

      {/* Recording Button */}
      <button
        type="button"
        onMouseDown={startRecording}
        onMouseUp={stopRecording}
        onMouseLeave={stopRecording}
        onTouchStart={startRecording}
        onTouchEnd={stopRecording}
        disabled={disabled}
        className={cn(
          'w-full px-6 py-4 rounded-lg font-medium',
          'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500',
          'bg-blue-600 text-white hover:bg-blue-700',
          'transition-colors duration-200',
          isRecording && 'recording-button',
          disabled && 'opacity-50 cursor-not-allowed'
        )}
      >
        <div className="flex items-center justify-center gap-2">
          <span
            className={cn(
              'text-2xl transition-transform duration-200',
              isRecording && 'recording-icon'
            )}
          >
            🎤
          </span>
          <span>
            {isRecording ? 'Grabando...' : 'Mantén presionado para hablar'}
          </span>
        </div>
      </button>

      <style>{`
        @keyframes breathe {
          0%, 100% {
            transform: scale(1);
            opacity: 1;
          }
          50% {
            transform: scale(0.98);
            opacity: 0.9;
          }
        }

        @keyframes icon-pulse {
          0%, 100% {
            transform: scale(1);
          }
          50% {
            transform: scale(1.1);
          }
        }

        .recording-button {
          animation: breathe 1.5s ease-in-out infinite;
        }

        .recording-icon {
          animation: icon-pulse 0.8s ease-in-out infinite;
        }
      `}</style>

      {/* Live Transcript */}
      {transcript && (
        <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-900">{transcript}</p>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mt-2 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-900">Error: {error}</p>
        </div>
      )}
    </div>
  );
};
