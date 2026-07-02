import { ref, shallowRef } from 'vue';
import { errorMessage } from '@/services/http';

// Drives a paginated list backed by the API's `meta.pagination` envelope.
// `fetcher(params)` must return the axios response (with `.data` + `.$meta`).
export function usePaginated(fetcher, { pageSize = 20 } = {}) {
  const items = shallowRef([]);
  const page = ref(1);
  const total = ref(0);
  const totalPages = ref(1);
  const loading = ref(false);
  const error = ref('');

  const load = async (extraParams = {}) => {
    loading.value = true;
    error.value = '';
    try {
      const res = await fetcher({ page: page.value, page_size: pageSize, ...extraParams });
      const body = res.data;
      // Lists come back either as a bare array (data) or already unwrapped.
      items.value = Array.isArray(body) ? body : body?.results || [];
      const pg = res.$meta?.pagination;
      if (pg) {
        total.value = pg.count ?? items.value.length;
        totalPages.value = pg.total_pages ?? 1;
      } else {
        total.value = items.value.length;
        totalPages.value = 1;
      }
    } catch (e) {
      error.value = errorMessage(e);
      items.value = [];
    } finally {
      loading.value = false;
    }
  };

  const goTo = (n, extraParams = {}) => {
    page.value = n;
    return load(extraParams);
  };

  return { items, page, total, totalPages, loading, error, load, goTo };
}
