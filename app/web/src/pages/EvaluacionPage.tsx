import React from 'react';
import { useSessionStore } from '../stores/sessionStore';
import { SessionInitializingView } from '../components/session/SessionInitializingView';

export const EvaluacionPage: React.FC = () => {
  const { isInitializing } = useSessionStore();

  // Show initializing view while session is being set up
  if (isInitializing) {
    return <SessionInitializingView />;
  }

  return (
    <div className="h-full overflow-auto bg-gray-50">
      <div className="max-w-4xl mx-auto p-8">
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Evaluación
          </h1>
          <p className="text-gray-600">
            Evalúa tus conocimientos y obtén retroalimentación personalizada
          </p>
        </header>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
          <div className="text-center py-12">
            <div className="w-20 h-20 mx-auto mb-6 bg-blue-100 rounded-full flex items-center justify-center">
              <svg className="w-10 h-10 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
              </svg>
            </div>
            <h2 className="text-2xl font-semibold text-gray-900 mb-2">
              Evaluaciones Personalizadas
            </h2>
            <p className="text-gray-600">
              Próximamente podrás realizar evaluaciones adaptadas a tu nivel de aprendizaje
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
