const form = document.getElementById("chat-form");
const input = document.getElementById("user-input");
const chatContainer = document.getElementById("chat-container");

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const userMsg = input.value.trim();
  if (!userMsg) return;

  addMessage(userMsg, "user");
  input.value = "";

  // Call FastAPI backend for real OpenAI response
  try {
    const response = await fetch("http://127.0.0.1:8000/ai/strategy", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: userMsg }),
    });

    if (!response.ok) throw new Error("Network response was not ok");
    const data = await response.json();

    // Backend returns: { "response": "AI's strategy suggestion" }
    addMessage(data.response, "bot");
  } catch (error) {
    console.error("Error:", error);
    addMessage("⚠️ Sorry, I couldn’t connect to the AI right now.", "bot");
  }
});
