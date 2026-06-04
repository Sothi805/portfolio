// ProPortfolio - WebSocket Client

class NotificationSocket {
  constructor() {
    this.socket = null;
    this.reconnectDelay = 1000;
    this.maxReconnectDelay = 30000;
  }

  connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const url = `${protocol}//${window.location.host}/ws/notifications/`;
    
    try {
      this.socket = new WebSocket(url);
      this.socket.onopen = () => {
        console.log('Notification socket connected');
        this.reconnectDelay = 1000;
      };
      this.socket.onmessage = (e) => this.handleMessage(JSON.parse(e.data));
      this.socket.onclose = () => {
        console.log('Notification socket closed, reconnecting...');
        setTimeout(() => this.connect(), this.reconnectDelay);
        this.reconnectDelay = Math.min(this.reconnectDelay * 2, this.maxReconnectDelay);
      };
      this.socket.onerror = (err) => console.error('WebSocket error:', err);
    } catch (e) {
      console.log('WebSocket not available');
    }
  }

  handleMessage(data) {
    if (data.type === 'notification') {
      this.showToast(data.title, data.message);
      this.updateBadge();
    }
  }

  showToast(title, message) {
    const container = document.getElementById('messages-container') || this.createContainer();
    const toast = document.createElement('div');
    toast.className = 'flex items-start gap-3 p-4 rounded-xl shadow-lg border bg-white border-blue-200 cursor-pointer message-item';
    toast.innerHTML = `
      <span class="material-symbols-outlined text-blue-600 text-lg shrink-0 mt-0.5">notifications</span>
      <div><p class="font-semibold text-sm text-gray-900">${title}</p><p class="text-sm text-gray-500">${message}</p></div>
    `;
    toast.onclick = () => toast.remove();
    container.appendChild(toast);
    setTimeout(() => { toast.style.opacity = '0'; setTimeout(() => toast.remove(), 300); }, 5000);
  }

  createContainer() {
    const c = document.createElement('div');
    c.id = 'messages-container';
    c.className = 'fixed top-20 right-4 z-50 flex flex-col gap-2 max-w-sm w-full';
    document.body.appendChild(c);
    return c;
  }

  updateBadge() {
    const badge = document.querySelector('#notif-btn .bg-error');
    if (badge) {
      badge.textContent = parseInt(badge.textContent || '0') + 1;
      badge.classList.remove('hidden');
    }
  }
}

class ForumSocket {
  constructor(threadId, onNewReply) {
    this.threadId = threadId;
    this.onNewReply = onNewReply;
    this.socket = null;
  }

  connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const url = `${protocol}//${window.location.host}/ws/forum/thread/${this.threadId}/`;
    try {
      this.socket = new WebSocket(url);
      this.socket.onmessage = (e) => {
        const data = JSON.parse(e.data);
        if (data.type === 'reply_posted' && this.onNewReply) {
          this.onNewReply(data);
        }
      };
    } catch (e) {
      console.log('Forum WebSocket not available');
    }
  }

  sendReply(user, content) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify({ type: 'new_reply', user, content }));
    }
  }
}
