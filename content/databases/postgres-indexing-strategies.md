---
category: databases
created: '2026-07-31'
modified: '2026-07-31'
related: []
slug: postgres-indexing-strategies
status: published
summary: Indexes speed up reads at the cost of slower writes and extra disk space
tags:
- reference
title: Postgres Indexing Strategies
---

# Postgres Indexing Strategies

Indexes speed up reads at the cost of slower writes and extra disk space.

## Common index types

- B-tree (default, good for equality and range queries)
- GIN (good for full-text search and JSONB)
- Hash (equality only)

Use `EXPLAIN ANALYZE` to check whether a query is actually using an index.