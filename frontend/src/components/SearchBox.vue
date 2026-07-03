<script setup>
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { Search, X, Loader2 } from 'lucide-vue-next';
import { storefront } from '@/services/storefront';
import { productImage, onImgError } from '@/utils/media';
import { t } from '@/i18n';

const props = defineProps({ autofocus: { type: Boolean, default: false } });
const emit = defineEmits(['navigate']);

const router = useRouter();
const q = ref('');
const results = ref([]);
const loading = ref(false);
const open = ref(false);
const root = ref(null);
const inputEl = ref(null);
let timer = null;

const price = (p) => p.price ?? p.min_price ?? p.display_price;
const currency = (p) => p.currency || p.store?.currency || '';
const img = (p) => p.primary_image?.image || p.image || p.images?.[0]?.image || productImage(p);

const runSearch = async () => {
  const term = q.value.trim();
  if (term.length < 2) {
    results.value = [];
    loading.value = false;
    return;
  }
  loading.value = true;
  open.value = true;
  try {
    const res = await storefront.products({ search: term, page_size: 6 });
    results.value = res.data?.results || res.data || [];
  } catch {
    results.value = [];
  } finally {
    loading.value = false;
  }
};

watch(q, () => {
  clearTimeout(timer);
  open.value = true;
  timer = setTimeout(runSearch, 300);
});

const close = () => (open.value = false);

const submit = () => {
  const term = q.value.trim();
  if (!term) return;
  close();
  emit('navigate');
  router.push({ name: 'products', query: { search: term } });
};

const goProduct = () => {
  close();
  emit('navigate');
};

const clear = () => {
  q.value = '';
  results.value = [];
  inputEl.value?.focus();
};

const onDocPointer = (e) => {
  if (root.value && !root.value.contains(e.target)) open.value = false;
};

onMounted(() => {
  document.addEventListener('mousedown', onDocPointer);
  if (props.autofocus) nextTick(() => inputEl.value?.focus());
});
onBeforeUnmount(() => {
  clearTimeout(timer);
  document.removeEventListener('mousedown', onDocPointer);
});
</script>

<template>
  <div ref="root" class="relative w-full">
    <form
      class="flex w-full items-center rounded-full border border-slate-200 bg-white ps-4 transition focus-within:border-primary-500 dark:border-slate-700 dark:bg-slate-800"
      @submit.prevent="submit"
    >
      <Search class="h-4 w-4 shrink-0 text-slate-400" />
      <input
        ref="inputEl"
        v-model="q"
        type="search"
        :placeholder="t('nav.searchPlaceholder')"
        class="w-full border-0 bg-transparent px-3 py-2.5 text-sm text-ink focus:outline-none"
        @focus="open = true"
      />
      <button
        v-if="q"
        type="button"
        class="me-1 grid h-7 w-7 shrink-0 place-items-center rounded-full text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700"
        @click="clear"
      >
        <X class="h-4 w-4" />
      </button>
      <button type="submit" class="btn btn-primary shrink-0 rounded-full px-6"><Search class="h-4 w-4" /></button>
    </form>

    <!-- Live results -->
    <div
      v-if="open && q.trim().length >= 2"
      class="absolute inset-x-0 top-full z-[110] mt-2 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-pop dark:border-slate-700 dark:bg-slate-800"
    >
      <div v-if="loading" class="flex items-center justify-center gap-2 py-6 text-sm text-muted">
        <Loader2 class="h-4 w-4 animate-spin" /> {{ t('common.loading') }}
      </div>
      <template v-else-if="results.length">
        <ul class="max-h-[70vh] overflow-y-auto">
          <li v-for="p in results" :key="p.id">
            <RouterLink
              :to="{ name: 'product', params: { id: p.id } }"
              class="flex items-center gap-3 border-b border-slate-50 px-3 py-2.5 transition last:border-0 hover:bg-lightbg dark:border-slate-700/60"
              @click="goProduct"
            >
              <img :src="img(p)" :alt="p.name" class="h-12 w-12 shrink-0 rounded-lg border border-slate-100 object-cover dark:border-slate-700" @error="onImgError" />
              <div class="min-w-0 flex-1">
                <p class="clamp-1 text-sm font-medium text-ink">{{ p.name }}</p>
                <p class="clamp-1 text-xs text-muted">{{ p.store?.name || p.store_slug }}</p>
              </div>
              <span class="shrink-0 text-sm font-bold text-primary-600">{{ price(p) }} {{ currency(p) }}</span>
            </RouterLink>
          </li>
        </ul>
        <button class="block w-full bg-lightbg px-3 py-2.5 text-center text-sm font-semibold text-primary-600 hover:underline" @click="submit">
          {{ t('nav.seeAllResults', { q: q.trim() }) }}
        </button>
      </template>
      <div v-else class="py-6 text-center text-sm text-muted">{{ t('nav.noSearchResults') }}</div>
    </div>
  </div>
</template>
