const inrFormatter = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  minimumFractionDigits: 0,
  maximumFractionDigits: 2
});
const inrPaiseFormatter = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2
});

function formatINR(value) {
  const amount = Number(value);
  if (!Number.isFinite(amount)) return inrFormatter.format(0);

  const roundedAmount = Number(amount.toFixed(2));
  const formatter = Number.isInteger(roundedAmount) ? inrFormatter : inrPaiseFormatter;
  return formatter.format(roundedAmount);
}

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
            "#0E6234",
            "#1958A7",
            "#D97706"
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
          label: "Invoiced Dues (INR)",
          data: cashflowData.invoiced,
          backgroundColor: "rgba(25, 88, 167, 0.75)",
          borderColor: "#1958A7",
          borderWidth: 1.5,
          borderRadius: 6
        },
        {
          label: "Collected Payments (INR)",
          data: cashflowData.collected,
          backgroundColor: "rgba(14, 98, 52, 0.85)",
          borderColor: "#0E6234",
          borderWidth: 1.5,
          borderRadius: 6
        },
        {
          label: "Operational Expenses (INR)",
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
            callback: (val) => formatINR(val)
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
            label: (ctx) => ` ${ctx.dataset.label}: ${formatINR(ctx.raw)}`
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
