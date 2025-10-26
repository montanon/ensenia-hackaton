-- Sample Curriculum Data for 5° Básico Matemática
-- Chilean Ministry of Education Standards

-- ============================================================================
-- MINISTRY STANDARDS (OAs - Objetivos de Aprendizaje)
-- ============================================================================

INSERT OR REPLACE INTO ministry_standards (
  oa_id, grade, subject, oa_code, description, skills, keywords, official_document_ref
) VALUES
  (
    'oa-mat-5-03',
    5,
    'Matemática',
    'OA-MAT-5-03',
    'Demostrar que comprenden las fracciones con denominadores 100, 12, 10, 8, 6, 5, 4, 3, 2: explicando que una fracción representa la parte de un todo o de un grupo de elementos y un lugar en la recta numérica.',
    '["representación", "comprensión conceptual", "visualización"]',
    'fracciones, denominadores, numeradores, partes, entero',
    'Bases Curriculares 2024 - Matemática 5° Básico'
  ),
  (
    'oa-mat-5-04',
    5,
    'Matemática',
    'OA-MAT-5-04',
    'Resolver adiciones y sustracciones de fracciones con igual denominador (denominadores 100, 12, 10, 8, 6, 5, 4, 3, 2).',
    '["operaciones", "resolución de problemas", "cálculo"]',
    'suma, resta, fracciones, mismo denominador',
    'Bases Curriculares 2024 - Matemática 5° Básico'
  ),
  (
    'oa-mat-5-05',
    5,
    'Matemática',
    'OA-MAT-5-05',
    'Comparar y ordenar fracciones con igual y distinto denominador.',
    '["comparación", "ordenamiento", "razonamiento"]',
    'mayor que, menor que, equivalentes, ordenar',
    'Bases Curriculares 2024 - Matemática 5° Básico'
  ),
  (
    'oa-mat-5-06',
    5,
    'Matemática',
    'OA-MAT-5-06',
    'Identificar, escribir y representar fracciones propias e impropias y números mixtos.',
    '["representación", "notación", "conversión"]',
    'fracciones propias, fracciones impropias, números mixtos',
    'Bases Curriculares 2024 - Matemática 5° Básico'
  ),
  (
    'oa-mat-5-07',
    5,
    'Matemática',
    'OA-MAT-5-07',
    'Resolver problemas rutinarios y no rutinarios que involucren las cuatro operaciones y combinaciones de ellas.',
    '["resolución de problemas", "aplicación", "razonamiento"]',
    'problemas, operaciones, aplicación',
    'Bases Curriculares 2024 - Matemática 5° Básico'
  );

-- ============================================================================
-- CURRICULUM CONTENT (Sample Lessons for 5° Básico Matemática)
-- ============================================================================

