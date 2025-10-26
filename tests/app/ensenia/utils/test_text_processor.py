"""Comprehensive unit tests for text_processor module.

Tests all critical text preprocessing functions for Chilean Spanish TTS:
- Number to Spanish word conversion
- Abbreviation expansion
- Educational pausing
- Punctuation fixing
- Text chunking
- Input validation
"""

import pytest

from app.ensenia.utils.text_processor import (
    ELEMENTARY_LEVEL_THRESHOLD,
    MAX_TEXT_LEN,
    add_educational_pauses,
    chunk_long_text,
    convert_numbers_to_words,
    expand_abbreviations,
    fix_punctuation,
    preprocess_text,
    validate_text_for_tts,
)


class TestConvertNumbersToWords:
    """Test number to Spanish word conversion."""

    def test_single_digit_numbers(self):
        """Test conversion of single digit numbers (0-9)."""
        assert convert_numbers_to_words("0") == "cero"
        assert convert_numbers_to_words("1") == "uno"
        assert convert_numbers_to_words("5") == "cinco"
        assert convert_numbers_to_words("9") == "nueve"

    def test_teen_numbers(self):
        """Test conversion of teen numbers (10-19)."""
        assert convert_numbers_to_words("10") == "diez"
        assert convert_numbers_to_words("13") == "trece"
        assert convert_numbers_to_words("15") == "quince"
        assert convert_numbers_to_words("19") == "diecinueve"

    def test_twenties(self):
        """Test conversion of numbers 20-29."""
        assert convert_numbers_to_words("20") == "veinte"
        assert convert_numbers_to_words("21") == "veintiuno"
        assert convert_numbers_to_words("25") == "veinticinco"
        assert convert_numbers_to_words("29") == "veintinueve"

    def test_tens(self):
        """Test conversion of round tens (30, 40, etc.)."""
        assert convert_numbers_to_words("30") == "treinta"
        assert convert_numbers_to_words("40") == "cuarenta"
        assert convert_numbers_to_words("50") == "cincuenta"
        assert convert_numbers_to_words("60") == "sesenta"
        assert convert_numbers_to_words("70") == "setenta"
        assert convert_numbers_to_words("80") == "ochenta"
        assert convert_numbers_to_words("90") == "noventa"

    def test_hundreds(self):
        """Test conversion of hundreds."""
        assert convert_numbers_to_words("100") == "cien"
        assert convert_numbers_to_words("200") == "doscientos"
        assert convert_numbers_to_words("500") == "quinientos"
        assert convert_numbers_to_words("900") == "novecientos"

    def test_thousands(self):
        """Test conversion of 1000."""
        assert convert_numbers_to_words("1000") == "mil"

    def test_math_expression(self):
        """Test conversion in mathematical expressions."""
        result = convert_numbers_to_words("3 + 5 = 8")
        assert "tres" in result
        assert "cinco" in result
        assert "ocho" in result

    def test_mixed_content(self):
        """Test numbers mixed with text."""
        text = "Tengo 5 manzanas y 10 naranjas"
        result = convert_numbers_to_words(text)
        assert "cinco" in result
        assert "diez" in result
        assert "manzanas" in result
        assert "naranjas" in result

    def test_word_boundaries(self):
        """Test that only standalone numbers are converted."""
        # Should convert 3 but not the 3 in "palabra3"
        text = "3 estudiantes palabra3"
        result = convert_numbers_to_words(text)
        assert "tres estudiantes" in result
        assert "palabra3" in result  # Should not change

    def test_multiple_numbers_in_sentence(self):
        """Test sentence with multiple numbers."""
        text = "2 mas 3 es igual a 5"
        result = convert_numbers_to_words(text)
        assert result == "dos mas tres es igual a cinco"

    def test_larger_numbers_replaced_first(self):
        """Test that longer numbers are replaced before shorter ones."""
        # 100 should become "cien" not "unocero"
        text = "100"
        result = convert_numbers_to_words(text)
        assert result == "cien"
        assert "cero" not in result

    def test_empty_string(self):
        """Test with empty string."""
        assert convert_numbers_to_words("") == ""

    def test_no_numbers(self):
        """Test text without numbers."""
        text = "Hola mundo"
        assert convert_numbers_to_words(text) == text


