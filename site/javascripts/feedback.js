// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
document$.subscribe(function () {
  var feedback = document.forms.feedback;
  if (typeof feedback === "undefined") return;

  feedback.hidden = false;

  feedback.addEventListener("submit", function (ev) {
    ev.preventDefault();

    var page = document.location.pathname;
    var data = ev.submitter.getAttribute("data-md-value");

    var issueUrl =
      "https://github.com/SafeVixAI/SafeVixAI/issues/new?template=feedback.yml&title=" +
      encodeURIComponent("Docs feedback: " + page) +
      "&page=" +
      encodeURIComponent(page) +
      "&rating=" +
      encodeURIComponent(data === "1" ? "helpful" : "needs-improvement");

    console.info("[SafeVixAI Docs] Feedback:", { page: page, rating: data });

    feedback.firstElementChild.disabled = true;

    var note = feedback.querySelector(
      ".md-feedback__note [data-md-value='" + data + "']"
    );
    if (note) {
      note.hidden = false;
      if (data === "0") {
        var link = note.querySelector("a");
        if (link) link.href = issueUrl;
      }
    }
  });
});
