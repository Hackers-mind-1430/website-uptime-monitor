document.addEventListener("DOMContentLoaded", () => {
    const statusElements = document.querySelectorAll(".status-value");
    statusElements.forEach((element) => {
        const value = element.textContent.trim().toLowerCase();
        const badge = element.closest(".status-item").querySelector(".status-badge");
        if (value === "online") {
            badge.classList.add("status-online");
        } else {
            badge.classList.add("status-offline");
        }
    });
});
