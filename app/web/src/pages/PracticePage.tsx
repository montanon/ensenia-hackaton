import React from 'react';
import { useSessionStore } from '../stores/sessionStore';
import { useExerciseStore } from '../stores/exerciseStore';
import { ExerciseCard } from '../components/exercises/ExerciseCard';
import { exerciseApi } from '../services/api';
import { Button } from '../components/ui/Button';

export const PracticePage: React.FC = () => {
  const { currentSession } = useSessionStore();
  const {
    currentExercise,
    exerciseSessionId,
    isGenerating,
    setCurrentExercise,
    setGenerating,
  } = useExerciseStore();

  const handleGenerateExercise = async () => {
    if (!currentSession) return;

    setGenerating(true);
    try {
      const response = await exerciseApi.generate({
        exercise_type: 'multiple_choice',
        grade: currentSession.grade,
        subject: currentSession.subject,
        topic: 'Tema actual',
        difficulty_level: 3,
      });

      const exercise = response.exercise;
      let assignedSessionId: number | undefined;

      if (exercise.id && currentSession.id) {
        const link = await exerciseApi.assignToSession(exercise.id, currentSession.id);
        assignedSessionId = link.exercise_session_id;
      }

      setCurrentExercise(exercise, assignedSessionId);
    } catch (error) {
      console.error('[Practice] Generation failed:', error);
    } finally {
      setGenerating(false);
    }
  };

  const handleSubmitExercise = async (answer: string) => {
    if (!exerciseSessionId) {
      throw new Error('El ejercicio aún no está vinculado a esta sesión.');
    }

    return exerciseApi.submit(exerciseSessionId, { answer });
  };

  return (
    <div className="h-full overflow-auto bg-gray-50">
      <div className="max-w-4xl mx-auto p-8">
        {currentSession ? (
          <>
            <header className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Practicar
              </h1>
              <p className="text-gray-600">
                {currentSession.subject} - {currentSession.grade}° Básico
              </p>
            </header>

            {!currentExercise && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
                <svg className="w-16 h-16 text-blue-500 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 4a2 2 0 114 0V0h3a2 2 0 012 2v14a2 2 0 01-2 2H7a2 2 0 01-2-2V2a2 2 0 012-2h3V4zm.5 2h3v6h-3V6z" />
                </svg>
                <h2 className="text-xl font-semibold text-gray-900 mb-2">
                  Ejercicios de Práctica
                </h2>
                <p className="text-gray-600 mb-6">
                  Genera ejercicios personalizados basados en el currículo chileno
                </p>
                <Button
                  onClick={handleGenerateExercise}
                  disabled={isGenerating}
                  variant="primary"
                >
                  {isGenerating ? (
                    <>
                      <svg className="inline-block w-4 h-4 mr-2 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      Generando...
                    </>
                  ) : (
                    <>
                      <svg className="inline-block w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.381-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                      </svg>
                      Generar Ejercicio
                    </>
                  )}
                </Button>
              </div>
            )}

            {currentExercise && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <ExerciseCard
                  exercise={currentExercise}
                  onSubmit={handleSubmitExercise}
                />
              </div>
            )}

            <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <svg className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 5v8a2 2 0 01-2 2h-5l-5 4v-4H4a2 2 0 01-2-2V5a2 2 0 012-2h12a2 2 0 012 2zm-11-4a1 1 0 11-2 0 1 1 0 012 0z" clipRule="evenodd" />
                </svg>
                <p className="text-sm text-blue-900">
                  <strong>Consejo:</strong> Puedes usar el asistente de voz para obtener ayuda con los ejercicios
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
              Crea una nueva sesión desde el menú lateral para comenzar a practicar
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
