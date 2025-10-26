import React, { useState } from 'react';
import { Dialog } from '@headlessui/react';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { GRADES, SUBJECTS, SESSION_MODES } from '../../utils/constants';
import type { SessionMode } from '../../types/session';
import { sessionApi } from '../../services/api';
import { useSessionStore } from '../../stores/sessionStore';
import { useChatStore } from '../../stores/chatStore';

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

  const { setCurrentSession, addToHistory, setMode: setSessionMode } = useSessionStore();
  const { clearMessages } = useChatStore();

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
        research_context: response.context_loaded ? topic : undefined,
      };

      setCurrentSession(session);
      addToHistory(session);
      setSessionMode(mode);
      clearMessages();

      onClose();
    } catch (err: any) {
      setError(err.response?.data?.message || 'Error al crear la sesión');
    } finally {
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

            <div className="flex gap-2 pt-2">
              <Button
                type="button"
                variant="ghost"
                onClick={onClose}
                className="flex-1"
                disabled={loading}
              >
                Cancelar
              </Button>
              <Button
                type="submit"
                variant="primary"
                className="flex-1"
                disabled={loading}
              >
                {loading ? 'Creando...' : 'Crear Sesión'}
              </Button>
            </div>
          </form>
        </Dialog.Panel>
      </div>
    </Dialog>
  );
};
