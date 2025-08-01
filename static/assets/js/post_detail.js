// Message close functionality
document.querySelectorAll('.message-close').forEach(button => {
    button.addEventListener('click', (e) => {
        e.target.closest('.message').remove();
    });
});

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all interactive elements
    initializePostLikes();
    initializeCommentLikes();
    initializeReplyButtons();
    initializeDeleteModals();
    initializeShareButtons();
    initializeCommentForm();
    // Remove duplicate initialization - we'll handle replies in the main function
});

// Initialize reply forms
function initializeReplyForms() {
    document.querySelectorAll('.reply-form').forEach(form => {
        if (!form.dataset.initialized) {
            form.addEventListener('submit', handleReplySubmit);
            form.dataset.initialized = 'true';
        }
    });
}

// Handle reply form submission
function handleReplySubmit(e) {
    e.preventDefault();
    
    const form = this;
    const formData = new FormData(form);
    const url = form.action;
    const commentId = form.getAttribute('data-comment-id');
    
    // Show loading state
    const submitButton = form.querySelector('button[type="submit"]');
    const originalButtonText = submitButton.innerHTML;
    submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    submitButton.disabled = true;
    
    fetch(url, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': formData.get('csrfmiddlewaretoken'),
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Clear the form
            form.reset();
            
            // Hide the reply form
            form.closest('.reply-form-container').style.display = 'none';
            
            // Add new reply to the comment
            const repliesContainer = document.getElementById(`replies-container-${commentId}`);
            
            // Create and insert new reply
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = data.reply_html;
            const newReply = tempDiv.firstChild;
            
            // Add current-user-comment class if this is the current user's reply
            if (newReply.querySelector('.delete-btn')) {
                newReply.classList.add('current-user-comment');
            }
            
            repliesContainer.appendChild(newReply);
            
            // Show success message
            showToast('Reply added successfully!');
        } else {
            showToast(data.error || 'Error adding reply');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error adding reply. Please try again.');
    })
    .finally(() => {
        // Restore button state
        submitButton.innerHTML = originalButtonText;
        submitButton.disabled = false;
    });
}

// Initialize post like buttons
function initializePostLikes() {
    const postLikeButtons = document.querySelectorAll('.like-btn[data-post-id]');
    postLikeButtons.forEach(button => {
        if (!button.dataset.initialized) {
            button.addEventListener('click', function() {
                const postId = this.getAttribute('data-post-id');
                handleLike('post', postId, this);
            });
            button.dataset.initialized = 'true';
        }
    });
}

// Initialize comment like buttons
function initializeCommentLikes(container = document) {
    const commentLikeButtons = container.querySelectorAll('.like-btn[data-comment-id]');
    commentLikeButtons.forEach(button => {
        // Only add listener if not already added
        if (!button.dataset.initialized) {
            button.addEventListener('click', function() {
                const commentId = this.getAttribute('data-comment-id');
                handleLike('comment', commentId, this);
            });
            button.dataset.initialized = 'true';
        }
    });
}

// Initialize reply buttons
function initializeReplyButtons() {
    const replyButtons = document.querySelectorAll('.reply-btn');
    replyButtons.forEach(button => {
        if (!button.dataset.initialized) {
            button.addEventListener('click', function() {
                const commentId = this.getAttribute('data-comment-id');
                const replyForm = document.getElementById(`reply-form-${commentId}`);
                
                // Hide all other reply forms first
                document.querySelectorAll('.reply-form-container').forEach(form => {
                    if (form.id !== `reply-form-${commentId}`) {
                        form.style.display = 'none';
                    }
                });
                
                // Toggle this reply form
                replyForm.style.display = replyForm.style.display === 'none' ? 'block' : 'none';
                
                // Focus on textarea if form is visible
                if (replyForm.style.display === 'block') {
                    replyForm.querySelector('textarea').focus();
                }
            });
            button.dataset.initialized = 'true';
        }
    });

    // Cancel reply buttons
    const cancelReplyButtons = document.querySelectorAll('.cancel-reply');
    cancelReplyButtons.forEach(button => {
        if (!button.dataset.initialized) {
            button.addEventListener('click', function() {
                const commentId = this.getAttribute('data-comment-id');
                const replyForm = document.getElementById(`reply-form-${commentId}`);
                replyForm.style.display = 'none';
            });
            button.dataset.initialized = 'true';
        }
    });
    
    // Initialize reply forms when reply buttons are set up
    initializeReplyForms();
}