INSERT OR REPLACE INTO curriculum_content (
  id, title, grade, subject, content_text, learning_objectives,
  ministry_standard_ref, keywords, difficulty_level
) VALUES
  (
    'curr-mat-5-001',
    'Fracciones: Conceptos Básicos',
    5,
    'Matemática',
    'Las fracciones son números que representan partes de un entero. Una fracción tiene dos componentes: el numerador (arriba) y el denominador (abajo). El denominador indica en cuántas partes iguales se divide el entero, y el numerador indica cuántas de esas partes estamos considerando. Por ejemplo, si dividimos una pizza en 8 partes iguales y tomamos 3, tenemos 3/8 de la pizza. Las fracciones son fundamentales en matemática porque nos permiten representar cantidades que no son números enteros. En Chile, usamos fracciones en muchos contextos: dividir un pastel, calcular descuentos en pesos, o medir ingredientes en recetas chilenas como empanadas.',
    '["oa-mat-5-03"]',
    'OA-MAT-5-03',
    'fracciones, numerador, denominador, partes, entero, conceptos básicos',
    'basic'
  ),
  (
    'curr-mat-5-002',
    'Suma de Fracciones con Mismo Denominador',
    5,
    'Matemática',
    'Para sumar fracciones con el mismo denominador, simplemente sumamos los numeradores y mantenemos el denominador igual. Por ejemplo: 2/5 + 1/5 = (2+1)/5 = 3/5. Esto funciona porque estamos sumando partes del mismo tamaño. Imagina que tienes 2 pedazos de una pizza cortada en 5 partes, y tu amigo te da 1 pedazo más. Ahora tienes 3 pedazos de los 5 totales, es decir 3/5. Es importante recordar que SOLO sumamos los numeradores, el denominador se mantiene igual porque las partes siguen siendo del mismo tamaño. Ejemplo chileno: Si gastas 2/10 de tus ahorros en un completo y 3/10 en un helado, has gastado 5/10 de tus ahorros en total.',
    '["oa-mat-5-04"]',
    'OA-MAT-5-04',
    'suma, fracciones, mismo denominador, operaciones',
    'basic'
  ),
  (
    'curr-mat-5-003',
    'Resta de Fracciones con Mismo Denominador',
    5,
    'Matemática',
    'Para restar fracciones con el mismo denominador, restamos los numeradores y mantenemos el denominador igual. Por ejemplo: 4/6 - 1/6 = (4-1)/6 = 3/6. Al igual que en la suma, solo restamos los numeradores porque las partes son del mismo tamaño. Imagina que tienes 4 de 6 pedazos de un queque y comes 1 pedazo. Te quedan 3 de los 6 pedazos, es decir 3/6. Podemos simplificar esta fracción dividiendo numerador y denominador por 3: 3/6 = 1/2. Ejemplo chileno: Si tienes 7/8 de una caja de chocolates y regalas 2/8 a tu hermana, te quedan 5/8 de la caja.',
    '["oa-mat-5-04"]',
    'OA-MAT-5-04',
    'resta, fracciones, mismo denominador, operaciones, simplificación',
    'basic'
  ),
  (
    'curr-mat-5-004',
    'Fracciones Equivalentes',
    5,
    'Matemática',
    'Las fracciones equivalentes son fracciones que representan la misma cantidad aunque tengan numeradores y denominadores diferentes. Por ejemplo: 1/2 = 2/4 = 4/8. Para encontrar fracciones equivalentes, multiplicamos o dividimos el numerador y el denominador por el mismo número. Si multiplicas 1/2 por 2/2 (que es igual a 1), obtienes 2/4. Si multiplicas 1/2 por 4/4, obtienes 4/8. Todas representan la mitad. Visualmente, si cortas una pizza en 2 partes y tomas 1, es lo mismo que si la cortas en 4 partes y tomas 2, o si la cortas en 8 y tomas 4. Ejemplo chileno: Si en una receta de sopaipillas necesitas 1/2 taza de harina, podrías usar 2/4 de taza o 4/8 de taza - todas son equivalentes.',
    '["oa-mat-5-03", "oa-mat-5-05"]',
    'OA-MAT-5-03, OA-MAT-5-05',
    'fracciones equivalentes, multiplicación, división, representación',
    'intermediate'
  ),
  (
    'curr-mat-5-005',
    'Comparación de Fracciones',
    5,
    'Matemática',
    'Para comparar fracciones con el mismo denominador, simplemente comparamos los numeradores. La fracción con el numerador mayor es la fracción mayor. Por ejemplo: 3/5 > 2/5 porque 3 > 2. Para comparar fracciones con diferentes denominadores, podemos: (1) convertirlas a fracciones equivalentes con el mismo denominador, (2) convertirlas a decimales, o (3) usar la multiplicación cruzada. Ejemplo: ¿Qué es mayor, 2/3 o 3/4? Convertimos a denominador común (12): 2/3 = 8/12 y 3/4 = 9/12. Como 9/12 > 8/12, entonces 3/4 > 2/3. Ejemplo chileno: Si María tiene 2/3 de una barra de chocolate y José tiene 3/4, José tiene más chocolate.',
    '["oa-mat-5-05"]',
    'OA-MAT-5-05',
    'comparación, mayor que, menor que, fracciones equivalentes',
    'intermediate'
  ),
  (
    'curr-mat-5-006',
    'Números Mixtos y Fracciones Impropias',
    5,
    'Matemática',
    'Una fracción propia tiene el numerador menor que el denominador (ejemplo: 3/4). Una fracción impropia tiene el numerador mayor o igual al denominador (ejemplo: 5/4). Un número mixto combina un número entero con una fracción (ejemplo: 1 1/4). Para convertir una fracción impropia a número mixto, dividimos el numerador por el denominador. El cociente es la parte entera, y el residuo sobre el denominador es la fracción. Ejemplo: 7/3 = 2 1/3 (porque 7÷3 = 2 con residuo 1). Para convertir un número mixto a fracción impropia, multiplicamos el entero por el denominador y sumamos el numerador. Ejemplo: 2 1/3 = (2×3 + 1)/3 = 7/3. Ejemplo chileno: Si compraste 2 pizzas y media, puedes escribirlo como 2 1/2 (número mixto) o 5/2 (fracción impropia).',
    '["oa-mat-5-06"]',
    'OA-MAT-5-06',
    'números mixtos, fracciones impropias, fracciones propias, conversión',
    'intermediate'
  );
