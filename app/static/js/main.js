/**
 * VillaVerse Main Application JavaScript
 * Handles responsive sidebar toggling, toast/alert timeouts, and UI interactions.
 */

document.addEventListener("DOMContentLoaded", () => {
  // 1. Mobile Sidebar Toggle
  const sidebarToggleBtn = document.getElementById("sidebarToggleBtn");
  const appSidebar = document.querySelector(".app-sidebar");

  if (sidebarToggleBtn && appSidebar) {
    sidebarToggleBtn.addEventListener("click", () => {
      appSidebar.classList.toggle("show");
    });

    // Close when clicking outside on mobile
    document.addEventListener("click", (e) => {
      if (
        window.innerWidth < 992 &&
        !appSidebar.contains(e.target) &&
        !sidebarToggleBtn.contains(e.target) &&
        appSidebar.classList.contains("show")
      ) {
        appSidebar.classList.remove("show");
      }
    });
  }

  // 2. Auto-fade Flash Alerts
  const alerts = document.querySelectorAll(".alert-dismissible");
  alerts.forEach((alert) => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) bsAlert.close();
    }, 6000);
  });

  // 3. Client-side Table Filter helper (for instant search in lists)
  const clientSearchInputs = document.querySelectorAll("[data-table-search]");
  clientSearchInputs.forEach((input) => {
    const targetTableId = input.getAttribute("data-table-search");
    const table = document.getElementById(targetTableId);
    if (!table) return;

    input.addEventListener("input", (e) => {
      const term = e.target.value.toLowerCase().trim();
      const rows = table.querySelectorAll("tbody tr");
      rows.forEach((row) => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(term) ? "" : "none";
      });
    });
  });
});
