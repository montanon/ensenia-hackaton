export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
export const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

export const GRADES = Array.from({ length: 12 }, (_, i) => i + 1);

export const SUBJECTS = [
  'Matemáticas',
  'Lenguaje y Comunicación',
  'Ciencias Naturales',
  'Historia y Geografía',
  'Inglés',
  'Artes',
  'Educación Física',
  'Tecnología',
] as const;

export const SESSION_MODES = [
  { value: 'learn', label: 'Aprender', icon: '📖', description: 'Explicaciones paso a paso' },
  { value: 'practice', label: 'Practicar', icon: '✏️', description: 'Ejercicios y retroalimentación' },
  { value: 'study', label: 'Estudiar', icon: '📝', description: 'Repasar conceptos' },
  { value: 'evaluation', label: 'Evaluación', icon: '📊', description: 'Probar conocimientos' },
] as const;

export const PLAYBACK_SPEEDS = [0.75, 1.0, 1.25, 1.5] as const;

export const DIFFICULTY_LEVELS = [
  { value: 1, label: 'Muy Fácil' },
  { value: 2, label: 'Fácil' },
  { value: 3, label: 'Medio' },
  { value: 4, label: 'Difícil' },
  { value: 5, label: 'Muy Difícil' },
] as const;
