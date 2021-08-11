

var delete_cart_row = function(cart_row_id) {
    var cart_row = document.getElementById(cart_row_id)
    cart_row.remove()
}


$(document).ready(function() {
    $('#cart_table').DataTable( {
        dom: '',
        "lengthMenu": [ [-1], ["All"]],
    } );

    $("[id^=quantity_]").bind('keyup mouseup', function (event) { // update total price per position
        current_value = parseInt(event.target.value) // entered quantity value
        max_value = parseInt(event.target.max) // max quantity value
        if (current_value < 0) { event.target.value = 0 }
        else if (current_value > max_value) { event.target.value = max_value }
        cart_row_id = event.target.parentElement.parentElement.id;
        var row_number = /cart_row_(.*)/.exec(cart_row_id)[1];
        product_end_user_price = document.getElementById('product_' + row_number + '_end_user_price'); // end price of the current product per piece
        total_end_user_price = document.getElementById('order_line_' + row_number + '_end_user_price'); // end price of the current product per line

        current_order_total_end_user_price = parseInt(0) // current total cart price
        for (total_per_row of $("[id^=order_line_]")) {current_order_total_end_user_price += parseFloat(total_per_row.innerHTML)}
        new_order_total_end_user_price = (current_order_total_end_user_price - parseFloat(total_end_user_price.innerHTML) + parseFloat(product_end_user_price.innerHTML) * current_value).toFixed(2) // total cart price with entered quantity value

        if (new_order_total_end_user_price > 9999.99) { // if total cart price is over 9999.99, roll back quantity
            current_value = event.target.value = event.target.defaultValue
            new_order_total_end_user_price = (current_order_total_end_user_price - parseFloat(total_end_user_price.innerHTML) + parseFloat(product_end_user_price.innerHTML) * current_value).toFixed(2)
            alert('Total price exceeds 9999.99 $')
        }
        // update all price sums
        total_end_user_price.innerHTML = (parseFloat(product_end_user_price.innerHTML) * current_value).toFixed(2)
        for (cart_total of $('[id^=cart_price]')) {cart_total.innerHTML = new_order_total_end_user_price}
    });

} );

