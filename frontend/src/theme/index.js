import { ref } from 'vue';

// Light is the default theme; persisted per user in localStorage.
const stored = localStorage.getItem('theme');
export const theme = ref(stored === 'dark' ? 'dark' : 'light');

export function applyTheme() {
  document.documentElement.classList.toggle('dark', theme.value === 'dark');
}

export function setTheme(t) {
  theme.value = t === 'dark' ? 'dark' : 'light';
  localStorage.setItem('theme', theme.value);
  applyTheme();
}

export function toggleTheme() {
  setTheme(theme.value === 'dark' ? 'light' : 'dark');
}

export function useTheme() {
  return { theme, setTheme, toggleTheme };
}
