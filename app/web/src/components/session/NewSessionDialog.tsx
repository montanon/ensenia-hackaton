import React, { useState, useEffect } from 'react';
import { Dialog } from '@headlessui/react';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { GRADES, SUBJECTS, SESSION_MODES } from '../../utils/constants';
import type { SessionMode } from '../../types/session';
import { sessionApi } from '../../services/api';
import { useSessionStore } from '../../stores/sessionStore';
import { useChatStore } from '../../stores/chatStore';
import { useExerciseStore } from '../../stores/exerciseStore';

interface NewSessionDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

export const NewSessionDialog: React.FC<NewSessionDialogProps> = ({ isOpen, onClose }) => {
  const [grade, setGrade] = useState(5);
  const [subject, setSubject] = useState('Matemáticas');
  const [mode, setMode] = useState<SessionMode>('learn');
  const [topic, setTopic] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Initialization tracking
  const [createdSessionId, setCreatedSessionId] = useState<number | null>(null);
  const [isInitializing, setIsInitializing] = useState(false);
  const [initStatus, setInitStatus] = useState({
    research_loaded: false,
    initial_exercises_ready: false,
    exercise_count: 0,
  });

  const { setCurrentSession, addToHistory, setMode: setSessionMode } = useSessionStore();
  const { clearMessages } = useChatStore();
  const { loadExercisePool } = useExerciseStore();

  // Poll for session initialization status
  useEffect(() => {
    if (!createdSessionId || !isInitializing) return;

    const pollInterval = setInterval(async () => {
      try {
        const status = await sessionApi.getStatus(createdSessionId);
        setInitStatus({
          research_loaded: status.research_loaded,
          initial_exercises_ready: status.initial_exercises_ready,
          exercise_count: status.exercise_count,
        });

        // Check if initialization is complete
        if (status.research_loaded && status.initial_exercises_ready) {
          setIsInitializing(false);
          clearInterval(pollInterval);

          // Load exercise pool
          await loadExercisePool(createdSessionId);

          // Close dialog after short delay
          setTimeout(() => {
            onClose();
            // Reset state
            setCreatedSessionId(null);
            setInitStatus({
              research_loaded: false,
              initial_exercises_ready: false,
              exercise_count: 0,
            });
          }, 500);
        }
      } catch (err) {
        console.error('Error polling session status:', err);
      }
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(pollInterval);
  }, [createdSessionId, isInitializing, loadExercisePool, onClose]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

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

      setCurrentSession(session);
      addToHistory(session);
      setSessionMode(mode);
      clearMessages();

      // Start polling for initialization
      setCreatedSessionId(response.session_id);
      setIsInitializing(true);
      setLoading(false);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Error al crear la sesión');
      setLoading(false);
    }
  };

  return (
    <Dialog open={isOpen} onClose={onClose} className="relative z-50">
      <div className="fixed inset-0 bg-black/30" aria-hidden="true" />

      <div className="fixed inset-0 flex items-center justify-center p-4">
        <Dialog.Panel className="mx-auto max-w-md w-full bg-white rounded-xl shadow-lg p-6">
          <Dialog.Title className="text-xl font-bold text-gray-900 mb-4">
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
                    <div className="text-xl mb-1">{sessionMode.icon}</div>
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

            {/* Initialization Progress */}
            {isInitializing && (
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg space-y-3">
                <div className="flex items-center gap-2 text-sm font-medium text-blue-900">
                  <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Inicializando sesión...
                </div>

                <div className="space-y-2 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-700">🔍 Investigación curricular</span>
                    <span className={`text-xs font-medium ${initStatus.research_loaded ? 'text-green-600' : 'text-gray-500'}`}>
                      {initStatus.research_loaded ? '✓ Completado' : 'En progreso...'}
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-gray-700">📝 Generando ejercicios</span>
                    <span className={`text-xs font-medium ${initStatus.initial_exercises_ready ? 'text-green-600' : 'text-gray-500'}`}>
                      {initStatus.initial_exercises_ready ? `✓ ${initStatus.exercise_count} listos` : `${initStatus.exercise_count}/5...`}
                    </span>
                  </div>
                </div>
              </div>
            )}

            <div className="flex gap-2 pt-2">
              <Button
                type="button"
                variant="ghost"
                onClick={onClose}
                className="flex-1"
                disabled={loading || isInitializing}
              >
                Cancelar
              </Button>
              <Button
                type="submit"
                variant="primary"
                className="flex-1"
                disabled={loading || isInitializing}
              >
                {loading ? 'Creando...' : isInitializing ? 'Inicializando...' : 'Crear Sesión'}
              </Button>
            </div>
          </form>
        </Dialog.Panel>
      </div>
    </Dialog>
  );
};
