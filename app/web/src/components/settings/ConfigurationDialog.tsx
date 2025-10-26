import React, { useState } from 'react';
import { Dialog } from '@headlessui/react';
import { Button } from '../ui/Button';

interface ConfigurationDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ConfigurationDialog: React.FC<ConfigurationDialogProps> = ({ isOpen, onClose }) => {
  // Simple Settings (always visible)
  const [ttsSpeed, setTtsSpeed] = useState(1.0);
  const [voice, setVoice] = useState('femenina');
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [fontSize, setFontSize] = useState<'small' | 'medium' | 'large'>('medium');
  const [defaultDifficulty, setDefaultDifficulty] = useState(3);

  // Advanced Settings (collapsible)
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [maxIterations, setMaxIterations] = useState(3);
  const [qualityThreshold, setQualityThreshold] = useState(8);
  const [autoPlayAudio, setAutoPlayAudio] = useState(false);
  const [autoSave, setAutoSave] = useState(true);
  const [researchDepth, setResearchDepth] = useState(5);
  const [debugMode, setDebugMode] = useState(false);
  const [exerciseTypes, setExerciseTypes] = useState({
    multiple_choice: true,
    true_false: true,
    short_answer: true,
    essay: false,
  });

  const handleSave = () => {
    // Mock: Save to localStorage (for demonstration)
    const config = {
      simple: { ttsSpeed, voice, theme, fontSize, defaultDifficulty },
      advanced: { maxIterations, qualityThreshold, autoPlayAudio, autoSave, researchDepth, debugMode, exerciseTypes },
    };
    localStorage.setItem('ensenia_config', JSON.stringify(config));
    console.log('Configuration saved:', config);
    onClose();
  };

