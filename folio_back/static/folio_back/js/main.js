(function($) {

	"use strict";

	var fullHeight = function() {

		$('.js-fullheight').css('height', $(window).height());
		$(window).resize(function(){
			$('.js-fullheight').css('height', $(window).height());
		});

	};
	fullHeight();

	$('#sidebarCollapse').on('click', function () {
      $('#sidebar').toggleClass('active');
	  /*$('#sidebarCollapse').hide();*/
  	});

	$('#sidebar').on('focusout', function () {
		window.setTimeout(function() {
		$('#sidebar').removeClass('active')
	}, 130);
	});

	$('#profile_pannel_collapse').on('click', function () {
		$('#profile_pannel').toggleClass('active');
	});

	$('#profile_pannel').on('focusout', function () {
		window.setTimeout(function() {
		$('#profile_pannel').removeClass('active')
	}, 130);
	});

	$('nav li a[href="/' + location.pathname.split("/")[1] + '"]').parent('li').addClass('active');

})(jQuery);