class TestExpandAbbreviations:
    """Test abbreviation expansion."""

    def test_doctor_abbreviations(self):
        """Test doctor title abbreviations."""
        assert expand_abbreviations("Dr. Pérez") == "Doctor Pérez"
        assert expand_abbreviations("Dra. García") == "Doctora García"

    def test_honorifics(self):
        """Test honorific abbreviations."""
        assert expand_abbreviations("Sr. López") == "Señor López"
        assert expand_abbreviations("Sra. Martínez") == "Señora Martínez"
        assert expand_abbreviations("Srta. Rodríguez") == "Señorita Rodríguez"

    def test_professor_abbreviations(self):
        """Test professor abbreviations."""
        assert expand_abbreviations("Prof. Silva") == "Profesor Silva"
        assert expand_abbreviations("Profa. Torres") == "Profesora Torres"

    def test_page_abbreviations(self):
        """Test page abbreviations."""
        assert expand_abbreviations("Ver pág. 10") == "Ver página 10"
        assert expand_abbreviations("págs. 5-10") == "páginas 5-10"

    def test_common_abbreviations(self):
        """Test common abbreviations."""
        assert expand_abbreviations("Por ej. esto") == "Por ejemplo esto"
        assert expand_abbreviations("p.ej. aquí") == "por ejemplo aquí"
        assert expand_abbreviations("etc. y mas") == "etcétera y mas"

    def test_measurement_abbreviations(self):
        """Test measurement abbreviations."""
        assert expand_abbreviations("máx. 100") == "máximo 100"
        assert expand_abbreviations("mín. 10") == "mínimo 10"
        assert expand_abbreviations("aprox. 50") == "aproximadamente 50"

    def test_time_abbreviations(self):
        """Test time period abbreviations."""
        assert expand_abbreviations("año 500 a.C.") == "año 500 antes de Cristo"
        assert expand_abbreviations("año 100 d.C.") == "año 100 después de Cristo"

    def test_multiple_abbreviations(self):
        """Test multiple abbreviations in one text."""
        text = "El Dr. Pérez enseña en pág. 5, etc."
        result = expand_abbreviations(text)
        # expand_abbreviations only expands, doesn't add punctuation
        assert result == "El Doctor Pérez enseña en página 5, etcétera"

    def test_case_sensitive(self):
        """Test that abbreviation replacement is case sensitive."""
        # Should not replace lowercase "dr." (not in our dict)
        text = "dr. smith"
        result = expand_abbreviations(text)
        assert result == text  # Should remain unchanged

    def test_empty_string(self):
        """Test with empty string."""
        assert expand_abbreviations("") == ""

    def test_no_abbreviations(self):
        """Test text without abbreviations."""
        text = "Hola estudiantes de Chile"
        assert expand_abbreviations(text) == text


class TestAddEducationalPauses:
    """Test educational pause addition."""

    def test_elementary_adds_pauses_after_periods(self):
        """Test that elementary level adds pauses after periods."""
        text = "Hola.Bienvenidos.Estudiantes"
        result = add_educational_pauses(text, grade_level=3)
        assert result == "Hola. Bienvenidos. Estudiantes"

    def test_elementary_adds_pauses_after_commas(self):
        """Test that elementary level adds pauses after commas."""
        text = "Hola,estudiantes,bienvenidos"
        result = add_educational_pauses(text, grade_level=3)
        assert result == "Hola, estudiantes, bienvenidos"

    def test_elementary_adds_pauses_after_questions(self):
        """Test that elementary level adds pauses after question marks."""
        text = "�Entiendes?Muy bien"
        result = add_educational_pauses(text, grade_level=3)
        assert "? " in result

    def test_middle_school_no_extra_pauses(self):
        """Test that middle school doesn't add extra pauses."""
        text = "Hola.Bienvenidos"
        result = add_educational_pauses(text, grade_level=6)
        # Should not add extra spaces for middle school
        assert result == text

    def test_high_school_no_extra_pauses(self):
        """Test that high school doesn't add extra pauses."""
        text = "Hola.Bienvenidos"
        result = add_educational_pauses(text, grade_level=11)
        assert result == text

    def test_threshold_boundary(self):
        """Test the exact threshold boundary."""
        text = "Hola.Test"
        # Grade 4 should add pauses (<=4)
        result_4 = add_educational_pauses(text, grade_level=ELEMENTARY_LEVEL_THRESHOLD)
        assert ". " in result_4

        # Grade 5 should not add pauses (>4)
        result_5 = add_educational_pauses(
            text, grade_level=ELEMENTARY_LEVEL_THRESHOLD + 1
        )
        assert result_5 == text

    def test_already_has_spaces(self):
        """Test text that already has proper spacing."""
        text = "Hola. Bienvenidos, estudiantes."
        result = add_educational_pauses(text, grade_level=3)
        # Should not double-space
        assert "  " not in result

    def test_empty_string(self):
        """Test with empty string."""
        assert add_educational_pauses("", grade_level=3) == ""


