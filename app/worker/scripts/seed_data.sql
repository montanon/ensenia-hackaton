-- Ensenia Seed Data - Realistic Chilean Curriculum Content
-- Based on Chilean Ministry of Education Standards (2024)

-- ============================================================================
-- MINISTRY STANDARDS - Sample Learning Objectives (OAs)
-- Based on real Chilean "Objetivos de Aprendizaje"
-- ============================================================================

-- Mathematics - Grade 5
INSERT INTO ministry_standards (oa_id, grade, subject, oa_code, description, skills, keywords, official_document_ref) VALUES
('MAT-5-OA01', 5, 'Matemática', 'OA 01', 'Representar y describir números naturales de hasta más de 6 dígitos y menores que 1 000 millones.', '["representación numérica","valor posicional","lectura de números"]', 'números, millones, valor posicional, lectura', 'Bases Curriculares 2012 - Matemática'),
('MAT-5-OA02', 5, 'Matemática', 'OA 02', 'Aplicar estrategias de cálculo mental para la multiplicación.', '["cálculo mental","multiplicación","estrategias"]', 'multiplicación, cálculo mental, estrategias', 'Bases Curriculares 2012 - Matemática'),
('MAT-5-OA03', 5, 'Matemática', 'OA 03', 'Demostrar que comprenden la adición y sustracción de decimales.', '["decimales","adición","sustracción","resolución de problemas"]', 'decimales, suma, resta, problemas', 'Bases Curriculares 2012 - Matemática'),
('MAT-5-OA04', 5, 'Matemática', 'OA 04', 'Resolver problemas rutinarios y no rutinarios que involucren las cuatro operaciones y combinaciones de ellas.', '["resolución de problemas","operaciones combinadas","razonamiento"]', 'problemas, operaciones, combinadas, razonamiento', 'Bases Curriculares 2012 - Matemática');

-- Language - Grade 5
INSERT INTO ministry_standards (oa_id, grade, subject, oa_code, description, skills, keywords, official_document_ref) VALUES
('LEN-5-OA01', 5, 'Lenguaje y Comunicación', 'OA 01', 'Leer de manera fluida textos variados apropiados a su edad.', '["lectura fluida","comprensión","textos variados"]', 'lectura, fluidez, comprensión, textos', 'Bases Curriculares 2012 - Lenguaje'),
('LEN-5-OA02', 5, 'Lenguaje y Comunicación', 'OA 02', 'Comprender textos aplicando estrategias de comprensión lectora.', '["comprensión lectora","estrategias","análisis"]', 'comprensión, estrategias, lectura, análisis', 'Bases Curriculares 2012 - Lenguaje'),
('LEN-5-OA03', 5, 'Lenguaje y Comunicación', 'OA 03', 'Leer y familiarizarse con un amplio repertorio de literatura para aumentar su conocimiento del mundo.', '["literatura","lectura extensiva","conocimiento del mundo"]', 'literatura, lectura, narrativa, poesía', 'Bases Curriculares 2012 - Lenguaje'),
('LEN-5-OA04', 5, 'Lenguaje y Comunicación', 'OA 04', 'Analizar aspectos relevantes de narraciones leídas para profundizar su comprensión.', '["análisis literario","narraciones","comprensión profunda"]', 'análisis, narraciones, personajes, ambiente', 'Bases Curriculares 2012 - Lenguaje');

-- Natural Sciences - Grade 5
INSERT INTO ministry_standards (oa_id, grade, subject, oa_code, description, skills, keywords, official_document_ref) VALUES
('CNA-5-OA01', 5, 'Ciencias Naturales', 'OA 01', 'Reconocer y explicar que los seres vivos están formados por una o más células.', '["célula","organismos","estructura celular"]', 'célula, organismos, unicelulares, pluricelulares', 'Bases Curriculares 2012 - Ciencias'),
('CNA-5-OA02', 5, 'Ciencias Naturales', 'OA 02', 'Identificar y describir por medio de modelos las estructuras básicas del sistema digestivo.', '["sistema digestivo","órganos","función"]', 'digestión, órganos, alimentación, nutrientes', 'Bases Curriculares 2012 - Ciencias'),
('CNA-5-OA03', 5, 'Ciencias Naturales', 'OA 03', 'Explicar por medio de modelos la respiración y el sistema respiratorio.', '["sistema respiratorio","respiración","intercambio gaseoso"]', 'respiración, pulmones, oxígeno, intercambio', 'Bases Curriculares 2012 - Ciencias');

