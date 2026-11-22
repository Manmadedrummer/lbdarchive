(function($){
	var closeTimer  = null;
	var curMenuItem = null;
	var type        = null;
	var config      = {};

	$.fn.zoogleNav = function(options) {
			config = $.extend({}, $.fn.zoogleNav.defaults, options);
			
			if( $(this).hasClass('navMenuVertical') ) {
				type = $.fn.zoogleNav.TypeVertical;
			} else {
				type = $.fn.zoogleNav.TypeHorizontal;
			}
			
			return this.each(function() {
				var $topLevel = $(this);
				var els = $topLevel.children('li');
				if( type !=  $.fn.zoogleNav.TypeVertical ) {
					layoutZoogleNav( $topLevel, els );
				}

				$(els).each( function(i,val) {
					var $this = $(this);
					$this.css( 'zIndex', 100 - i );
					
					var img = $this.find('img');
					if(img.length > 0) {
						var hoverSrc = img.attr('src').replace('.' + config.imageSuffix, '-over.' + config.imageSuffix);
						$("<img>").attr("src", hoverSrc).appendTo('body').css({display: 'none'});
					}
					
					var ul = $this.find('ul');
					var maxWidth = 0;
					$('li', ul).each( function() {
						var w = $(this).width();
						if( w > maxWidth ) maxWidth = w;
					}).each( function() {
						$(this).width( maxWidth );
					});
					
					ul.width(maxWidth);
					
					if( ul.length != 0 ) {
						if( type == $.fn.zoogleNav.TypeHorizontal ) {
							var width = Math.max( $this.innerWidth(), ul.width() );
							ul.css({
								'left' : Math.ceil(( $this.innerWidth() - width ) / 2 ) + 'px',
								/* 'top' removed to allow CSS to handle positioning */
								'width': width + 'px'
							});
						}
					}
					$this.hover(openMenu, startCloseTimer);
				});
			});
	};
	
	function setNavActivation(isOpen) {
		var ulVis = (isOpen) ? 'visible' : 'hidden';
		if (curMenuItem) {
			var img = curMenuItem.find('img');
			var suffix = '.' + config.imageSuffix;
			var swap = [suffix, '-over' + suffix];
			if( !isOpen ) swap.reverse();
			
			if(img.length > 0) {
				img.attr('src', img.attr('src').replace( swap[0], swap[1] ) );
			}
			curMenuItem.find('ul').css('visibility', ulVis );
		}
	}
	
	function openMenu() {
		cancelTimer();
		closeMenu();
		curMenuItem = $(this);
		setNavActivation( true );
	}
	
	function closeMenu() {
		if(curMenuItem) {
			setNavActivation( false );
			curMenuItem = null;
		}
	}
	
	function startCloseTimer() {
		closeTimer = window.setTimeout( closeMenu, config.timeout );
	}
	
	function cancelTimer() {
		if(closeTimer) {
			window.clearTimeout(closeTimer);
			closeTimer = null;
		}
	}

	$.fn.zoogleNav.TypeHorizontal = 'horizontal';
	$.fn.zoogleNav.TypeVertical   = 'vertical';
	$.fn.zoogleNav.defaults = {
		timeout: 500,
		imageSuffix: 'png'
	};
})(jQuery);

function layoutZoogleNav($topLevel, els) {
	var $ = jQuery;
	var maxWidth = $topLevel.parent().width();
	var rows = [{width:0,children:[]}];
	var cur = 0;
	
	els.each(function(i) {
		var $li = $(this);
		var tW  = $li.outerWidth(true);
		if( rows[cur].width + tW > maxWidth ) {
			cur++;
			rows.push({width:0,children:[]});
		}
		rows[cur].width += tW;
		rows[cur].children.push( $li );
	});
	
	$(rows).each(function() {
		var t = $topLevel.clone().empty();
		$(this.children).each(function() { t.append( this ); } );
		t.css({
			'padding': '0 ' + Math.max(0, (maxWidth - this.width)/2) + 'px',
			'clear': 'left'
		});
		$topLevel.before( t );
	});
	$topLevel.remove();
}