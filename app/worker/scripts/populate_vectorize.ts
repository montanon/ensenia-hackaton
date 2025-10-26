/**
 * Populate Vectorize Index with Curriculum Embeddings
 *
 * This script reads curriculum content from D1 database,
 * generates embeddings using Workers AI, and inserts them
 * into the Vectorize index for semantic search.
 *
 * Usage:
 *   npx tsx scripts/populate_vectorize.ts
 */

import { Env, AiEmbeddingResponse } from '../src/types/env';

interface CurriculumRow {
  id: string;
  title: string;
  grade: number;
  subject: string;
  content_text: string;
  learning_objectives: string;
  ministry_standard_ref: string;
  keywords: string;
}

/**
 * Main function to populate Vectorize index
 */
async function populateVectorize(env: Env): Promise<void> {
  console.log('================================================');
  console.log('Populating Vectorize Index with Embeddings');
  console.log('================================================\n');

  // Step 1: Fetch all curriculum content from D1
  console.log('Step 1: Fetching curriculum content from D1...');
  const query = `
    SELECT
      id,
      title,
      grade,
      subject,
      content_text,
      learning_objectives,
      ministry_standard_ref,
      keywords
    FROM curriculum_content
    ORDER BY grade, subject, id
  `;

  const result = await env.DB.prepare(query).all();

  if (!result.success) {
    throw new Error('Failed to fetch curriculum content from D1');
  }

  const contents = result.results as unknown as CurriculumRow[];
  console.log(`✓ Found ${contents.length} curriculum items\n`);

  // Step 2: Generate embeddings and insert into Vectorize
  console.log('Step 2: Generating embeddings and inserting into Vectorize...');
  console.log('(This may take a few moments)\n');

  let successCount = 0;
  let errorCount = 0;

  for (const content of contents) {
    try {
      // Create searchable text combining title, content, and keywords
      const searchableText = `${content.title}\n\n${content.content_text}\n\nPalabras clave: ${content.keywords}`;

      // Generate embedding using Workers AI
      console.log(`  Processing: ${content.id} - ${content.title}`);
      const embeddingResponse = await env.AI.run(env.EMBEDDING_MODEL, {
        text: searchableText,
      }) as AiEmbeddingResponse;

      const embedding = embeddingResponse.data[0];

      if (!embedding || embedding.length === 0) {
        console.error(`  ❌ Failed to generate embedding for ${content.id}`);
        errorCount++;
        continue;
      }

      // Parse learning objectives (stored as JSON string)
      let learningObjectives: string[] = [];
      try {
        learningObjectives = JSON.parse(content.learning_objectives);
      } catch {
        learningObjectives = [];
      }

      // Extract OA code from first learning objective if available
      let oaCode = '';
      if (learningObjectives.length > 0) {
        oaCode = learningObjectives[0];
      }

      // Insert into Vectorize with metadata
      await env.VECTOR_INDEX.insert([
        {
          id: content.id,
          values: embedding,
          metadata: {
            title: content.title,
            grade: content.grade,
            subject: content.subject,
            oa: oaCode,
            ministry_ref: content.ministry_standard_ref,
            keywords: content.keywords,
          },
        },
      ]);

      console.log(`  ✓ Inserted embedding for ${content.id}`);
      successCount++;

      // Small delay to avoid rate limiting
      await new Promise((resolve) => setTimeout(resolve, 100));
    } catch (error: any) {
      console.error(`  ❌ Error processing ${content.id}: ${error.message}`);
      errorCount++;
    }
  }

  // Summary
  console.log('\n================================================');
  console.log('Summary');
  console.log('================================================');
  console.log(`✓ Successfully inserted: ${successCount}`);
  console.log(`❌ Errors: ${errorCount}`);
  console.log(`📊 Total processed: ${contents.length}`);
  console.log('================================================\n');

  if (successCount > 0) {
    console.log('✓ Vectorize index populated successfully!');
    console.log('\nNext steps:');
    console.log('1. Run "npm run dev" to start the Worker');
    console.log('2. Test search endpoint with: POST /search');
    console.log('3. Query example: {"query": "multiplicación", "grade": 5, "subject": "Matemática"}');
  } else {
    console.log('❌ Failed to populate Vectorize index');
    process.exit(1);
  }
}

/**
 * Standalone execution (for testing)
 * Note: In production, this would be called from Worker context
 */
if (require.main === module) {
  console.log('⚠️  This script needs to run in Worker context');
  console.log('Use: wrangler dev --local --persist');
  console.log('Then call this as a Worker endpoint or use wrangler CLI\n');
  console.log('Alternative: Create a temporary endpoint in index.ts that calls this function');
  process.exit(0);
}

export { populateVectorize };
