// var delete_cart_row = function(cart_row_id) {
//     var cart_row = document.getElementById(cart_row_id)
//     cart_row.remove()
// }

// var check = false;

// function changeVal(el) {
//   var qt = parseFloat(el.parent().children(".qt").html());
//   var price = parseFloat(el.parent().children(".price").html());
//   var eq = Math.round(price * qt * 100) / 100;

//   el.parent().children(".full-price").html( eq + "€" );

//   changeTotal();
// }

// function changeTotal() {

//   var price = 0;

//   $(".full-price").each(function(index){
//     price += parseFloat($(".full-price").eq(index).html());
//   });

//   price = Math.round(price * 100) / 100;
//   var tax = Math.round(price * 0.05 * 100) / 100
//   var shipping = parseFloat($(".shipping span").html());
//   var fullPrice = Math.round((price + tax + shipping) *100) / 100;

//   if(price == 0) {
//     fullPrice = 0;
//   }

//   $(".subtotal span").html(price);
//   $(".tax span").html(tax);
//   $(".total span").html(fullPrice);
// }

$(document).ready(function() {
    // $('#cart_table').DataTable( {
    //     dom: '',
    //     "lengthMenu": [ [-1], ["All"]],
    // } );

    $("[id^=quantity_]").change(function (event) { // update total price per position
        current_value = parseInt(event.target.value) // entered quantity value

        // quantity cannot be more then stock
        stock = $(this).parent().parent().children(".product-stock").children(".stock-number")[0].innerHTML; // number of products available
        if (current_value > stock) {
            event.target.value = stock
            var myModal = new jBox('Modal', {
                title: "Sorry, we're not able to ship more of this product yet",
                content: "Only " + stock + " items available",
                animation: 'zoomIn',
                addClass: 'alert_no_stock',
            });
            myModal.open();
            return;}

        max_value = parseInt(event.target.max) // max quantity value
        if (current_value < 0) { event.target.value = 0 }
        else if (current_value > max_value) { event.target.value = max_value }
        cart_row_id = event.target.parentElement.parentElement.parentElement.id;
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

        // update items_total
        new_items_total = 0
        for (items_number of $("[id^=quantity_]")) {new_items_total += parseInt(items_number.value)}
        for (items_total of $('#cart_items')) {items_total.innerHTML = new_items_total}

    });

    $(".remove").click(function(){
        var el = $(this);
        // this makes total prices and items counters update on remove
        el.parent().parent().children("footer").children(".qt").children("input").val(0).change()
        el.parent().parent().addClass("removed");
        window.setTimeout(
          function(){
            el.parent().parent().slideUp('fast', function() {
              el.parent().parent().remove();
              if($(".product").length == 0) {
                // if(check) {
                //   $("#cart").html("<h1>The shop does not function, yet!</h1><p>If you liked my shopping cart, please take a second and heart this Pen on <a href='https://codepen.io/ziga-miklic/pen/xhpob'>CodePen</a>. Thank you!</p>");
                // } else {
                  $("#cart").html("<h1>No products!</h1>");
                // }
              }
            //   changeTotal();
            });
          }, 200);
      });

      $(".qt-plus").click(function(){
        // $(this).parent().children(".qt").children("input").val(parseInt($(this).parent().children(".qt").children("input").val()) + 1);
        var el = $(this);
        child = el.parent().children(".qt").children("input");

        child.val(parseInt(child.val()) + 1).change();
        el.parent().children(".full-price").addClass("added");
        window.setTimeout(function(){el.parent().children(".full-price").removeClass("added");
        // changeVal(el)
        ;}, 150);
      });

      $(".qt-minus").click(function(){
        var el = $(this);

        child = el.parent().children(".qt").children("input");

        if(parseInt(child.val()) > 1) {child.val(parseInt(child.val()) - 1).change();}

        el.parent().children(".full-price").addClass("minused");
        window.setTimeout(function(){el.parent().children(".full-price").removeClass("minused");
        // changeVal(el);
        }, 150);
      });

      window.setTimeout(function(){$(".is-open").removeClass("is-open")}, 1200);

    //   $(".btn").click(function(){
    //     check = true;
    //     $(".remove").click();
    //   });

} );