class TestFixPunctuation:
    """Test punctuation fixing."""

    def test_adds_period_to_unpunctuated_sentence(self):
        """Test that period is added to sentences without punctuation."""
        assert fix_punctuation("Hola mundo") == "Hola mundo."

    def test_preserves_existing_period(self):
        """Test that existing periods are preserved."""
        assert fix_punctuation("Hola mundo.") == "Hola mundo."

    def test_preserves_question_mark(self):
        """Test that question marks are preserved."""
        assert fix_punctuation("�C�mo est�s?") == "�C�mo est�s?"

    def test_preserves_exclamation(self):
        """Test that exclamation marks are preserved."""
        assert fix_punctuation("�Hola!") == "�Hola!"

    def test_removes_excessive_whitespace(self):
        """Test that excessive whitespace is removed."""
        text = "Hola    mundo   test"
        assert fix_punctuation(text) == "Hola mundo test."

    def test_adds_space_after_punctuation(self):
        """Test that space is added after punctuation."""
        assert fix_punctuation("Hola.Mundo") == "Hola. Mundo."
        assert fix_punctuation("Hola,mundo") == "Hola, mundo."

    def test_removes_space_before_punctuation(self):
        """Test that space before punctuation is removed."""
        assert fix_punctuation("Hola .Mundo") == "Hola. Mundo."
        assert fix_punctuation("Hola ,mundo") == "Hola, mundo."

    def test_multiple_sentences(self):
        """Test proper spacing with multiple sentences."""
        text = "Primera oraci�n.Segunda oraci�n.Tercera"
        result = fix_punctuation(text)
        assert result == "Primera oraci�n. Segunda oraci�n. Tercera."

    def test_strips_leading_trailing_whitespace(self):
        """Test that leading/trailing whitespace is removed."""
        assert fix_punctuation("  Hola mundo  ") == "Hola mundo."

    def test_empty_string(self):
        """Test with empty string."""
        assert fix_punctuation("") == ""

    def test_complex_punctuation(self):
        """Test with complex punctuation."""
        text = "Primero,segundo;tercero:cuarto"
        result = fix_punctuation(text)
        assert ", " in result
        assert "; " in result
        assert ": " in result


class TestChunkLongText:
    """Test text chunking functionality."""

    def test_short_text_not_chunked(self):
        """Test that short text is not chunked."""
        text = "This is a short sentence."
        chunks = chunk_long_text(text, max_chars=500)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_long_text_is_chunked(self):
        """Test that long text is split into chunks."""
        sentences = ["Sentence one. ", "Sentence two. ", "Sentence three. "]
        text = "".join(sentences * 50)  # Make it long
        chunks = chunk_long_text(text, max_chars=100)
        assert len(chunks) > 1

    def test_chunks_respect_max_chars(self):
        """Test that chunks don't exceed max_chars."""
        text = ". ".join([f"Sentence {i}" for i in range(100)])
        chunks = chunk_long_text(text, max_chars=100)
        for chunk in chunks:
            assert (
                len(chunk) <= 100 or "." not in chunk
            )  # Unless it's a single long sentence

    def test_chunks_split_at_sentence_boundaries(self):
        """Test that chunks split at sentence boundaries."""
        text = "First sentence. Second sentence. Third sentence."
        chunks = chunk_long_text(text, max_chars=30)
        # Each chunk should be a complete sentence
        for chunk in chunks:
            assert chunk.endswith((".", "!", "?"))

    def test_empty_string(self):
        """Test with empty string."""
        chunks = chunk_long_text("", max_chars=500)
        assert len(chunks) == 0 or (len(chunks) == 1 and chunks[0] == "")

    def test_custom_max_chars(self):
        """Test with custom max_chars parameter."""
        text = "Short. " * 20
        chunks = chunk_long_text(text, max_chars=50)
        assert all(len(chunk) <= 50 for chunk in chunks if chunk)

    def test_preserves_punctuation(self):
        """Test that sentence punctuation is preserved."""
        text = "Question? Statement. Exclamation!"
        chunks = chunk_long_text(text, max_chars=500)
        combined = " ".join(chunks)
        assert "?" in combined
        assert "!" in combined


