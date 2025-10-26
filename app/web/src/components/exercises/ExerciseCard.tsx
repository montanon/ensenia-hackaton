import React, { useState } from 'react';
import type { Exercise } from '../../types/exercise';
import { MultipleChoice } from './MultipleChoice';
import { TrueFalse } from './TrueFalse';
import { ShortAnswer } from './ShortAnswer';
import { ExerciseResults } from './ExerciseResults';

interface ExerciseCardProps {
  exercise: Exercise;
  onSubmit: (answer: string) => Promise<any>;
}

export const ExerciseCard: React.FC<ExerciseCardProps> = ({
  exercise,
  onSubmit,
}) => {
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleSubmit = async (answer: string) => {
    setSubmitting(true);
    try {
      const response = await onSubmit(answer);
      setResult(response);
    } catch (error) {
      console.error('[Exercise] Submission failed:', error);
      alert('Error al enviar respuesta');
    } finally {
      setSubmitting(false);
    }
  };

  const renderExercise = () => {
    switch (exercise.exercise_type) {
      case 'multiple_choice':
        return (
          <MultipleChoice
            content={exercise.content as any}
            onSubmit={handleSubmit}
            disabled={submitting || !!result}
          />
        );
      case 'true_false':
        return (
          <TrueFalse
            content={exercise.content as any}
            onSubmit={handleSubmit}
            disabled={submitting || !!result}
          />
        );
      case 'short_answer':
        return (
          <ShortAnswer
            content={exercise.content as any}
            onSubmit={handleSubmit}
            disabled={submitting || !!result}
          />
        );
      default:
        return (
          <div className="text-gray-500">
            Tipo de ejercicio no soportado: {exercise.exercise_type}
          </div>
        );
    }
  };

  return (
    <div className="bg-white border-2 border-blue-200 rounded-lg p-6 shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between mb-4 pb-4 border-b border-gray-200">
        <div>
          <h2 className="text-xl font-bold text-gray-900">
            🎯 Ejercicio de Práctica
          </h2>
          <p className="text-sm text-gray-600">
            {exercise.subject} • {exercise.topic} • Dificultad: {exercise.difficulty_level}/5
          </p>
        </div>
        {exercise.validation_score && (
          <div className="text-sm text-gray-600">
            Calidad: {exercise.validation_score}/10
          </div>
        )}
      </div>

      {/* Exercise Content */}
      {renderExercise()}

      {/* Results */}
      {result && (
        <div className="mt-4">
          <ExerciseResults
            isCorrect={result.is_correct || false}
            explanation={result.feedback || result.explanation || 'Respuesta recibida'}
          />
        </div>
      )}

      {/* Loading */}
      {submitting && (
        <div className="mt-4 text-center text-gray-600">
          Verificando respuesta...
        </div>
      )}
    </div>
  );
};