-- History and Geography - Grade 5
INSERT INTO ministry_standards (oa_id, grade, subject, oa_code, description, skills, keywords, official_document_ref) VALUES
('HIS-5-OA01', 5, 'Historia, Geografía y Ciencias Sociales', 'OA 01', 'Caracterizar las grandes zonas de Chile y sus paisajes.', '["geografía","Chile","zonas naturales","paisajes"]', 'zonas, Chile, Norte Grande, Sur, paisajes', 'Bases Curriculares 2012 - Historia'),
('HIS-5-OA02', 5, 'Historia, Geografía y Ciencias Sociales', 'OA 02', 'Comparar diversos ambientes naturales en Chile.', '["ambientes naturales","clima","flora y fauna","comparación"]', 'ambientes, climas, flora, fauna, Chile', 'Bases Curriculares 2012 - Historia');

-- ============================================================================
-- CURRICULUM CONTENT - Sample Educational Content
-- Realistic Chilean content aligned with Ministry standards
-- ============================================================================

-- Mathematics Content
INSERT INTO curriculum_content (id, title, grade, subject, content_text, learning_objectives, ministry_standard_ref, ministry_approved, keywords, difficulty_level) VALUES
('MAT-5-C001', 'Números hasta el millón', 5, 'Matemática',
'Los números naturales pueden ser muy grandes. En Chile, la población supera los 19 millones de habitantes. Para leer estos números grandes, los agrupamos en períodos de tres cifras cada uno.

Por ejemplo, el número 19.678.363 se lee: "diecinueve millones, seiscientos setenta y ocho mil, trescientos sesenta y tres".

Cada período tiene un nombre:
- Unidades (U): las primeras tres cifras de derecha a izquierda
- Miles (M): las siguientes tres cifras
- Millones (MM): las siguientes tres cifras

Ejercicio: El presupuesto de una municipalidad chilena es de $5.234.500.000 (cinco mil doscientos treinta y cuatro millones quinientos mil pesos). ¿Puedes identificar cada período?',
'["MAT-5-OA01"]', 'Bases Curriculares 2012 - Matemática OA 01', 1,
'números grandes, millones, valor posicional, lectura de números, Chile', 'medium'),

('MAT-5-C002', 'Multiplicación: Cálculo Mental', 5, 'Matemática',
'El cálculo mental nos ayuda a resolver multiplicaciones rápidamente. Una estrategia útil es descomponer los números.

Por ejemplo, para calcular 15 × 12:
- Podemos pensar: 15 × 10 = 150 (más fácil)
- Luego: 15 × 2 = 30
- Sumamos: 150 + 30 = 180

Otro ejemplo con pesos chilenos: Si una empanada cuesta $800 y compras 15 empanadas, ¿cuánto pagas?
- 800 × 15 = 800 × 10 + 800 × 5
- = 8.000 + 4.000
- = $12.000

Practica estos métodos para ser más rápido en matemática.',
'["MAT-5-OA02"]', 'Bases Curriculares 2012 - Matemática OA 02', 1,
'multiplicación, cálculo mental, estrategias, descomposición, pesos chilenos', 'medium'),

('MAT-5-C003', 'Decimales: Suma y Resta', 5, 'Matemática',
'Los números decimales se usan mucho en la vida diaria. Por ejemplo, cuando compramos en el supermercado o medimos distancias.

Para sumar o restar decimales, es importante alinear las comas decimales:

Ejemplo 1: María compró leche por $1.250,50 y pan por $850,75. ¿Cuánto gastó en total?
   1.250,50
  +  850,75
  ---------
   2.101,25

María gastó $2.101,25 en total.

Ejemplo 2: Un corredor chileno corrió 10,5 kilómetros el lunes y 8,75 kilómetros el martes. ¿Cuántos kilómetros más corrió el lunes?
   10,50
  -  8,75
  -------
    1,75

Corrió 1,75 kilómetros más el lunes.',
'["MAT-5-OA03"]', 'Bases Curriculares 2012 - Matemática OA 03', 1,
'decimales, suma, resta, problemas, dinero, medidas', 'medium');

