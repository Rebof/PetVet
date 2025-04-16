document.addEventListener("DOMContentLoaded", () => {
  // Sidebar toggle functionality
  const sidebarToggleBtn = document.getElementById("sidebar-toggle-btn");
  const sidebar = document.getElementById("sidebar");
  const adminLayout = document.querySelector(".admin-layout");
  const mobileSidebarToggle = document.getElementById("mobile-sidebar-toggle");

  // Initialize sidebar state from localStorage
  if (sidebar && adminLayout) {
    const isCollapsed = localStorage.getItem("sidebar-collapsed") === "true";
    if (isCollapsed) {
      sidebar.classList.add("collapsed");
      adminLayout.classList.add("sidebar-collapsed");
    }
  }

  // Desktop sidebar toggle
  if (sidebarToggleBtn && sidebar && adminLayout) {
    sidebarToggleBtn.addEventListener("click", (e) => {
      e.stopPropagation(); // Prevent event bubbling
      sidebar.classList.toggle("collapsed");
      adminLayout.classList.toggle("sidebar-collapsed");

      // Save sidebar state to localStorage
      const isCollapsed = sidebar.classList.contains("collapsed");
      localStorage.setItem("sidebar-collapsed", isCollapsed);
    });
  }

  // Mobile sidebar toggle
  if (mobileSidebarToggle && sidebar) {
    mobileSidebarToggle.addEventListener("click", (e) => {
      e.stopPropagation(); // Prevent event bubbling
      sidebar.classList.toggle("mobile-open");
    });

    // Close sidebar when clicking outside on mobile
    document.addEventListener("click", (e) => {
      const isMobile = window.innerWidth <= 768;
      const isClickInsideSidebar = sidebar.contains(e.target);
      const isClickOnToggle = mobileSidebarToggle.contains(e.target);
      
      if (isMobile && !isClickInsideSidebar && !isClickOnToggle && sidebar.classList.contains("mobile-open")) {
        sidebar.classList.remove("mobile-open");
      }
    });
  }

  // User dropdown functionality
  const userDropdownBtn = document.querySelector(".user-dropdown-btn");
  const userDropdown = document.querySelector(".user-dropdown");

  if (userDropdownBtn && userDropdown) {
    userDropdownBtn.addEventListener("click", (e) => {
      e.stopPropagation(); // Prevent event bubbling
      userDropdown.classList.toggle("active");
    });

    // Close dropdown when clicking outside
    document.addEventListener("click", (e) => {
      if (userDropdown.classList.contains("active") && 
          !userDropdown.contains(e.target) && 
          !userDropdownBtn.contains(e.target)) {
        userDropdown.classList.remove("active");
      }
    });
  }

  // Message close buttons
  const messageCloseButtons = document.querySelectorAll(".message-close");
  messageCloseButtons.forEach((button) => {
    button.addEventListener("click", function() {
      const message = this.closest(".message");
      if (message) {
        message.remove();
      }
    });
  });

  // Initialize charts if they exist on the page
  function initializeCharts() {
    // User statistics chart
    const userStatsChart = document.getElementById("userStatsChart");
    if (userStatsChart && window.Chart) {
      new window.Chart(userStatsChart, {
        type: "bar",
        data: {
          labels: ["Vets", "Pet Owners", "Total Users"],
          datasets: [
            {
              label: "User Count",
              data: [
                userStatsChart.dataset.vets,
                userStatsChart.dataset.petOwners,
                userStatsChart.dataset.totalUsers,
              ],
              backgroundColor: [
                "rgba(78, 205, 196, 0.6)",  // Teal
                "rgba(255, 107, 107, 0.6)", // Coral
                "rgba(59, 130, 246, 0.6)",  // Blue
              ],
              borderColor: [
                "rgba(78, 205, 196, 1)",
                "rgba(255, 107, 107, 1)",
                "rgba(59, 130, 246, 1)",
              ],
              borderWidth: 1,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: {
              beginAtZero: true,
              ticks: {
                precision: 0,
              },
            },
          },
        },
      });
    }

    // Post statistics chart
    const postStatsChart = document.getElementById("postStatsChart");
    if (postStatsChart && window.Chart) {
      const labels = JSON.parse(postStatsChart.dataset.labels || '[]');
      const data = JSON.parse(postStatsChart.dataset.values || '[]');

      new window.Chart(postStatsChart, {
        type: "pie",
        data: {
          labels: labels,
          datasets: [
            {
              data: data,
              backgroundColor: [
                "rgba(78, 205, 196, 0.6)",  // Teal
                "rgba(255, 107, 107, 0.6)", // Coral
                "rgba(59, 130, 246, 0.6)",  // Blue
                "rgba(245, 158, 11, 0.6)",  // Yellow
                "rgba(239, 68, 68, 0.6)",   // Red
                "rgba(168, 85, 247, 0.6)",  // Purple
                "rgba(236, 72, 153, 0.6)",  // Pink
              ],
              borderWidth: 1,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: "right",
            },
          },
        },
      });
    }
  }

  // Call chart initialization if Chart.js is loaded
  if (typeof window.Chart !== "undefined") {
    initializeCharts();
  }
});