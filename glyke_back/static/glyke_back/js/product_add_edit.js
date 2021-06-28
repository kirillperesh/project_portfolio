
var previewImages = function(event) {
    var image_list = document.getElementById('img-preview-container');
    if (image_list.firstChild.textContent == 'Uploaded images preview will apper here') {image_list.removeChild(image_list.firstChild)};
    main_loop:
    for (file of event.target.files) {
        for (div_img of image_list.children) {
            if (file.name == div_img.alt) {continue main_loop;}};
        var elem = document.createElement("img");
        elem.src = URL.createObjectURL(file);
        elem.className = "img-preview";
        elem.alt = file.name;
        image_list.appendChild(elem)
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



    // if (img.classList.contains('img-to-delete')){
    //     img.classList.remove('img-to-delete')
    //     event.target.className = 'fas fa-times trans02s remove-photo-toggle'
    //     console.log(photos_to_delete.value)
    // } else {
    //     img.classList.add('img-to-delete')
    //     event.target.className = 'fas fa-recycle trans02s remove-photo-toggle restore-photo'
    //     if (photos_to_delete.value) {var temp_thing = [photos_to_delete.value,]} else {var temp_thing = []}
    //     temp_thing.push(img_id)
    //     photos_to_delete.setAttribute('value', temp_thing);
    //     console.log(photos_to_delete.value)

    // }
}



