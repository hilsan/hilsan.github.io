// Vanilla JS fallback for navbar hamburger toggle
// (Bootstrap 4 collapse requires jQuery; this ensures it works even if jQuery CDN is slow/blocked)
document.addEventListener("DOMContentLoaded", function () {
  var toggler = document.querySelector(".navbar-toggler");
  var target = document.getElementById("navbarNav");
  if (toggler && target) {
    toggler.addEventListener("click", function () {
      var isOpen = target.classList.contains("show");
      target.classList.toggle("show", !isOpen);
      toggler.classList.toggle("collapsed", isOpen);
      toggler.setAttribute("aria-expanded", isOpen ? "false" : "true");
    });
  }
});

// add bootstrap classes to tables
$(document).ready(function () {
  $("table").each(function () {
    if (determineComputedTheme() == "dark") {
      $(this).addClass("table-dark");
    } else {
      $(this).removeClass("table-dark");
    }

    // only select tables that are not inside an element with "news" (about page) or "card" (cv page) class
    if (
      $(this).parents('[class*="news"]').length == 0 &&
      $(this).parents('[class*="card"]').length == 0 &&
      $(this).parents('[class*="archive"]').length == 0 &&
      $(this).parents("code").length == 0
    ) {
      // make table use bootstrap-table
      $(this).attr("data-toggle", "table");
      // add some classes to make the table look better
      // $(this).addClass('table-sm');
      $(this).addClass("table-hover");
    }
  });
});
