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
