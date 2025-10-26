import React from 'react';
import { Button } from '../ui/Button';
import { useSessionStore } from '../../stores/sessionStore';

export const SessionInitializingView: React.FC = () => {
  const { initStatus, initError, setInitError, clearSession } = useSessionStore();

  const handleRetry = () => {
    setInitError(null);
    clearSession();
  };

  if (initError) {
    return (
      <div className="h-full flex flex-col items-center justify-center gap-6 bg-gradient-to-b from-gray-50 to-white p-6">
        {/* Error Icon */}
        <svg className="w-16 h-16 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4v2m0-6a6 6 0 100 12 6 6 0 000-12zm0-8a8 8 0 100 16 8 8 0 000-16zm1 11h-2v2h2v-2zm0-6h-2v2h2V8z" />
        </svg>
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
    : 30;

  return (
    <div className="h-full flex flex-col items-center justify-center gap-8 bg-gradient-to-b from-gray-50 to-white p-6">
      {/* Graduation Hat */}
      <div className="text-7xl">🎓</div>

      {/* Status Title */}
      <div className="flex items-center gap-3 flex-col">
        <svg className="animate-spin h-6 w-6 text-blue-500" fill="none" viewBox="0 0 24 24">
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
        {/* Research Status */}
        <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-gray-200">
          <span className="flex items-center gap-3 text-gray-700">
            <svg className="w-5 h-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <span>Análisis de currículo</span>
          </span>
          {initStatus.research_loaded ? (
            <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          ) : (
            <svg className="w-5 h-5 text-blue-500 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
          )}
        </div>

        {/* Exercises Status */}
        <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-gray-200">
          <span className="flex items-center gap-3 text-gray-700">
            <svg className="w-5 h-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <span>Generando ejercicios</span>
          </span>
          {initStatus.initial_exercises_ready ? (
            <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          ) : (
            <span className="text-xs font-medium text-gray-600">{initStatus.exercise_count}/5</span>
          )}
        </div>
      </div>

      {/* Exercise Cards Animation */}
      {initStatus.research_loaded && !initStatus.initial_exercises_ready && (
        <div className="w-full max-w-md">
          <p className="text-sm font-medium text-gray-700 mb-3 text-center">
            Preparando ejercicios personalizados...
          </p>
          <div className="grid grid-cols-5 gap-2">
            {[0, 1, 2, 3, 4].map((index) => (
              <div
                key={index}
                className={`aspect-square rounded-lg border-2 transition-all duration-500 flex items-center justify-center ${
                  index < initStatus.exercise_count
                    ? 'border-green-500 bg-green-50 scale-100 opacity-100'
                    : 'border-gray-200 bg-gray-50 scale-95 opacity-50'
                }`}
                style={{
                  transitionDelay: `${index * 100}ms`,
                }}
              >
                {index < initStatus.exercise_count ? (
                  <svg className="w-6 h-6 text-green-600 animate-bounce" fill="currentColor" viewBox="0 0 20 20" style={{ animationDelay: `${index * 100}ms` }}>
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                ) : (
                  <div className="w-2 h-2 bg-gray-300 rounded-full animate-pulse" style={{ animationDelay: `${index * 150}ms` }} />
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Info Message */}
      <p className="text-center text-sm text-gray-600 max-w-md">
        Esto puede tomar un momento mientras el sistema realiza la investigación profunda con inteligencia artificial.
      </p>
    </div>
  );
};
