document.addEventListener('DOMContentLoaded', function() {
    // Initialize reply buttons
    document.querySelectorAll('.reply-btn').forEach(button => {
        button.addEventListener('click', function() {
            const commentId = this.dataset.commentId;
            const replyForm = document.getElementById(`reply-form-${commentId}`);
            
            // Hide all other reply forms first
            document.querySelectorAll('.reply-form-container').forEach(form => {
                if (form.id !== `reply-form-${commentId}`) {
                    form.style.display = 'none';
                }
            });
            
            // Toggle current reply form
            if (replyForm.style.display === 'none' || !replyForm.style.display) {
                replyForm.style.display = 'block';
                replyForm.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            } else {
                replyForm.style.display = 'none';
            }
        });
    });

    // Initialize cancel reply buttons
    document.querySelectorAll('.cancel-reply').forEach(button => {
        button.addEventListener('click', function() {
            const commentId = this.dataset.commentId;
            document.getElementById(`reply-form-${commentId}`).style.display = 'none';
        });
    });

    

    // Delete confirmation functions
    window.confirmDeletePost = function(postId) {
        if (confirm('Are you sure you want to delete this post?')) {
            fetch(`/posts/${postId}/delete/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
            .then(response => {
                if (response.ok) {
                    window.location.href = '/';
                }
            });
        }
    };

    window.confirmDeleteComment = function(commentId) {
        if (confirm('Are you sure you want to delete this comment?')) {
            fetch(`/comments/${commentId}/delete/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
            .then(response => {
                if (response.ok) {
                    document.getElementById(`comment-${commentId}`).remove();
                }
            });
        }
    };

    window.confirmDeleteReply = function(replyId) {
        if (confirm('Are you sure you want to delete this reply?')) {
            fetch(`/replies/${replyId}/delete/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
            .then(response => {
                if (response.ok) {
                    document.getElementById(`reply-${replyId}`).remove();
                }
            });
        }
    };

    // Helper function to get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});