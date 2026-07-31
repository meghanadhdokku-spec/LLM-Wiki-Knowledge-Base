---
category: programming
created: '2026-07-31'
modified: '2026-07-31'
related: []
slug: python-list-comprehensions
status: published
summary: List comprehensions are a concise way to build lists in Python
tags:
- python
- javascript
title: Python List Comprehensions
---

# Python List Comprehensions

List comprehensions are a concise way to build lists in Python.

```python
squares = [x * x for x in range(10)]
evens = [x for x in range(20) if x % 2 == 0]
```

They are generally faster than an equivalent `for` loop with `.append()`.