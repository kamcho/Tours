// Like/Unlike functionality
function likeTour(tourId) {
    if (!isAuthenticated) {
        showLoginModal();
        return;
    }
    
    fetch(`/listings/tour/${tourId}/like/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showNotification(data.error, 'error');
        } else {
            updateLikeUI(tourId, data.liked, data.total_likes);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('An error occurred while processing your request.', 'error');
    });
}

function likeEvent(eventId) {
    if (!isAuthenticated) {
        showLoginModal();
        return;
    }
    
    fetch(`/listings/event/${eventId}/like/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showNotification(data.error, 'error');
        } else {
            updateEventLikeUI(eventId, data.liked, data.total_likes);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('An error occurred while processing your request.', 'error');
    });
}

// Bookmark functionality
function bookmarkTour(tourId) {
    if (!isAuthenticated) {
        showLoginModal();
        return;
    }
    
    fetch(`/listings/tour/${tourId}/bookmark/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showNotification(data.error, 'error');
        } else {
            updateBookmarkUI(tourId, data.bookmarked, data.total_bookmarks);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('An error occurred while processing your request.', 'error');
    });
}

function bookmarkEvent(eventId) {
    if (!isAuthenticated) {
        showLoginModal();
        return;
    }
    
    fetch(`/listings/event/${eventId}/bookmark/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showNotification(data.error, 'error');
        } else {
            updateEventBookmarkUI(eventId, data.bookmarked, data.total_bookmarks);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('An error occurred while processing your request.', 'error');
    });
}

// Comment functionality
function addTourComment(tourId) {
    if (!isAuthenticated) {
        showLoginModal();
        return;
    }
    
    const commentInput = document.getElementById(`tour-comment-input-${tourId}`);
    const content = commentInput.value.trim();
    
    if (!content) {
        showNotification('Please enter a comment before posting.', 'warning');
        return;
    }
    
    // Create FormData object
    const formData = new FormData();
    formData.append('content', content);
    
    fetch(`/listings/tour/${tourId}/comment/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showNotification(data.error, 'error');
        } else if (data.success) {
            // Clear the input
            commentInput.value = '';
            
            // Add comment to UI
            addCommentToUI(tourId, data, 'tour');
            
            showNotification('Comment posted successfully!', 'success');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('An error occurred while posting your comment.', 'error');
    });
}

function addEventComment(eventId) {
    if (!isAuthenticated) {
        showLoginModal();
        return;
    }
    
    const commentInput = document.getElementById(`event-comment-input-${eventId}`);
    const content = commentInput.value.trim();
    
    if (!content) {
        showNotification('Please enter a comment before posting.', 'warning');
        return;
    }
    
    // Create FormData object
    const formData = new FormData();
    formData.append('content', content);
    
    fetch(`/listings/event/${eventId}/comment/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showNotification(data.error, 'error');
        } else if (data.success) {
            // Clear the input
            commentInput.value = '';
            
            // Add comment to UI
            addCommentToUI(eventId, data, 'event');
            
            showNotification('Comment posted successfully!', 'success');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('An error occurred while posting your comment.', 'error');
    });
}

// Booking functionality
function bookTour(tourId) {
    if (!isAuthenticated) {
        showLoginModal();
        return;
    }
    
    const participants = document.getElementById(`tour-participants-${tourId}`).value;
    const specialRequests = document.getElementById(`tour-special-requests-${tourId}`).value;
    
    if (!participants || participants < 1) {
        showNotification('Please enter a valid number of participants.', 'warning');
        return;
    }
    
    fetch(`/listings/tour/${tourId}/book/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            participants: participants,
            special_requests: specialRequests 
        }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showNotification(data.error, 'error');
        } else {
            showNotification(data.message, 'success');
            // Close modal or redirect
            closeBookingModal(tourId);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('An error occurred while processing your booking.', 'error');
    });
}

function bookEvent(eventId) {
    if (!isAuthenticated) {
        showLoginModal();
        return;
    }
    
    const participants = document.getElementById(`event-participants-${eventId}`).value;
    const specialRequests = document.getElementById(`event-special-requests-${eventId}`).value;
    
    if (!participants || participants < 1) {
        showNotification('Please enter a valid number of participants.', 'warning');
        return;
    }
    
    fetch(`/listings/event/${eventId}/book/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            participants: participants,
            special_requests: specialRequests 
        }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showNotification(data.error, 'error');
        } else {
            showNotification(data.message, 'success');
            // Close modal or redirect
            closeBookingModal(eventId);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('An error occurred while processing your booking.', 'error');
    });
}

// UI Update Functions
function updateLikeUI(tourId, liked, totalLikes) {
    const likeBtn = document.getElementById(`tour-like-btn-${tourId}`);
    const likeCount = document.getElementById(`tour-like-count-${tourId}`);
    
    if (likeBtn && likeCount) {
        if (liked) {
            likeBtn.classList.add('text-red-500');
            likeBtn.classList.remove('text-gray-400');
        } else {
            likeBtn.classList.remove('text-red-500');
            likeBtn.classList.add('text-gray-400');
        }
        likeCount.textContent = totalLikes;
    }
}

