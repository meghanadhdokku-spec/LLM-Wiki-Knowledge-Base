---
category: databases
created: '2026-07-31'
modified: '2026-07-31'
related:
- postgres-indexing-strategies
slug: redis-caching-patterns
status: published
summary: Redis caching techniques
tags:
- redis
- caching
title: Redis Caching Patterns
---

# Redis Caching Patterns

Redis is an in-memory data store commonly used as a cache in front of a slower database.

## Common patterns

- Cache-aside: check cache, on miss read from DB and populate cache
- Write-through: write to cache and DB together
- TTL-based expiry to avoid stale data

Use `EXPIRE` to set a time-to-live on keys so the cache doesn't grow unbounded.