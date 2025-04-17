document.addEventListener('DOMContentLoaded', function() {
    // Modal elements
    const createPostTrigger = document.getElementById('create-post-trigger');
    const createPostModal = document.getElementById('create-post-modal');
    const closeModal = document.getElementById('close-modal');
    const cancelPost = document.getElementById('cancel-post');
    
    // Image upload elements
    const imageInput = document.getElementById('image');
    const imagePreview = document.getElementById('image-preview');
    
    // Sorting elements
    const sortButtons = document.querySelectorAll('.sort-btn');
    const dateFilterBtn = document.getElementById('date-filter-btn');
    const datePickerContainer = document.getElementById('date-picker-container');
    const dateFilterInput = document.getElementById('date-filter');
    const clearDateFilterBtn = document.getElementById('clear-date-filter');
    const applyDateFilterBtn = document.getElementById('apply-date-filter');
    
    // Open modal when clicking on "What's on your mind?"
    if (createPostTrigger) {
        createPostTrigger.addEventListener('click', function() {
            createPostModal.style.display = 'flex';
            document.body.style.overflow = 'hidden'; // Prevent scrolling when modal is open
        });
    }
    
    // Close modal functions
    function closePostModal() {
        createPostModal.style.display = 'none';
        document.body.style.overflow = 'auto'; // Re-enable scrolling
    }
    
    if (closeModal) {
        closeModal.addEventListener('click', closePostModal);
    }
    
    if (cancelPost) {
        cancelPost.addEventListener('click', closePostModal);
    }
    
    // Close modal when clicking outside of it
    window.addEventListener('click', function(event) {
        if (event.target === createPostModal) {
            closePostModal();
        }
    });
    
    // Image preview functionality
    if (imageInput) {
        imageInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                
                reader.onload = function(e) {
                    // Clear previous content
                    imagePreview.innerHTML = '';
                    
                    // Create image element
                    const img = document.createElement('img');
                    img.src = e.target.result;
                    img.alt = 'Image Preview';
                    
                    // Add image to preview
                    imagePreview.appendChild(img);
                };
                
                reader.readAsDataURL(file);
            } else {
                // Reset preview if no file selected
                imagePreview.innerHTML = `
                    <i class="fas fa-image"></i>
                    <span>No image selected</span>
                `;
            }
        });
    }
    
 // Function to fetch sorted posts
function fetchSortedPosts(sortType, dateFilter) {
    console.log("Fetching sorted posts:", sortType, dateFilter);
    
    // Show loading state
    const feedPosts = document.querySelector('.feed-posts');
    if (feedPosts) {
        feedPosts.innerHTML = `
            <div class="loading-posts glass-card">
                <i class="fas fa-spinner fa-spin"></i>
                <p>Loading posts...</p>
            </div>
        `;
    }
    
    // Build query parameters
    const params = new URLSearchParams();
    params.append('sort', sortType);
    if (dateFilter) {
        params.append('date', dateFilter);
    }
    
    // Get current URL path without query parameters
    const currentPath = window.location.pathname;
    
    // Fetch sorted posts
    fetch(`${currentPath}?${params.toString()}`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json'
        },
    })
    .then(function(response) {
        console.log("Response status:", response.status);
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.text();
    })
    .then(function(html) {
        console.log("Received HTML response");
        // Replace feed posts with new HTML
        if (feedPosts) {
            feedPosts.innerHTML = html;
            
            // Update URL in browser without reloading
            const newUrl = `${currentPath}?${params.toString()}`;
            window.history.pushState({ path: newUrl }, '', newUrl);
            
        }
    })
    .catch(function(error) {
        console.error('Error fetching sorted posts:', error);
        if (feedPosts) {
            feedPosts.innerHTML = `
                <div class="error-loading glass-card">
                    <i class="fas fa-exclamation-circle"></i>
                    <p>Error loading posts. Please try again.</p>
                </div>
            `;
        }
    });
}

// Sorting functionality
if (sortButtons && sortButtons.length > 0) {
    sortButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            console.log("Sort button clicked:", this.getAttribute("data-sort"));
            
            // Remove active class from all buttons
            sortButtons.forEach(function(btn) {
                btn.classList.remove('active');
            });
            
            // Add active class to clicked button
            this.classList.add('active');
            
            // Get sort type
            const sortType = this.getAttribute('data-sort');
            
            // Get current date filter
            const dateFilter = dateFilterInput && dateFilterInput.value ? dateFilterInput.value : null;
            
            // Send AJAX request to sort posts
            fetchSortedPosts(sortType, dateFilter);
        });
    });
}

});

