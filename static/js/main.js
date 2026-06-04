// ProPortfolio - Main JS

/* =============================================
   Utility Helpers
   ============================================= */

function getCsrfToken() {
  return document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
    document.cookie.split('; ').find(r => r.startsWith('csrftoken='))?.split('=')[1] || '';
}

function escapeHtml(text) {
  return $('<div>').text(String(text)).html();
}

function showToast(message, type) {
  type = type || 'success';
  const isError = type === 'error';
  const bg = isError ? 'bg-error-container text-on-error-container' : 'bg-secondary-container text-on-secondary-container';
  const icon = isError ? 'error' : 'check_circle';
  const $toast = $(`
    <div class="flex items-center gap-sm px-md py-sm rounded-xl shadow-elevation-3 ${bg} pointer-events-auto transition-opacity duration-300 opacity-0 cursor-pointer">
      <span class="material-symbols-outlined text-[18px]">${icon}</span>
      <p class="font-label-md text-label-md">${escapeHtml(message)}</p>
    </div>
  `);
  let $container = $('#toast-container');
  if (!$container.length) {
    $container = $('<div id="toast-container" class="fixed top-4 right-4 flex flex-col gap-sm z-[200] pointer-events-none max-w-xs"></div>');
    $('body').append($container);
  }
  $container.append($toast);
  $toast.on('click', () => $toast.remove());
  setTimeout(() => $toast.css('opacity', '1'), 10);
  setTimeout(() => { $toast.css('opacity', '0'); setTimeout(() => $toast.remove(), 400); }, 4000);
}

function toggleReplyForm(formId) {
  const $wrapper = $('#' + formId);
  $wrapper.toggleClass('hidden');
  if (!$wrapper.hasClass('hidden')) {
    $wrapper.find('textarea').first().focus();
  }
}

function buildReplyHTML(reply) {
  const avatar = reply.avatar
    ? `<img src="${escapeHtml(reply.avatar)}" class="w-8 h-8 rounded-full object-cover" alt="${escapeHtml(reply.username)}">`
    : `<div class="w-8 h-8 rounded-full bg-primary-container flex items-center justify-center font-label-md text-primary">${escapeHtml(reply.username.charAt(0).toUpperCase())}</div>`;

  const upvoteUrl = `/forum/reply/${reply.id}/upvote/`;
  const csrf = escapeHtml(getCsrfToken());

  return `
    <div id="reply-${reply.id}" class="rounded-xl bg-surface-container-low p-md border border-outline-variant">
      <div class="flex items-center gap-sm mb-sm">
        ${avatar}
        <div>
          <p class="font-label-md text-label-md text-on-surface">${escapeHtml(reply.username)}</p>
          <p class="font-body-sm text-body-sm text-on-surface-variant">Just now</p>
        </div>
        <form method="post" class="ml-auto upvote-reply-form" action="${escapeHtml(upvoteUrl)}" data-reply-id="${reply.id}">
          <input type="hidden" name="csrfmiddlewaretoken" value="${csrf}">
          <button type="submit" class="flex items-center gap-xs font-label-sm text-label-sm border border-outline-variant px-xs py-0.5 rounded-full hover:border-primary hover:text-primary transition-colors">
            <span class="material-symbols-outlined text-[14px]">thumb_up</span> <span class="reply-upvote-count">0</span>
          </button>
        </form>
      </div>
      <p class="font-body-md text-body-md text-on-surface whitespace-pre-line">${escapeHtml(reply.content)}</p>
    </div>
  `;
}

/* =============================================
   Legacy helpers (used by portfolio edit views)
   ============================================= */
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

/* =============================================
   jQuery AJAX Handlers
   ============================================= */
