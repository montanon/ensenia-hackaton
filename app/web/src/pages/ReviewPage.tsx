import React from 'react';
import { useSessionStore } from '../stores/sessionStore';

export const ReviewPage: React.FC = () => {
  const { currentSession } = useSessionStore();

  return (
    <div className="h-full overflow-auto bg-gray-50">
      <div className="max-w-4xl mx-auto p-8">
        {currentSession ? (
          <>
            <header className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Repasar
              </h1>
              <p className="text-gray-600">
                {currentSession.subject} - {currentSession.grade}° Básico
              </p>
            </header>

            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Material de Repaso
              </h2>
              <p className="text-gray-700 mb-4">
                Revisa y consolida los conceptos aprendidos
              </p>
            </div>

            <div className="grid grid-cols-1 gap-4">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-start gap-4">
                  <svg className="w-8 h-8 text-blue-500 flex-shrink-0 mt-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900 mb-2">Resumen de Conceptos</h3>
                    <p className="text-sm text-gray-600">
                      Repasa los conceptos clave aprendidos en esta sesión
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-start gap-4">
                  <svg className="w-8 h-8 text-blue-500 flex-shrink-0 mt-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900 mb-2">Progreso</h3>
                    <p className="text-sm text-gray-600">
                      Visualiza tu progreso y áreas de mejora
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-start gap-4">
                  <svg className="w-8 h-8 text-blue-500 flex-shrink-0 mt-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900 mb-2">Ejercicios Completados</h3>
                    <p className="text-sm text-gray-600">
                      Revisa los ejercicios que has completado
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <svg className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 5v8a2 2 0 01-2 2h-5l-5 4v-4H4a2 2 0 01-2-2V5a2 2 0 012-2h12a2 2 0 012 2zm-11-4a1 1 0 11-2 0 1 1 0 012 0z" clipRule="evenodd" />
                </svg>
                <p className="text-sm text-blue-900">
                  <strong>Usa el asistente</strong> para repasar conceptos específicos o resolver dudas
                </p>
              </div>
            </div>
          </>
        ) : (
          <div className="text-center py-16">
            <div className="text-6xl mb-4">🎓</div>
            <h2 className="text-2xl font-semibold text-gray-900 mb-2">
              Sin sesión activa
            </h2>
            <p className="text-gray-600">
              Crea una nueva sesión desde el menú lateral para comenzar a repasar
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
