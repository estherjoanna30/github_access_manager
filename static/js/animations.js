// Add glow effect to buttons when clicked
document.querySelectorAll("button").forEach(btn => {
    btn.addEventListener("click", () => {
        btn.style.boxShadow = "0 0 10px #58a6ff";
        setTimeout(() => {
            btn.style.boxShadow = "";
        }, 300);
    });
});

// Smooth fade-in for sections
document.querySelectorAll(".section").forEach((section, index) => {
    section.style.opacity = 0;
    section.style.transform = "translateY(15px)";
    setTimeout(() => {
        section.style.transition = "opacity 0.6s ease, transform 0.6s ease";
        section.style.opacity = 1;
        section.style.transform = "translateY(0)";
    }, index * 150);
});

// Collapsible sections
document.querySelectorAll(".section h2").forEach(header => {
    header.style.cursor = "pointer";
    header.addEventListener("click", () => {
        let content = header.nextElementSibling;
        if (content.style.display === "none") {
            content.style.display = "block";
            content.style.opacity = 1;
        } else {
            content.style.display = "none";
        }
    });
});
