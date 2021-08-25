
var reset_uploaded_images = function(event) {
    document.getElementById('photosInput').value = null;
    var image_preview_container = document.getElementById('img-preview-container');
    image_preview_container.innerHTML = ''
    image_preview_container.textContent = 'Uploaded images preview will apper here';
}

var set_class_for_all_uploaded_images = function(new_class) {
    var image_preview_container_children = document.getElementById('img-preview-container').children;
    for (image of image_preview_container_children) {
        image.setAttribute('class', new_class);
    }
}

var previewImages = function(event) {
    var image_preview_container = document.getElementById('img-preview-container');
    if (image_preview_container.firstChild.textContent == 'Uploaded images preview') {image_preview_container.removeChild(image_preview_container.firstChild)};
    main_loop:
    for (file of event.target.files) {
        for (div_img of image_preview_container.children) {
            if (file.name == div_img.id) {continue main_loop;}};
        var elem = document.createElement("img");
        elem.setAttribute('src', URL.createObjectURL(file));
        elem.setAttribute('class', "img-preview");
        elem.setAttribute('id', file.name);
        image_preview_container.appendChild(elem);

        // // adds a 'remove' button
        // var remove_btn_a = document.createElement('a');
        // remove_btn_a.setAttribute('onclick', 'remove_selected_image(event)')
        // remove_btn_a.setAttribute('id', file.name + '_id')
        // image_preview_container.appendChild(remove_btn_a);
        // var remove_btn_span = document.createElement('span')
        // remove_btn_span.setAttribute('id', file.name + '_span')
        // remove_btn_span.setAttribute('class', "fas fa-times trans02s remove-photo-toggle")
        // remove_btn_a.appendChild(remove_btn_span)
    };
};

var toggleRemoveCurrentImg = function(event) {
    var img_id = event.target.id.slice(0, -5) // removes "_span" in the end
    var img = document.getElementById(img_id)
    var to_del_img_id = 'to_del_photo_' + img_id

    if (document.getElementById(to_del_img_id)) {
        document.getElementById(to_del_img_id).remove()
        event.target.className = 'fas fa-times trans02s remove-photo-toggle'
        img.className = 'img-preview'
    }
    else {
        var photo_to_delete = document.createElement("input")
        photo_to_delete.setAttribute('id', to_del_img_id)
        photo_to_delete.setAttribute('name', to_del_img_id)
        photo_to_delete.setAttribute('value', img_id)
        photo_to_delete.setAttribute('type', 'hidden')
        document.getElementById('main_product_form').appendChild(photo_to_delete)
        event.target.className = 'fas fa-recycle trans02s remove-photo-toggle restore-photo'
        img.className = 'img-preview img-to-delete'
    }
}

var setMainPhoto = function(event) {
    var main_photo_mark = document.getElementById('main-photo-mark')
    main_photo_mark.classList.add('photo-is-main-updated')
    event.target.parentNode.insertBefore(main_photo_mark, document.getElementById(event.target.id + '_span').parentNode)
    if (document.getElementById('new_main_photo')) {document.getElementById('new_main_photo').remove()}
    var new_main_photo = document.createElement("input")
        new_main_photo.setAttribute('id', 'new_main_photo')
        new_main_photo.setAttribute('name', 'new_main_photo')
        new_main_photo.setAttribute('value', event.target.id)
        new_main_photo.setAttribute('type', 'hidden')
    document.getElementById('main_product_form').appendChild(new_main_photo)
}


new jBox('Confirm', {
    title: 'Confirm deletion/recovery',
    confirmButton: "I'm sure",
    cancelButton: 'Cancel',
    addClass: 'trans02s delete_confirm',
    offset: {x: 0, y:-100},
});