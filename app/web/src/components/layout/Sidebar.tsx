import React, { useState } from 'react';
import { useSessionStore } from '../../stores/sessionStore';
import { useChatStore } from '../../stores/chatStore';
import { useNavigationStore, type PageType } from '../../stores/navigationStore';
import { SESSION_MODES } from '../../utils/constants';
import type { SessionMode } from '../../types/session';
import { Button } from '../ui/Button';
import { cn } from '../../utils/helpers';
import { NewSessionDialog } from '../session/NewSessionDialog';
import { ConfigurationDialog } from '../settings/ConfigurationDialog';
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
  const [showConfiguration, setShowConfiguration] = useState(false);
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
        <h1 className="text-xl font-bold text-gray-900">Ense<span className="text-blue-600">ñ</span>IA</h1>
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
          onClick={() => setShowConfiguration(true)}
          aria-label="Abrir configuración"
          className="w-full text-left px-3 py-2.5 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-100 hover:text-gray-900 transition-all duration-200 flex items-center gap-3 group"
        >
          <svg
            className="w-5 h-5 text-gray-500 group-hover:text-gray-700 group-hover:rotate-90 transition-all duration-300"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
            />
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
            />
          </svg>
          <span>Configuración</span>
        </button>
      </div>

      {/* New Session Dialog */}
      <NewSessionDialog
        isOpen={showNewSession}
        onClose={() => setShowNewSession(false)}
      />

      {/* Configuration Dialog */}
      <ConfigurationDialog
        isOpen={showConfiguration}
        onClose={() => setShowConfiguration(false)}
      />
    </div>
  );
};
