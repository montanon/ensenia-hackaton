"""Exercise generation service using LangGraph.

This service orchestrates an agent-validator loop to generate high-quality
exercises aligned with Chilean Ministry of Education curriculum standards.

Architecture:
- Generator Agent: Creates initial exercise using OpenAI
- Validator Agent: Evaluates quality, curriculum alignment, and difficulty
- Refinement Loop: Iteratively improves exercise until quality threshold is met

Uses LangGraph for state management and conditional routing.
"""

import json
import logging
from typing import Annotated, Any

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

from app.ensenia.core.config import settings
from app.ensenia.schemas.exercises import (
    DifficultyLevel,
    EssayContent,
    ExerciseType,
    MultipleChoiceContent,
    ShortAnswerContent,
    TrueFalseContent,
    ValidationResult,
)

logger = logging.getLogger(__name__)


# ============================================================================
# State Schema
# ============================================================================


class GenerationState(BaseModel):
    """State for the exercise generation workflow."""

    # Input parameters
    exercise_type: ExerciseType
    grade: int
    subject: str
    topic: str
    difficulty_level: DifficultyLevel
    curriculum_context: str | None = None

    # Configuration
    max_iterations: int
    quality_threshold: int

    # State tracking
    messages: Annotated[list[BaseMessage], add_messages] = Field(default_factory=list)
    exercise_draft: dict[str, Any] | None = None
    validation_feedback: str | None = None
    validation_score: int = 0
    iteration_count: int = 0
    is_approved: bool = False
    validation_history: list[ValidationResult] = Field(default_factory=list)


# ============================================================================
# Prompt Templates
# ============================================================================

GENERATOR_SYSTEM_PROMPT = """Eres un experto en educación chilena y diseño de ejercicios pedagógicos.  # noqa: E501
Tu tarea es crear ejercicios de alta calidad alineados con las Bases Curriculares del Ministerio de Educación de Chile.  # noqa: E501

INSTRUCCIONES IMPORTANTES:
1. El ejercicio DEBE estar completamente en español chileno
2. Usar terminología y ejemplos apropiados para estudiantes chilenos
3. Alinearse con los objetivos de aprendizaje del currículo nacional
4. Ser apropiado para el nivel de grado especificado
5. Tener el nivel de dificultad solicitado
6. Ser claro, preciso y pedagógicamente sólido

CONTEXTO CURRICULAR:
{curriculum_context}

PARÁMETROS DEL EJERCICIO:
- Tipo: {exercise_type}
- Grado: {grade}
- Asignatura: {subject}
- Tema: {topic}
- Nivel de dificultad: {difficulty_level}/5

{type_specific_instructions}

IMPORTANTE: Responde SOLO con un JSON válido que siga exactamente el esquema especificado.  # noqa: E501
No incluyas texto adicional, solo el JSON."""

VALIDATOR_SYSTEM_PROMPT = """Eres un evaluador experto de ejercicios educativos para el sistema educativo chileno.  # noqa: E501
Tu tarea es evaluar la calidad de ejercicios generados y proporcionar retroalimentación constructiva.  # noqa: E501

CRITERIOS DE EVALUACIÓN (puntaje 0-10):
1. Alineación curricular (0-2 puntos): ¿Se alinea con las Bases Curriculares?
2. Apropiado para el grado (0-2 puntos): ¿Es adecuado para el nivel?
3. Nivel de dificultad correcto (0-2 puntos): ¿Coincide con el nivel solicitado?
4. Calidad pedagógica (0-2 puntos): ¿Es claro, preciso y educativo?
5. Español chileno correcto (0-2 puntos): ¿Usa terminología y contexto chileno?

UMBRALES:
- 8-10: Excelente, aprobado
- 6-7: Bueno, pero necesita mejoras
- 0-5: Insuficiente, requiere revisión significativa

Proporciona:
1. Puntaje total (0-10)
2. Desglose por criterio
3. Retroalimentación específica para mejorar
4. Recomendación: APROBAR o REVISAR"""


