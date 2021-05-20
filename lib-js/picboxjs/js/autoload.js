if (!/android|iphone|ipod|series60|symbian|windows ce|blackberry/i.test(navigator.userAgent)) {
	jQuery(function($) {
		$("a[href]").filter(function() {
			return /\.(jpg|png|gif)$/i.test(this.href);
		}).picbox({}, null, function(el) {
			return (this == el) || (this.parentNode && (this.parentNode == el.parentNode));
		});
	});
}
