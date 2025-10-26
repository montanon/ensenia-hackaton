import React, { useState, useEffect } from 'react';
import { speechRecognitionService } from '../../services/speech';
import { cn } from '../../utils/helpers';

interface VoiceButtonProps {
  onTranscript: (text: string) => void;
  disabled?: boolean;
}

export const VoiceButton: React.FC<VoiceButtonProps> = ({ onTranscript, disabled }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSupported] = useState(speechRecognitionService.isAvailable());

  useEffect(() => {
    return () => {
      if (isRecording) {
        speechRecognitionService.abort();
      }
    };
  }, [isRecording]);

  const startRecording = () => {
    if (!isSupported || disabled) return;

    setError(null);
    setTranscript('');
    setIsRecording(true);

    speechRecognitionService.start(
      (text, isFinal) => {
        setTranscript(text);
        if (isFinal) {
          onTranscript(text);
          setIsRecording(false);
          setTranscript('');
        }
      },
      (err) => {
        setError(err);
        setIsRecording(false);
        setTranscript('');
      },
      () => {
        setIsRecording(false);
      }
    );
  };

  const stopRecording = () => {
    if (transcript) {
      onTranscript(transcript);
    }
    speechRecognitionService.stop();
    setIsRecording(false);
    setTranscript('');
  };

  if (!isSupported) {
    return (
      <div className="text-sm text-gray-500 px-4 py-2 bg-gray-100 rounded-lg">
        🎤 Micrófono no disponible en este navegador
      </div>
    );
  }

  return (
    <div className="w-full">
      {/* Recording Button */}
      <button
        type="button"
        onMouseDown={startRecording}
        onMouseUp={stopRecording}
        onMouseLeave={stopRecording}
        onTouchStart={startRecording}
        onTouchEnd={stopRecording}
        disabled={disabled}
        className={cn(
          'w-full px-6 py-4 rounded-lg font-medium',
          'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500',
          'bg-blue-600 text-white hover:bg-blue-700',
          'transition-colors duration-200',
          isRecording && 'recording-button',
          disabled && 'opacity-50 cursor-not-allowed'
        )}
      >
        <div className="flex items-center justify-center gap-2">
          <span className={cn(
            "text-2xl transition-transform duration-200",
            isRecording && "recording-icon"
          )}>
            🎤
          </span>
          <span>
            {isRecording ? 'Grabando...' : 'Mantén presionado para hablar'}
          </span>
        </div>
      </button>

      <style>{`
        @keyframes breathe {
          0%, 100% {
            transform: scale(1);
            opacity: 1;
          }
          50% {
            transform: scale(0.98);
            opacity: 0.9;
          }
        }

        @keyframes icon-pulse {
          0%, 100% {
            transform: scale(1);
          }
          50% {
            transform: scale(1.1);
          }
        }

        .recording-button {
          animation: breathe 1.5s ease-in-out infinite;
        }

        .recording-icon {
          animation: icon-pulse 0.8s ease-in-out infinite;
        }
      `}</style>

      {/* Live Transcript */}
      {transcript && (
        <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-900">{transcript}</p>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mt-2 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-900">Error: {error}</p>
        </div>
      )}
    </div>
  );
};
