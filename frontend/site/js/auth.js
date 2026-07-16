// Trivial demo auth — any credentials succeed. No real security boundary.
document.addEventListener('DOMContentLoaded', function () {
  var signupForm = document.getElementById('signup-form');
  if (signupForm) {
    signupForm.addEventListener('submit', function (e) {
      e.preventDefault();
      var okMsg = document.getElementById('msg-ok');
      var errMsg = document.getElementById('msg-err');
      fetch('/api/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company: document.getElementById('company').value,
          email: document.getElementById('email').value,
        }),
      })
        .then(function (res) { return res.json(); })
        .then(function () {
          okMsg.style.display = 'block';
          errMsg.style.display = 'none';
          setTimeout(function () { window.location.href = 'dashboard.html'; }, 900);
        })
        .catch(function () {
          errMsg.style.display = 'block';
        });
    });
  }

  var loginForm = document.getElementById('login-form');
  if (loginForm) {
    loginForm.addEventListener('submit', function (e) {
      e.preventDefault();
      var errMsg = document.getElementById('msg-err');
      fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: document.getElementById('email').value,
          password: document.getElementById('password').value,
        }),
      })
        .then(function (res) { return res.json(); })
        .then(function () {
          window.location.href = 'dashboard.html';
        })
        .catch(function () {
          errMsg.style.display = 'block';
        });
    });
  }
});
