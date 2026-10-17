window.LabelLensUI = (() => {
  let toastTimer;

  function showToast(message) {
    const toast = document.getElementById("ll-toast");
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add("is-visible");
    window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(() => toast.classList.remove("is-visible"), 3200);
  }

  function forceDark() {
    document.body.classList.add("dark");
    document.documentElement.style.colorScheme = "dark";
  }

  function initNavigation() {
    const toggle = document.querySelector(".ll-menu-toggle");
    const nav = document.getElementById("ll-nav");
    if (!toggle || !nav) return;

    const setOpen = (open) => {
      toggle.setAttribute("aria-expanded", String(open));
      toggle.setAttribute("aria-label", open ? "Close navigation" : "Open navigation");
      nav.classList.toggle("is-open", open);
    };

    toggle.addEventListener("click", () => {
      setOpen(toggle.getAttribute("aria-expanded") !== "true");
    });
    nav.addEventListener("click", (event) => {
      if (event.target.closest("a, button")) setOpen(false);
    });
    document.addEventListener("click", (event) => {
      if (!nav.contains(event.target) && !toggle.contains(event.target)) setOpen(false);
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") setOpen(false);
    });
  }

  function initDialogs() {
    let opener = null;
    document.addEventListener("click", (event) => {
      const openButton = event.target.closest("[data-dialog-open]");
      if (openButton) {
        const dialog = document.getElementById(openButton.dataset.dialogOpen);
        if (dialog instanceof HTMLDialogElement && !dialog.open) {
          opener = openButton;
          dialog.showModal();
          dialog.querySelector("[data-dialog-close]")?.focus();
        }
        return;
      }

      const closeButton = event.target.closest("[data-dialog-close]");
      if (closeButton) closeButton.closest("dialog")?.close();
    });

    document.querySelectorAll("dialog.ll-dialog").forEach((dialog) => {
      dialog.addEventListener("click", (event) => {
        if (event.target === dialog) dialog.close();
      });
      dialog.addEventListener("close", () => opener?.focus());
    });
  }

  function initCopyButtons() {
    document.addEventListener("click", async (event) => {
      const button = event.target.closest("[data-copy-text]");
      if (!button) return;
      try {
        await navigator.clipboard.writeText(button.dataset.copyText || "");
        if (navigator.vibrate) navigator.vibrate(12);
        showToast("Question copied to clipboard.");
      } catch {
        showToast("Clipboard access is unavailable in this browser.");
      }
    });
  }

  function initLoadingState() {
    const button = document.getElementById("analyze-btn");
    if (!button || !window.MutationObserver) return;

    const update = () => {
      const busy = button.disabled || button.getAttribute("aria-busy") === "true";
      button.setAttribute("aria-busy", String(busy));
    };
    new MutationObserver(update).observe(button, {
      attributes: true,
      attributeFilter: ["disabled", "aria-busy"],
    });
    update();
  }

  // On a phone the results land below the fold: bring them into view.
  function initResultsScroll() {
    const results = document.getElementById("results");
    if (!results || !window.MutationObserver) return;
    new MutationObserver(() => {
      if (results.querySelector(".ll-card")) {
        document.getElementById("results-heading")?.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    }).observe(results, { childList: true, subtree: true });
  }

  function initPreview() {
    const input = document.getElementById("demo-image");
    const preview = document.getElementById("demo-preview");
    const analyze = document.getElementById("demo-analyze");
    if (!input || !preview || !analyze) return;

    input.addEventListener("change", () => {
      const [file] = input.files || [];
      if (!file) return;
      preview.src = URL.createObjectURL(file);
      preview.hidden = false;
      showToast("Photo ready. Connect the analyze action to your app backend.");
    });
    analyze.addEventListener("click", () => {
      showToast(input.files?.length ? "This standalone preview has no analysis backend." : "Choose or take a label photo first.");
    });
  }

  function init() {
    if (document.documentElement.dataset.labelLensReady === "true") return;
    document.documentElement.dataset.labelLensReady = "true";
    forceDark();
    initNavigation();
    initDialogs();
    initCopyButtons();
    initLoadingState();
    initResultsScroll();
    initPreview();
  }

  return { init, showToast };
})();