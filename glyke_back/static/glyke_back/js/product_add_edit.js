var remove_selected_image = function(event) {
    var img_id = event.target.id.slice(0, -5) // removes "_span" in the end
    document.getElementById(img_id + '_id').remove() // removes a tag and its child span tag
    document.getElementById(img_id).remove() // removes img tag
    var file_list = document.getElementById('photosInput').files;
    console.log(file_list)
    console.log(img_id)
    for (file of file_list) {
        if (file.name == img_id) {
            file.value = ''
            console.log(file)
        }
    }
    // TODO doesn't delete the file from list (readonly)

}

var previewImages = function(event) {
    var image_list = document.getElementById('img-preview-container');
    if (image_list.firstChild.textContent == 'Uploaded images preview will apper here') {image_list.removeChild(image_list.firstChild)};
    main_loop:
    for (file of event.target.files) {
        for (div_img of image_list.children) {
            if (file.name == div_img.id) {continue main_loop;}};
        var elem = document.createElement("img");
        elem.setAttribute('src', URL.createObjectURL(file));
        elem.setAttribute('class', "img-preview");
        elem.setAttribute('id', file.name);
        image_list.appendChild(elem);

        var remove_btn_a = document.createElement('a');
        remove_btn_a.setAttribute('onclick', 'remove_selected_image(event)')
        remove_btn_a.setAttribute('id', file.name + '_id')
        image_list.appendChild(remove_btn_a);
        var remove_btn_span = document.createElement('span')
        remove_btn_span.setAttribute('id', file.name + '_span')
        remove_btn_span.setAttribute('class', "fas fa-times trans02s remove-photo-toggle")
        remove_btn_a.appendChild(remove_btn_span)
    };
};

var toggleRemoveCurrentImg = function(event) {
    var img_id = event.target.id.slice(0, -5) // removes "_span" in the end
    // var img = document.getElementById(img_id)
    var to_del_img_id = 'to_del_photo_' + img_id

    if (document.getElementById(to_del_img_id)) {
        document.getElementById(to_del_img_id).remove()
        event.target.className = 'fas fa-times trans02s remove-photo-toggle'
    }
    else {
        var photo_to_delete = document.createElement("input")
        photo_to_delete.setAttribute('id', to_del_img_id)
        photo_to_delete.setAttribute('name', to_del_img_id)
        photo_to_delete.setAttribute('value', img_id)
        photo_to_delete.setAttribute('type', 'hidden')
        document.getElementById('main_product_form').appendChild(photo_to_delete)
        event.target.className = 'fas fa-recycle trans02s remove-photo-toggle restore-photo'
    }
}


