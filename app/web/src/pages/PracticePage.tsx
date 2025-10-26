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
                <div className="text-6xl mb-4">✏️</div>
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
                  {isGenerating ? '⏳ Generando...' : '✨ Generar Ejercicio'}
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
              <p className="text-sm text-blue-900">
                💡 <strong>Consejo:</strong> Puedes usar el asistente de voz para obtener ayuda con los ejercicios
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
              Crea una nueva sesión desde el menú lateral para comenzar a practicar
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
