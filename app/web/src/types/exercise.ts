export type ExerciseType = 'multiple_choice' | 'true_false' | 'short_answer' | 'essay';

export interface MultipleChoiceContent {
  question: string;
  learning_objective: string;
  options: string[];
  correct_answer: number;
  explanation: string;
}

export interface TrueFalseContent {
  question: string;
  learning_objective: string;
  correct_answer: boolean;
  explanation: string;
}

export interface ShortAnswerContent {
  question: string;
  learning_objective: string;
  rubric: string;
  example_answer: string;
}

export interface EssayContent {
  question: string;
  learning_objective: string;
  rubric: string;
  key_points: string[];
  min_words: number;
  max_words: number;
}

export type ExerciseContent =
  | MultipleChoiceContent
  | TrueFalseContent
  | ShortAnswerContent
  | EssayContent;

export interface Exercise {
  id: number;
  exercise_type: ExerciseType;
  grade: number;
  subject: string;
  topic: string;
  content: ExerciseContent;
  validation_score: number;
  difficulty_level: number;
  is_public: boolean;
  created_at: string;
}

export interface GenerateExerciseRequest {
  exercise_type: ExerciseType;
  grade: number;
  subject: string;
  topic: string;
  difficulty_level: number;
  max_iterations?: number;
  quality_threshold?: number;
  curriculum_context?: string;
}

export interface SubmitAnswerRequest {
  answer: string;
}

export interface ValidationResult {
  score: number;
  feedback: string;
  issues: string[];
}

export interface GenerateExerciseResponse {
  exercise: Exercise;
  validation_history: ValidationResult[];
  iterations_used: number;
}
