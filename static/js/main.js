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

  /* =============================================
     Auth Forms
     ============================================= */

  /* ---- Login ---- */
  $('#login-form').on('submit', function (e) {
    e.preventDefault();
    const $form = $(this);
    const $btn = $form.find('button[type="submit"]');
    $btn.prop('disabled', true);
    $form.find('.form-error, .field-error').remove();
    $.post(window.location.href, $form.serialize())
      .done(function (data) {
        if (data.status === 'ok') window.location.href = data.redirect;
      })
      .fail(function (xhr) {
        const data = xhr.responseJSON || {};
        if (data.message) {
          $form.prepend(`<div class="form-error bg-error-container text-on-error-container rounded-lg p-sm font-body-sm text-body-sm flex items-center gap-xs mb-sm"><span class="material-symbols-outlined text-[16px]">error</span>&nbsp;${escapeHtml(data.message)}</div>`);
        } else if (data.errors) {
          Object.entries(data.errors).forEach(([field, msg]) => {
            $form.find(`[name="${field}"]`).after(`<p class="field-error font-label-sm text-label-sm text-error mt-xs flex items-center gap-xs"><span class="material-symbols-outlined text-[14px]">error</span>&nbsp;${escapeHtml(msg)}</p>`);
          });
        }
        $btn.prop('disabled', false);
      });
  });

  /* ---- Register ---- */
  $('#register-form').on('submit', function (e) {
    e.preventDefault();
    const $form = $(this);
    const $btn = $form.find('button[type="submit"]');
    $btn.prop('disabled', true);
    $form.find('.form-error, .field-error').remove();
    $.post(window.location.href, $form.serialize())
      .done(function (data) {
        if (data.status === 'ok') {
          if (data.message) showToast(data.message);
          window.location.href = data.redirect;
        }
      })
      .fail(function (xhr) {
        const data = xhr.responseJSON || {};
        if (data.errors) {
          Object.entries(data.errors).forEach(([field, msg]) => {
            $form.find(`[name="${field}"]`).after(`<p class="field-error font-label-sm text-label-sm text-error mt-xs flex items-center gap-xs"><span class="material-symbols-outlined text-[14px]">error</span>&nbsp;${escapeHtml(msg)}</p>`);
          });
        } else {
          showToast(data.message || 'Registration failed.', 'error');
        }
        $btn.prop('disabled', false);
      });
  });

  /* ---- Profile Update ---- */
  $('#profile-form').on('submit', function (e) {
    e.preventDefault();
    const $form = $(this);
    const $btn = $form.find('button[type="submit"]');
    $btn.prop('disabled', true);
    $.ajax({
      url: window.location.href,
      type: 'POST',
      data: new FormData(this),
      processData: false,
      contentType: false,
    })
      .done(function (data) {
        if (data.status === 'ok') {
          showToast('Profile updated successfully!');
          if (data.avatar_url) {
            $('#avatar-preview').attr('src', data.avatar_url).removeClass('hidden');
            $('#avatar-default').addClass('hidden');
          }
        }
      })
      .fail(function (xhr) {
        const data = xhr.responseJSON || {};
        showToast(data.message || 'Failed to update profile.', 'error');
      })
      .always(function () { $btn.prop('disabled', false); });
  });

  /* =============================================
     Portfolio Create
     ============================================= */

  $('#create-portfolio-form').on('submit', function (e) {
    e.preventDefault();
    const $form = $(this);
    const $btn = $form.find('button[type="submit"]');
    $btn.prop('disabled', true);
    $.post(window.location.href, $form.serialize())
      .done(function (data) {
        if (data.status === 'ok') window.location.href = data.redirect;
      })
      .fail(function (xhr) {
        const data = xhr.responseJSON || {};
        showToast(data.message || 'Could not create portfolio.', 'error');
        $btn.prop('disabled', false);
      });
  });

  /* =============================================
     Portfolio Edit — About / Contact / Status / Title
     ============================================= */

  /* ---- About ---- */
  $('#about-form').on('submit', function (e) {
    e.preventDefault();
    const $btn = $(this).find('button[type="submit"]');
    $btn.prop('disabled', true);
    $.post(window.location.href, $(this).serialize())
      .done(function (data) { if (data.status === 'ok') showToast('About section saved!'); })
      .fail(function () { showToast('Could not save about section.', 'error'); })
      .always(function () { $btn.prop('disabled', false); });
  });

  /* ---- Contact ---- */
  $('#contact-form').on('submit', function (e) {
    e.preventDefault();
    const $btn = $(this).find('button[type="submit"]');
    $btn.prop('disabled', true);
    $.post(window.location.href, $(this).serialize())
      .done(function (data) { if (data.status === 'ok') showToast('Contact info saved!'); })
      .fail(function () { showToast('Could not save contact info.', 'error'); })
      .always(function () { $btn.prop('disabled', false); });
  });

  /* ---- Status ---- */
  $('#status-form').on('submit', function (e) {
    e.preventDefault();
    const $btn = $(this).find('button[type="submit"]');
    $btn.prop('disabled', true);
    $.post(window.location.href, $(this).serialize())
      .done(function (data) {
        if (data.status === 'ok') {
          showToast('Portfolio status updated!');
          const $badge = $('#portfolio-status-badge');
          $badge.text(data.new_status).removeClass('bg-green-100 text-green-700 bg-yellow-100 text-yellow-700 bg-surface-container text-on-surface-variant');
          if (data.new_status === 'public') $badge.addClass('bg-green-100 text-green-700');
          else if (data.new_status === 'private') $badge.addClass('bg-yellow-100 text-yellow-700');
          else $badge.addClass('bg-surface-container text-on-surface-variant');
        }
      })
      .fail(function () { showToast('Could not update status.', 'error'); })
      .always(function () { $btn.prop('disabled', false); });
  });

  /* ---- Title ---- */
  $('#title-form').on('submit', function (e) {
    e.preventDefault();
    const $btn = $(this).find('button[type="submit"]');
    $btn.prop('disabled', true);
    $.post(window.location.href, $(this).serialize())
      .done(function (data) {
        if (data.status === 'ok') {
          showToast('Title updated!');
          $('#portfolio-title-display').text(data.title);
          document.title = 'Edit ' + data.title + ' \u2013 ProPortfolio';
        }
      })
      .fail(function () { showToast('Could not update title.', 'error'); })
      .always(function () { $btn.prop('disabled', false); });
  });

  /* ---- Template ---- */
  $('#template-form').on('submit', function (e) {
    e.preventDefault();
    const $btn = $(this).find('button[type="submit"]');
    $btn.prop('disabled', true);
    $.post(window.location.href, $(this).serialize())
      .done(function (data) {
        if (data.status === 'ok') {
          showToast('Template changed to ' + data.template_name + '!');
          $('#current-template-name').text(data.template_name);
        }
      })
      .fail(function () { showToast('Could not change template.', 'error'); })
      .always(function () { $btn.prop('disabled', false); });
  });

  /* =============================================
     Portfolio Edit — Projects
     ============================================= */

  /* ---- Delete project (delegated) ---- */
  $(document).on('submit', '.delete-project-form', function (e) {
    e.preventDefault();
    const $form = $(this);
    $.post(window.location.href, $form.serialize())
      .done(function (data) {
        if (data.status === 'ok') {
          $form.parent().remove();
          showToast('Project removed.');
        }
      })
      .fail(function () { showToast('Could not remove project.', 'error'); });
  });

  /* ---- Add project ---- */
  $('#add-project-form').on('submit', function (e) {
    e.preventDefault();
    const $form = $(this);
    const $btn = $form.find('button[type="submit"]');
    $btn.prop('disabled', true);
    $.ajax({
      url: window.location.href,
      type: 'POST',
      data: new FormData(this),
      processData: false,
      contentType: false,
    })
      .done(function (data) {
        if (data.status === 'ok') {
          const p = data.project;
          const csrf = escapeHtml(getCsrfToken());
          const img = p.image_url
            ? `<img src="${escapeHtml(p.image_url)}" alt="${escapeHtml(p.title)}" class="w-14 h-14 rounded-lg object-cover shrink-0"/>`
            : `<div class="w-14 h-14 rounded-lg bg-surface-container flex items-center justify-center shrink-0"><span class="material-symbols-outlined text-outline text-[22px]">image</span></div>`;
          const urlLink = p.url
            ? `<a href="${escapeHtml(p.url)}" target="_blank" class="font-label-sm text-label-sm text-primary hover:underline flex items-center gap-xs mt-0.5"><span class="material-symbols-outlined text-[12px]">open_in_new</span>${escapeHtml(p.url.length > 30 ? p.url.substring(0, 30) + '\u2026' : p.url)}</a>`
            : '';
          const html = `
            <div class="flex items-center justify-between p-sm border border-outline-variant rounded-xl mb-sm gap-sm hover:border-primary/40 transition-colors">
              ${img}
              <div class="flex-grow min-w-0">
                <p class="font-label-md text-label-md text-on-surface">${escapeHtml(p.title)}</p>
                <p class="font-body-sm text-body-sm text-on-surface-variant line-clamp-1">${escapeHtml(p.description || '')}</p>
                ${urlLink}
              </div>
              <form method="post" class="delete-project-form" data-project-id="${p.id}">
                <input type="hidden" name="csrfmiddlewaretoken" value="${csrf}">
                <input type="hidden" name="action" value="delete_project"/>
                <input type="hidden" name="project_id" value="${p.id}"/>
                <button type="submit" class="text-error hover:bg-error-container p-xs rounded-lg transition-colors shrink-0" title="Delete project"><span class="material-symbols-outlined text-[18px]">delete</span></button>
              </form>
            </div>`;
          $form.closest('details').before(html);
          $form.closest('.shadow-sm').find('p.border-dashed').remove();
          $form[0].reset();
          if (typeof clearProjectImage === 'function') clearProjectImage();
          showToast('Project added!');
        }
      })
      .fail(function (xhr) {
        const data = xhr.responseJSON || {};
        showToast(data.message || 'Could not add project.', 'error');
      })
      .always(function () { $btn.prop('disabled', false); });
  });

  /* =============================================
     Portfolio Edit — Skills
     ============================================= */

  /* ---- Delete skill (delegated) ---- */
  $(document).on('submit', '.delete-skill-form', function (e) {
    e.preventDefault();
    const $form = $(this);
    $.post(window.location.href, $form.serialize())
      .done(function (data) {
        if (data.status === 'ok') $form.parent().remove();
      })
      .fail(function () { showToast('Could not remove skill.', 'error'); });
  });

  /* ---- Add skill ---- */
  $('#add-skill-form').on('submit', function (e) {
    e.preventDefault();
    const $form = $(this);
    const $btn = $form.find('button[type="submit"]');
    $btn.prop('disabled', true);
    $.post(window.location.href, $form.serialize())
      .done(function (data) {
        if (data.status === 'ok') {
          const s = data.skill;
          const csrf = escapeHtml(getCsrfToken());
          const html = `
            <div class="flex items-center gap-xs px-sm py-xs rounded-full border border-outline-variant bg-surface-container group">
              <span class="font-label-md text-label-md text-on-surface">${escapeHtml(s.name)}</span>
              <span class="font-label-sm text-label-sm text-on-surface-variant capitalize bg-surface-container-high px-xs py-0.5 rounded-full">${escapeHtml(s.proficiency)}</span>
              <form method="post" class="delete-skill-form inline" data-skill-id="${s.id}">
                <input type="hidden" name="csrfmiddlewaretoken" value="${csrf}">
                <input type="hidden" name="action" value="delete_skill"/>
                <input type="hidden" name="skill_id" value="${s.id}"/>
                <button type="submit" class="text-error ml-xs opacity-0 group-hover:opacity-100 transition-opacity" title="Remove skill"><span class="material-symbols-outlined text-[14px]">close</span></button>
              </form>
            </div>`;
          $form.closest('details').before(html);
          $form.closest('.shadow-sm').find('p:contains("No skills")').remove();
          $form[0].reset();
          showToast('Skill added!');
        }
      })
      .fail(function (xhr) {
        const data = xhr.responseJSON || {};
        showToast(data.message || 'Could not add skill.', 'error');
      })
      .always(function () { $btn.prop('disabled', false); });
  });

  /* =============================================
     Portfolio Edit — Experience
     ============================================= */

  /* ---- Delete experience (delegated) ---- */
  $(document).on('submit', '.delete-experience-form', function (e) {
    e.preventDefault();
    const $form = $(this);
    $.post(window.location.href, $form.serialize())
      .done(function (data) {
        if (data.status === 'ok') {
          $form.parent().remove();
          showToast('Experience removed.');
        }
      })
      .fail(function () { showToast('Could not remove experience.', 'error'); });
  });

  /* ---- Add experience ---- */
  $('#add-experience-form').on('submit', function (e) {
    e.preventDefault();
    const $form = $(this);
    const $btn = $form.find('button[type="submit"]');
    $btn.prop('disabled', true);
    $.post(window.location.href, $form.serialize())
      .done(function (data) {
        if (data.status === 'ok') {
          const x = data.experience;
          const csrf = escapeHtml(getCsrfToken());
          const desc = x.description ? `<p class="font-body-sm text-body-sm text-on-surface-variant line-clamp-1 mt-xs">${escapeHtml(x.description)}</p>` : '';
          const html = `
            <div class="flex items-start justify-between p-sm border border-outline-variant rounded-xl mb-sm gap-sm hover:border-primary/40 transition-colors">
              <div class="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
                <span class="material-symbols-outlined text-primary text-[18px]">business</span>
              </div>
              <div class="flex-grow min-w-0">
                <p class="font-label-md text-label-md text-on-surface">${escapeHtml(x.role)}</p>
                <p class="font-body-sm text-body-sm text-primary">${escapeHtml(x.company)}</p>
                <p class="font-label-sm text-label-sm text-on-surface-variant">${escapeHtml(x.period)}</p>
                ${desc}
              </div>
              <form method="post" class="delete-experience-form" data-exp-id="${x.id}">
                <input type="hidden" name="csrfmiddlewaretoken" value="${csrf}">
                <input type="hidden" name="action" value="delete_experience"/>
                <input type="hidden" name="experience_id" value="${x.id}"/>
                <button type="submit" class="text-error hover:bg-error-container p-xs rounded-lg transition-colors" title="Delete"><span class="material-symbols-outlined text-[18px]">delete</span></button>
              </form>
            </div>`;
          $form.closest('details').before(html);
          $form.closest('.shadow-sm').find('p.border-dashed').remove();
          $form[0].reset();
          showToast('Experience added!');
        }
      })
      .fail(function (xhr) {
        const data = xhr.responseJSON || {};
        showToast(data.message || 'Could not add experience.', 'error');
      })
      .always(function () { $btn.prop('disabled', false); });
  });

  /* =============================================
     Portfolio Edit — Education
     ============================================= */

  /* ---- Delete education (delegated) ---- */
  $(document).on('submit', '.delete-education-form', function (e) {
    e.preventDefault();
    const $form = $(this);
    $.post(window.location.href, $form.serialize())
      .done(function (data) {
        if (data.status === 'ok') {
          $form.parent().remove();
          showToast('Education removed.');
        }
      })
      .fail(function () { showToast('Could not remove education.', 'error'); });
  });

  /* ---- Add education ---- */
  $('#add-education-form').on('submit', function (e) {
    e.preventDefault();
    const $form = $(this);
    const $btn = $form.find('button[type="submit"]');
    $btn.prop('disabled', true);
    $.post(window.location.href, $form.serialize())
      .done(function (data) {
        if (data.status === 'ok') {
          const edu = data.education;
          const csrf = escapeHtml(getCsrfToken());
          const degree = edu.degree
            ? `<p class="font-body-sm text-body-sm text-primary">${escapeHtml(edu.degree)}${edu.field_of_study ? ' \u2013 ' + escapeHtml(edu.field_of_study) : ''}</p>`
            : '';
          const desc = edu.description ? `<p class="font-body-sm text-body-sm text-on-surface-variant line-clamp-1 mt-xs">${escapeHtml(edu.description)}</p>` : '';
          const html = `
            <div class="flex items-start justify-between p-sm border border-outline-variant rounded-xl mb-sm gap-sm hover:border-primary/40 transition-colors">
              <div class="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
                <span class="material-symbols-outlined text-primary text-[18px]">school</span>
              </div>
              <div class="flex-grow min-w-0">
                <p class="font-label-md text-label-md text-on-surface">${escapeHtml(edu.institution)}</p>
                ${degree}
                <p class="font-label-sm text-label-sm text-on-surface-variant">${escapeHtml(edu.period)}</p>
                ${desc}
              </div>
              <form method="post" class="delete-education-form" data-edu-id="${edu.id}">
                <input type="hidden" name="csrfmiddlewaretoken" value="${csrf}">
                <input type="hidden" name="action" value="delete_education"/>
                <input type="hidden" name="education_id" value="${edu.id}"/>
                <button type="submit" class="text-error hover:bg-error-container p-xs rounded-lg transition-colors" title="Delete"><span class="material-symbols-outlined text-[18px]">delete</span></button>
              </form>
            </div>`;
          $form.closest('details').before(html);
          $form.closest('.shadow-sm').find('p.border-dashed').remove();
          $form[0].reset();
          showToast('Education added!');
        }
      })
      .fail(function (xhr) {
        const data = xhr.responseJSON || {};
        showToast(data.message || 'Could not add education.', 'error');
      })
      .always(function () { $btn.prop('disabled', false); });
  });

  /* =============================================
     Forum — Create Thread
     ============================================= */

  $('#create-thread-form').on('submit', function (e) {
    e.preventDefault();
    const $form = $(this);
    const $btn = $form.find('button[type="submit"]');
    $btn.prop('disabled', true);
    $.post(window.location.href, $form.serialize())
      .done(function (data) {
        if (data.status === 'ok') window.location.href = data.redirect;
      })
      .fail(function (xhr) {
        const data = xhr.responseJSON || {};
        showToast(data.message || 'Could not create thread.', 'error');
        $btn.prop('disabled', false);
      });
  });

});

