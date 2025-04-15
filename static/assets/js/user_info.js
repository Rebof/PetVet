
document.addEventListener('DOMContentLoaded', function() {
        // Like functionality
        document.querySelectorAll('.btn-like').forEach(button => {
            button.addEventListener('click', function() {
                const commentId = this.dataset.commentId;
                const likeUrl = `/comments/${commentId}/like/`;
                const likeCount = this.querySelector('.like-count');
                
                fetch(likeUrl, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': '{{ csrf_token }}',
                        'Content-Type': 'application/json'
                    },
                    credentials: 'same-origin'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'liked') {
                        this.classList.add('liked');
                        likeCount.textContent = data.likes_count;
                    } else if (data.status === 'unliked') {
                        this.classList.remove('liked');
                        likeCount.textContent = data.likes_count;
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                });
            });
        });
    });
    
    function editComment(commentId) {
        // Replace with your actual edit comment URL
        window.location.href = `/comments/${commentId}/edit/`;
    }
    
    function confirmDeleteComment(commentId) {
        if (confirm('Are you sure you want to delete this comment? This action cannot be undone.')) {
            fetch(`/comments/${commentId}/delete/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': '{{ csrf_token }}',
                    'Content-Type': 'application/json'
                }
            })
            .then(response => {
                if (response.ok) {
                    window.location.reload();
                } else {
                    alert('Error deleting comment');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error deleting comment');
            });
        }
    }

function editPost(postId) {
        // Replace with your actual edit post URL
        window.location.href = `/posts/${postId}/edit/`;
    }
    
    function confirmDelete(postId) {
        if (confirm('Are you sure you want to delete this post? This action cannot be undone.')) {
            // Replace with your actual delete post endpoint
            fetch(`/posts/${postId}/delete/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': '{{ csrf_token }}',
                    'Content-Type': 'application/json'
                }
            })
            .then(response => {
                if (response.ok) {
                    window.location.reload();
                } else {
                    alert('Error deleting post');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error deleting post');
            });
        }
    }
    document.addEventListener('DOMContentLoaded', function() {
        // Toggle between view and edit modes
        const toggleEdit = document.getElementById('toggleEdit');
        const viewMode = document.getElementById('viewMode');
        const editMode = document.getElementById('editMode');
        const cancelEdit = document.getElementById('cancelEdit');
        
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
        
        // Image preview functionality
        const imageUpload = document.getElementById('profile_picture');
        const imagePreview = document.getElementById('imagePreview');
        
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
    });
