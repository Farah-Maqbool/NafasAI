function switchTab(tab) {
  document.getElementById('form-login').classList.toggle('hidden', tab !== 'login');
  document.getElementById('form-signup').classList.toggle('hidden', tab !== 'signup');
  document.getElementById('tab-login').classList.toggle('active', tab === 'login');
  document.getElementById('tab-signup').classList.toggle('active', tab !== 'login');
}

function showError(id, msg) {
  document.getElementById(id).textContent = msg;
}

function saveSession(data) {
  localStorage.setItem('nafasai_token', data.token);
  localStorage.setItem('nafasai_user', JSON.stringify({
    name: data.name,
    default_city: data.default_city,
    health_profile: data.health_profile
  }));
}

async function handleLogin() {
  const email    = document.getElementById('login-email').value.trim();
  const password = document.getElementById('login-password').value.trim();
  showError('login-error', '');

  if (!email || !password) {
    showError('login-error', 'Please fill in all fields');
    return;
  }

  const btn = document.getElementById('login-btn');
  btn.disabled = true;
  btn.textContent = 'Signing in...';

  try {
    const res  = await fetch('/api/login', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ email, password })
    });
    const data = await res.json();

    if (data.success) {
      saveSession(data);
      window.location.href = '/';
    } else {
      showError('login-error', data.error || 'Login failed');
    }
  } catch (e) {
    showError('login-error', 'Connection error. Please try again.');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Sign In';
  }
}

async function handleSignup() {
  const name    = document.getElementById('signup-name').value.trim();
  const email   = document.getElementById('signup-email').value.trim();
  const password = document.getElementById('signup-password').value.trim();
  const city    = document.getElementById('signup-city').value;
  const profile = document.getElementById('signup-profile').value;
  showError('signup-error', '');

  if (!name || !email || !password) {
    showError('signup-error', 'Please fill in all fields');
    return;
  }
  if (password.length < 6) {
    showError('signup-error', 'Password must be at least 6 characters');
    return;
  }

  const btn = document.getElementById('signup-btn');
  btn.disabled = true;
  btn.textContent = 'Creating account...';

  try {
    const res  = await fetch('/api/signup', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({
        name, email, password,
        default_city: city,
        health_profile: profile
      })
    });
    const data = await res.json();

    if (data.success) {
      saveSession(data);
      window.location.href = '/';
    } else {
      showError('signup-error', data.error || 'Signup failed');
    }
  } catch (e) {
    showError('signup-error', 'Connection error. Please try again.');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Create Account';
  }
}