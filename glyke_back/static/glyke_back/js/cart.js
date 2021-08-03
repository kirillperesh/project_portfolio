var delete_cart_row = function(cart_row_id) {
    var cart_row = document.getElementById(cart_row_id)
    console.log(cart_row_id)
    cart_row.remove()
}