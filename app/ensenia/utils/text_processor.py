"""Text preprocessing for Chilean Spanish TTS.

Critical for:
- Number pronunciation in Spanish
- Abbreviation expansion
- Proper pacing for education
- Chilean Spanish specific handling
"""

import re

MAX_TEXT_LEN = 5_000
ELEMENTARY_LEVEL_THRESHOLD = 4


def preprocess_text(text: str, grade_level: int) -> str:
    """Preprocess text for optimal TTS pronunciation in Chilean Spanish.

    Args:
        text: Input text
        grade_level: Student grade level (affects pacing)

    Returns:
        Preprocessed text optimized for TTS

    """
    # Apply transformations in order
    text = convert_numbers_to_words(text)
    text = expand_abbreviations(text)
    text = add_educational_pauses(text, grade_level)
    return fix_punctuation(text)


def convert_numbers_to_words(text: str) -> str:
    """Convert numerical digits to Spanish words.

    Critical for math content - numbers must be spoken correctly.

    Args:
        text: Text containing numbers

    Returns:
        Text with numbers replaced by Spanish words

    """
    number_map = {
        "0": "cero",
        "1": "uno",
        "2": "dos",
        "3": "tres",
        "4": "cuatro",
        "5": "cinco",
        "6": "seis",
        "7": "siete",
        "8": "ocho",
        "9": "nueve",
        "10": "diez",
        "11": "once",
        "12": "doce",
        "13": "trece",
        "14": "catorce",
        "15": "quince",
        "16": "dieciséis",
        "17": "diecisiete",
        "18": "dieciocho",
        "19": "diecinueve",
        "20": "veinte",
        "21": "veintiuno",
        "22": "veintidós",
        "23": "veintitrés",
        "24": "veinticuatro",
        "25": "veinticinco",
        "26": "veintiséis",
        "27": "veintisiete",
        "28": "veintiocho",
        "29": "veintinueve",
        "30": "treinta",
        "40": "cuarenta",
        "50": "cincuenta",
        "60": "sesenta",
        "70": "setenta",
        "80": "ochenta",
        "90": "noventa",
        "100": "cien",
        "200": "doscientos",
        "300": "trescientos",
        "400": "cuatrocientos",
        "500": "quinientos",
        "600": "seiscientos",
        "700": "setecientos",
        "800": "ochocientos",
        "900": "novecientos",
        "1000": "mil",
    }

    # Replace standalone numbers (word boundaries)
    # Sort by length descending to replace longer numbers first
    for num, word in sorted(number_map.items(), key=lambda x: len(x[0]), reverse=True):
        text = re.sub(r"\b" + num + r"\b", word, text)

    return text


def expand_abbreviations(text: str) -> str:
    """Expand common Spanish abbreviations for clear pronunciation.

    Args:
        text: Text with abbreviations

    Returns:
        Text with expanded abbreviations

    """
    abbreviations = {
        "Dr.": "Doctor",
        "Dra.": "Doctora",
        "Sr.": "Señor",
        "Sra.": "Señora",
        "Srta.": "Señorita",
        "Prof.": "Profesor",
        "Profa.": "Profesora",
        "pág.": "página",
        "págs.": "páginas",
        "ej.": "ejemplo",
        "etc.": "etcétera",
        "p.ej.": "por ejemplo",
        "aprox.": "aproximadamente",
        "máx.": "máximo",
        "mín.": "mínimo",
        "cap.": "capítulo",
        "vs.": "versus",
        "a.C.": "antes de Cristo",
        "d.C.": "después de Cristo",
    }

    for abbr, full in abbreviations.items():
        text = text.replace(abbr, full)

    return text


def add_educational_pauses(text: str, grade_level: int) -> str:
    """Add pauses for better educational delivery.

    Younger students benefit from more pauses for comprehension.

    Args:
        text: Text to add pauses to
        grade_level: Student grade (1-12)

    Returns:
        Text with appropriate pauses

    """
    # Elementary students need more pauses
    if grade_level <= ELEMENTARY_LEVEL_THRESHOLD:
        # Ensure space after periods for pause
        text = re.sub(r"\.([^\s])", r". \1", text)
        # Ensure space after commas
        text = re.sub(r",([^\s])", r", \1", text)
        # Add extra pause after questions
        text = re.sub(r"\?", "? ", text)

    return text


def fix_punctuation(text: str) -> str:
    """Ensure proper punctuation for TTS pacing.

    Args:
        text: Text to fix

    Returns:
        Text with proper punctuation

    """
    # Ensure sentences end with punctuation
    if text and text[-1] not in ".!?":
        text += "."

    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text)

    # Ensure space after punctuation
    text = re.sub(r"([.!?,;:])([^\s])", r"\1 \2", text)

    # Remove space before punctuation
    text = re.sub(r"\s+([.!?,;:])", r"\1", text)

    return text.strip()


def chunk_long_text(text: str, max_chars: int = 500) -> list[str]:
    """Split long text into TTS-friendly chunks at sentence boundaries.

    Args:
        text: Long text to split
        max_chars: Maximum characters per chunk

    Returns:
        List of text chunks

    """
    # Split on sentence boundaries
    sentences = re.split(r"([.!?]+\s+)", text)

    chunks = []
    current_chunk = ""

    for i in range(0, len(sentences), 2):
        sentence = sentences[i]
        punctuation = sentences[i + 1] if i + 1 < len(sentences) else ""
        full_sentence = sentence + punctuation

        if len(current_chunk) + len(full_sentence) < max_chars:
            current_chunk += full_sentence
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = full_sentence

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def validate_text_for_tts(text: str) -> tuple[bool, str]:
    """Validate text is suitable for TTS.

    Args:
        text: Text to validate

    Returns:
        Tuple of (is_valid, error_message)

    """
    if not text or not text.strip():
        return False, "Text cannot be empty"

    if len(text) > MAX_TEXT_LEN:
        return False, "Text exceeds maximum length (5000 characters)"

    # Check for potential issues
    if re.search(r"https?://", text):
        return False, "Text contains URLs - remove before TTS"

    return True, ""
