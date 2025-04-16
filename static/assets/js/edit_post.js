document.addEventListener('DOMContentLoaded', function() {
    // Handle media replacement
    document.querySelectorAll('.replace-media-btn input[type="file"]').forEach(input => {
        input.addEventListener('change', function() {
            const file = this.files[0];
            if (!file) return;
            
            const mediaContainer = this.closest('.current-media');
            const previewElement = mediaContainer.querySelector('img, video');
            
            if (file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    if (previewElement) {
                        previewElement.src = e.target.result;
                    } else {
                        const img = document.createElement('img');
                        img.src = e.target.result;
                        img.className = 'current-image';
                        mediaContainer.insertBefore(img, mediaContainer.firstChild);
                    }
                };
                reader.readAsDataURL(file);
            } else if (file.type.startsWith('video/')) {
                const video = document.createElement('video');
                video.controls = true;
                video.className = 'current-video';
                video.src = URL.createObjectURL(file);
                
                if (previewElement) {
                    mediaContainer.replaceChild(video, previewElement);
                } else {
                    mediaContainer.insertBefore(video, mediaContainer.firstChild);
                }
            }
        });
    });
    
    // Handle media removal
    document.querySelectorAll('.remove-media-btn').forEach(button => {
        button.addEventListener('click', function() {
            const mediaType = this.getAttribute('data-media-type');
            const mediaContainer = this.closest('.current-media');
            const previewElement = mediaContainer.querySelector('img, video');
            
            if (previewElement) {
                previewElement.remove();
            }
            
            // Create hidden input to indicate removal
            const existingInput = mediaContainer.querySelector('input[name="remove_' + mediaType + '"]');
            if (!existingInput) {
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = 'remove_' + mediaType;
                input.value = 'true';
                mediaContainer.appendChild(input);
            }
            
            // Update UI
            const noMediaDiv = document.createElement('div');
            noMediaDiv.className = 'no-media';
            noMediaDiv.innerHTML = '<i class="fas fa-image"></i><p>No media attached</p>';
            mediaContainer.insertBefore(noMediaDiv, mediaContainer.firstChild);
            
            // Hide actions since media is removed
            this.closest('.media-actions').style.display = 'none';
        });
    });
    
    // Preview new media before upload
    document.querySelectorAll('input[name="new_image"], input[name="new_video"]').forEach(input => {
        input.addEventListener('change', function() {
            const file = this.files[0];
            if (!file) return;
            
            const mediaContainer = document.createElement('div');
            mediaContainer.className = 'current-media';
            
            if (file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const img = document.createElement('img');
                    img.src = e.target.result;
                    img.className = 'current-image';
                    mediaContainer.appendChild(img);
                    
                    const actionsDiv = document.createElement('div');
                    actionsDiv.className = 'media-actions';
                    actionsDiv.innerHTML = `
                        <button type="button" class="remove-media-btn" data-media-type="new_${input.name}">
                            <i class="fas fa-trash"></i> Remove
                        </button>
                    `;
                    mediaContainer.appendChild(actionsDiv);
                    
                    // Insert before the media-options div
                    const mediaOptions = document.querySelector('.media-options');
                    mediaOptions.parentNode.insertBefore(mediaContainer, mediaOptions);
                };
                reader.readAsDataURL(file);
            } else if (file.type.startsWith('video/')) {
                const video = document.createElement('video');
                video.controls = true;
                video.className = 'current-video';
                video.src = URL.createObjectURL(file);
                mediaContainer.appendChild(video);
                
                const actionsDiv = document.createElement('div');
                actionsDiv.className = 'media-actions';
                actionsDiv.innerHTML = `
                    <button type="button" class="remove-media-btn" data-media-type="new_${input.name}">
                        <i class="fas fa-trash"></i> Remove
                    </button>
                `;
                mediaContainer.appendChild(actionsDiv);
                
                // Insert before the media-options div
                const mediaOptions = document.querySelector('.media-options');
                mediaOptions.parentNode.insertBefore(mediaContainer, mediaOptions);
            }
            
            // Clear the input so the same file can be selected again if needed
            this.value = '';
        });
    });
});