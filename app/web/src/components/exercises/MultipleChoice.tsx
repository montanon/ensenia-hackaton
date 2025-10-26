import React, { useState } from 'react';
import type { MultipleChoiceContent } from '../../types/exercise';
import { Button } from '../ui/Button';
import { cn } from '../../utils/helpers';

interface MultipleChoiceProps {
  content: MultipleChoiceContent;
  onSubmit: (answer: string) => void;
  disabled?: boolean;
}

export const MultipleChoice: React.FC<MultipleChoiceProps> = ({
  content,
  onSubmit,
  disabled,
}) => {
  const [selectedOption, setSelectedOption] = useState<number | null>(null);

  const handleSubmit = () => {
    if (selectedOption !== null) {
      onSubmit(selectedOption.toString());
    }
  };

  return (
    <div className="space-y-4">
      {/* Question */}
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

      {/* Options */}
      <div className="space-y-2">
        {content.options.map((option, index) => (
          <button
            key={index}
            onClick={() => setSelectedOption(index)}
            disabled={disabled}
            className={cn(
              'w-full text-left px-4 py-3 rounded-lg border-2 transition-colors',
              selectedOption === index
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300',
              disabled && 'opacity-50 cursor-not-allowed'
            )}
          >
            <div className="flex items-center gap-3">
              <div className={cn(
                'w-5 h-5 rounded-full border-2 flex items-center justify-center',
                selectedOption === index
                  ? 'border-blue-500 bg-blue-500'
                  : 'border-gray-300'
              )}>
                {selectedOption === index && (
                  <div className="w-2 h-2 bg-white rounded-full" />
                )}
              </div>
              <span className="text-gray-900">{option}</span>
            </div>
          </button>
        ))}
      </div>

      {/* Submit Button */}
      <Button
        onClick={handleSubmit}
        disabled={disabled || selectedOption === null}
        variant="primary"
        className="w-full"
      >
        Verificar Respuesta
      </Button>
    </div>
  );
};