// Initialize delete modals
function initializeDeleteModals() {
    createDeleteModal();
    
    // Expose delete functions to window
    window.confirmDeletePost = function(postId) {
        showDeleteModal('post', postId);
    };
    
    window.confirmDeleteComment = function(commentId) {
        showDeleteModal('comment', commentId);
    };
    
    window.confirmDeleteReply = function(replyId) {
        showDeleteModal('reply', replyId);
    };
}

// Initialize share buttons
function initializeShareButtons() {
    document.querySelectorAll('.share-btn').forEach(button => {
        if (!button.dataset.initialized) {
            button.addEventListener('click', function() {
                const url = window.location.href;
                
                if (navigator.share) {
                    navigator.share({
                        title: document.title,
                        url: url
                    }).catch(error => console.error('Error sharing:', error));
                } else {
                    navigator.clipboard.writeText(url)
                        .then(() => showToast('Link copied to clipboard!'))
                        .catch(err => console.error('Could not copy text: ', err));
                }
            });
            button.dataset.initialized = 'true';
        }
    });
}

// Initialize comment form
function initializeCommentForm() {
    const commentForm = document.querySelector('.comment-form');
    
    if (commentForm && !commentForm.dataset.initialized) {
        commentForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const url = this.action;
            
            // Show loading state
            const submitButton = this.querySelector('button[type="submit"]');
            const originalButtonText = submitButton.innerHTML;
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            submitButton.disabled = true;
            
            fetch(url, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': formData.get('csrfmiddlewaretoken'),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    // Clear the form
                    this.reset();
                    
                    // Add new comment to the comments section
                    const commentsSection = document.querySelector('.comments-section');
                    
                    // Remove empty state if exists
                    const emptyState = commentsSection.querySelector('.empty-comments');
                    if (emptyState) {
                        emptyState.remove();
                    }
                    
                    // Create and insert new comment
                    const tempDiv = document.createElement('div');
                    tempDiv.innerHTML = data.comment_html;
                    const newComment = tempDiv.firstChild;
                    
                    // Add current-user-comment class if this is the current user's comment
                    if (newComment.querySelector('.delete-btn')) {
                        newComment.classList.add('current-user-comment');
                    }
                    
                    // Insert after the header
                    const commentsHeader = commentsSection.querySelector('.comments-header');
                    commentsSection.insertBefore(newComment, commentsHeader.nextSibling);
                    
                    // Initialize interactive elements for the new comment
                    initializeCommentLikes(newComment);
                    initializeReplyButtons();
                    
                    // Update comment count
                    updateCommentCount();
                    
                    // Show success message
                    showToast('Comment added successfully!');
                } else {
                    showToast(data.error || 'Error adding comment');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('Error adding comment. Please try again.');
            })
            .finally(() => {
                // Restore button state
                submitButton.innerHTML = originalButtonText;
                submitButton.disabled = false;
            });
        });
        commentForm.dataset.initialized = 'true';
    }
}