TYPE_SPECIFIC_INSTRUCTIONS = {
    ExerciseType.MULTIPLE_CHOICE: """
FORMATO DE SALIDA (JSON):
{
    "question": "La pregunta del ejercicio",
    "learning_objective": "Objetivo de aprendizaje de las Bases Curriculares",
    "options": ["Opción 1", "Opción 2", "Opción 3", "Opción 4"],
    "correct_answer": 0,  // Índice (0-based) de la respuesta correcta
    "explanation": "Explicación de por qué la respuesta es correcta"
}

REQUISITOS:
- La pregunta debe ser clara y sin ambigüedades
- Proporcionar 4 opciones (pueden ser más si es necesario)
- Solo UNA opción debe ser correcta
- Los distractores deben ser plausibles pero incorrectos
- La explicación debe ayudar al estudiante a entender el concepto
""",
    ExerciseType.TRUE_FALSE: """
FORMATO DE SALIDA (JSON):
{
    "question": "La afirmación a evaluar",
    "learning_objective": "Objetivo de aprendizaje de las Bases Curriculares",
    "correct_answer": true,  // o false
    "explanation": "Explicación de por qué la afirmación es verdadera o falsa"
}

REQUISITOS:
- La afirmación debe ser claramente verdadera o falsa
- Evitar afirmaciones ambiguas o con excepciones
- La explicación debe aclarar por qué es V o F
""",
    ExerciseType.SHORT_ANSWER: """
FORMATO DE SALIDA (JSON):
{
    "question": "La pregunta que requiere respuesta breve",
    "learning_objective": "Objetivo de aprendizaje de las Bases Curriculares",
    "rubric": [
        "Criterio 1 de evaluación",
        "Criterio 2 de evaluación",
        "Criterio 3 de evaluación"
    ],
    "example_answer": "Ejemplo de una buena respuesta (1-3 oraciones)",
    "max_words": 100
}

REQUISITOS:
- La pregunta debe poder responderse en 1-3 oraciones
- La rúbrica debe tener 2-10 criterios claros
- La respuesta de ejemplo debe demostrar una respuesta completa
""",
    ExerciseType.ESSAY: """
FORMATO DE SALIDA (JSON):
{
    "question": "La pregunta que requiere respuesta extensa",
    "learning_objective": "Objetivo de aprendizaje de las Bases Curriculares",
    "rubric": [
        "Criterio 1 de evaluación",
        "Criterio 2 de evaluación",
        "Criterio 3 de evaluación",
        "Criterio 4 de evaluación"
    ],
    "key_points": [
        "Punto clave 1 que debe abordarse",
        "Punto clave 2 que debe abordarse",
        "Punto clave 3 que debe abordarse"
    ],
    "min_words": 150,
    "max_words": 500
}

REQUISITOS:
- La pregunta debe requerir análisis profundo o argumentación
- La rúbrica debe tener 3-15 criterios claros
- Los puntos clave deben cubrir los aspectos principales del tema
""",
}


# ============================================================================
# Node Functions
# ============================================================================


def generate_node(state: GenerationState) -> dict[str, Any]:
    """Generate or refine exercise using OpenAI.

    On first iteration: Creates initial exercise.
    On subsequent iterations: Refines based on validation feedback.
    """
    llm = ChatOpenAI(
        model=settings.generation_model,
        api_key=settings.openai_api_key,
        temperature=0.7,
    )

    # Build curriculum context
    curriculum_context = state.curriculum_context or (
        f"No se proporcionó contexto específico. "
        f"Usar conocimiento general de las Bases Curriculares "
        f"para {state.subject} en {state.grade}° básico/medio."
    )

    # Get type-specific instructions
    type_instructions = TYPE_SPECIFIC_INSTRUCTIONS.get(
        state.exercise_type, "Generar ejercicio apropiado."
    )

    # Build system prompt
    system_prompt = GENERATOR_SYSTEM_PROMPT.format(
        curriculum_context=curriculum_context,
        exercise_type=state.exercise_type.value,
        grade=state.grade,
        subject=state.subject,
        topic=state.topic,
        difficulty_level=state.difficulty_level.value,
        type_specific_instructions=type_instructions,
    )

    # Build user message
    if state.iteration_count == 0:
        user_message = f"Genera un ejercicio de tipo {state.exercise_type.value} sobre el tema: {state.topic}"
    else:
        user_message = f"""Mejora el siguiente ejercicio basándote en esta retroalimentación:  # noqa: E501

RETROALIMENTACIÓN:
{state.validation_feedback}

EJERCICIO ACTUAL:
{json.dumps(state.exercise_draft, indent=2, ensure_ascii=False)}

Genera una versión mejorada que aborde todos los puntos de la retroalimentación."""

    # Call LLM
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message),
    ]

    response = llm.invoke(messages)
    response_text = response.content

    # Parse JSON response
    try:
        # Extract JSON from response (in case there's extra text)
        start_idx = response_text.find("{")
        end_idx = response_text.rfind("}") + 1
        if start_idx != -1 and end_idx > start_idx:
            json_text = response_text[start_idx:end_idx]
            exercise_draft = json.loads(json_text)
        else:
            msg = f"No JSON found in response: {response_text}"
            logger.error(msg)
            exercise_draft = {"error": "Failed to parse exercise"}
    except json.JSONDecodeError as e:
        msg = f"JSON decode error: {e}\nResponse: {response_text}"
        logger.exception(msg)
        exercise_draft = {"error": "Invalid JSON format"}

    msg = (
        f"Generated exercise (iteration {state.iteration_count + 1}): "
        f"{json.dumps(exercise_draft, ensure_ascii=False)[:200]}..."
    )
    logger.info(msg)

    return {
        "exercise_draft": exercise_draft,
        "iteration_count": state.iteration_count + 1,
        "messages": [*messages, response],
    }


