(function () {
  var prefix = window.MARKBASE_PREFIX || "";
  var idx = null;
  var docsBySlug = {};

  var overlay = document.getElementById("search-overlay");
  var input = document.getElementById("search-input");
  var results = document.getElementById("search-results");
  var trigger = document.getElementById("search-trigger");
  var hamburger = document.getElementById("hamburger");
  var sidebar = document.getElementById("sidebar");

  function loadIndex() {
    if (idx) return Promise.resolve();
    return fetch(prefix + "search-index.json")
      .then(function (r) { return r.json(); })
      .then(function (docs) {
        docs.forEach(function (d) { docsBySlug[d.slug] = d; });
        idx = lunr(function () {
          this.ref("slug");
          this.field("title", { boost: 10 });
          this.field("tags", { boost: 5 });
          this.field("summary", { boost: 3 });
          this.field("body");
          docs.forEach(function (d) { this.add(d); }, this);
        });
      });
  }

  function openSearch() {
    overlay.classList.add("open");
    loadIndex().then(function () {
      input.focus();
    });
  }

  function closeSearch() {
    overlay.classList.remove("open");
    input.value = "";
    results.innerHTML = "";
  }

  function renderResults(matches) {
    results.innerHTML = "";
    if (matches.length === 0) {
      var li = document.createElement("li");
      li.textContent = "No results found";
      results.appendChild(li);
      return;
    }
    matches.forEach(function (m) {
      var doc = docsBySlug[m.ref];
      var li = document.createElement("li");
      var a = document.createElement("a");
      a.href = prefix + doc.url;
      a.textContent = doc.title;
      var meta = document.createElement("div");
      meta.className = "result-meta";
      meta.textContent = doc.category + " — " + doc.summary;
      li.appendChild(a);
      li.appendChild(meta);
      results.appendChild(li);
    });
  }

  if (trigger) {
    trigger.addEventListener("click", openSearch);
  }

  if (input) {
    input.addEventListener("input", function () {
      var q = input.value.trim();
      if (!q) {
        results.innerHTML = "";
        return;
      }
      if (!idx) return;
      try {
        var matches = idx.query(function (query) {
          q.split(/\s+/).forEach(function (term) {
            query.term(term, { boost: 2, wildcard: lunr.Query.wildcard.TRAILING });
            query.term(term);
          });
        });
        renderResults(matches);
      } catch (e) {
        renderResults([]);
      }
    });
  }

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      closeSearch();
      if (sidebar) sidebar.classList.remove("open");
    }
  });

  if (overlay) {
    overlay.addEventListener("click", function (e) {
      if (e.target === overlay) closeSearch();
    });
  }

  if (hamburger && sidebar) {
    hamburger.addEventListener("click", function () {
      sidebar.classList.toggle("open");
    });
  }
})();
