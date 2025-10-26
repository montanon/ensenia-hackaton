import React, { useEffect, useState, useRef } from 'react';
import { useSessionStore } from '../../stores/sessionStore';
import { useChatStore } from '../../stores/chatStore';
import { useAudioStore } from '../../stores/audioStore';
import { useExerciseStore } from '../../stores/exerciseStore';
import { websocketService } from '../../services/websocket';
import { exerciseApi } from '../../services/api';
import { API_URL } from '../../utils/constants';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import { ExerciseCard } from '../exercises/ExerciseCard';
import { Button } from '../ui/Button';

export const ChatTab: React.FC = () => {
  const { currentSession, outputMode, mode } = useSessionStore();
  const {
    addMessage,
    appendStreamChunk,
    completeStream,
    startStreaming,
  } = useChatStore();
  const { setCurrentAudio, setSpeaking, setPlaying } = useAudioStore();
  const {
    currentExercise,
    exerciseSessionId,
    isGenerating,
    setCurrentExercise,
    setGenerating,
  } = useExerciseStore();
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const handleGenerateExercise = async () => {
    if (!currentSession) return;

    setGenerating(true);
    try {
      const response = await exerciseApi.generate({
        exercise_type: 'multiple_choice',
        grade: currentSession.grade,
        subject: currentSession.subject,
        topic: 'Tema actual',
        difficulty_level: 3,
      });

      const exercise = response.exercise;
      let assignedSessionId: number | undefined;

      if (exercise.id && currentSession.id) {
        const link = await exerciseApi.assignToSession(exercise.id, currentSession.id);
        assignedSessionId = link.exercise_session_id;
      }

      setCurrentExercise(exercise, assignedSessionId);
      setError(null);
    } catch (error) {
      console.error('[Exercise] Generation failed:', error);
      setError('Error al generar ejercicio. Por favor intenta nuevamente.');
    } finally {
      setGenerating(false);
    }
  };

  const handleSubmitExercise = async (answer: string) => {
    if (!exerciseSessionId) {
      throw new Error('El ejercicio aún no está vinculado a esta sesión.');
    }

    return exerciseApi.submit(exerciseSessionId, { answer });
  };

  useEffect(() => {
    if (!currentSession) return;

    console.log('[ChatTab] Connecting to WebSocket for session:', currentSession.id);
    console.log('[ChatTab] Initial outputMode:', outputMode);

    // Connect WebSocket
    websocketService.connect(currentSession.id, {
      onConnected: () => {
        console.log('[ChatTab] WebSocket connected successfully');
        setIsConnected(true);

        // Sync initial output mode with backend
        const wsMode = outputMode === 'voice' ? 'audio' : 'text';
        console.log('[ChatTab] Syncing initial mode to backend:', wsMode);
        websocketService.setMode(wsMode);
      },

      onTextChunk: (msg) => {
        appendStreamChunk(msg.content);
      },

      onMessageComplete: (msg) => {
        completeStream(msg.message_id);
      },

      onAudioReady: (msg) => {
        console.log('[ChatTab] Audio ready received:', msg);
        console.log('[ChatTab] Current outputMode:', outputMode);

        const audioUrl = `${API_URL}${msg.url}`;
        console.log('[ChatTab] Constructed audio URL:', audioUrl);

        setCurrentAudio(audioUrl);

        // Auto-play if output mode is voice
        if (outputMode === 'voice') {
          console.log('[ChatTab] Auto-playing audio...');

          // Clean up previous audio if playing
          if (audioRef.current) {
            audioRef.current.pause();
            audioRef.current = null;
          }

          const audio = new Audio(audioUrl);
          audioRef.current = audio;
          setSpeaking(true);
          setPlaying(true);

          audio.onplay = () => {
            console.log('[ChatTab] Audio playback started');
            setSpeaking(true);
          };

          audio.onended = () => {
            console.log('[ChatTab] Audio playback ended');
            setSpeaking(false);
            setPlaying(false);
            audioRef.current = null;
          };

          audio.onerror = (e) => {
            console.error('[ChatTab] Audio playback error:', e);
            console.error('[ChatTab] Audio error details:', audio.error);
            setSpeaking(false);
            setPlaying(false);
            audioRef.current = null;
          };

          audio.play().catch(err => {
            console.error('[ChatTab] Audio playback failed:', err);
            setSpeaking(false);
            setPlaying(false);
            audioRef.current = null;
          });
        } else {
          console.log('[ChatTab] Output mode is text, not auto-playing audio');
        }
      },

      onModeChanged: () => {
        // Mode changed - could update UI if needed
      },

      onError: (msg) => {
        console.error('[Chat] WebSocket error:', msg.message);
        setError(`Error: ${msg.message}`);
      },

      onDisconnect: () => {
        setIsConnected(false);
      },
    });

    return () => {
      websocketService.disconnect();
      setIsConnected(false);

      // Clean up audio if playing
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, [currentSession, outputMode, appendStreamChunk, completeStream, setCurrentAudio, setSpeaking, setPlaying]);

  // Update WebSocket mode when output mode changes
  useEffect(() => {
    if (isConnected && currentSession) {
      const wsMode = outputMode === 'voice' ? 'audio' : 'text';
      console.log('[ChatTab] Output mode changed to:', outputMode);
      console.log('[ChatTab] Sending mode change to backend:', wsMode);
      websocketService.setMode(wsMode);
    }
  }, [outputMode, isConnected, currentSession]);

  const handleSendMessage = (message: string) => {
    if (!currentSession || !isConnected) return;

    // Add user message to store
    addMessage({
      role: 'user',
      content: message,
      timestamp: new Date().toISOString(),
    });

    // Start streaming
    startStreaming();

    // Send via WebSocket
    websocketService.sendMessage(message);
  };

  if (!currentSession) {
    return null;
  }

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              {currentSession.subject} - {currentSession.grade}° Básico
            </h2>
            <p className="text-sm text-gray-500">
              {isConnected ? (
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                  Conectado
                </span>
              ) : (
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 bg-red-500 rounded-full"></span>
                  Desconectado
                </span>
              )}
            </p>
          </div>

          <div className="text-sm">
            <span className="px-3 py-1 bg-gray-100 rounded-full text-gray-700 flex items-center gap-2">
              {outputMode === 'voice' ? (
                <>
                  <svg className="w-4 h-4 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M8 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zM15 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0z" />
                    <path d="M3 4a1 1 0 00-1 1v10a1 1 0 001 1h12a1 1 0 001-1V5a1 1 0 00-1-1H3zM14.707 6.293a1 1 0 00-1.414 1.414l1.414-1.414zM1.5 9a.5.5 0 100-1 .5.5 0 000 1z" />
                  </svg>
                  Audio
                </>
              ) : (
                <>
                  <svg className="w-4 h-4 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C6.5 6.253 2 10.998 2 17s4.5 10.747 10 10.747c5.5 0 10-4.998 10-10.747S17.5 6.253 12 6.253z" />
                  </svg>
                  Texto
                </>
              )}
            </span>
          </div>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="px-6 py-3 bg-red-50 border-b border-red-200 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            <p className="text-sm text-red-800">{error}</p>
          </div>
          <button
            onClick={() => setError(null)}
            className="text-red-600 hover:text-red-800 text-sm font-medium"
          >
            Cerrar
          </button>
        </div>
      )}

      {/* Generate Exercise Button (Practice Mode) */}
      {mode === 'practice' && !currentExercise && (
        <div className="px-6 py-3 bg-blue-50 border-b border-blue-200">
          <Button
            onClick={handleGenerateExercise}
            disabled={isGenerating || !isConnected}
            variant="primary"
            size="sm"
          >
            {isGenerating ? (
              <>
                <svg className="inline-block w-4 h-4 mr-2 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Generando ejercicio...
              </>
            ) : (
              <>
                <svg className="inline-block w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 4a2 2 0 114 0V0h3a2 2 0 012 2v14a2 2 0 01-2 2H7a2 2 0 01-2-2V2a2 2 0 012-2h3V4zm.5 2h3v6h-3V6z" />
                </svg>
                Generar Ejercicio
              </>
            )}
          </Button>
        </div>
      )}

      {/* Exercise Card */}
      {currentExercise && (
        <div className="px-6 py-4 bg-gray-50 border-b border-gray-200 max-h-96 overflow-y-auto">
          <ExerciseCard
            exercise={currentExercise}
            onSubmit={handleSubmitExercise}
          />
        </div>
      )}

      {/* Messages */}
      <MessageList />

      {/* Input */}
      <ChatInput
        onSendMessage={handleSendMessage}
        disabled={!isConnected}
      />
    </div>
  );
};
