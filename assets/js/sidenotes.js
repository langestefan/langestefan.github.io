// Numbers Distill sidenotes and their in-text markers so the two always agree.
//
// A pure-CSS counter looked sufficient but is not: the marker
// (<span class="sidenote-ref">) is usually nested inside a paragraph or list
// item, while the <aside> has to be a direct child of <d-article> for Distill's
// grid to place it in the gutter. The two therefore sit in different parts of
// the tree and did not resolve to the same counter value.
//
// Pairing them in document order is unambiguous: the Nth marker belongs to the
// Nth aside. The numbers are written to data-sidenote and rendered by CSS via
// attr(), so nothing is hardcoded in the markup.
(function () {
  "use strict";

  function number(article) {
    var refs = article.querySelectorAll(".sidenote-ref");
    var asides = article.querySelectorAll("aside");

    for (var i = 0; i < Math.max(refs.length, asides.length); i++) {
      var n = i + 1;
      if (refs[i]) refs[i].setAttribute("data-sidenote", n);
      if (asides[i]) asides[i].setAttribute("data-sidenote", n);
    }

    // A mismatch means a marker has no note or vice versa. Warn rather than
    // renumber silently, since the pairing would be wrong from that point on.
    if (refs.length !== asides.length) {
      console.warn("[sidenotes] " + refs.length + " marker(s) but " + asides.length + " aside(s) - numbering past the mismatch will be wrong.");
    }
  }

  function start() {
    var articles = document.querySelectorAll("d-article");
    for (var i = 0; i < articles.length; i++) number(articles[i]);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();
