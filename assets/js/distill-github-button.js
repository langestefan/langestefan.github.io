// Adds a "GitHub" source button to the byline of Distill posts.
//
// The source URL is supplied per-page by _plugins/site_assets.rb as
// window.__alGithubSourceUrl, because it depends on the document's path and
// this file is a static asset.
//
// <d-byline> is a web component hydrated by the Distill runtime, so the inner
// .byline.grid element does not exist at DOMContentLoaded. We observe the DOM
// until it appears rather than assuming it is already there.
(function () {
  "use strict";

  function styleFor(isDark, hovered) {
    if (isDark) {
      return hovered
        ? { backgroundColor: "rgba(255, 255, 255, 0.22)", borderColor: "rgba(255, 255, 255, 0.4)", color: "#fff" }
        : { backgroundColor: "rgba(255, 255, 255, 0.12)", borderColor: "rgba(255, 255, 255, 0.25)", color: "#dee2e6" };
    }
    return hovered
      ? { backgroundColor: "rgba(0, 0, 0, 0.15)", borderColor: "rgba(0, 0, 0, 0.35)", color: "#000" }
      : { backgroundColor: "rgba(0, 0, 0, 0.08)", borderColor: "rgba(0, 0, 0, 0.2)", color: "#212529" };
  }

  function isDarkTheme() {
    return document.documentElement.getAttribute("data-theme") === "dark";
  }

  function build(bylineGrid, url) {
    var githubCol = document.createElement("div");
    githubCol.className = "github-source";
    githubCol.style.display = "flex";
    githubCol.style.alignItems = "center";
    githubCol.innerHTML =
      '<a class="github-btn" href="' +
      url +
      '" target="_blank" rel="noopener noreferrer">' +
      '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="20" height="20" fill="currentColor" style="vertical-align: -0.15em; margin-right: 6px;">' +
      '<path d="M8 0c4.42 0 8 3.58 8 8a8.013 8.013 0 0 1-5.45 7.59c-.4.08-.55-.17-.55-.38 0-.27.01-1.13.01-2.2 0-.75-.25-1.23-.54-1.48 1.78-.2 3.65-.88 3.65-3.95 0-.88-.31-1.59-.82-2.15.08-.2.36-1.02-.08-2.12 0 0-.67-.22-2.2.82-.64-.18-1.32-.27-2-.27-.68 0-1.36.09-2 .27-1.53-1.03-2.2-.82-2.2-.82-.44 1.1-.16 1.92-.08 2.12-.51.56-.82 1.28-.82 2.15 0 3.06 1.86 3.75 3.64 3.95-.23.2-.44.55-.51 1.07-.46.21-1.61.55-2.33-.66-.15-.24-.6-.83-1.23-.82-.67.01-.27.38.01.53.34.19.73.9.82 1.13.16.45.68 1.31 2.69.94 0 .67.01 1.3.01 1.49 0 .21-.15.45-.55.38A7.995 7.995 0 0 1 0 8c0-4.42 3.58-8 8-8Z"></path>' +
      "</svg>" +
      "GitHub" +
      "</a>";
    bylineGrid.appendChild(githubCol);

    var btn = githubCol.querySelector(".github-btn");

    function apply(hovered) {
      var s = styleFor(isDarkTheme(), hovered);
      btn.style.backgroundColor = s.backgroundColor;
      btn.style.border = "1px solid " + s.borderColor;
      btn.style.color = s.color;
    }

    apply(false);

    // al_folio_core's theme.js sets data-theme on <html>; follow it.
    new MutationObserver(function () {
      apply(false);
    }).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });

    btn.addEventListener("mouseenter", function () {
      apply(true);
    });
    btn.addEventListener("mouseleave", function () {
      apply(false);
    });
  }

  function attach() {
    var url = window.__alGithubSourceUrl;
    if (!url) return true; // nothing to do on this page
    var bylineGrid = document.querySelector("d-byline .byline.grid");
    if (!bylineGrid) return false;
    if (bylineGrid.querySelector(".github-source")) return true;
    build(bylineGrid, url);
    return true;
  }

  function start() {
    if (attach()) return;
    var observer = new MutationObserver(function () {
      if (attach()) observer.disconnect();
    });
    observer.observe(document.body, { childList: true, subtree: true });
    // Stop watching after 10s so a page without a byline does not observe forever.
    setTimeout(function () {
      observer.disconnect();
    }, 10000);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();
