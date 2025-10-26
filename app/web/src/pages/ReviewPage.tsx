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
                  <div className="text-3xl">📝</div>
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
                  <div className="text-3xl">📊</div>
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
                  <div className="text-3xl">🎯</div>
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
              <p className="text-sm text-blue-900">
                💡 <strong>Usa el asistente</strong> para repasar conceptos específicos o resolver dudas
              </p>
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
