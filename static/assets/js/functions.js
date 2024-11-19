// liking mechanism for frontend
$(document).ready(function(){

    $(document).on("click", "#like-btn",function(){
        // console.log("liked");

        let button_val = $(this).attr("data-like-btn")

        $.ajax({
            url: "/like-post/",
            dataType: "json",
            data: {
                "id": button_val
            },

            success: function(response) {
                if(response.data.bool === true) {
                    $("#likes-count" + button_val).text(response.data.likes);
                    $(".like-btn" + button_val).addClass("text-blue-500");
                    $(".like-btn" + button_val).removeClass("text-black");
                } else {
                    $("#likes-count" + button_val).text(response.data.likes);
                    $(".like-btn" + button_val).addClass("text-black");
                    $(".like-btn" + button_val).removeClass("text-blue-500");
                }
            }
        })
    })

    //comment frontend logic
})

console.log("hello world")



 //comment frontend logic
 $(document).ready(function() {

    $(document).on("click", "#comment-btn", function(){
        
        let post_id = $(this).attr("data-comment-btn")
        let cmt = $("#comment-input"+post_id).val()
        // console.log(post_id);
        // console.log(cmt);

        $.ajax({
            url: "/comment-post/",
            dataType: "json",
            data: {
                "id": post_id,
                "cmt": cmt
            },
        
            success: function(response) {
                console.log(response);
                let newCommentId = response.data.comment_id;
                let newcomment = '<div class="flex card shadowp-2">\
    <div>\
        <div class="text-gray-700 py-2 px-3 rounded-md bg-gray-100 relative lg:ml-5 ml-2 lg:mr-12  dark:bg-gray-800 dark:text-gray-100">\
            <p class="leading-6"> ' + response.data.username + ' </p>\
            <p class="leading-6">' + response.data.comment + '</p>\
            <div class="absolute w-3 h-3 top-3 -left-1 bg-gray-100 transform rotate-45 dark:bg-gray-800"></div>\
        </div>\
        <div class="text-xs flex items-center space-x-3 mt-2 ml-5">\
            <a id="like-comment-btn" data-like-comment="' + newCommentId + '" class="like-comment' + newCommentId + '" style="color: gray;"  {% endif %}> <i style="cursor: pointer;" id="comment-icon' + newCommentId + '" class=" fas fa-heart  "></i></a> <small><span class="" id="comment-likes-count' + newCommentId + '">0</span></small>\
            <details>\
    <summary>\
        <div class="">Reply</div>\
    </summary>\
    <details-menu role="menu" class="origin-top-right relative right-0 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 focus:outline-none">\
        <div class="py-1" role="none">\
            <div class="p-1 d-flex">\
                <input type="text" class="with-border" name="" id="reply-input' + newCommentId + '">\
                <button id="reply-comment-btn" data-reply-comment-btn="' + newCommentId + '" type="submit" class="reply-comment-btn' + newCommentId + ' block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-gray-900" role="menuitem">\
                    <ion-icon name="send"></ion-icon>\
                </button>\
            </div>\
        </div>\
    </details-menu>\
</details>\
            <span> ' + response.data.date + ' ago </span>\
        </div>\
        <div class="reply-div' + newCommentId + ' mt-4 space-y-4" style="border-left: 2px solid red; padding-left: 10px;"> \
    </div>\
</div>\
' 
$("#comment-div"+post_id).prepend(newcomment)
$("#comment-input"+post_id).val("")
$("#comments-count" + post_id).text(response.data.comment_count);
            } 

        })
    })

 })

//comment liking logic
 $(document).ready(function() {

    $(document).on("click", "#like-comment-btn", function(){
        let cmt_id = $(this).attr("data-like-comment")
        

        $.ajax({
            url: "/comment-like/",
            dataType: "json",
            data: {
                "id": cmt_id,
            },
        
            success: function(response) {
                console.log(response);
                if(response.data.bool === true) {
                    $("#comment-likes-count" + cmt_id).text(response.data.likes);
                    $(".like-comment" + cmt_id).css('color', 'red');
                } else {
                    $("#comment-likes-count" + cmt_id).text(response.data.likes);
                    $(".like-comment" + cmt_id).css('color', 'gray');
                }
            }

        })
    })

 })


 // reply to comment logic
 $(document).ready(function() {
    $(document).on("click", "#reply-comment-btn", function(){
        // console.log("check this if it works ot not")
        let cmt_id= $(this).attr("data-reply-comment-btn")
        let reply= $("#reply-input"+cmt_id).val()
        console.log(cmt_id);
        console.log(reply);
        
        
        $.ajax({
            url: "/comment-reply/",
            dataType: "json",
            data: {
                "id": cmt_id,
                "reply": reply
            },

            success: function(response){
                let newReply = '<div class="flex mr-12" style="margin-right: 20px;">\
    <div>\
        <div class="text-gray-700 py-2 px-3 rounded-md bg-gray-100 relative lg:ml-5 ml-2 lg:mr-12 dark:bg-gray-800 dark:text-gray-100">\
            <p class="leading-6">' + response.data.username + '</p>\
            <p class="leading-6">' + response.data.reply + '</p>\
            <div class="absolute w-3 h-3 top-3 -left-1 bg-gray-100 transform rotate-45 dark:bg-gray-800"></div>\
        </div>\
    </div>\
</div>\
'
$(".reply-div"+cmt_id).prepend(newReply)
$("#reply-input"+cmt_id).val("")
            }
        })
            

    })
 })

































