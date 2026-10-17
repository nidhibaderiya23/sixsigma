// ERGent: small browser helpers.
//  1. Row buttons send one Shiny input (data-rw-input) instead of one input per call.
//  2. Running clocks are repainted once a second from the server's clock message,
//     so the tables never have to be redrawn just because time passed.
(function () {
  "use strict";

  function fmt(s) {
    s = Math.max(0, Math.floor(s));
    var m = Math.floor(s / 60), r = s % 60;
    return m + ":" + (r < 10 ? "0" : "") + r;
  }

  function level(elapsed, target) {
    if (elapsed > target) return "red";
    if (elapsed > 0.8 * target) return "amber";
    return "green";
  }
  var rank = { green: 0, amber: 1, red: 2 };

  // Repaint every running clock for the app clock value `now` (seconds, naive epoch).
  function paint(now) {
    document.querySelectorAll(".rw-clock").forEach(function (el) {
      var since = parseFloat(el.getAttribute("data-since"));
      var target = parseFloat(el.getAttribute("data-target"));
      var e = Math.max(0, now - since);
      el.textContent = fmt(e);
      el.setAttribute("data-sev", level(e, target));
    });
    document.querySelectorAll(".rw-row[data-live]").forEach(function (row) {
      var worst = "green";
      row.querySelectorAll(".rw-clock, .rw-final").forEach(function (el) {
        var sev = el.getAttribute("data-sev") || "green";
        if (rank[sev] > rank[worst]) worst = sev;
      });
      row.setAttribute("data-sev", worst);
    });
    var d = new Date(now * 1000);
    var iso = d.toISOString();          // the app clock is a naive time, so read it as UTC
    document.querySelectorAll(".rw-nowtime").forEach(function (el) {
      el.textContent = iso.substr(11, 8);
    });
    document.querySelectorAll(".rw-nowdate").forEach(function (el) {
      el.textContent = iso.substr(0, 10);
    });
  }

  // A scrolling list (.rw-scroll[data-rw-key]) keeps its scroll position when the server
  // redraws it, so a reader halfway down the list is not thrown back to the top.
  function keepScroll() {
    window.jQuery(document).on("shiny:value", function (e) {
      var host = e.target;
      if (!host || !host.querySelectorAll) return;
      var saved = {}, any = false;
      host.querySelectorAll(".rw-scroll[data-rw-key]").forEach(function (el) {
        saved[el.getAttribute("data-rw-key")] = el.scrollTop;
        any = true;
      });
      if (!any) return;
      var done = false;
      var observer = new MutationObserver(function () {
        host.querySelectorAll(".rw-scroll[data-rw-key]").forEach(function (el) {
          var top = saved[el.getAttribute("data-rw-key")];
          if (top) el.scrollTop = top;
          done = true;
        });
        if (done) observer.disconnect();
      });
      observer.observe(host, { childList: true, subtree: true });
      setTimeout(function () { observer.disconnect(); }, 3000);
    });
  }

  function register() {
    if (window.Shiny && Shiny.addCustomMessageHandler && window.jQuery) {
      Shiny.addCustomMessageHandler("rw_clock", function (msg) { paint(msg.now); });
      keepScroll();
    } else {
      setTimeout(register, 50);
    }
  }
  register();

  // One click handler for every row button: [data-rw-action] inside [data-rw-input].
  document.addEventListener("click", function (e) {
    var btn = e.target.closest("[data-rw-action]");
    if (!btn || btn.disabled) return;
    var host = btn.closest("[data-rw-input]");
    if (!host || !window.Shiny) return;
    var payload = {
      action: btn.getAttribute("data-rw-action"),
      call: btn.getAttribute("data-rw-call"),
      unit: btn.getAttribute("data-rw-unit"),
      nonce: Math.random()
    };
    var pickId = btn.getAttribute("data-rw-pick");
    if (pickId) {
      var sel = document.getElementById(pickId);
      payload.pick = sel ? sel.value : null;
    }
    Shiny.setInputValue(host.getAttribute("data-rw-input"), payload, { priority: "event" });
  });

  // Remember which unit was picked for a call, so a redraw does not reset the choice.
  document.addEventListener("change", function (e) {
    var sel = e.target.closest(".rw-unit-pick");
    if (!sel || !window.Shiny) return;
    var host = sel.closest("[data-rw-pick-input]");
    if (!host) return;
    Shiny.setInputValue(host.getAttribute("data-rw-pick-input"),
      { call: sel.getAttribute("data-rw-call"), unit: sel.value }, { priority: "event" });
  });

  // The page is dark; make Bootstrap's own parts (modals, selects) dark too.
  document.documentElement.setAttribute("data-bs-theme", "dark");
})();
