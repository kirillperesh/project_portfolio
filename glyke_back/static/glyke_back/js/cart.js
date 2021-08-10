


$(document).ready(function() {
    $('#cart_table').DataTable( {
        dom: '',
        "lengthMenu": [ [-1], ["All"]],
    } );

    $("[id^=quantity_]").bind('keyup mouseup', function (event) {
        // update total per position
        current_value = parseInt(event.target.value)
        max_value = parseInt(event.target.max)
        if (current_value < 0) { event.target.value = 0 }
        else if (current_value > max_value) { event.target.value = max_value }
        cart_row_id = event.target.parentElement.parentElement.id;
        var row_number = /cart_row_(.*)/.exec(cart_row_id)[1];
        product_end_user_price = document.getElementById('product_' + row_number + '_end_user_price');
        total_end_user_price = document.getElementById('order_line_' + row_number + '_end_user_price');
        total_end_user_price.innerHTML = (parseFloat(product_end_user_price.innerHTML) * current_value).toFixed(2)

        //update total per order
        order_total_end_user_price = parseFloat(0)
        for (total_per_row of $("[id^=order_line_]")) {order_total_end_user_price += parseFloat(total_per_row.innerHTML)}

        if (order_total_end_user_price > 9999.99) {
            current_value = event.target.value = event.target.defaultValue

            // total_end_user_price = document.getElementById('order_line_' + row_number + '_end_user_price');
            total_end_user_price.innerHTML = (parseFloat(product_end_user_price.innerHTML) * current_value).toFixed(2)

            order_total_end_user_price = parseFloat(0)
            for (total_per_row of $("[id^=order_line_]")) {order_total_end_user_price += parseFloat(total_per_row.innerHTML)}
            alert('Total price exceeds 9999 $')
        }
        for (cart_total of $('[id^=cart_price]')) {cart_total.innerHTML = order_total_end_user_price}
        // TODO finish this part

    });

    var delete_cart_row = function(cart_row_id) {
        var cart_row = document.getElementById(cart_row_id)
        cart_row.remove()
    }

} );