function updateEventLikeUI(eventId, liked, totalLikes) {
    const likeBtn = document.getElementById(`event-like-btn-${eventId}`);
    const likeCount = document.getElementById(`event-like-count-${eventId}`);
    
    if (likeBtn && likeCount) {
        if (liked) {
            likeBtn.classList.add('text-red-500');
            likeBtn.classList.remove('text-gray-400');
        } else {
            likeBtn.classList.remove('text-red-500');
            likeBtn.classList.add('text-gray-400');
        }
        likeCount.textContent = totalLikes;
    }
}

function updateBookmarkUI(tourId, bookmarked, totalBookmarks) {
    const bookmarkBtn = document.getElementById(`tour-bookmark-btn-${tourId}`);
    const bookmarkCount = document.getElementById(`tour-bookmark-count-${tourId}`);
    
    if (bookmarkBtn && bookmarkCount) {
        if (bookmarked) {
            bookmarkBtn.classList.add('text-yellow-500');
            bookmarkBtn.classList.remove('text-gray-400');
        } else {
            bookmarkBtn.classList.remove('text-yellow-500');
            bookmarkBtn.classList.add('text-gray-400');
        }
        bookmarkCount.textContent = totalBookmarks;
    }
}

function updateEventBookmarkUI(eventId, bookmarked, totalBookmarks) {
    const bookmarkBtn = document.getElementById(`event-bookmark-btn-${eventId}`);
    const bookmarkCount = document.getElementById(`event-bookmark-count-${eventId}`);
    
    if (bookmarkBtn && bookmarkCount) {
        if (bookmarked) {
            bookmarkBtn.classList.add('text-yellow-500');
            bookmarkBtn.classList.remove('text-gray-400');
        } else {
            bookmarkBtn.classList.remove('text-yellow-500');
            bookmarkBtn.classList.add('text-gray-400');
        }
        bookmarkCount.textContent = totalBookmarks;
    }
}

function addCommentToUI(itemId, commentData, type) {
    const commentsContainer = document.getElementById(`${type}-comments-${itemId}`);
    if (!commentsContainer) return;
    
    const commentHTML = `
        <div class="bg-gray-50 rounded-lg p-4 mb-4">
            <div class="flex items-start justify-between mb-2">
                <div class="flex items-center gap-2">
                    <div class="w-8 h-8 bg-${type === 'tour' ? 'emerald' : 'blue'}-100 rounded-full flex items-center justify-center">
                        <svg class="w-4 h-4 text-${type === 'tour' ? 'emerald' : 'blue'}-600" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-6-3a2 2 0 11-4 0 2 2 0 014 0zm-2 4a5 5 0 00-4.546 2.916A5.986 5.986 0 0010 16a5.986 5.986 0 004.546-2.084A5 5 0 0010 11z" clip-rule="evenodd"/>
                        </svg>
                    </div>
                    <span class="font-semibold text-gray-800">${commentData.user_email}</span>
                </div>
                <span class="text-sm text-gray-500">${commentData.created_at}</span>
            </div>
            <p class="text-gray-700">${commentData.content}</p>
        </div>
    `;
    
    commentsContainer.insertAdjacentHTML('afterbegin', commentHTML);
}

// Utility Functions
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

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg transition-all duration-300 transform translate-x-full`;
    
    let bgColor, textColor, icon;
    switch (type) {
        case 'success':
            bgColor = 'bg-green-500';
            textColor = 'text-white';
            icon = '✓';
            break;
        case 'error':
            bgColor = 'bg-red-500';
            textColor = 'text-white';
            icon = '✗';
            break;
        case 'warning':
            bgColor = 'bg-yellow-500';
            textColor = 'text-white';
            icon = '⚠';
            break;
        default:
            bgColor = 'bg-blue-500';
            textColor = 'text-white';
            icon = 'ℹ';
    }
    
    notification.className += ` ${bgColor} ${textColor}`;
    notification.innerHTML = `
        <div class="flex items-center gap-2">
            <span class="text-lg">${icon}</span>
            <span>${message}</span>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.classList.remove('translate-x-full');
    }, 100);
    
    // Remove after 5 seconds
    setTimeout(() => {
        notification.classList.add('translate-x-full');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 5000);
}

function showLoginModal() {
    showNotification('Please log in to perform this action.', 'warning');
    // Don't redirect - let the user stay on the current page
}

function closeBookingModal(itemId) {
    const modal = document.getElementById(`booking-modal-${itemId}`);
    if (modal) {
        modal.classList.add('hidden');
    }
}

function openBookingModal(itemId) {
    const modal = document.getElementById(`booking-modal-${itemId}`);
    if (modal) {
        modal.classList.remove('hidden');
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Check if user is authenticated (set by Django template)
    if (typeof window.isAuthenticated === 'undefined') {
        window.isAuthenticated = false;
    }
}); 