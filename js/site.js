(function(){
  var links=[].slice.call(document.querySelectorAll('a[data-lb]'));
  if(!links.length) return;
  var box=document.createElement('div');box.className='lb';box.setAttribute('role','dialog');box.setAttribute('aria-label','Photo viewer');
  box.innerHTML='<button class="x" aria-label="Close">×</button><button class="p" aria-label="Previous">‹</button><img alt=""><button class="n" aria-label="Next">›</button>';
  document.body.appendChild(box);
  var img=box.querySelector('img'),i=0;
  function show(k){i=(k+links.length)%links.length;img.src=links[i].href;img.alt=links[i].querySelector('img').alt;box.classList.add('open');}
  function hide(){box.classList.remove('open');img.removeAttribute('src');}
  links.forEach(function(a,k){a.addEventListener('click',function(e){e.preventDefault();show(k);});});
  box.querySelector('.x').onclick=hide;box.querySelector('.p').onclick=function(){show(i-1)};box.querySelector('.n').onclick=function(){show(i+1)};
  box.addEventListener('click',function(e){if(e.target===box)hide();});
  document.addEventListener('keydown',function(e){if(!box.classList.contains('open'))return;
    if(e.key==='Escape')hide();else if(e.key==='ArrowLeft')show(i-1);else if(e.key==='ArrowRight')show(i+1);});
})();
