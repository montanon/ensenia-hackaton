import React, { useState } from 'react';
import type { TrueFalseContent } from '../../types/exercise';
import { Button } from '../ui/Button';
import { cn } from '../../utils/helpers';

interface TrueFalseProps {
  content: TrueFalseContent;
  onSubmit: (answer: string) => void;
  disabled?: boolean;
}

export const TrueFalse: React.FC<TrueFalseProps> = ({
  content,
  onSubmit,
  disabled,
}) => {
  const [selected, setSelected] = useState<boolean | null>(null);

  const handleSubmit = () => {
    if (selected !== null) {
      onSubmit(selected.toString());
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          {content.question}
        </h3>
        {content.learning_objective && (
          <p className="text-sm text-gray-600 mb-4">
            📚 Objetivo: {content.learning_objective}
          </p>
        )}
      </div>

      <div className="flex gap-3">
        <button
          onClick={() => setSelected(true)}
          disabled={disabled}
          className={cn(
            'flex-1 px-6 py-4 rounded-lg border-2 font-medium transition-colors',
            selected === true
              ? 'border-green-500 bg-green-50 text-green-900'
              : 'border-gray-200 hover:border-gray-300',
            disabled && 'opacity-50 cursor-not-allowed'
          )}
        >
          ✓ Verdadero
        </button>
        <button
          onClick={() => setSelected(false)}
          disabled={disabled}
          className={cn(
            'flex-1 px-6 py-4 rounded-lg border-2 font-medium transition-colors',
            selected === false
              ? 'border-red-500 bg-red-50 text-red-900'
              : 'border-gray-200 hover:border-gray-300',
            disabled && 'opacity-50 cursor-not-allowed'
          )}
        >
          ✗ Falso
        </button>
      </div>

      <Button
        onClick={handleSubmit}
        disabled={disabled || selected === null}
        variant="primary"
        className="w-full"
      >
        Verificar Respuesta
      </Button>
    </div>
  );
};