-- Language Content
INSERT INTO curriculum_content (id, title, grade, subject, content_text, learning_objectives, ministry_standard_ref, ministry_approved, keywords, difficulty_level) VALUES
('LEN-5-C001', 'Estrategias de Comprensión Lectora', 5, 'Lenguaje y Comunicación',
'Para comprender mejor lo que lees, puedes usar varias estrategias:

1. Antes de leer:
   - Observa el título y las imágenes
   - Piensa: ¿De qué tratará el texto?
   - Recuerda lo que ya sabes del tema

2. Durante la lectura:
   - Haz pausas y pregúntate: ¿Qué entendí hasta aquí?
   - Si una palabra no la entiendes, intenta adivinar su significado por el contexto
   - Visualiza lo que describes el texto

3. Después de leer:
   - Resume lo más importante con tus propias palabras
   - Piensa: ¿Qué aprendí?
   - Haz conexiones con tu vida

Ejemplo: Si lees un cuento sobre Violeta Parra, puedes pensar en canciones chilenas que conoces o en artistas que admiras.',
'["LEN-5-OA02"]', 'Bases Curriculares 2012 - Lenguaje OA 02', 1,
'comprensión lectora, estrategias, antes durante después, visualización', 'medium'),

('LEN-5-C002', 'Análisis de Narraciones', 5, 'Lenguaje y Comunicación',
'Cuando lees un cuento o novela, puedes analizar varios aspectos para comprenderlo mejor:

**Personajes**: ¿Quiénes son? ¿Cómo son físicamente? ¿Cómo se comportan?
Por ejemplo, en "Papelucho" de Marcela Paz, el personaje principal es un niño creativo y curioso que vive en Santiago.

**Ambiente**: ¿Dónde y cuándo ocurre la historia?
"Papelucho" ocurre en Santiago de Chile, en un barrio de la capital.

**Problema y Solución**: ¿Qué problema enfrentan los personajes? ¿Cómo lo resuelven?
En las aventuras de Papelucho, siempre hay problemas que él intenta resolver con su ingenio.

**Inicio, Desarrollo y Final**: ¿Cómo comienza la historia? ¿Qué sucede? ¿Cómo termina?

Practica identificando estos elementos en tus lecturas.',
'["LEN-5-OA04"]', 'Bases Curriculares 2012 - Lenguaje OA 04', 1,
'análisis literario, narraciones, personajes, ambiente, Papelucho, literatura chilena', 'medium');

-- Natural Sciences Content
INSERT INTO curriculum_content (id, title, grade, subject, content_text, learning_objectives, ministry_standard_ref, ministry_approved, keywords, difficulty_level) VALUES
('CNA-5-C001', 'La Célula: Unidad de Vida', 5, 'Ciencias Naturales',
'Todos los seres vivos están formados por células. La célula es la unidad más pequeña de vida.

**Organismos Unicelulares**: Tienen una sola célula. Ejemplo: las bacterias, algunas algas. Estas células realizan todas las funciones vitales por sí mismas.

**Organismos Pluricelulares**: Tienen muchas células. Ejemplo: los seres humanos, los árboles nativos de Chile como el araucaria o el alerce, los animales como el pudú.

Las células tienen partes importantes:
- Membrana celular: protege la célula
- Citoplasma: donde ocurren las funciones
- Núcleo: contiene la información genética

En Chile, científicos estudian células de especies nativas para entender mejor la biodiversidad de nuestro país.',
'["CNA-5-OA01"]', 'Bases Curriculares 2012 - Ciencias OA 01', 1,
'célula, organismos, unicelulares, pluricelulares, especies chilenas, biodiversidad', 'medium'),

('CNA-5-C002', 'Sistema Digestivo', 5, 'Ciencias Naturales',
'El sistema digestivo transforma los alimentos en nutrientes que nuestro cuerpo puede usar.

**Órganos principales**:
1. Boca: masticamos y mezclamos con saliva
2. Esófago: tubo que lleva el alimento al estómago
3. Estómago: mezcla y descompone con jugos gástricos
4. Intestino delgado: absorbe los nutrientes
5. Intestino grueso: absorbe agua, forma las heces

Ejemplo con comida chilena: Cuando comes un plato de porotos con rienda (comida típica chilena), tu sistema digestivo:
- En la boca, masticas los porotos, fideos y longaniza
- En el estómago, se descomponen las proteínas de la carne
- En el intestino delgado, se absorben los nutrientes: proteínas, carbohidratos, vitaminas
- El proceso completo toma varias horas

Una alimentación saludable, con frutas y verduras chilenas, ayuda a tu sistema digestivo.',
'["CNA-5-OA02"]', 'Bases Curriculares 2012 - Ciencias OA 02', 1,
'sistema digestivo, órganos, digestión, nutrientes, alimentación saludable, comida chilena', 'medium');

