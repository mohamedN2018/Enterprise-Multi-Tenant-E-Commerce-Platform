import { ref, shallowRef } from 'vue';
import { errorMessage } from '@/services/http';

// Wrap an async producer with loading / error / data state.
// `fn` receives whatever arguments are passed to `run(...)` and should return
// an axios response (its `.data` is stored) or a plain value.
export function useAsync(fn, { immediate = false } = {}) {
  const data = shallowRef(null);
  const meta = shallowRef(null);
  const loading = ref(false);
  const error = ref('');

  const run = async (...args) => {
    loading.value = true;
    error.value = '';
    try {
      const res = await fn(...args);
      if (res && typeof res === 'object' && 'data' in res && '$meta' in res) {
        data.value = res.data;
        meta.value = res.$meta;
      } else if (res && typeof res === 'object' && 'data' in res && 'config' in res) {
        data.value = res.data;
      } else {
        data.value = res;
      }
      return data.value;
    } catch (e) {
      error.value = errorMessage(e);
      throw e;
    } finally {
      loading.value = false;
    }
  };

  if (immediate) run();

  return { data, meta, loading, error, run };
}
