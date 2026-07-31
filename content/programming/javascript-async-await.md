---
category: programming
created: '2026-07-31'
modified: '2026-07-31'
related: []
slug: javascript-async-await
status: published
summary: '`async`/`await` is syntactic sugar over Promises that makes asynchronous
  code read like synchronous code'
tags:
- python
- javascript
title: JavaScript Async/Await
---

# JavaScript Async/Await

`async`/`await` is syntactic sugar over Promises that makes asynchronous code read like synchronous code.

```javascript
async function fetchUser(id) {
  const res = await fetch(`/api/users/${id}`);
  return res.json();
}
```

Always wrap `await` calls in `try`/`catch` to handle rejected promises.