import React, { useState, useEffect } from 'react';
import { useSessionStore } from '../stores/sessionStore';
import { SessionInitializingView } from '../components/session/SessionInitializingView';
import { sessionApi } from '../services/api';

interface LearningContent {
  title: string;
  overview: string;
  learning_objectives: string[];
  sections: Array<{
    title: string;
    content: string;
    key_points: string[];
    examples: Array<{
      description: string;
      explanation: string;
    }>;
  }>;
  vocabulary: Array<{
    term: string;
    definition: string;
  }>;
  summary: string;
}

export const LearnPage: React.FC = () => {
  const { currentSession, isInitializing } = useSessionStore();
  const [learningContent, setLearningContent] = useState<LearningContent | null>(null);
  const [contentLoading, setContentLoading] = useState(false);
  const [contentError, setContentError] = useState<string | null>(null);

  // Load learning content when session changes
  useEffect(() => {
    if (currentSession && !isInitializing) {
      loadLearningContent();
    }
  }, [currentSession, isInitializing]);

  const loadLearningContent = async () => {
    if (!currentSession) return;

    setContentLoading(true);
    setContentError(null);

    try {
      const response = await sessionApi.getLearningContent(currentSession.id);
      setLearningContent(response.content);
    } catch (error: any) {
      // Content might not be ready yet (202) or not available
      if (error.response?.status === 202) {
        setContentError('El contenido aún se está generando. Por favor, espera un momento.');
      } else {
        setContentError(null); // Silently fail - we still have chat
      }
    } finally {
      setContentLoading(false);
    }
  };

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

            {/* Learning Content Display */}
            {learningContent ? (
              <div className="space-y-6 mb-8">
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">
                    {learningContent.title}
                  </h2>
                  <p className="text-gray-700 mb-4">{learningContent.overview}</p>

                  {/* Learning Objectives */}
                  {learningContent.learning_objectives.length > 0 && (
                    <div className="mb-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-3">
                        Objetivos de Aprendizaje
                      </h3>
                      <ul className="space-y-2">
                        {learningContent.learning_objectives.map((obj, idx) => (
                          <li key={idx} className="flex items-start">
                            <span className="inline-flex items-center justify-center h-6 w-6 rounded-full bg-blue-100 text-blue-800 text-sm font-semibold mr-3 flex-shrink-0 mt-0.5">
                              {idx + 1}
                            </span>
                            <span className="text-gray-700">{obj}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                {/* Content Sections */}
                {learningContent.sections.map((section, sectionIdx) => (
                  <div key={sectionIdx} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <h3 className="text-xl font-semibold text-gray-900 mb-3">
                      {section.title}
                    </h3>
                    <p className="text-gray-700 whitespace-pre-wrap mb-4">{section.content}</p>

                    {/* Key Points */}
                    {section.key_points.length > 0 && (
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                        <h4 className="font-semibold text-gray-900 mb-2">Puntos Clave:</h4>
                        <ul className="space-y-2">
                          {section.key_points.map((point, idx) => (
                            <li key={idx} className="flex items-start text-sm text-gray-700">
                              <span className="text-blue-600 mr-2">•</span>
                              {point}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Examples */}
                    {section.examples.length > 0 && (
                      <div>
                        <h4 className="font-semibold text-gray-900 mb-3">Ejemplos:</h4>
                        <div className="space-y-3">
                          {section.examples.map((example, idx) => (
                            <div key={idx} className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                              <p className="font-medium text-gray-900 mb-2">{example.description}</p>
                              <p className="text-sm text-gray-700">{example.explanation}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}

                {/* Vocabulary */}
                {learningContent.vocabulary.length > 0 && (
                  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <h3 className="text-xl font-semibold text-gray-900 mb-4">
                      Vocabulario Importante
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {learningContent.vocabulary.map((vocab, idx) => (
                        <div key={idx} className="border-l-4 border-blue-500 pl-4">
                          <p className="font-semibold text-gray-900">{vocab.term}</p>
                          <p className="text-sm text-gray-600">{vocab.definition}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Summary */}
                <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Resumen</h3>
                  <p className="text-gray-700 whitespace-pre-wrap">{learningContent.summary}</p>
                </div>
              </div>
            ) : contentLoading ? (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6 text-center">
                <div className="inline-flex items-center justify-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mr-3"></div>
                  <p className="text-gray-700">Generando contenido de aprendizaje...</p>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                  Contenido de Aprendizaje
                </h2>
                <p className="text-gray-700 mb-4">
                  El contenido estructurado aparecerá aquí cuando esté disponible. Mientras tanto, puedes usar el asistente para hacer preguntas.
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
            )}

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
