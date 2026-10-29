/**
 * VillaVerse Dashboard Visualizations
 * Fetches database-calculated analytical data and renders Chart.js charts.
 */

document.addEventListener("DOMContentLoaded", () => {
  fetchChartData();
});

async function fetchChartData() {
  try {
    const response = await fetch("/api/chart-data");
    if (!response.ok) {
      console.warn("Failed to retrieve dashboard chart metrics.");
      return;
    }
    const data = await response.json();

    // Initialize individual charts
    renderOccupancyChart(data.occupancy);
    renderCashflowChart(data.cashflow);
    renderMaintenanceCategoryChart(data.maintenance_categories);
  } catch (error) {
    console.error("Error loading dashboard charts:", error);
  }
}

function renderOccupancyChart(occupancyData) {
  const ctx = document.getElementById("occupancyChart");
  if (!ctx) return;

  new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: occupancyData.labels,
      datasets: [
        {
          data: occupancyData.data,
          backgroundColor: [
            "#0E6234", // Occupied (Forest Green)
            "#1958A7", // Available (Calm Blue)
            "#D97706"  // Under Construction (Amber)
          ],
          borderWidth: 2,
          borderColor: "#FFFFFF",
          hoverOffset: 6
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "bottom",
          labels: {
            font: { family: "'Plus Jakarta Sans', sans-serif", size: 12, weight: "500" },
            padding: 18,
            usePointStyle: true
          }
        },
        tooltip: {
          backgroundColor: "#0F382C",
          titleFont: { family: "'Plus Jakarta Sans', sans-serif", weight: "bold" },
          bodyFont: { family: "'Plus Jakarta Sans', sans-serif" },
          padding: 12,
          cornerRadius: 8
        }
      },
      cutout: "68%"
    }
  });
}

function renderCashflowChart(cashflowData) {
  const ctx = document.getElementById("cashflowChart");
  if (!ctx) return;

  new Chart(ctx, {
    type: "bar",
    data: {
      labels: cashflowData.labels,
      datasets: [
        {
          label: "Invoiced Dues ($)",
          data: cashflowData.invoiced,
          backgroundColor: "rgba(25, 88, 167, 0.75)",
          borderColor: "#1958A7",
          borderWidth: 1.5,
          borderRadius: 6
        },
        {
          label: "Collected Payments ($)",
          data: cashflowData.collected,
          backgroundColor: "rgba(14, 98, 52, 0.85)",
          borderColor: "#0E6234",
          borderWidth: 1.5,
          borderRadius: 6
        },
        {
          label: "Operational Expenses ($)",
          data: cashflowData.expenses,
          backgroundColor: "rgba(225, 29, 72, 0.75)",
          borderColor: "#E11D48",
          borderWidth: 1.5,
          borderRadius: 6
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          grid: { display: false },
          ticks: { font: { family: "'Plus Jakarta Sans', sans-serif", size: 11 } }
        },
        y: {
          grid: { color: "#EDF1EE" },
          ticks: {
            font: { family: "'Plus Jakarta Sans', sans-serif", size: 11 },
            callback: (val) => "$" + Number(val).toLocaleString()
          }
        }
      },
      plugins: {
        legend: {
          position: "top",
          align: "end",
          labels: {
            font: { family: "'Plus Jakarta Sans', sans-serif", size: 12, weight: "500" },
            usePointStyle: true,
            boxWidth: 8
          }
        },
        tooltip: {
          backgroundColor: "#0F382C",
          padding: 12,
          cornerRadius: 8,
          callbacks: {
            label: (ctx) => ` ${ctx.dataset.label}: $${Number(ctx.raw).toLocaleString(undefined, {minimumFractionDigits: 2})}`
          }
        }
      }
    }
  });
}

function renderMaintenanceCategoryChart(categoryData) {
  const ctx = document.getElementById("maintenanceCategoryChart");
  if (!ctx) return;

  new Chart(ctx, {
    type: "bar",
    data: {
      labels: categoryData.labels,
      datasets: [
        {
          label: "Tickets Logged",
          data: categoryData.data,
          backgroundColor: "rgba(197, 155, 39, 0.8)",
          borderColor: "#C59B27",
          borderWidth: 1.5,
          borderRadius: 6
        }
      ]
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          grid: { color: "#EDF1EE" },
          ticks: { stepSize: 1, precision: 0 }
        },
        y: {
          grid: { display: false }
        }
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#0F382C",
          padding: 10,
          cornerRadius: 8
        }
      }
    }
  });
}
