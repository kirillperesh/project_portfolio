
window.onload = function() {
    var other_photos_containers = document.getElementsByClassName('other-photos-container')
    for (container of other_photos_containers) {
        if (container.children.length > 3) {
            container.removeChild(container.lastElementChild);
        }
    }
}