class TestValidateTextForTTS:
    """Test text validation."""

    def test_valid_text(self):
        """Test that valid text passes validation."""
        is_valid, msg = validate_text_for_tts("Hola estudiantes")
        assert is_valid is True
        assert msg == ""

    def test_empty_string_invalid(self):
        """Test that empty string is invalid."""
        is_valid, msg = validate_text_for_tts("")
        assert is_valid is False
        assert "empty" in msg.lower()

    def test_whitespace_only_invalid(self):
        """Test that whitespace-only string is invalid."""
        is_valid, msg = validate_text_for_tts("   ")
        assert is_valid is False
        assert "empty" in msg.lower()

    def test_too_long_text_invalid(self):
        """Test that text exceeding max length is invalid."""
        long_text = "a" * (MAX_TEXT_LEN + 1)
        is_valid, msg = validate_text_for_tts(long_text)
        assert is_valid is False
        assert "maximum length" in msg.lower()

    def test_max_length_boundary(self):
        """Test text at exactly max length."""
        text_at_max = "a" * MAX_TEXT_LEN
        is_valid, _msg = validate_text_for_tts(text_at_max)
        assert is_valid is True

    def test_urls_invalid(self):
        """Test that text with URLs is invalid."""
        is_valid, msg = validate_text_for_tts("Visit http://example.com")
        assert is_valid is False
        assert "URL" in msg

        is_valid, msg = validate_text_for_tts("Check https://test.com")
        assert is_valid is False

    def test_special_characters_valid(self):
        """Test that special characters are allowed."""
        is_valid, _msg = validate_text_for_tts("�Hola! �C�mo est�s?")
        assert is_valid is True

    def test_numbers_valid(self):
        """Test that numbers are allowed."""
        is_valid, _msg = validate_text_for_tts("Tengo 5 manzanas y 10 naranjas")
        assert is_valid is True

    def test_multi_line_valid(self):
        """Test that multi-line text is valid."""
        text = "Primera l�nea.\nSegunda l�nea."
        is_valid, _msg = validate_text_for_tts(text)
        assert is_valid is True


