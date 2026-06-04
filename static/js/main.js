// ProPortfolio - Main JS

document.addEventListener('DOMContentLoaded', function() {
  // Auto-dismiss messages after 4s
  setTimeout(() => {
    document.querySelectorAll('.message-item').forEach(el => {
      el.style.opacity = '0';
      el.style.transform = 'translateX(100%)';
      setTimeout(() => el.remove(), 300);
    });
  }, 4000);
});

// CSRF helper for AJAX
function getCsrfToken() {
  return document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
    document.cookie.split('; ').find(r => r.startsWith('csrftoken='))?.split('=')[1];
}

// Generic AJAX POST helper
async function apiPost(url, data) {
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCsrfToken(),
      'X-Requested-With': 'XMLHttpRequest',
    },
    body: JSON.stringify(data),
  });
  return response.json();
}

// Auto-save portfolio content sections
function initAutoSave(sectionName, formId) {
  const form = document.getElementById(formId);
  if (!form) return;
  let timer;
  form.addEventListener('input', () => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      const content = {};
      form.querySelectorAll('[data-field]').forEach(el => {
        content[el.dataset.field] = el.value;
      });
      apiPost(window.location.href, { section: sectionName, content })
        .then(data => {
          if (data.status === 'success') console.log(`${sectionName} auto-saved`);
        });
    }, 2000);
  });
}
