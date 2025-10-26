import React, { useState } from 'react';
import { useSessionStore } from '../../stores/sessionStore';
import { useChatStore } from '../../stores/chatStore';
import { useNavigationStore, type PageType } from '../../stores/navigationStore';
import { SESSION_MODES } from '../../utils/constants';
import type { SessionMode } from '../../types/session';
import { Button } from '../ui/Button';
import { cn } from '../../utils/helpers';
import { NewSessionDialog } from '../session/NewSessionDialog';
import { sessionApi } from '../../services/api';

export const Sidebar: React.FC = () => {
  const {
    currentSession,
    mode,
    inputMode,
    outputMode,
    setMode,
    toggleInputMode,
    toggleOutputMode,
    setCurrentSession,
    addToHistory,
  } = useSessionStore();
  const { clearMessages } = useChatStore();
  const { currentPage, setCurrentPage } = useNavigationStore();

  const [showNewSession, setShowNewSession] = useState(false);
  const [isSwitchingMode, setIsSwitchingMode] = useState(false);
  const [modeError, setModeError] = useState<string | null>(null);

  const navigationPages: Array<{ id: PageType; label: string; icon: string }> = [
    { id: 'learn', label: 'Aprender', icon: '📚' },
    { id: 'practice', label: 'Practicar', icon: '✏️' },
    { id: 'review', label: 'Repasar', icon: '📝' },
    { id: 'evaluacion', label: 'Evaluación', icon: '✅' },
  ];

  const handleModeSelect = async (nextMode: SessionMode) => {
    setMode(nextMode);

    if (!currentSession) {
      return;
    }

    if (currentSession.mode === nextMode) {
      return;
    }

    const confirmed = window.confirm(
      'Cambiar el modo reiniciará la sesión actual. ¿Deseas continuar?'
    );

    if (!confirmed) {
      setMode(currentSession.mode as SessionMode);
      return;
    }

    setIsSwitchingMode(true);
    setModeError(null);

    try {
      const response = await sessionApi.create({
        grade: currentSession.grade,
        subject: currentSession.subject,
        mode: nextMode,
      });

      const newSession = {
        id: response.session_id,
        grade: response.grade,
        subject: response.subject,
        mode: response.mode,
        created_at: response.created_at,
        current_mode: 'text' as const,
        research_context: currentSession.research_context,
      };

      setCurrentSession(newSession);
      addToHistory(newSession);
      clearMessages();
    } catch (error) {
      console.error('[Sidebar] Failed to switch learning mode:', error);
      setModeError('No se pudo cambiar el modo. Intenta nuevamente.');
      setMode(currentSession.mode as SessionMode);
    } finally {
      setIsSwitchingMode(false);
    }
  };

  return (
    <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <h1 className="text-xl font-bold text-gray-900">Ensenia</h1>
        <p className="text-sm text-gray-500">Tu asistente educativo</p>
      </div>

      {/* Current Session */}
      {currentSession ? (
        <div className="p-4 border-b border-gray-200 bg-blue-50">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h3 className="font-semibold text-gray-900">{currentSession.subject}</h3>
              <p className="text-sm text-gray-600">{currentSession.grade}° Básico</p>
              <span className="inline-block mt-1 px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-800 rounded">
                {SESSION_MODES.find(m => m.value === currentSession.mode)?.label}
              </span>
            </div>
          </div>
        </div>
      ) : (
        <div className="p-4 border-b border-gray-200">
          <p className="text-sm text-gray-500 mb-2">Sin sesión activa</p>
          <Button
            variant="primary"
            size="sm"
            className="w-full"
            onClick={() => setShowNewSession(true)}
          >
            + Nueva Sesión
          </Button>
        </div>
      )}

      {/* Navigation */}
      <div className="p-4 border-b border-gray-200">
        <h4 className="text-sm font-medium text-gray-700 mb-2">Navegación</h4>
        <div className="space-y-1">
          {navigationPages.map((page) => (
            <button
              key={page.id}
              onClick={() => setCurrentPage(page.id)}
              className={cn(
                'w-full text-left px-3 py-2 rounded-lg text-sm transition-colors',
                currentPage === page.id
                  ? 'bg-blue-100 text-blue-900 font-medium'
                  : 'text-gray-700 hover:bg-gray-100'
              )}
            >
              <div className="flex items-center gap-2">
                <span>{page.icon}</span>
                <span>{page.label}</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Mode Selector */}
      {currentSession && (
        <div className="p-4 border-b border-gray-200">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Modo de Aprendizaje</h4>
          <div className="space-y-1">
            {SESSION_MODES.map((sessionMode) => (
              <button
                key={sessionMode.value}
                onClick={() => handleModeSelect(sessionMode.value as SessionMode)}
                className={cn(
                  'w-full text-left px-3 py-2 rounded-lg text-sm transition-colors',
                  mode === sessionMode.value
                    ? 'bg-blue-100 text-blue-900 font-medium'
                    : 'text-gray-700 hover:bg-gray-100'
                )}
                disabled={isSwitchingMode}
              >
                <div className="flex items-center gap-2">
                  <span>{sessionMode.icon}</span>
                  <div>
                    <div className="font-medium">{sessionMode.label}</div>
                    <div className="text-xs opacity-75">{sessionMode.description}</div>
                  </div>
                </div>
              </button>
            ))}
          </div>
          {modeError && (
            <p className="mt-2 text-xs text-red-600">{modeError}</p>
          )}
        </div>
      )}

      {/* I/O Mode Controls */}
      {currentSession && (
        <div className="p-4 border-b border-gray-200">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Preferencias</h4>

          {/* Input Mode */}
          <div className="mb-3">
            <label className="text-xs text-gray-600 mb-1 block">Tu entrada:</label>
            <div className="flex gap-2">
              <button
                onClick={() => toggleInputMode()}
                aria-label={`Cambiar entrada a ${inputMode === 'text' ? 'voz' : 'texto'}`}
                className={cn(
                  'flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                  inputMode === 'text'
                    ? 'bg-green-100 text-green-900'
                    : 'bg-gray-100 text-gray-700'
                )}
              >
                📝 {inputMode === 'text' ? 'Texto' : 'Voz'}
              </button>
            </div>
          </div>

          {/* Output Mode */}
          <div>
            <label className="text-xs text-gray-600 mb-1 block">Respuesta del AI:</label>
            <div className="flex gap-2">
              <button
                onClick={() => toggleOutputMode()}
                aria-label={`Cambiar salida a ${outputMode === 'voice' ? 'texto' : 'audio'}`}
                className={cn(
                  'flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                  outputMode === 'voice'
                    ? 'bg-purple-100 text-purple-900'
                    : 'bg-gray-100 text-gray-700'
                )}
              >
                {outputMode === 'voice' ? '🔊 Audio' : '📖 Texto'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Session History */}
      <div className="flex-1 overflow-y-auto p-4">
        <h4 className="text-sm font-medium text-gray-700 mb-2">Historial</h4>
        <p className="text-xs text-gray-500">Sin sesiones anteriores</p>
      </div>

      {/* Settings */}
      <div className="p-4 border-t border-gray-200">
        <button
          aria-label="Abrir configuración"
          className="w-full text-left px-3 py-2 rounded-lg text-sm text-gray-700 hover:bg-gray-100 transition-colors flex items-center gap-2"
        >
          <span>⚙️</span>
          <span>Configuración</span>
        </button>
      </div>

      {/* New Session Dialog */}
      <NewSessionDialog
        isOpen={showNewSession}
        onClose={() => setShowNewSession(false)}
      />
    </div>
  );
};
