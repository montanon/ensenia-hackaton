import React, { useState } from 'react';
import type { ShortAnswerContent } from '../../types/exercise';
import { Button } from '../ui/Button';

interface ShortAnswerProps {
  content: ShortAnswerContent;
  onSubmit: (answer: string) => void;
  disabled?: boolean;
}

export const ShortAnswer: React.FC<ShortAnswerProps> = ({
  content,
  onSubmit,
  disabled,
}) => {
  const [answer, setAnswer] = useState('');

  const handleSubmit = () => {
    if (answer.trim()) {
      onSubmit(answer.trim());
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

      <div>
        <textarea
          value={answer}
          onChange={(e) => setAnswer(e.target.value)}
          placeholder="Escribe tu respuesta aquí..."
          disabled={disabled}
          rows={4}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none disabled:bg-gray-100"
        />
        <p className="mt-1 text-sm text-gray-500">
          {answer.length} caracteres
        </p>
      </div>

      <Button
        onClick={handleSubmit}
        disabled={disabled || !answer.trim()}
        variant="primary"
        className="w-full"
      >
        Enviar Respuesta
      </Button>
    </div>
  );
};
