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
    iconLink.innerHTML = '<i class="ti ti-link"></i>';
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
