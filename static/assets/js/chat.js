document.addEventListener('DOMContentLoaded', function() {
    // Get elements
    const chatForm = document.querySelector('#chat-f');
    const textarea = document.querySelector('#chat-input-area');
    const chatMessages = document.querySelector('.chat-messages');
    const blockBtn = document.getElementById('block-user-btn');
    const blockModal = document.getElementById('block-modal');
    const closeModal = document.querySelector('.close-modal');
    const cancelBlock = document.getElementById('cancel-block');
    const searchInput = document.getElementById('search-contacts');
    
    // Auto-resize textarea
    if (textarea) {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
            
            // Enable/disable send button based on content
            const sendBtn = document.querySelector('#send-btn');
            if (sendBtn) {
                sendBtn.disabled = this.value.trim() === '';
                sendBtn.style.opacity = this.value.trim() === '' ? '0.6' : '1';
            }
        });
    }
    
    // Block user functionality
    if (blockBtn) {
        blockBtn.addEventListener('click', function() {
            if (blockModal) {
                blockModal.style.display = 'flex';
            }
        });
    }
    
    // Close modal
    if (closeModal) {
        closeModal.addEventListener('click', function() {
            blockModal.style.display = 'none';
        });
    }
    
    // Cancel block
    if (cancelBlock) {
        cancelBlock.addEventListener('click', function() {
            blockModal.style.display = 'none';
        });
    }
    
    // Close modal when clicking outside
    window.addEventListener('click', function(event) {
        if (event.target === blockModal) {
            blockModal.style.display = 'none';
        }
    });
    
    // Search functionality
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const chatItems = document.querySelectorAll('.chat-item');
            
            chatItems.forEach(item => {
                const username = item.querySelector('h4').textContent.toLowerCase();
                const lastMessage = item.querySelector('p').textContent.toLowerCase();
                
                if (username.includes(searchTerm) || lastMessage.includes(searchTerm)) {
                    item.closest('.chat-link').style.display = 'block';
                } else {
                    item.closest('.chat-link').style.display = 'none';
                }
            });
        });
    }
    
    // WebSocket functionality
    const setupWebSocket = () => {
        // Get current and receiver usernames
        const currentUser = document.querySelector('meta[name="current-user"]')?.content;
        const receiverUsername = document.querySelector('meta[name="receiver-user"]')?.content;
        
        if (!currentUser || !receiverUsername) return;
        
        // Create consistent room name (sorted usernames to ensure same group for both users)
        const roomName = [currentUser, receiverUsername].sort().join('_');
        
        // WebSocket connection
        const wsScheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
        const wsPath = `${wsScheme}://${window.location.host}/ws/chat/${roomName}/`;
        let chatSocket = new WebSocket(wsPath);
        
        // Track if we've already sent a message to avoid duplicates
        let sentMessages = new Set();

        // WebSocket event handlers
        chatSocket.onopen = function() {
            console.log('WebSocket connection established for room:', roomName);
        };

        chatSocket.onerror = function(error) {
            console.error('WebSocket error:', error);
        };

        chatSocket.onclose = function() {
            console.log('WebSocket connection closed, attempting to reconnect...');
            setTimeout(function() {
                chatSocket = new WebSocket(wsPath);
            }, 3000);
        };

        // Handle incoming messages
        chatSocket.onmessage = function(e) {
            const data = JSON.parse(e.data);
            console.log('Received message:', data);
            
            // Create a unique ID for this message to prevent duplicates
            const messageId = `${data.sender}_${data.timestamp}`;
            
            // Skip if we've already processed this message
            if (sentMessages.has(messageId)) {
                return;
            }
            
            // Only process if this message is relevant to current chat
            if ((data.sender === currentUser && data.receiver === receiverUsername) || 
                (data.sender === receiverUsername && data.receiver === currentUser)) {
                
                const isSent = data.sender === currentUser;
                const messageTime = data.timestamp ? 
                    new Date(data.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 
                    new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

                // Create message element
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${isSent ? 'sent' : 'received'}`;
                messageDiv.innerHTML = `
                    <div class="message-content">${data.message}</div>
                    <div class="message-meta">
                        <span class="message-time">${messageTime}</span>
                        ${isSent ? '<span class="message-status"><i class="fas fa-check"></i></span>' : ''}
                    </div>
                `;
                
                // Remove empty state if it exists
                const emptyMessages = chatMessages.querySelector('.empty-messages');
                if (emptyMessages) {
                    emptyMessages.remove();
                }

                // Append to chat
                chatMessages.appendChild(messageDiv);
                chatMessages.scrollTop = chatMessages.scrollHeight;

                // Update chat list preview if this is a received message (not sent by current user)
                if (!isSent) {
                    updateChatListPreview(data.sender, data.message);
                }
                
                // Add to sent messages set to prevent duplicates
                sentMessages.add(messageId);
            }
        };

        // Handle form submission
        if (chatForm) {
            chatForm.addEventListener('submit', function(e) {
                e.preventDefault();
                const message = textarea.value.trim();
                
                if (message && chatSocket.readyState === WebSocket.OPEN) {
                    // Create message data with timestamp for unique ID
                    const timestamp = new Date().toISOString();
                    const messageData = {
                        'message': message,
                        'sender': currentUser,
                        'receiver': receiverUsername,
                        'timestamp': timestamp
                    };
                    
                    // Create unique ID for this message
                    const messageId = `${currentUser}_${timestamp}`;
                    
                    // Add to sent messages set to prevent duplicates
                    sentMessages.add(messageId);

                    // Send via WebSocket
                    chatSocket.send(JSON.stringify(messageData));
                    
                    // Also add to UI immediately (optimistic update)
                    const messageDiv = document.createElement('div');
                    messageDiv.className = 'message sent';
                    messageDiv.innerHTML = `
                        <div class="message-content">${message}</div>
                        <div class="message-meta">
                            <span class="message-time">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                            <span class="message-status"><i class="fas fa-check"></i></span>
                        </div>
                    `;
                    
                    // Remove empty state if it exists
                    const emptyMessages = chatMessages.querySelector('.empty-messages');
                    if (emptyMessages) {
                        emptyMessages.remove();
                    }
                    
                    chatMessages.appendChild(messageDiv);
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                    
                    // Clear input and reset height
                    textarea.value = '';
                    textarea.style.height = 'auto';
                    
                    // Don't update chat list preview for messages sent by current user
                    // This prevents unread badges from appearing for own messages
                }
            });
        }
    };

    // Update chat list preview
    function updateChatListPreview(username, message) {
        const chatItems = document.querySelectorAll('.chat-item');
        chatItems.forEach(item => {
            if (item.dataset.username === username) {
                // Update last message preview
                const preview = item.querySelector('p');
                if (preview) {
                    preview.textContent = message.length > 28 ? message.substring(0, 28) + '...' : message;
                }
                
                // Update time
                const timeElement = item.querySelector('.chat-time');
                if (timeElement) {
                    timeElement.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                }
                
                // Add unread badge if this is a received message
                // Only add unread badge for messages received from others, not sent by current user
                const currentUser = document.querySelector('meta[name="current-user"]')?.content;
                if (username !== currentUser) {
                    let badge = item.querySelector('.unread-badge');
                    if (!badge) {
                        badge = document.createElement('span');
                        badge.className = 'unread-badge';
                        item.appendChild(badge);
                    }
                }
                
                // Move this conversation to the top
                const parent = item.closest('.chat-link');
                const container = parent.parentNode;
                container.insertBefore(parent, container.firstChild);
            }
        });
    }

    // Add meta tags for current user and receiver
    function addUserMetaTags() {
        // Extract usernames from the page
        const currentUser = document.querySelector('.chat-window')?.dataset?.currentUser || '';
        const receiverUser = document.querySelector('.chat-header-user h3')?.textContent.trim() || '';
        
        // Create meta tags if they don't exist
        if (!document.querySelector('meta[name="current-user"]')) {
            const currentUserMeta = document.createElement('meta');
            currentUserMeta.name = 'current-user';
            currentUserMeta.content = currentUser;
            document.head.appendChild(currentUserMeta);
        }
        
        if (!document.querySelector('meta[name="receiver-user"]') && receiverUser) {
            const receiverUserMeta = document.createElement('meta');
            receiverUserMeta.name = 'receiver-user';
            receiverUserMeta.content = receiverUser;
            document.head.appendChild(receiverUserMeta);
        }
    }

    // Initialize WebSocket if we have a receiver
    if (document.querySelector('.chat-header')) {
        addUserMetaTags();
        setupWebSocket();
    }

    // Initial scroll to bottom of messages
    if (chatMessages) {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Block user form submission
    const blockForm = document.getElementById('block-form');
    if (blockForm) {
        blockForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            
            fetch(this.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrfToken
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Show success message
                    const successMessage = document.createElement('div');
                    successMessage.className = 'block-success-message';
                    successMessage.innerHTML = `
                        <i class="fas fa-check-circle"></i>
                        <p>${data.message || 'User has been blocked successfully.'}</p>
                    `;
                    document.body.appendChild(successMessage);
                    
                    // Redirect after a short delay
                    setTimeout(() => {
                        window.location.href = '/inbox/';
                    }, 2000);
                } else {
                    alert(data.message || 'An error occurred while blocking the user.');
                    blockModal.style.display = 'none';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while processing your request.');
                blockModal.style.display = 'none';
            });
        });
    }
});