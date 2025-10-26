import React from 'react';

interface ExerciseResultsProps {
  isCorrect: boolean;
  explanation: string;
}

export const ExerciseResults: React.FC<ExerciseResultsProps> = ({
  isCorrect,
  explanation,
}) => {
  return (
    <div
      className={`p-4 rounded-lg border-2 ${
        isCorrect
          ? 'bg-green-50 border-green-200'
          : 'bg-yellow-50 border-yellow-200'
      }`}
    >
      <div className="flex items-start gap-3">
        <span className="text-2xl">
          {isCorrect ? '✅' : '💡'}
        </span>
        <div className="flex-1">
          <h4 className={`font-semibold mb-1 ${
            isCorrect ? 'text-green-900' : 'text-yellow-900'
          }`}>
            {isCorrect ? '¡Correcto!' : 'Revisemos esto'}
          </h4>
          <p className={`text-sm ${
            isCorrect ? 'text-green-800' : 'text-yellow-800'
          }`}>
            {explanation}
          </p>
        </div>
      </div>
    </div>
  );
};
