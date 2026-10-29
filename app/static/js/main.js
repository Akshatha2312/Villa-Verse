document.addEventListener("DOMContentLoaded", () => {
  const sidebarToggleBtn = document.getElementById("sidebarToggleBtn");
  const appSidebar = document.querySelector(".app-sidebar");

  if (sidebarToggleBtn && appSidebar) {
    sidebarToggleBtn.addEventListener("click", () => {
      appSidebar.classList.toggle("show");
    });

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

  const alerts = document.querySelectorAll(".alert-dismissible");
  alerts.forEach((alert) => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) bsAlert.close();
    }, 6000);
  });

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