// Handle like functionality
function handleLike(type, id, button) {
    // Add animation class
    button.classList.add('like-animation');
    
    // Remove animation class after animation completes
    setTimeout(() => {
        button.classList.remove('like-animation');
    }, 300);

    // Get current like count
    const likeCountElement = button.querySelector('.like-count');
    let likeCount = parseInt(likeCountElement.textContent);
    
    // Toggle like state
    const isLiked = button.classList.contains('active');
    const newLikeState = !isLiked;
    
    // Update UI immediately for better responsiveness
    if (newLikeState) {
        button.classList.add('active');
        likeCount++;
    } else {
        button.classList.remove('active');
        likeCount--;
    }
    likeCountElement.textContent = likeCount;
    
    // Show loading state
    const originalButtonContent = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    button.disabled = true;
    
    // Send like request to server
    const url = type === 'post' ? `/like-post/${id}/` : `/like-comment/${id}/`;
    
    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            'liked': newLikeState
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        // Update like count from server response if needed
        if (data.likes !== undefined) {
            likeCountElement.textContent = data.likes;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        // Revert UI changes on error
        if (newLikeState) {
            button.classList.remove('active');
            likeCount--;
        } else {
            button.classList.add('active');
            likeCount++;
        }
        likeCountElement.textContent = likeCount;
    })
    .finally(() => {
        button.innerHTML = originalButtonContent;
        button.disabled = false;
    });
}

// Delete modal functions
function createDeleteModal() {
    // Only create if it doesn't exist
    if (!document.getElementById('delete-modal')) {
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.id = 'delete-modal';
        
        modal.innerHTML = `
            <div class="modal-content">
                <h3 class="modal-title">Confirm Delete</h3>
                <p>Are you sure you want to delete this? This action cannot be undone.</p>
                <div class="modal-actions">
                    <button id="cancel-delete" class="btn btn-outline">Cancel</button>
                    <button id="confirm-delete" class="btn btn-danger">Delete</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        document.getElementById('cancel-delete').addEventListener('click', closeDeleteModal);
        modal.addEventListener('click', function(event) {
            if (event.target === modal) {
                closeDeleteModal();
            }
        });
    }
}

function showDeleteModal(type, id) {
    const modal = document.getElementById('delete-modal');
    modal.style.display = 'flex';
    
    const confirmButton = document.getElementById('confirm-delete');
    confirmButton.onclick = function() {
        deleteItem(type, id);
        closeDeleteModal();
    };
}

function closeDeleteModal() {
    const modal = document.getElementById('delete-modal');
    modal.style.display = 'none';
}

function deleteItem(type, id) {
    let url;
    
    switch(type) {
        case 'post':
            url = `/delete-post/${id}/`;
            break;
        case 'comment':
            url = `/delete-comment/${id}/`;
            break;
        case 'reply':
            url = `/delete-reply/${id}/`;
            break;
        default:
            console.error('Invalid delete type');
            return;
    }
    
    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            if (type === 'post') {
                window.location.href = '/';
            } else if (type === 'comment') {
                const comment = document.getElementById(`comment-${id}`);
                comment.remove();
                updateCommentCount();
            } else if (type === 'reply') {
                const reply = document.getElementById(`reply-${id}`);
                reply.remove();
            }
            
            showToast('Item deleted successfully');
        } else {
            console.error('Error:', data.error);
            showToast(data.error || 'Error deleting item');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error deleting item. Please try again.');
    });
}

// Update comment count
function updateCommentCount() {
    const commentCount = document.querySelectorAll('.comment:not(.reply)').length;
    const countElements = document.querySelectorAll('.comment-count');
    
    countElements.forEach(el => {
        el.textContent = commentCount;
    });
    
    // Show empty state if no comments
    const commentsSection = document.querySelector('.comments-section');
    if (commentCount === 0 && !commentsSection.querySelector('.empty-comments')) {
        const emptyState = document.createElement('div');
        emptyState.className = 'empty-comments';
        emptyState.innerHTML = `
            <i class="far fa-comment-dots"></i>
            <p>No comments yet. Be the first to share what you think!</p>
        `;
        commentsSection.appendChild(emptyState);
    }
}

// Toast notification
function showToast(message) {
    if (!document.getElementById('toast')) {
        const toast = document.createElement('div');
        toast.id = 'toast';
        document.body.appendChild(toast);
    }
    
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.style.opacity = '1';
    
    setTimeout(() => {
        toast.style.opacity = '0';
    }, 3000);
}

// Get CSRF token
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