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

    // Connect WebSocket
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
          // Clean up previous audio if playing
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
            console.error('[Chat] Audio playback failed:', err);
            setSpeaking(false);
            setPlaying(false);
            audioRef.current = null;
          });
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
    return (
      <div className="h-full flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="text-6xl mb-4">🎓</div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">
            Sin sesión activa
          </h3>
          <p className="text-gray-600">
            Crea una nueva sesión para comenzar
          </p>
        </div>
      </div>
    );
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
            <span className="px-3 py-1 bg-gray-100 rounded-full text-gray-700">
              {outputMode === 'voice' ? '🔊 Audio' : '📖 Texto'}
            </span>
          </div>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="px-6 py-3 bg-red-50 border-b border-red-200 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-red-600">⚠️</span>
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
            {isGenerating ? '⏳ Generando ejercicio...' : '✏️ Generar Ejercicio'}
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