  return (
    <Dialog open={isOpen} onClose={onClose} className="relative z-50">
      <div className="fixed inset-0 bg-black/30" aria-hidden="true" />

      <div className="fixed inset-0 flex items-center justify-center p-4">
        <Dialog.Panel className="mx-auto max-w-2xl w-full bg-white rounded-xl shadow-lg max-h-[90vh] overflow-y-auto">
          {/* Header */}
          <div className="p-6 border-b border-gray-200 sticky top-0 bg-white z-10">
            <Dialog.Title className="text-2xl font-bold text-gray-900 flex items-center gap-3">
              <svg
                className="w-6 h-6 text-blue-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                />
              </svg>
              Configuración
            </Dialog.Title>
            <p className="text-sm text-gray-500 mt-1">Personaliza tu experiencia de aprendizaje</p>
          </div>

          <div className="p-6 space-y-6">
            {/* Simple Configuration */}
            <div className="space-y-5">
              <h3 className="text-lg font-semibold text-gray-900">Configuración General</h3>

              {/* TTS Speed */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Velocidad de Voz: {ttsSpeed.toFixed(1)}x
                </label>
                <input
                  type="range"
                  min="0.5"
                  max="2.0"
                  step="0.1"
                  value={ttsSpeed}
                  onChange={(e) => setTtsSpeed(parseFloat(e.target.value))}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>Lento (0.5x)</span>
                  <span>Rápido (2.0x)</span>
                </div>
              </div>

              {/* Voice Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Voz
                </label>
                <select
                  value={voice}
                  onChange={(e) => setVoice(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="femenina">Femenina</option>
                  <option value="masculina">Masculina</option>
                </select>
              </div>

              {/* Theme */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Tema
                </label>
                <div className="flex gap-3">
                  <button
                    onClick={() => setTheme('light')}
                    className={`flex-1 px-4 py-2 rounded-lg border-2 transition-colors ${
                      theme === 'light'
                        ? 'border-blue-500 bg-blue-50 text-blue-900'
                        : 'border-gray-300 hover:border-gray-400'
                    }`}
                  >
                    ☀️ Claro
                  </button>
                  <button
                    onClick={() => setTheme('dark')}
                    className={`flex-1 px-4 py-2 rounded-lg border-2 transition-colors ${
                      theme === 'dark'
                        ? 'border-blue-500 bg-blue-50 text-blue-900'
                        : 'border-gray-300 hover:border-gray-400'
                    }`}
                  >
                    🌙 Oscuro
                  </button>
                </div>
              </div>

              {/* Font Size */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Tamaño de Fuente
                </label>
                <div className="flex gap-2">
                  {(['small', 'medium', 'large'] as const).map((size) => (
                    <button
                      key={size}
                      onClick={() => setFontSize(size)}
                      className={`flex-1 px-4 py-2 rounded-lg border-2 transition-colors capitalize ${
                        fontSize === size
                          ? 'border-blue-500 bg-blue-50 text-blue-900'
                          : 'border-gray-300 hover:border-gray-400'
                      }`}
                    >
                      {size === 'small' ? 'Pequeño' : size === 'medium' ? 'Medio' : 'Grande'}
                    </button>
                  ))}
                </div>
              </div>

              {/* Default Difficulty */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Dificultad Predeterminada: {defaultDifficulty}/5
                </label>
                <input
                  type="range"
                  min="1"
                  max="5"
                  step="1"
                  value={defaultDifficulty}
                  onChange={(e) => setDefaultDifficulty(parseInt(e.target.value))}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>Fácil</span>
                  <span>Medio</span>
                  <span>Difícil</span>
                </div>
              </div>
            </div>

            {/* Advanced Configuration (Collapsible) */}
            <div className="border-t border-gray-200 pt-5">
              <button
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="w-full flex items-center justify-between text-left group"
              >
                <h3 className="text-lg font-semibold text-gray-900">Configuración Avanzada</h3>
                <svg
                  className={`w-5 h-5 text-gray-500 group-hover:text-gray-700 transition-transform duration-200 ${
                    showAdvanced ? 'rotate-180' : ''
                  }`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {showAdvanced && (
                <div className="mt-5 space-y-5 animate-fadeIn">
                  {/* Max Iterations */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Iteraciones Máximas (Generación): {maxIterations}
                    </label>
                    <input
                      type="range"
                      min="1"
                      max="5"
                      step="1"
                      value={maxIterations}
                      onChange={(e) => setMaxIterations(parseInt(e.target.value))}
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                    />
                  </div>

                  {/* Quality Threshold */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Umbral de Calidad: {qualityThreshold}/10
                    </label>
                    <input
                      type="range"
                      min="6"
                      max="10"
                      step="1"
                      value={qualityThreshold}
                      onChange={(e) => setQualityThreshold(parseInt(e.target.value))}
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                    />
                  </div>

                  {/* Research Depth */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Profundidad de Investigación: {researchDepth} elementos
                    </label>
                    <input
                      type="range"
                      min="3"
                      max="10"
                      step="1"
                      value={researchDepth}
                      onChange={(e) => setResearchDepth(parseInt(e.target.value))}
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                    />
                  </div>

                  {/* Toggles */}
                  <div className="space-y-3">
                    <label className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <span className="text-sm font-medium text-gray-700">Auto-reproducir Audio</span>
                      <input
                        type="checkbox"
                        checked={autoPlayAudio}
                        onChange={(e) => setAutoPlayAudio(e.target.checked)}
                        className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                      />
                    </label>

                    <label className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <span className="text-sm font-medium text-gray-700">Auto-guardar Sesión</span>
                      <input
                        type="checkbox"
                        checked={autoSave}
                        onChange={(e) => setAutoSave(e.target.checked)}
                        className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                      />
                    </label>

                    <label className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <span className="text-sm font-medium text-gray-700">Modo Debug</span>
                      <input
                        type="checkbox"
                        checked={debugMode}
                        onChange={(e) => setDebugMode(e.target.checked)}
                        className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                      />
                    </label>
                  </div>

                  {/* Exercise Types */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Tipos de Ejercicios Habilitados
                    </label>
                    <div className="space-y-2">
                      <label className="flex items-center p-2 rounded hover:bg-gray-50">
                        <input
                          type="checkbox"
                          checked={exerciseTypes.multiple_choice}
                          onChange={(e) => setExerciseTypes({ ...exerciseTypes, multiple_choice: e.target.checked })}
                          className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                        />
                        <span className="ml-2 text-sm text-gray-700">Selección Múltiple</span>
                      </label>
                      <label className="flex items-center p-2 rounded hover:bg-gray-50">
                        <input
                          type="checkbox"
                          checked={exerciseTypes.true_false}
                          onChange={(e) => setExerciseTypes({ ...exerciseTypes, true_false: e.target.checked })}
                          className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                        />
                        <span className="ml-2 text-sm text-gray-700">Verdadero/Falso</span>
                      </label>
                      <label className="flex items-center p-2 rounded hover:bg-gray-50">
                        <input
                          type="checkbox"
                          checked={exerciseTypes.short_answer}
                          onChange={(e) => setExerciseTypes({ ...exerciseTypes, short_answer: e.target.checked })}
                          className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                        />
                        <span className="ml-2 text-sm text-gray-700">Respuesta Corta</span>
                      </label>
                      <label className="flex items-center p-2 rounded hover:bg-gray-50">
                        <input
                          type="checkbox"
                          checked={exerciseTypes.essay}
                          onChange={(e) => setExerciseTypes({ ...exerciseTypes, essay: e.target.checked })}
                          className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                        />
                        <span className="ml-2 text-sm text-gray-700">Ensayo</span>
                      </label>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Footer */}
          <div className="p-6 border-t border-gray-200 bg-gray-50 flex gap-3 sticky bottom-0">
            <Button
              type="button"
              variant="ghost"
              onClick={onClose}
              className="flex-1"
            >
              Cancelar
            </Button>
            <Button
              type="button"
              variant="primary"
              onClick={handleSave}
              className="flex-1"
            >
              Guardar Configuración
            </Button>
          </div>
        </Dialog.Panel>
      </div>
    </Dialog>
  );
};
