(function () {
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");
  const messages = document.getElementById("chat-messages");

  function appendBubble(text, role) {
    const emptyHint = messages.querySelector("p.text-center");
    if (emptyHint) emptyHint.remove();

    const row = document.createElement("div");
    row.className = `flex ${role === "user" ? "justify-end" : "justify-start"}`;

    const bubble = document.createElement("div");
    bubble.className = `max-w-[80%] px-4 py-2.5 rounded-2xl text-sm ${
      role === "user"
        ? "bg-green-600 text-white"
        : "bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-100"
    }`;
    bubble.textContent = text;

    row.appendChild(bubble);
    messages.appendChild(row);
    messages.scrollTop = messages.scrollHeight;
    return row;
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) return;

    appendBubble(text, "user");
    input.value = "";
    input.disabled = true;

    const typingRow = appendBubble("Thinking...", "model");

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      const data = await res.json();

      if (!res.ok) throw new Error(data.error || "AI Chat is temporarily unavailable.");

      typingRow.firstChild.textContent = data.reply.text;
    } catch (err) {
      typingRow.firstChild.textContent = err.message || "Something went wrong. Please try again.";
      typingRow.firstChild.className += " text-red-500";
    } finally {
      input.disabled = false;
      input.focus();
    }
  });
})();
