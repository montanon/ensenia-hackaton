import React from 'react';
import { Button } from '../ui/Button';
import { useSessionStore } from '../../stores/sessionStore';

export const SessionInitializingView: React.FC = () => {
  const { initStatus, initError, setInitializing, setInitError, clearSession } = useSessionStore();

  const handleRetry = () => {
    setInitError(null);
    clearSession();
  };

  if (initError) {
    return (
      <div className="h-full flex flex-col items-center justify-center gap-6 bg-gradient-to-b from-gray-50 to-white p-6">
        <div className="text-6xl">⚠️</div>
        <div className="text-center">
          <h2 className="text-2xl font-semibold text-gray-900 mb-2">
            Error en la Inicialización
          </h2>
          <p className="text-gray-600 mb-6">
            {initError}
          </p>
        </div>
        <Button variant="primary" onClick={handleRetry}>
          Reintentar
        </Button>
      </div>
    );
  }

  // Calculate progress percentage
  const progress = initStatus.research_loaded && initStatus.initial_exercises_ready
    ? 100
    : initStatus.research_loaded
    ? 60 + (Math.min(initStatus.exercise_count, 5) / 5) * 35
    : 30 + (Math.random() * 10);

  return (
    <div className="h-full flex flex-col items-center justify-center gap-8 bg-gradient-to-b from-gray-50 to-white p-6">
      {/* Spinner */}
      <div className="flex items-center gap-3">
        <svg className="animate-spin h-8 w-8 text-blue-500" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
        <h2 className="text-2xl font-semibold text-gray-900">
          Analizando el contenido...
        </h2>
      </div>

      {/* Progress Bar */}
      <div className="w-full max-w-md">
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-blue-400 to-blue-600 transition-all duration-500 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
        <p className="text-center text-sm text-gray-600 mt-3">
          {Math.round(progress)}%
        </p>
      </div>

      {/* Status Items */}
      <div className="w-full max-w-md space-y-3">
        <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-gray-200">
          <span className="flex items-center gap-2 text-gray-700">
            <span className="text-lg">🔍</span>
            <span>Investigación curricular</span>
          </span>
          <span className={`text-sm font-medium ${initStatus.research_loaded ? 'text-green-600' : 'text-gray-500'}`}>
            {initStatus.research_loaded ? '✓' : '⏳'}
          </span>
        </div>

        <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-gray-200">
          <span className="flex items-center gap-2 text-gray-700">
            <span className="text-lg">📝</span>
            <span>Generando ejercicios</span>
          </span>
          <span className={`text-sm font-medium ${initStatus.initial_exercises_ready ? 'text-green-600' : 'text-gray-500'}`}>
            {initStatus.initial_exercises_ready ? '✓' : `${initStatus.exercise_count}/5`}
          </span>
        </div>
      </div>

      {/* Info Message */}
      <p className="text-center text-sm text-gray-600 max-w-md">
        Esto puede tomar un momento mientras el sistema realiza la investigación profunda con inteligencia artificial.
      </p>
    </div>
  );
};
