// Content collection config — the wiki (symlinked at src/content/docs)
// loaded as a plain glob collection. The authoritative schema lives in
// AGENTS.md and tools/brain.py validate; the schema below is permissive
// (all fields optional except title) so it never over-constrains pages
// that are valid per brain.py.

import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro:schema';

const brainFrontmatter = z.object({
  title: z.string(),
  kind: z.string().optional(),
  status: z.string().optional(),
  confidence: z.string().optional(),
  summary: z.string().optional(),
  team: z.string().optional(),
  division: z.string().optional(),
  appetite: z.string().optional(),
  repos: z.array(z.string()).optional(),
  affects: z.array(z.string()).optional(),
  affected_by: z.array(z.string()).optional(),
  depends_on: z.array(z.string()).optional(),
  consumed_by: z.array(z.string()).optional(),
  supersedes: z.string().optional(),
  superseded_by: z.string().optional(),
  sources: z.array(z.string()).optional(),
  affected_personas: z.array(z.string()).optional(),
  ai_suggestion: z.boolean().optional(),
  parent_epic: z.string().optional(),
  // 'updated' is sometimes a YAML date and sometimes a string in the
  // brain corpus — accept either.
  updated: z.union([z.date(), z.string()]).optional(),
});

export const collections = {
  docs: defineCollection({
    loader: glob({ pattern: '**/*.md', base: './src/content/docs' }),
    schema: brainFrontmatter,
  }),
};