def validate_node(state: GenerationState) -> dict[str, Any]:
    """Validate exercise quality and provide feedback."""
    llm = ChatOpenAI(
        model=settings.generation_model,
        api_key=settings.openai_api_key,
        temperature=0.3,  # Lower temperature for consistent evaluation
    )

    # Build validation prompt
    system_prompt = VALIDATOR_SYSTEM_PROMPT

    user_message = f"""Evalúa el siguiente ejercicio:

PARÁMETROS ESPERADOS:
- Tipo: {state.exercise_type.value}
- Grado: {state.grade}
- Asignatura: {state.subject}
- Tema: {state.topic}
- Nivel de dificultad esperado: {state.difficulty_level.value}/5

EJERCICIO A EVALUAR:
{json.dumps(state.exercise_draft, indent=2, ensure_ascii=False)}

Proporciona tu evaluación en el siguiente formato JSON:
{{
    "score": 8,  // Puntaje total (0-10)
    "breakdown": {{
        "curriculum_alignment": 2,
        "grade_appropriate": 2,
        "difficulty_match": 2,
        "pedagogical_quality": 1,
        "chilean_spanish": 2
    }},
    "feedback": "Retroalimentación detallada aquí...",
    "recommendation": "APROBAR"  // o "REVISAR"
}}"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message),
    ]

    response = llm.invoke(messages)
    response_text = response.content

    # Parse validation result
    try:
        start_idx = response_text.find("{")
        end_idx = response_text.rfind("}") + 1
        if start_idx != -1 and end_idx > start_idx:
            json_text = response_text[start_idx:end_idx]
            validation_result = json.loads(json_text)
        else:
            msg = f"No JSON in validation response: {response_text}"
            logger.error(msg)
            validation_result = {
                "score": 5,
                "feedback": "Validation failed",
                "recommendation": "REVISAR",
            }
    except json.JSONDecodeError as e:
        msg = f"Validation JSON decode error: {e}\nResponse: {response_text}"
        logger.exception(msg)
        validation_result = {
            "score": 5,
            "feedback": "Invalid validation format",
            "recommendation": "REVISAR",
        }

    score = validation_result.get("score", 0)
    feedback = validation_result.get("feedback", "No feedback provided")
    recommendation = validation_result.get("recommendation", "REVISAR")

    is_approved = score >= state.quality_threshold or recommendation == "APROBAR"

    # Record in validation history
    validation_record = ValidationResult(
        score=score,
        feedback=feedback,
        is_approved=is_approved,
        iteration=state.iteration_count,
    )

    msg = (
        f"Validation (iteration {state.iteration_count}): "
        f"score={score}, approved={is_approved}"
    )
    logger.info(msg)

    return {
        "validation_score": score,
        "validation_feedback": feedback,
        "is_approved": is_approved,
        "validation_history": [*state.validation_history, validation_record],
        "messages": [*messages, response],
    }


def should_continue(state: GenerationState) -> str:
    """Decide whether to continue refining or end the workflow."""
    # Check if approved
    if state.is_approved:
        logger.info("Exercise approved! Ending workflow.")
        return END

    # Check if max iterations reached
    if state.iteration_count >= state.max_iterations:
        msg = (
            f"Max iterations ({state.max_iterations}) reached. "
            f"Accepting with score {state.validation_score}"
        )
        logger.warning(msg)
        return END
    # Continue refining
    msg = (
        f"Score {state.validation_score} < threshold {state.quality_threshold}. "
        f"Continuing to iteration {state.iteration_count + 1}"
    )
    logger.info(msg)
    return "generate"


# ============================================================================
# Graph Construction
# ============================================================================


def create_generation_graph() -> StateGraph:
    """Create the LangGraph state machine for exercise generation."""
    workflow = StateGraph(GenerationState)

    # Add nodes
    workflow.add_node("generate", generate_node)
    workflow.add_node("validate", validate_node)

    # Add edges
    workflow.set_entry_point("generate")
    workflow.add_edge("generate", "validate")
    workflow.add_conditional_edges(
        "validate",
        should_continue,
        {
            "generate": "generate",  # Continue loop
            END: END,  # Finish
        },
    )

    return workflow.compile()


# ============================================================================
# Service Class
# ============================================================================


class GenerationService:
    """Service for generating exercises using LangGraph agent-validator loop."""

    def __init__(self) -> None:
        """Initialize the generation service."""
        self.graph = create_generation_graph()
        logger.info("GenerationService initialized with LangGraph workflow")

    async def generate_exercise(
        self,
        exercise_type: ExerciseType,
        grade: int,
        subject: str,
        topic: str,
        difficulty_level: DifficultyLevel = DifficultyLevel.MEDIUM,
        max_iterations: int | None = None,
        quality_threshold: int | None = None,
        curriculum_context: str | None = None,
    ) -> tuple[dict[str, Any], list[ValidationResult], int]:
        """Generate an exercise using the agent-validator loop.

        Args:
            exercise_type: Type of exercise to generate
            grade: Grade level (1-12)
            subject: Subject area
            topic: Specific topic
            difficulty_level: Desired difficulty (1-5)
            max_iterations: Max validation iterations (overrides config)
            quality_threshold: Min quality score (overrides config)
            curriculum_context: Additional curriculum context

        Returns:
            Tuple of (exercise_content, validation_history, iterations_used)

        """
        # Use config defaults if not specified
        max_iter = max_iterations or settings.generation_max_iterations
        quality_thresh = quality_threshold or settings.generation_quality_threshold

        msg = (
            f"Generating {exercise_type.value} exercise: "
            f"grade={grade}, subject={subject}, topic={topic}, "
            f"difficulty={difficulty_level.value}, max_iter={max_iter}, "
            f"threshold={quality_thresh}"
        )
        logger.info(msg)
        # Initialize state
        initial_state = GenerationState(
            exercise_type=exercise_type,
            grade=grade,
            subject=subject,
            topic=topic,
            difficulty_level=difficulty_level,
            curriculum_context=curriculum_context,
            max_iterations=max_iter,
            quality_threshold=quality_thresh,
        )

        # Run the graph
        final_state = self.graph.invoke(initial_state)

        # Extract results
        exercise_content = final_state["exercise_draft"]
        validation_history = final_state["validation_history"]
        iterations_used = final_state["iteration_count"]

        msg = (
            f"Exercise generation complete: "
            f"iterations={iterations_used}, "
            f"final_score={final_state['validation_score']}"
        )

        return exercise_content, validation_history, iterations_used

    def validate_content_schema(
        self, exercise_type: ExerciseType, content: dict[str, Any]
    ) -> bool:
        """Validate that content matches the expected schema for exercise type.

        Args:
            exercise_type: Type of exercise
            content: Exercise content to validate

        Returns:
            True if valid, False otherwise

        """
        try:
            if exercise_type == ExerciseType.MULTIPLE_CHOICE:
                MultipleChoiceContent(**content)
            elif exercise_type == ExerciseType.TRUE_FALSE:
                TrueFalseContent(**content)
            elif exercise_type == ExerciseType.SHORT_ANSWER:
                ShortAnswerContent(**content)
            elif exercise_type == ExerciseType.ESSAY:
                EssayContent(**content)
            else:
                return False
            return True
        except Exception:
            msg = "Content validation failed"
            logger.exception(msg)
            return False


# ============================================================================
# Dependency Injection
# ============================================================================

_generation_service: GenerationService | None = None


def get_generation_service() -> GenerationService:
    """Get or create the singleton GenerationService instance."""
    global _generation_service  # noqa: PLW0603
    if _generation_service is None:
        _generation_service = GenerationService()
    return _generation_service
