// static/app.js
document.addEventListener("DOMContentLoaded", () => {
    const userInput = document.getElementById("user-input");
    const sendButton = document.getElementById("send-button");
    const chatMessages = document.getElementById("chat-messages");

    const addMessage = (sender, message) => {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("message", sender);
        messageDiv.textContent = message;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight; // Auto-scroll
    };

    const showTypingIndicator = () => {
        const typingDiv = document.createElement("div");
        typingDiv.classList.add("message", "typing");
        typingDiv.id = "typing-indicator";
        typingDiv.textContent = "Typing...";
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    };

    const removeTypingIndicator = () => {
        const typingDiv = document.getElementById("typing-indicator");
        if (typingDiv) {
            typingDiv.remove();
        }
    };

    const sendMessage = async () => {
        const message = userInput.value.trim();
        if (message === "") return;

        addMessage("user", message);
        userInput.value = "";
        showTypingIndicator();

        try {
            const response = await fetch("/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ message: message }),
            });

            const data = await response.json();
            
            removeTypingIndicator();
            
            // This is the key! We only display the 'answer' field.
            addMessage("bot", data.answer);

        } catch (error) {
            removeTypingIndicator();
            addMessage("bot", "Sorry, something went wrong. Please try again.");
            console.error("Error:", error);
        }
    };

    sendButton.addEventListener("click", sendMessage);
    userInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            sendMessage();
        }
    });
});