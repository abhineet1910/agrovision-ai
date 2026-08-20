(function () {
  const input = document.getElementById("image-input");
  const placeholder = document.getElementById("upload-placeholder");
  const previewWrap = document.getElementById("image-preview-wrap");
  const previewImg = document.getElementById("image-preview");
  const clearBtn = document.getElementById("clear-image-btn");
  const analyzeBtn = document.getElementById("analyze-btn");

  const emptyState = document.getElementById("empty-state");
  const loadingState = document.getElementById("loading-state");
  const errorState = document.getElementById("error-state");
  const errorMessage = document.getElementById("error-message");
  const resultState = document.getElementById("result-state");

  let selectedFile = null;

  function showOnly(el) {
    [emptyState, loadingState, errorState, resultState].forEach((e) => e.classList.add("hidden"));
    el.classList.remove("hidden");
    if (el === loadingState) el.classList.add("flex");
  }

  input.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (!file) return;
    selectedFile = file;

    const reader = new FileReader();
    reader.onload = (ev) => {
      previewImg.src = ev.target.result;
      placeholder.classList.add("hidden");
      previewWrap.classList.remove("hidden");
      previewWrap.classList.add("flex");
      showOnly(emptyState);
    };
    reader.readAsDataURL(file);
  });

  clearBtn.addEventListener("click", () => {
    selectedFile = null;
    input.value = "";
    previewWrap.classList.add("hidden");
    previewWrap.classList.remove("flex");
    placeholder.classList.remove("hidden");
    showOnly(emptyState);
  });

  analyzeBtn.addEventListener("click", async () => {
    if (!selectedFile) return;
    showOnly(loadingState);

    const formData = new FormData();
    formData.append("image", selectedFile);

    try {
      const res = await fetch("/api/scan", { method: "POST", body: formData });
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || "Analysis failed. Please try again.");
      }

      renderResult(data);
      showOnly(resultState);
    } catch (err) {
      errorMessage.textContent = err.message || "Analysis failed. Please try again.";
      showOnly(errorState);
    }
  });

  function renderResult(result) {
    const severityColors = {
      High: { bg: "bg-red-50 dark:bg-red-900/20", badge: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300" },
      Medium: { bg: "bg-yellow-50 dark:bg-yellow-900/20", badge: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300" },
      Low: { bg: "bg-green-50 dark:bg-green-900/20", badge: "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300" },
    };
    const colors = severityColors[result.severity] || severityColors.Medium;

    document.getElementById("result-header").className = `p-6 ${colors.bg}`;
    document.getElementById("result-disease").textContent = result.diseaseName;

    const severityEl = document.getElementById("result-severity");
    severityEl.textContent = `${result.severity} Severity`;
    severityEl.className = `text-sm font-semibold px-2 py-0.5 rounded-full ${colors.badge}`;

    document.getElementById("result-confidence").textContent = `${Math.round(result.confidence * 100)}% confidence`;
    document.getElementById("result-description").textContent = result.description;

    const treatmentsEl = document.getElementById("result-treatments");
    treatmentsEl.innerHTML = "";
    (result.treatments || []).forEach((t) => {
      const li = document.createElement("li");
      li.textContent = t;
      treatmentsEl.appendChild(li);
    });

    const fert = result.fertilizer || {};
    document.getElementById("result-fertilizer").textContent =
      `${fert.name || "—"} · ${fert.dosage || "—"} · ${fert.schedule || "—"}`;
  }
})();
