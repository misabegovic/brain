// Content collection config — extends Starlight's default schema with
// the brain's frontmatter fields (kind, status, confidence, team,
// repos, etc.) so Starlight's content validator doesn't reject them.
//
// Authoritative schema lives in AGENTS.md and tools/brain.py validate;
// the schema below is permissive (all fields optional) so it never
// over-constrains pages that are valid per brain.py.

import { defineCollection } from 'astro:content';
import { docsLoader } from '@astrojs/starlight/loaders';
import { docsSchema } from '@astrojs/starlight/schema';
import { z } from 'astro:schema';

const brainFrontmatter = z.object({
  kind: z.string().optional(),
  status: z.string().optional(),
  confidence: z.string().optional(),
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
  // 'updated' is sometimes a YAML date and sometimes a string in the
  // brain corpus — accept either.
  updated: z.union([z.date(), z.string()]).optional(),
});

export const collections = {
  docs: defineCollection({
    loader: docsLoader(),
    schema: docsSchema({ extend: brainFrontmatter }),
  }),
};