$(function () {

  // Global CSRF header for all non-safe jQuery AJAX requests
  $.ajaxSetup({
    beforeSend: function (xhr, settings) {
      if (!(/^(GET|HEAD|OPTIONS|TRACE)$/.test(settings.type)) && !this.crossDomain) {
        xhr.setRequestHeader('X-CSRFToken', getCsrfToken());
        xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
      }
    }
  });

  // Auto-dismiss Django messages
  setTimeout(function () {
    $('.message-item').css({ opacity: '0', transform: 'translateX(100%)' });
    setTimeout(() => $('.message-item').remove(), 300);
  }, 4000);

  /* ---- Thread upvote ---- */
  $('#upvote-thread-form').on('submit', function (e) {
    e.preventDefault();
    const $form = $(this);
    $.post(window.location.href, $form.serialize())
      .done(function (data) {
        if (data.status === 'ok') {
          $('#thread-upvote-count').text(data.count);
          const $btn = $('#thread-upvote-btn');
          const $icon = $('#thread-upvote-icon');
          if (data.upvoted) {
            $btn.addClass('bg-primary-fixed text-primary border-primary');
            $icon.addClass('icon-fill');
            showToast('Upvoted!');
          } else {
            $btn.removeClass('bg-primary-fixed text-primary border-primary');
            $icon.removeClass('icon-fill');
            showToast('Upvote removed.');
          }
        }
      })
      .fail(function () { showToast('Could not upvote. Try again.', 'error'); });
  });

  /* ---- Reply upvote (delegated – works for dynamically added replies) ---- */
  $(document).on('submit', '.upvote-reply-form', function (e) {
    e.preventDefault();
    const $form = $(this);
    $.post($form.attr('action'), $form.serialize())
      .done(function (data) {
        if (data.status === 'ok') {
          $form.find('.reply-upvote-count').text(data.count);
          const $btn = $form.find('button[type="submit"]');
          const $icon = $btn.find('.material-symbols-outlined');
          if (data.upvoted) {
            $btn.addClass('bg-primary-fixed text-primary border-primary');
            $icon.addClass('icon-fill');
          } else {
            $btn.removeClass('bg-primary-fixed text-primary border-primary');
            $icon.removeClass('icon-fill');
          }
        }
      })
      .fail(function () { showToast('Could not upvote reply.', 'error'); });
  });

  /* ---- Flag thread ---- */
  $('#flag-thread-form').on('submit', function (e) {
    e.preventDefault();
    const $form = $(this);
    $.post(window.location.href, $form.serialize())
      .done(function (data) {
        if (data.status === 'ok') {
          showToast('Thread reported for review.');
          $form.find('button[type="submit"]').prop('disabled', true).text('Reported');
        }
      })
      .fail(function () { showToast('Could not report thread.', 'error'); });
  });

  /* ---- Main reply form ---- */
  $('#main-reply-form').on('submit', function (e) {
    e.preventDefault();
    const $form = $(this);
    const $btn = $form.find('button[type="submit"]');
    $btn.prop('disabled', true);
    $.post(window.location.href, $form.serialize())
      .done(function (data) {
        if (data.status === 'ok') {
          $('#replies-list').append(buildReplyHTML(data.reply));
          $form.find('textarea').val('');
          showToast('Reply posted!');
        } else {
          showToast(data.message || 'Could not post reply.', 'error');
        }
      })
      .fail(function () { showToast('Could not post reply.', 'error'); })
      .always(function () { $btn.prop('disabled', false); });
  });

  /* ---- Nested inline reply forms (delegated) ---- */
  $(document).on('submit', '.nested-reply-form', function (e) {
    e.preventDefault();
    const $form = $(this);
    const $btn = $form.find('button[type="submit"]');
    $btn.prop('disabled', true);
    $.post(window.location.href, $form.serialize())
      .done(function (data) {
        if (data.status === 'ok') {
          const parentId = data.reply.parent_id;
          let $container = $(`#reply-${parentId} > .child-replies-container`);
          if (!$container.length) {
            $container = $('<div class="border-t border-outline-variant child-replies-container mt-sm pl-md flex flex-col gap-sm pt-sm"></div>');
            $(`#reply-${parentId}`).append($container);
          }
          $container.append(buildReplyHTML(data.reply));
          // Hide the reply form wrapper after posting
          $form.closest('[id^="reply-form-"]').addClass('hidden');
          $form.find('textarea').val('');
          showToast('Reply posted!');
        } else {
          showToast(data.message || 'Could not post reply.', 'error');
        }
      })
      .fail(function () { showToast('Could not post reply.', 'error'); })
      .always(function () { $btn.prop('disabled', false); });
  });

  /* ---- Mark all notifications read ---- */
  $('#mark-all-read-form').on('submit', function (e) {
    e.preventDefault();
    const $form = $(this);
    $.post($form.attr('action'), $form.serialize())
      .done(function (data) {
        if (data.status === 'ok') {
          $('.notif-unread-dot').remove();
          $('.notif-item').removeClass('bg-surface-container-low');
          $('#notif-badge').addClass('hidden').text('');
          showToast('All notifications marked as read.');
        }
      })
      .fail(function () { showToast('Could not mark notifications as read.', 'error'); });
  });

});

