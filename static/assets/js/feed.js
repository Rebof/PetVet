document.addEventListener('DOMContentLoaded', function() {
    // Profile menu toggle
    const profileBtn = document.getElementById('profile-menu-btn');
    const profileMenu = document.querySelector('.profile-menu');
    
    profileBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        profileMenu.classList.toggle('show');
    });
    
    // Close profile menu when clicking elsewhere
    document.addEventListener('click', function() {
        profileMenu.classList.remove('show');
    });
    
    // Prevent profile menu from closing when clicking inside it
    profileMenu.addEventListener('click', function(e) {
        e.stopPropagation();
    });

    // Search form submission
    const searchInput = document.querySelector('.search-bar input');
    const searchForm = document.querySelector('.search-bar form');
    
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchForm.submit();
        }
    });
    
    
    // Active sidebar link highlighting
    const currentUrl = window.location.pathname;
    const sidebarLinks = document.querySelectorAll('.sidebar-section a');
    
    sidebarLinks.forEach(link => {
        if (link.getAttribute('href') === currentUrl) {
            link.classList.add('active');
        }
    });
});