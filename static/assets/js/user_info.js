document.addEventListener('DOMContentLoaded', function() {
    // Toggle between view and edit modes
    const toggleEdit = document.getElementById('toggleEdit');
    const viewMode = document.getElementById('viewMode');
    const editMode = document.getElementById('editMode');
    const cancelEdit = document.getElementById('cancelEdit');
    
    if (toggleEdit && viewMode && editMode && cancelEdit) {
        toggleEdit.addEventListener('click', function() {
            viewMode.style.display = 'none';
            editMode.style.display = 'block';
            this.style.display = 'none';
        });
        
        cancelEdit.addEventListener('click', function() {
            viewMode.style.display = 'block';
            editMode.style.display = 'none';
            toggleEdit.style.display = 'inline-flex';
        });
    }
    
    // Image preview functionality
    const imageUpload = document.getElementById('profile_picture');
    const imagePreview = document.getElementById('imagePreview');
    
    if (imageUpload && imagePreview) {
        imageUpload.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                
                reader.addEventListener('load', function() {
                    imagePreview.innerHTML = '';
                    const img = document.createElement('img');
                    img.src = this.result;
                    imagePreview.appendChild(img);
                });
                
                reader.readAsDataURL(file);
            } else if (imagePreview.querySelector('img')) {
                // Keep existing image if no new file selected
                return;
            } else {
                imagePreview.innerHTML = '<i class="fas fa-camera"></i><span>No image selected</span>';
            }
        });
    }
    
    // Form submission handling
    const editForm = document.getElementById('editMode');
    if (editForm) {
        editForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            
            fetch(this.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                },
            })
            .then(response => {
                if (response.redirected) {
                    window.location.href = response.url;
                }
                return response.json();
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    }
});

// Helper function to get CSRF token
function getCsrfToken() {
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
    return cookieValue || '';
}


// Edit post function
function editPost(postSlug) {
    window.location.href = `/edit-post/${postSlug}/`;
}


// Message close functionality
document.querySelectorAll('.message-close').forEach(button => {
    button.addEventListener('click', (e) => {
        const message = e.target.closest('.message');
        message.classList.add('hide');
        setTimeout(() => {
            message.remove();
        }, 300);
    });
});

// Auto-hide messages after 5 seconds
setTimeout(() => {
    document.querySelectorAll('.message').forEach(message => {
        message.classList.add('hide');
        setTimeout(() => {
            message.remove();
        }, 300);
    });
}, 5000);