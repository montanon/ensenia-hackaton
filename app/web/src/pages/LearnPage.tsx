import React from 'react';
import { useSessionStore } from '../stores/sessionStore';
import { SessionInitializingView } from '../components/session/SessionInitializingView';

export const LearnPage: React.FC = () => {
  const { currentSession, isInitializing } = useSessionStore();

  // Show initializing view while session is being set up
  if (isInitializing) {
    return <SessionInitializingView />;
  }

  return (
    <div className="h-full overflow-auto bg-gray-50">
      <div className="max-w-4xl mx-auto p-8">
        {currentSession ? (
          <>
            <header className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Aprender
              </h1>
              <p className="text-gray-600">
                {currentSession.subject} - {currentSession.grade}° Básico
              </p>
            </header>

            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Contenido de Aprendizaje
              </h2>
              <p className="text-gray-700 mb-4">
                Esta sección contendrá el material de estudio alineado con el currículo del Ministerio de Educación chileno.
              </p>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-sm text-blue-900">
                  💡 <strong>Usa el asistente</strong> en la esquina inferior derecha para:
                </p>
                <ul className="mt-2 ml-6 text-sm text-blue-800 list-disc">
                  <li>Hacer preguntas sobre el tema</li>
                  <li>Solicitar explicaciones adicionales</li>
                  <li>Obtener ejemplos prácticos</li>
                  <li>Mantén presionado el botón para hablar por voz</li>
                </ul>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="text-4xl mb-3">📚</div>
                <h3 className="font-semibold text-gray-900 mb-2">Teoría</h3>
                <p className="text-sm text-gray-600">
                  Conceptos fundamentales y explicaciones detalladas
                </p>
              </div>

              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="text-4xl mb-3">🎯</div>
                <h3 className="font-semibold text-gray-900 mb-2">Ejemplos</h3>
                <p className="text-sm text-gray-600">
                  Casos prácticos y aplicaciones reales
                </p>
              </div>

              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="text-4xl mb-3">🔍</div>
                <h3 className="font-semibold text-gray-900 mb-2">Exploración</h3>
                <p className="text-sm text-gray-600">
                  Investigación profunda con Cloudflare Deep Research
                </p>
              </div>

              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="text-4xl mb-3">💬</div>
                <h3 className="font-semibold text-gray-900 mb-2">Preguntas</h3>
                <p className="text-sm text-gray-600">
                  Asistencia personalizada vía texto o voz
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
              Crea una nueva sesión desde el menú lateral para comenzar a aprender
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
