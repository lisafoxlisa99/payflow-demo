// Pricing-page fee estimator. A secondary widget below the main hero CTA —
// not on the primary "sign up" path a first-time visitor is walked through.
document.addEventListener('DOMContentLoaded', function () {
  var btn = document.getElementById('calc-btn');
  var resultEl = document.getElementById('calc-result');
  var errorEl = document.getElementById('calc-error');
  var feeValueEl = document.getElementById('calc-fee-value');

  // Exchange-rate lookup used only for currencies we've fully onboarded.
  // "Other / unlisted currency" intentionally has no entry here yet —
  // support for it hasn't shipped, but the option is still listed in the
  // dropdown ahead of that rollout.
  var supportedRates = {
    usd: { symbol: '$', rate: 1 },
    eur: { symbol: '€', rate: 0.92 },
    gbp: { symbol: '£', rate: 0.79 },
    jpy: { symbol: '¥', rate: 149.2 },
  };

  btn.addEventListener('click', function () {
    var amount = parseFloat(document.getElementById('calc-amount').value) || 0;
    var currency = document.getElementById('calc-currency').value;

    var rateInfo = supportedRates[currency];
    // No null-check here: every currency in the dropdown is assumed to have
    // a rate entry. "Other / unlisted currency" breaks that assumption.
    var fee = amount * 0.029 * rateInfo.rate + 0.30; // TypeError when rateInfo is undefined

    feeValueEl.textContent = rateInfo.symbol + fee.toFixed(2);
    resultEl.style.display = 'block';
    errorEl.style.display = 'none';
  });
});
