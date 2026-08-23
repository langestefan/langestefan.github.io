// Add clickable anchor links to all headings with IDs
document.addEventListener("DOMContentLoaded", function () {
  var headings = document.querySelectorAll(
    "article h1[id], article h2[id], article h3[id], article h4[id], article h5[id], article h6[id], " +
      "d-article h1[id], d-article h2[id], d-article h3[id], d-article h4[id], d-article h5[id], d-article h6[id]"
  );

  headings.forEach(function (heading) {
    // Skip if already processed
    if (heading.querySelector(".heading-anchor")) return;

    // Wrap the heading text in a clickable link
    var textLink = document.createElement("a");
    textLink.className = "heading-text-link";
    textLink.href = "#" + heading.id;
    // Move all child nodes into the text link
    while (heading.firstChild) {
      textLink.appendChild(heading.firstChild);
    }
    heading.appendChild(textLink);

    // Copy link to clipboard on heading text click
    textLink.addEventListener("click", function (e) {
      e.preventDefault();
      var url = window.location.origin + window.location.pathname + "#" + heading.id;
      navigator.clipboard
        .writeText(url)
        .then(function () {
          iconLink.classList.add("copied");
          setTimeout(function () {
            iconLink.classList.remove("copied");
          }, 1500);
        })
        .catch(function () {
          window.location.hash = heading.id;
        });
    });

    // Add the separate link icon
    var iconLink = document.createElement("a");
    iconLink.className = "heading-anchor";
    iconLink.href = "#" + heading.id;
    iconLink.setAttribute("aria-label", "Copy link to this section");
    // Inline SVG rather than an icon font: al-folio v1 ships FontAwesome and
    // Academicons via al_icons, but no longer the Tabler set this used to use.
    iconLink.innerHTML =
      '<svg xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" ' +
      'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" ' +
      'stroke-linejoin="round" aria-hidden="true" focusable="false">' +
      '<path d="M9 15l6 -6" />' +
      '<path d="M11 6l.463 -.536a5 5 0 0 1 7.071 7.072l-.534 .464" />' +
      '<path d="M13 18l-.397 .534a5.068 5.068 0 0 1 -7.127 0a4.972 4.972 0 0 1 0 -7.071l.524 -.463" />' +
      "</svg>";
    heading.appendChild(iconLink);

    // Copy link to clipboard on icon click
    iconLink.addEventListener("click", function (e) {
      e.preventDefault();
      var url = window.location.origin + window.location.pathname + "#" + heading.id;
      navigator.clipboard
        .writeText(url)
        .then(function () {
          iconLink.classList.add("copied");
          setTimeout(function () {
            iconLink.classList.remove("copied");
          }, 1500);
        })
        .catch(function () {
          window.location.hash = heading.id;
        });
    });
  });
});
