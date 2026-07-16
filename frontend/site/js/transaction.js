document.addEventListener('DOMContentLoaded', function () {
  var params = new URLSearchParams(window.location.search);
  var id = params.get('id');
  var wrap = document.getElementById('txn-detail-wrap');

  if (!id) {
    wrap.innerHTML = '<div class="dash__loading">No transaction specified.</div>';
    return;
  }

  fetch('/api/transactions/' + encodeURIComponent(id))
    .then(function (r) {
      if (!r.ok) {
        return r.json().then(function (body) {
          throw new Error(body.detail || ('Request failed with status ' + r.status));
        });
      }
      return r.json();
    })
    .then(function (t) {
      wrap.innerHTML =
        '<div class="detail-card">' +
        row('Transaction ID', t.id) +
        row('Customer', t.customer) +
        row('Amount', '$' + t.amount.toFixed(2)) +
        row('Status', t.status) +
        row('Created', t.created_at) +
        row('Settled', t.settled_at) +
        row('Settlement time', t.settlement_duration) +
        '</div>';
    })
    .catch(function (err) {
      wrap.innerHTML =
        '<div class="error-banner">This transaction could not be loaded: ' + err.message + '</div>';
    });

  function row(k, v) {
    return '<div class="detail-row"><span class="k">' + k + '</span><span class="v">' + v + '</span></div>';
  }
});
