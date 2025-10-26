import React from 'react';

export const SoundWaveVisualization: React.FC = () => {
  return (
    <div className="flex items-center justify-center gap-1 h-12 px-4">
      {[...Array(5)].map((_, i) => (
        <div
          key={i}
          className="w-1 bg-gradient-to-t from-blue-400 to-blue-600 rounded-full animate-pulse"
          style={{
            height: `${20 + Math.random() * 30}px`,
            animationDuration: `${0.5 + Math.random() * 0.5}s`,
            animationDelay: `${i * 0.1}s`,
          }}
        />
      ))}
    </div>
  );
};
