import React, { useState } from 'react';
import { Dialog } from '@headlessui/react';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { GRADES, SUBJECTS, SESSION_MODES } from '../../utils/constants';
import type { SessionMode } from '../../types/session';
import { sessionApi } from '../../services/api';
import { useSessionStore } from '../../stores/sessionStore';
import { useChatStore } from '../../stores/chatStore';
import { useExerciseStore } from '../../stores/exerciseStore';
import { useBubbleStore } from '../../stores/bubbleStore';

const MAX_POLLS = 60; // 60 polls × 2 seconds = 2 minutes max

interface NewSessionDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

export const NewSessionDialog: React.FC<NewSessionDialogProps> = ({ isOpen, onClose }) => {
  const [grade, setGrade] = useState(5);
  const [subject, setSubject] = useState('Matemáticas');
  const [mode, setMode] = useState<SessionMode>('learn');
  const [topic, setTopic] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const {
    setCurrentSession,
    addToHistory,
    setMode: setSessionMode,
    setInitializing,
    setInitStatus,
    setInitError,
  } = useSessionStore();
  const { clearMessages } = useChatStore();
  const { loadExercisePool } = useExerciseStore();
  const { closeChat } = useBubbleStore();

  // Polling for session initialization status with timeout protection
  const pollSessionStatus = async (sessionId: number) => {
    let pollCount = 0;
    let isComplete = false;

    const pollInterval = setInterval(async () => {
      pollCount++;

      // Timeout protection - stop after max polls
      if (pollCount > MAX_POLLS) {
        setInitializing(false);
        clearInterval(pollInterval);
        setInitError('El tiempo de inicialización se agotó. Por favor intenta nuevamente.');
        return;
      }

      try {
        const status = await sessionApi.getStatus(sessionId);
        setInitStatus({
          research_loaded: status.research_loaded,
          initial_exercises_ready: status.initial_exercises_ready,
          exercise_count: status.exercise_count,
        });

        // Check if initialization is complete
        if ((status.research_loaded && status.initial_exercises_ready) || pollCount >= 3) {
          if (!isComplete) {
            isComplete = true;
            setInitializing(false);
            clearInterval(pollInterval);

            // Load exercise pool
            try {
              await loadExercisePool(sessionId);
            } catch (err) {
              console.error('Error loading exercise pool:', err);
            }
          }
        }
      } catch (err) {
        console.error('Error polling session status:', err);
      }
    }, 2000); // Poll every 2 seconds
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);

    try {
      const response = await sessionApi.create({
        grade,
        subject,
        mode,
        topic: topic || undefined,
      });

      const session = {
        id: response.session_id,
        grade: response.grade,
        subject: response.subject,
        mode: response.mode,
        created_at: response.created_at,
        current_mode: 'text' as const,
        research_context: undefined, // Will be loaded in background
      };

      // Set session and start initialization
      setCurrentSession(session);
      addToHistory(session);
      setSessionMode(mode);
      clearMessages();

      // Close chat panel (only opens when user clicks bubble)
      closeChat();

      // Start polling for initialization in the background
      setInitializing(true);
      setInitStatus({
        research_loaded: false,
        initial_exercises_ready: false,
        exercise_count: 0,
      });
      setInitError(null);

      // Close dialog immediately
      onClose();
      setSubmitting(false);

      // Start polling for initialization status
      pollSessionStatus(response.session_id);

      // Reset form for next time
      setGrade(5);
      setSubject('Matemáticas');
      setMode('learn');
      setTopic('');
    } catch (err: any) {
      setError(err.response?.data?.message || 'Error al crear la sesión');
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={isOpen} onClose={onClose} className="relative z-50">
      <div className="fixed inset-0 bg-black/30" aria-hidden="true" />

      <div className="fixed inset-0 flex items-center justify-center p-4">
        <Dialog.Panel className="mx-auto max-w-md w-full bg-white rounded-xl shadow-lg p-6">
          <Dialog.Title className="text-xl font-bold text-gray-900 mb-6">
            Nueva Sesión
          </Dialog.Title>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Grade Selector */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Grado
              </label>
              <select
                value={grade}
                onChange={(e) => setGrade(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {GRADES.map((g) => (
                  <option key={g} value={g}>
                    {g}° Básico
                  </option>
                ))}
              </select>
            </div>

            {/* Subject Selector */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Asignatura
              </label>
              <select
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {SUBJECTS.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>

            {/* Mode Selector */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Modo de Aprendizaje
              </label>
              <div className="grid grid-cols-2 gap-2">
                {SESSION_MODES.map((sessionMode) => (
                  <button
                    key={sessionMode.value}
                    type="button"
                    onClick={() => setMode(sessionMode.value as SessionMode)}
                    className={`p-3 rounded-lg border-2 transition-colors text-left ${
                      mode === sessionMode.value
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    {/* Icon based on mode - matches Sidebar */}
                    <div className="w-6 h-6 mb-2 text-blue-500">
                      {sessionMode.value === 'learn' && (
                        <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                      )}
                      {sessionMode.value === 'practice' && (
                        <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                        </svg>
                      )}
                      {sessionMode.value === 'study' && (
                        <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C6.5 6.253 2 10.998 2 17s4.5 10.747 10 10.747c5.5 0 10-4.998 10-10.747S17.5 6.253 12 6.253z" />
                        </svg>
                      )}
                      {sessionMode.value === 'evaluation' && (
                        <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                        </svg>
                      )}
                    </div>
                    <div className="text-sm font-medium">{sessionMode.label}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Topic (Optional) */}
            <Input
              label="Tema (opcional)"
              placeholder="ej: Fracciones"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
            />

            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
                {error}
              </div>
            )}

            <div className="flex gap-2 pt-2">
              <Button
                type="button"
                variant="ghost"
                onClick={onClose}
                className="flex-1"
                disabled={submitting}
              >
                Cancelar
              </Button>
              <Button
                type="submit"
                variant="primary"
                className="flex-1"
                disabled={submitting}
              >
                {submitting ? 'Creando...' : 'Crear Sesión'}
              </Button>
            </div>
          </form>
        </Dialog.Panel>
      </div>
    </Dialog>
  );
};
