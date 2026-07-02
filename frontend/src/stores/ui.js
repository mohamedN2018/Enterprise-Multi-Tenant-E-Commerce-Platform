import { defineStore } from 'pinia';

let seq = 0;

// Lightweight toast notifications.
export const useUiStore = defineStore('ui', {
  state: () => ({ toasts: [] }),
  actions: {
    push(message, type = 'info', timeout = 3500) {
      const id = ++seq;
      this.toasts.push({ id, message, type });
      if (timeout) setTimeout(() => this.dismiss(id), timeout);
      return id;
    },
    success(m) {
      return this.push(m, 'success');
    },
    error(m) {
      return this.push(m, 'error', 5000);
    },
    info(m) {
      return this.push(m, 'info');
    },
    dismiss(id) {
      this.toasts = this.toasts.filter((t) => t.id !== id);
    }
  }
});
