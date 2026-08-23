// Places and numbers Distill sidenotes.
//
// Authors write {% sidenote %}...{% endsidenote %} inline (see
// _plugins/sidenote.rb), which emits a marker plus the note body in a hidden
// sibling span. This script lifts each body into a real <aside> and inserts it as
// a direct child of <d-article>, immediately after the block being annotated --
// Distill's `grid-column: gutter` only positions direct children, so the note
// cannot stay where it was written.
//
// Numbering is done here rather than with a CSS counter: the marker is nested
// in the prose while the aside is a top-level child, so the two sit in
// different branches of the tree and never resolve to the same counter value.
// Pairing the Nth marker with the Nth aside in document order is unambiguous.
(function () {
  "use strict";

  // The ancestor of `el` that is a direct child of `article`.
  function topLevelBlock(el, article) {
    var node = el;
    while (node.parentElement && node.parentElement !== article) {
      node = node.parentElement;
    }
    return node.parentElement === article ? node : null;
  }

  function liftBodies(article) {
    var refs = article.querySelectorAll(".sidenote-ref");
    // Several notes can hang off one paragraph; keep them in source order by
    // inserting each after the previous one rather than all at the same point.
    var lastInsertedFor = new Map();

    for (var i = 0; i < refs.length; i++) {
      var ref = refs[i];
      var tpl = ref.nextElementSibling;
      if (!tpl || !tpl.classList.contains("sidenote-body")) continue;

      var block = topLevelBlock(ref, article);
      if (!block) continue;

      var aside = document.createElement("aside");
      aside.innerHTML = tpl.innerHTML;

      var after = lastInsertedFor.get(block) || block;
      article.insertBefore(aside, after.nextSibling);
      lastInsertedFor.set(block, aside);

      tpl.parentNode.removeChild(tpl);
    }
  }

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
    for (var i = 0; i < articles.length; i++) {
      liftBodies(articles[i]);
      number(articles[i]);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();
