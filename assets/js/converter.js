(function () {
  var go = document.getElementById('go'); if (!go) return;
  var PY = 400 / 121;
  function fmt(x) { return (Math.round(x * 100) / 100).toLocaleString('ko-KR'); }
  go.addEventListener('click', function () {
    var v = parseFloat(document.getElementById('v').value), d = document.getElementById('d').value, o = document.getElementById('out');
    if (!isFinite(v)) { o.textContent = '숫자를 입력해 주세요.'; return; }
    o.innerHTML = d === 'p2m' ? '<b>' + fmt(v) + '평</b> = <b>' + fmt(v * PY) + '㎡</b>' : '<b>' + fmt(v) + '㎡</b> = <b>' + fmt(v / PY) + '평</b>';
  });
})();
