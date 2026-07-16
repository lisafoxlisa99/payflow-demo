document.addEventListener('DOMContentLoaded', function () {
  loadMetrics();
  loadTransactions('');

  document.getElementById('txn-search-btn').addEventListener('click', function () {
    loadTransactions(document.getElementById('txn-search').value.trim());
  });
  document.getElementById('txn-search').addEventListener('keydown', function (e) {
    if (e.key === 'Enter') loadTransactions(this.value.trim());
  });
});

function loadMetrics() {
  fetch('/api/metrics')
    .then(function (r) { return r.json(); })
    .then(function (m) {
      var cards = document.querySelectorAll('#metric-cards .metric-card');
      cards[0].innerHTML = '<div class="label">Volume (30d)</div><div class="value">$' + m.volume_30d.toLocaleString() + '</div><div class="trend trend--up">↑ ' + m.volume_trend + '%</div>';
      cards[1].innerHTML = '<div class="label">Success rate</div><div class="value">' + m.success_rate + '%</div><div class="trend trend--up">↑ 0.4%</div>';
      cards[2].innerHTML = '<div class="label">Disputes</div><div class="value">' + m.disputes + '</div><div class="trend trend--down">↓ 2</div>';
      cards[3].innerHTML = '<div class="label">Payouts pending</div><div class="value">$' + m.payouts_pending.toLocaleString() + '</div>';
    });
}

function loadTransactions(query) {
  var wrap = document.getElementById('txn-table-wrap');
  wrap.innerHTML = '<div class="dash__loading">Loading transactions…</div>';
  var url = '/api/transactions' + (query ? ('?q=' + encodeURIComponent(query)) : '');

  fetch(url)
    .then(function (r) { return r.json(); })
    .then(function (rows) {
      if (!rows.length) {
        wrap.innerHTML = '<div class="dash__loading">No transactions match that search.</div>';
        return;
      }
      var html = '<table class="txn-table"><thead><tr>' +
        '<th>ID</th><th>Customer</th><th>Amount</th><th>Status</th><th>Date</th>' +
        '</tr></thead><tbody>';
      rows.forEach(function (t) {
        html += '<tr>' +
          '<td><a class="txn-id" href="transaction.html?id=' + encodeURIComponent(t.id) + '">' + t.id + '</a></td>' +
          '<td>' + t.customer + '</td>' +
          '<td>$' + t.amount.toFixed(2) + '</td>' +
          '<td><span class="pill pill--' + t.status + '">' + t.status + '</span></td>' +
          '<td>' + t.created_at + '</td>' +
          '</tr>';
      });
      html += '</tbody></table>';
      wrap.innerHTML = html;
    })
    .catch(function () {
      wrap.innerHTML = '<div class="dash__loading">Could not load transactions.</div>';
    });
}