/* <script>
    console.log("hello")
    $(document).ready(function() {
        $("#post-Form").submit(function(event) {
            event.preventDefault(); // Prevent the default form submission

            // Create a FormData object from the form
            var formData = new FormData(this);

            // Send AJAX request
            $.ajax({
                url: '/your-create-post-url/', // Update with your URL
                type: 'POST',
                data: formData, // Use the form data
                processData: false,
                contentType: false,
                success: function (response) {
                    console.log('Response:', response); // Log the response
                    if (response.post) {
                        var newPostHtml = `
                            <div class="card lg:mx-0 uk-animation-slide-bottom-small" id="post-${response.post.id}">
                                <div class="flex justify-between items-center lg:p-4 p-2.5">
                                    <div class="flex flex-1 items-center space-x-4">
                                        <a href="#">
                                            <img src="${response.profile_image}" class="bg-gray-200 border border-white rounded-full w-10 h-10">
                                        </a>
                                        <div class="flex-1 font-semibold capitalize">
                                            <a href="#" class="text-black dark:text-gray-100">${response.post.username}</a>
                                            <div class="category">
                                                <strong>Category:</strong> ${response.post.category}
                                            </div>
                                            <div class="text-gray-700 flex items-center space-x-2">
                                                ${response.post.date} ago
                                            </div>
                                        </div>
                                    </div>
                                    <div>
                                        <a href="#">
                                            <i class="icon-feather-more-horizontal text-2xl hover:bg-gray-200 rounded-full p-2 transition -mr-1 dark:hover:bg-gray-700"></i>
                                        </a>
                                    </div>
                                </div>
            
                                <div uk-lightbox>
                                    <a href="${response.post.image}">  
                                        <img src="${response.post.image}" alt="${response.post.title}" class="max-h-96 w-full object-cover">
                                    </a>
                                </div>
            
                                <div class="p-4 space-y-3">
                                    <h3 class="font-bold text-lg">${response.post.title}</h3>
                                    <p class="text-gray-600 dark:text-gray-100">${response.post.body}</p>
                                    <div class="flex space-x-4 lg:font-bold">
                                        <a href="#" class="flex items-center space-x-2">
                                            <div class="p-2 rounded-full text-black lg:bg-gray-100 dark:bg-gray-600">
                                                <!-- Like icon -->
                                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" width="22" height="22" class="dark:text-gray-100">
                                                    <path d="M2 10.5a1.5 1.5 0 113 0v6a1.5 1.5 0 01-3 0v-6zM6 10.333v5.43a2 2 0 001.106 1.79l.05.025A4 4 0 008.943 18h5.416a2 2 0 001.962-1.608l1.2-6A2 2 0 0015.56 8H12V4a2 2 0 00-2-2 1 1 0 00-1 1v.667a4 4 0 01-.8 2.4L6.8 7.933a4 4 0 00-.8 2.4z"/>
                                                </svg>
                                            </div>
                                            <div>Like</div>
                                        </a>
                                        <a href="#" class="flex items-center space-x-2">
                                            <div class="p-2 rounded-full text-black lg:bg-gray-100 dark:bg-gray-600">
                                                <!-- Comment icon -->
                                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" width="22" height="22" class="dark:text-gray-100">
                                                    <path fill-rule="evenodd" d="M18 5v8a2 2 0 01-2 2h-5l-5 4v-4H4a2 2 0 01-2-2V5a2 2 0 012-2h12a2 2 0 012 2zM7 8H5v2h2V8zm2 0h2v2H9V8zm6 0h-2v2h2V8z" clip-rule="evenodd"/>
                                                </svg>
                                            </div>
                                            <div>Comment</div>
                                        </a>
                                    </div>
                                </div>
                            </div>
                        `;
                        // Append the new post HTML to the posts container
                        $('#posts-container').prepend(newPostHtml); // Adjust selector as needed
                    } else {
                        // Handle errors or display messages
                        alert(response.error);
                    }
                },
                error: function (xhr, status, error) {
                    console.error('AJAX Error:', error);
                    console.log('Response:', xhr.responseText); // Log the response for debugging
                }
            });
        })
    });
</script> */