-- History and Geography Content
INSERT INTO curriculum_content (id, title, grade, subject, content_text, learning_objectives, ministry_standard_ref, ministry_approved, keywords, difficulty_level) VALUES
('HIS-5-C001', 'Las Grandes Zonas de Chile', 5, 'Historia, Geografía y Ciencias Sociales',
'Chile se divide en grandes zonas naturales, cada una con características únicas:

**Norte Grande**:
- Regiones de Arica y Parinacota, Tarapacá, Antofagasta
- Clima: desértico, muy seco
- Paisaje: Desierto de Atacama, el más árido del mundo
- Recursos: minería (cobre, litio)

**Norte Chico**:
- Regiones de Atacama y Coquimbo
- Clima: semi árido
- Paisaje: valles transversales
- Recursos: minería, agricultura (uvas, pisco)

**Zona Central**:
- Regiones de Valparaíso, Metropolitana, O''Higgins, Maule
- Clima: mediterráneo
- Paisaje: valle central, costa
- Recursos: agricultura, industria, servicios
- Aquí vive la mayoría de la población chilena

**Zona Sur**:
- Regiones de Ñuble, Biobío, Araucanía, Los Ríos, Los Lagos
- Clima: lluvioso
- Paisaje: bosques, lagos, volcanes
- Recursos: agricultura, ganadería, turismo

**Zona Austral**:
- Regiones de Aysén, Magallanes
- Clima: frío, lluvioso
- Paisaje: campos de hielo, fiordos, estepa patagónica
- Recursos: ganadería, pesca, turismo

Cada zona tiene su propia cultura, comidas típicas y tradiciones.',
'["HIS-5-OA01"]', 'Bases Curriculares 2012 - Historia OA 01', 1,
'zonas de Chile, Norte Grande, Centro, Sur, Austral, geografía chilena, paisajes', 'medium');

-- ============================================================================
-- Additional Mathematics Content (Grade 6 preview for variety)
-- ============================================================================

INSERT INTO ministry_standards (oa_id, grade, subject, oa_code, description, skills, keywords, official_document_ref) VALUES
('MAT-6-OA01', 6, 'Matemática', 'OA 01', 'Demostrar que comprenden los factores y múltiplos.', '["factores","múltiplos","divisibilidad"]', 'factores, múltiplos, divisibilidad, números', 'Bases Curriculares 2012 - Matemática');

INSERT INTO curriculum_content (id, title, grade, subject, content_text, learning_objectives, ministry_standard_ref, ministry_approved, keywords, difficulty_level) VALUES
('MAT-6-C001', 'Factores y Múltiplos', 6, 'Matemática',
'Los factores y múltiplos son conceptos importantes en matemática:

**Factores**: Son los números que dividen exactamente a otro número.
Ejemplo: Los factores de 12 son: 1, 2, 3, 4, 6, 12
Porque: 12 ÷ 1 = 12, 12 ÷ 2 = 6, 12 ÷ 3 = 4, etc.

**Múltiplos**: Son los resultados de multiplicar un número por los naturales.
Ejemplo: Los múltiplos de 5 son: 5, 10, 15, 20, 25, 30...
Porque: 5×1=5, 5×2=10, 5×3=15, etc.

Aplicación con dinero chileno:
Si tienes monedas de $100, puedes formar cantidades que sean múltiplos de 100: $100, $200, $300, $400...
No puedes formar $150 porque no es múltiplo de 100.

Los factores y múltiplos nos ayudan a resolver problemas de la vida diaria.',
'["MAT-6-OA01"]', 'Bases Curriculares 2012 - Matemática OA 01', 1,
'factores, múltiplos, divisibilidad, operaciones, dinero', 'medium');
