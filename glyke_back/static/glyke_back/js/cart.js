var delete_cart_row = function(cart_row_id) {
    var cart_row = document.getElementById(cart_row_id)
    // console.log(cart_row_id)
    cart_row.remove()
}

// var updateCart = function() {
//     document.getElementById('update_cart').click()
// }




$(document).ready(function() {
    $('#cart_table').DataTable( {
        dom: '',
        "lengthMenu": [ [-1], ["All"]],
    } );
} );

$("[id^=quantity_]").bind('keyup mouseup', function () {
    document.getElementById('update_cart').click();
});