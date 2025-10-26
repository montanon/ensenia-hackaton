import React, { useState, useEffect } from 'react';
import { useSessionStore } from '../stores/sessionStore';
import { sessionApi } from '../services/api';

interface StudyGuide {
  title: string;
  subject: string;
  grade: number;
  key_concepts: Array<{
    concept: string;
    explanation: string;
    importance: string;
  }>;
  summary_sections: Array<{
    title: string;
    summary: string;
    remember: string[];
  }>;
  common_mistakes: Array<{
    mistake: string;
    correction: string;
    explanation: string;
  }>;
  practice_tips: string[];
  review_questions: string[];
}

export const ReviewPage: React.FC = () => {
  const { currentSession } = useSessionStore();
  const [studyGuide, setStudyGuide] = useState<StudyGuide | null>(null);
  const [guideLoading, setGuideLoading] = useState(false);
  const [guideError, setGuideError] = useState<string | null>(null);

  // Load study guide when session changes
  useEffect(() => {
    if (currentSession) {
      loadStudyGuide();
    }
  }, [currentSession]);

  const loadStudyGuide = async () => {
    if (!currentSession) return;

    setGuideLoading(true);
    setGuideError(null);

    try {
      const response = await sessionApi.getStudyGuide(currentSession.id);
      setStudyGuide(response.guide);
    } catch (error: any) {
      // Guide might not be ready yet (202) or not available
      if (error.response?.status === 202) {
        setGuideError('La guía de estudio aún se está generando. Por favor, espera un momento.');
      } else {
        setGuideError(null); // Silently fail - we still have chat
      }
    } finally {
      setGuideLoading(false);
    }
  };

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

            {/* Study Guide Display */}
            {studyGuide ? (
              <div className="space-y-6 mb-8">
                {/* Key Concepts */}
                {studyGuide.key_concepts.length > 0 && (
                  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <h2 className="text-2xl font-bold text-gray-900 mb-4">
                      Conceptos Clave
                    </h2>
                    <div className="space-y-4">
                      {studyGuide.key_concepts.map((concept, idx) => (
                        <div key={idx} className="border-l-4 border-purple-500 pl-4">
                          <h3 className="text-lg font-semibold text-gray-900">{concept.concept}</h3>
                          <p className="text-gray-700 mt-1">{concept.explanation}</p>
                          <p className="text-sm text-purple-600 mt-2">
                            <strong>¿Por qué es importante?</strong> {concept.importance}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Summary Sections */}
                {studyGuide.summary_sections.map((section, sectionIdx) => (
                  <div key={sectionIdx} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <h2 className="text-2xl font-bold text-gray-900 mb-4">{section.title}</h2>
                    <p className="text-gray-700 whitespace-pre-wrap mb-4">{section.summary}</p>

                    {section.remember.length > 0 && (
                      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                        <h4 className="font-semibold text-gray-900 mb-2">Recuerda:</h4>
                        <ul className="space-y-2">
                          {section.remember.map((item, idx) => (
                            <li key={idx} className="flex items-start text-sm text-gray-700">
                              <span className="text-yellow-600 mr-2">★</span>
                              {item}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}

                {/* Common Mistakes */}
                {studyGuide.common_mistakes.length > 0 && (
                  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <h2 className="text-2xl font-bold text-gray-900 mb-4">Errores Comunes</h2>
                    <div className="space-y-4">
                      {studyGuide.common_mistakes.map((item, idx) => (
                        <div key={idx} className="border-l-4 border-red-500 pl-4">
                          <p className="font-semibold text-gray-900 text-red-700">❌ {item.mistake}</p>
                          <p className="text-gray-700 mt-2">{item.explanation}</p>
                          <p className="text-green-700 mt-2">✅ <strong>Corrección:</strong> {item.correction}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Practice Tips */}
                {studyGuide.practice_tips.length > 0 && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                    <h2 className="text-xl font-bold text-gray-900 mb-4">Consejos de Estudio</h2>
                    <div className="space-y-3">
                      {studyGuide.practice_tips.map((tip, idx) => (
                        <div key={idx} className="flex items-start">
                          <span className="inline-flex items-center justify-center h-6 w-6 rounded-full bg-green-200 text-green-800 text-sm font-semibold mr-3 flex-shrink-0 mt-0.5">
                            {idx + 1}
                          </span>
                          <span className="text-gray-700">{tip}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Review Questions */}
                {studyGuide.review_questions.length > 0 && (
                  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <h2 className="text-2xl font-bold text-gray-900 mb-4">Preguntas de Repaso</h2>
                    <div className="space-y-4">
                      {studyGuide.review_questions.map((question, idx) => (
                        <div key={idx} className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                          <p className="font-semibold text-gray-900 mb-2">
                            {idx + 1}. {question}
                          </p>
                          <p className="text-sm text-blue-600">
                            💡 Usa el asistente para verificar tu respuesta
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : guideLoading ? (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6 text-center">
                <div className="inline-flex items-center justify-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mr-3"></div>
                  <p className="text-gray-700">Generando guía de estudio...</p>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-4">
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                  <div className="flex items-start gap-4">
                    <svg className="w-8 h-8 text-blue-500 flex-shrink-0 mt-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900 mb-2">Resumen de Conceptos</h3>
                      <p className="text-sm text-gray-600">
                        La guía de estudio aparecerá aquí cuando esté disponible
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
            )}

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