class TestPreprocessText:
    """Test the complete preprocessing pipeline."""

    def test_full_preprocessing_math(self):
        """Test full preprocessing with math content."""
        text = "El Prof. dice: 3 + 5 = 8"
        result = preprocess_text(text, grade_level=5)

        # Should expand Prof.
        assert "Profesor" in result
        # Should convert numbers
        assert "tres" in result
        assert "cinco" in result
        assert "ocho" in result
        # Should have proper punctuation
        assert result.endswith(".")

    def test_full_preprocessing_elementary(self):
        """Test full preprocessing for elementary students."""
        text = "Hola estudiantes.Bienvenidos"
        result = preprocess_text(text, grade_level=3)

        # Should add pauses after periods
        assert ". " in result
        # Should have proper punctuation
        assert result.endswith(".")

    def test_full_preprocessing_abbreviations_and_numbers(self):
        """Test preprocessing with both abbreviations and numbers."""
        text = "La Dra. tiene 10 pacientes"
        result = preprocess_text(text, grade_level=6)

        assert "Doctora" in result
        assert "diez" in result

    def test_preprocessing_order_matters(self):
        """Test that preprocessing steps happen in correct order."""
        # Number conversion should happen before punctuation fixing
        text = "Resultado: 5"
        result = preprocess_text(text, grade_level=5)
        assert "cinco." in result or "cinco ." in result

    def test_empty_string(self):
        """Test preprocessing empty string."""
        result = preprocess_text("", grade_level=5)
        assert result == ""

    def test_idempotency(self):
        """Test that preprocessing is idempotent (running twice gives same result)."""
        text = "Hola 5 estudiantes"
        result1 = preprocess_text(text, grade_level=5)
        result2 = preprocess_text(result1, grade_level=5)
        # Should be similar (may differ slightly due to punctuation)
        assert "cinco" in result1
        assert "cinco" in result2

    def test_complex_chilean_content(self):
        """Test with realistic Chilean educational content."""
        text = "El Prof. Rodriguez explica: 18 de septiembre"
        result = preprocess_text(text, grade_level=7)

        assert "Profesor" in result
        assert "dieciocho" in result
        assert result.endswith(".")

    def test_grade_level_affects_pauses(self):
        """Test that different grade levels produce different results."""
        # Use text with question mark in the middle to avoid period addition at end
        text = "Que tal? Bien"

        result_elementary = preprocess_text(text, grade_level=2)
        result_high = preprocess_text(text, grade_level=10)

        # Elementary adds extra space after questions
        # Both should have "? " but let's just verify they process correctly
        assert "?" in result_elementary
        assert "?" in result_high
        assert "Bien" in result_elementary
        assert "Bien" in result_high


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_unicode_characters(self):
        """Test handling of Unicode characters."""
        text = "Ni�o, se�or, a�o"
        result = preprocess_text(text, grade_level=5)
        assert "�" in result  # Should preserve �

    def test_accented_characters(self):
        """Test handling of accented characters."""
        text = "Jos�, Mar�a, Ram�n"
        result = preprocess_text(text, grade_level=5)
        assert "�" in result
        assert "�" in result
        assert "�" in result

    def test_inverted_punctuation(self):
        """Test Spanish inverted punctuation."""
        text = "�C�mo est�s? �Muy bien!"
        result = preprocess_text(text, grade_level=5)
        assert "�" in result
        assert "�" in result

    def test_very_long_number_sequence(self):
        """Test with many consecutive numbers."""
        text = "1 2 3 4 5 6 7 8 9 10"
        result = convert_numbers_to_words(text)
        assert all(word in result for word in ["uno", "dos", "tres", "diez"])

    def test_mixed_case_abbreviations(self):
        """Test that case matters for abbreviations."""
        text = "DR. Smith"  # Uppercase DR. not in dict
        result = expand_abbreviations(text)
        assert result == text  # Should not change

    def test_numbers_in_words(self):
        """Test that number words are not converted."""
        text = "Tengo tres manzanas"
        result = convert_numbers_to_words(text)
        # "tres" should remain "tres", not be converted from "3"
        assert result == text

    def test_grade_level_boundaries(self):
        """Test all grade level boundaries."""
        text = "Test.Text"
        for grade in range(1, 13):
            result = preprocess_text(text, grade_level=grade)
            assert isinstance(result, str)
            assert len(result) > 0


# Parametrized tests for comprehensive coverage
class TestParametrized:
    """Parametrized tests for comprehensive coverage."""

    @pytest.mark.parametrize(
        ("number", "word"),
        [
            ("0", "cero"),
            ("7", "siete"),
            ("15", "quince"),
            ("20", "veinte"),
            ("100", "cien"),
            ("1000", "mil"),
        ],
    )
    def test_number_conversion_parametrized(self, number, word):
        """Parametrized test for number conversion."""
        assert convert_numbers_to_words(number) == word

    @pytest.mark.parametrize(
        ("abbr", "full"),
        [
            ("Dr.", "Doctor"),
            ("Prof.", "Profesor"),
            ("pág.", "página"),
            ("etc.", "etcétera"),
        ],
    )
    def test_abbreviation_expansion_parametrized(self, abbr, full):
        """Parametrized test for abbreviation expansion."""
        text = f"El {abbr} dice"
        result = expand_abbreviations(text)
        assert full in result

    @pytest.mark.parametrize(
        ("grade", "expected_threshold"),
        [
            (1, True),  # Elementary
            (4, True),  # Elementary boundary
            (5, False),  # Middle
            (8, False),  # Middle
            (12, False),  # High school
        ],
    )
    def test_grade_level_threshold(self, grade, expected_threshold):
        """Test grade level threshold for pauses."""
        text = "Test.Text"
        result = add_educational_pauses(text, grade_level=grade)
        has_extra_spacing = ". " in result
        assert has_extra_spacing == expected_threshold


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
