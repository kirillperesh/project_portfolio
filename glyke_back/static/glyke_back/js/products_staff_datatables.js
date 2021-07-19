$(document).ready(function() {
    $('#products_staff_table').DataTable( {
        "pagingType": "full_numbers",
        scrollX: true,
        "lengthMenu": [ [25, 50, 100, -1], [25, 50, 100, "All"]],

    } );
} );