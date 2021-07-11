var update_active_photo = function(event, photo_image_url) {
    var active_photo_a = document.getElementById('active_photo_id')
    var active_photo_img = document.getElementById('active_photo_img')
    active_photo_a.setAttribute('href', photo_image_url)
    active_photo_img.setAttribute('src', photo_image_url)
}