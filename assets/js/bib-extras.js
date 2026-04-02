/**
 * bib-extras.js
 * Handles the "more authors" expand/collapse and annotation popovers
 * on the publications page.
 */
$(document).ready(function () {
  var delay = 10; // ms per character in the typewriter animation

  // ── More authors expand/collapse ──────────────────────────────────────────
  // The span stores its two states in data attributes so we avoid inline-onclick
  // encoding issues with special characters in author names.
  $(document).on("click", "span.more-authors", function () {
    var $el   = $(this);
    var show  = $el.data("more-show") || "";
    var hide  = $el.data("more-hide") || "";

    // Decide which direction we're going
    var isHidden = $el.text().trim() === hide;
    var target   = isHidden ? show : hide;

    $el.attr("title", isHidden ? "" : "click to view " + hide);

    // Typewriter animation
    var pos = 0;
    var timer = setInterval(function () {
      $el.html(target.substring(0, pos + 1));
      if (++pos === target.length) {
        clearInterval(timer);
      }
    }, delay);
  });

  // ── Annotation popovers ───────────────────────────────────────────────────
  // Re-initialise after any dynamic content and ensure they're attached to
  // body so z-index / overflow clipping doesn't hide them.
  $('[data-toggle="popover"]').popover({
    trigger:   "focus hover",
    container: "body",
  });
});
