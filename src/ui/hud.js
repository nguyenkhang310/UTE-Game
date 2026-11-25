// Lớp giao diện: overlay vào game, thanh tải, nhắc tương tác, phụ đề.

export class HUD {
  constructor() {
    this.overlay = document.getElementById('overlay');
    this.kicker = document.getElementById('overlay-kicker');
    this.title = document.getElementById('overlay-title');
    this.copy = document.getElementById('overlay-copy');
    this.loadWrap = document.getElementById('load-wrap');
    this.loadFill = document.getElementById('load-fill');
    this.loadLabel = document.getElementById('load-label');
    this.enterButton = document.getElementById('enter-btn');
    this.foot = document.getElementById('overlay-foot');

    this.promptEl = document.getElementById('prompt');
    this.subtitleEl = document.getElementById('subtitle');
    this.torchEl = document.getElementById('torch');
    this.flashEl = document.getElementById('flash');

    this.mode = 'loading';
    this.promptText = '';
    this.subtitleTimer = null;
    this.onEnter = null;

    this.overlay.addEventListener('click', () => {
      if (this.mode === 'ready' || this.mode === 'paused') this.onEnter?.();
    });
  }

  setEnterHandler(handler) {
    this.onEnter = handler;
  }

  setLoading(progress) {
    const percent = Math.round(progress * 100);
    this.loadFill.style.width = `${Math.min(100, percent)}%`;
    this.loadLabel.textContent = `Đang tải khu B… ${percent}%`;
  }

  setReady() {
    this.mode = 'ready';
    this.loadWrap.classList.add('hidden');
    this.enterButton.disabled = false;
    this.enterButton.textContent = 'BẤM ALT HOẶC CLICK ĐỂ BƯỚC VÀO';
    this.copy.textContent =
      'Đêm nay khu B thật yên ắng. Có một ngôi miếu, có giọng của môt ba đù nào đó...';
  }

  showPause() {
    this.mode = 'paused';
    this.overlay.classList.remove('hidden');
    this.kicker.textContent = 'KHU B · SÂN VƯỜN SAU GIỜ HỌC';
    this.title.textContent = 'Khu B vẫn đứng đó';
    this.enterButton.disabled = false;
    this.enterButton.textContent = 'TIẾP TỤC';
    this.foot.classList.remove('hidden');
  }

  hideOverlay() {
    this.overlay.classList.add('hidden');
  }

  showError(message) {
    this.mode = 'error';
    this.loadWrap.classList.add('hidden');
    this.kicker.textContent = 'KHÔNG TẢI ĐƯỢC';
    this.title.textContent = 'Khu B biến mất';
    this.copy.textContent = `Không thể tải tài nguyên. Hãy chạy game qua HTTP (npm run dev) thay vì mở trực tiếp file index.html.\n\n${message}`;
    this.enterButton.hidden = true;
    this.foot.classList.add('hidden');
  }

  setPrompt(text) {
    const value = text || '';
    if (value === this.promptText) return;
    this.promptText = value;
    this.promptEl.textContent = value;
  }

  showSubtitle(text, duration = 2800) {
    clearTimeout(this.subtitleTimer);
    this.subtitleEl.textContent = text;
    this.subtitleEl.classList.add('show');
    this.subtitleTimer = setTimeout(() => {
      this.subtitleEl.classList.remove('show');
    }, duration);
  }

  setTorch(on) {
    this.torchEl.innerHTML = `ĐÈN PIN <b class="${on ? 'on' : ''}">${on ? 'BẬT' : 'TẮT'}</b> <span>[F]</span>`;
  }

  glitch() {
    document.body.classList.add('glitching');
    this.flashEl.classList.add('active');
    setTimeout(() => {
      document.body.classList.remove('glitching');
      this.flashEl.classList.remove('active');
    }, 520);
  }
}
