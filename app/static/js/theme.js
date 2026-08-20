(function () {
  const root = document.documentElement;
  const btn = document.getElementById("theme-toggle-btn");
  const iconWrap = document.getElementById("theme-toggle-icon");
  const sun = document.getElementById("icon-sun");
  const moon = document.getElementById("icon-moon");

  let rotation = 0;

  function applyTheme(isDark) {
    root.classList.toggle("dark", isDark);
    sun.classList.toggle("hidden", isDark);
    moon.classList.toggle("hidden", !isDark);
  }

  // Respect a previously chosen theme; default to light (matches original app default).
  const saved = window.localStorage.getItem("agrovision-theme");
  applyTheme(saved === "dark");

  btn.addEventListener("click", function () {
    rotation += 360;
    iconWrap.style.transform = `rotate(${rotation}deg)`;

    const isDark = !root.classList.contains("dark");
    applyTheme(isDark);
    window.localStorage.setItem("agrovision-theme", isDark ? "dark" : "light");
  });
})();
