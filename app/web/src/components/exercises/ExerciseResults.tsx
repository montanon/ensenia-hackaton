import React from 'react';

interface ExerciseResultsProps {
  isCorrect: boolean;
  explanation: string;
  onNext?: () => void;
  isLoadingNext?: boolean;
}

export const ExerciseResults: React.FC<ExerciseResultsProps> = ({
  isCorrect,
  explanation,
  onNext,
  isLoadingNext,
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

      {/* Next Exercise Button */}
      {onNext && (
        <div className="mt-4 flex gap-3">
          <button
            onClick={onNext}
            disabled={isLoadingNext}
            className="flex-1 py-2 px-4 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 text-white font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            {isLoadingNext ? (
              <>
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Cargando...
              </>
            ) : (
              <>
                Siguiente Ejercicio
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </>
            )}
          </button>
        </div>
      )}
    </div>
  );
};
