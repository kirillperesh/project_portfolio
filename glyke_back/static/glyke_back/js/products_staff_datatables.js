$(document).ready(function() {
    $('#products_staff_table').DataTable( {
        dom: 'Blfrtip',
        "pagingType": "full_numbers",
        scrollX: true,
        "lengthMenu": [ [25, 50, 100, -1], [25, 50, 100, "All"]],
        buttons: [
            'colvis'
        ],

        initComplete: function () {
            this.api().columns().every( function () {
                var column = this;
                var select = $('<select style="width: 100%;" class="col-filter"><option value=""></option></select>')
                    .appendTo( $(column.footer()).empty() )
                    .on( 'change', function () {
                        var val = $.fn.dataTable.util.escapeRegex(
                            $(this).val()
                        );

                        column
                            .search( val ? '^'+val+'$' : '', true, false )
                            .draw();
                    } );

                column.data().unique().sort().each( function ( d, j ) {
                    select.append( '<option value="'+d+'">'+d+'</option>' )
                } );
            } );
        }


    } );

} );