<script setup>
import { ref, onMounted } from 'vue';
import { Palette, Check, RotateCcw, ShoppingCart, Star, Heart } from 'lucide-vue-next';
import PageHeader from '@/components/ui/PageHeader.vue';
import Spinner from '@/components/ui/Spinner.vue';
import { useUiStore } from '@/stores/ui';
import { seller } from '@/services/seller';
import { errorMessage } from '@/services/http';
import { applyBrand, brand } from '@/theme';
import { t } from '@/i18n';

const ui = useUiStore();

const FONTS = ['Cairo', 'Roboto', 'Open Sans'];
const DEFAULT = { preset: 'sunset', primary: '#F28B00', secondary: '#F92400', background: '#F5F5F5', font: 'Cairo' };

// Curated ready-made themes.
const PRESETS = [
  { key: 'sunset', primary: '#F28B00', secondary: '#F92400', background: '#F5F5F5', font: 'Cairo' },
  { key: 'ocean', primary: '#2563EB', secondary: '#0EA5E9', background: '#F1F5F9', font: 'Cairo' },
  { key: 'forest', primary: '#16A34A', secondary: '#F59E0B', background: '#F1F5F0', font: 'Cairo' },
  { key: 'grape', primary: '#7C3AED', secondary: '#EC4899', background: '#F5F3FF', font: 'Roboto' },
  { key: 'rose', primary: '#E11D48', secondary: '#9333EA', background: '#FFF1F2', font: 'Cairo' },
  { key: 'charcoal', primary: '#334155', secondary: '#F97316', background: '#F1F5F9', font: 'Open Sans' }
];

const form = ref({ ...DEFAULT });
const loading = ref(true);
const saving = ref(false);

// Preview the current form live across the whole app.
const preview = () => applyBrand(form.value);

const pickPreset = (p) => {
  form.value = { preset: p.key, primary: p.primary, secondary: p.secondary, background: p.background, font: p.font };
  preview();
};
const onField = () => {
  form.value.preset = 'custom';
  preview();
};

const save = async () => {
  saving.value = true;
  try {
    const res = await seller.updatePlatformTheme(form.value);
    brand.value = res.data;
    localStorage.setItem('brand', JSON.stringify(res.data));
    applyBrand(res.data);
    ui.success(t('appearance.saved'));
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    saving.value = false;
  }
};

const resetDefault = () => {
  form.value = { ...DEFAULT };
  preview();
};

onMounted(async () => {
  try {
    const res = await seller.getPlatformTheme();
    form.value = { ...DEFAULT, ...res.data };
  } catch {
    form.value = { ...(brand.value || DEFAULT) };
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div>
    <PageHeader :title="$t('appearance.title')" :subtitle="$t('appearance.subtitle')" />

    <div v-if="loading" class="flex min-h-[30vh] items-center justify-center"><Spinner :size="28" /></div>

    <div v-else class="grid gap-6 lg:grid-cols-3">
      <div class="space-y-6 lg:col-span-2">
        <!-- Ready-made themes -->
        <section class="card p-6">
          <h2 class="mb-4 flex items-center gap-2 font-semibold"><Palette class="h-5 w-5 text-primary-600" /> {{ $t('appearance.presets') }}</h2>
          <div class="grid grid-cols-2 gap-3 sm:grid-cols-3">
            <button
              v-for="p in PRESETS"
              :key="p.key"
              class="group relative overflow-hidden rounded-xl border p-3 text-start transition hover:shadow-pop"
              :class="form.preset === p.key ? 'border-primary-500 ring-2 ring-primary-200' : 'border-slate-200 dark:border-slate-700'"
              @click="pickPreset(p)"
            >
              <div class="flex gap-1.5">
                <span class="h-8 w-8 rounded-lg" :style="{ background: p.primary }"></span>
                <span class="h-8 w-8 rounded-lg" :style="{ background: p.secondary }"></span>
                <span class="h-8 w-8 rounded-lg border border-slate-200" :style="{ background: p.background }"></span>
              </div>
              <p class="mt-2 text-sm font-medium">{{ $t('appearance.theme_' + p.key) }}</p>
              <span v-if="form.preset === p.key" class="absolute end-2 top-2 grid h-5 w-5 place-items-center rounded-full bg-primary-600 text-white"><Check class="h-3 w-3" /></span>
            </button>
          </div>
        </section>

        <!-- Custom colors + font -->
        <section class="card p-6">
          <h2 class="mb-4 font-semibold">{{ $t('appearance.custom') }}</h2>
          <div class="grid gap-5 sm:grid-cols-2">
            <label class="block">
              <span class="label">{{ $t('appearance.primary') }}</span>
              <div class="flex items-center gap-2">
                <input v-model="form.primary" type="color" class="h-10 w-14 cursor-pointer rounded-lg border border-slate-200 bg-transparent" @input="onField" />
                <input v-model="form.primary" class="input font-mono" @input="onField" />
              </div>
            </label>
            <label class="block">
              <span class="label">{{ $t('appearance.secondary') }}</span>
              <div class="flex items-center gap-2">
                <input v-model="form.secondary" type="color" class="h-10 w-14 cursor-pointer rounded-lg border border-slate-200 bg-transparent" @input="onField" />
                <input v-model="form.secondary" class="input font-mono" @input="onField" />
              </div>
            </label>
            <label class="block">
              <span class="label">{{ $t('appearance.background') }}</span>
              <div class="flex items-center gap-2">
                <input v-model="form.background" type="color" class="h-10 w-14 cursor-pointer rounded-lg border border-slate-200 bg-transparent" @input="onField" />
                <input v-model="form.background" class="input font-mono" @input="onField" />
              </div>
            </label>
            <label class="block">
              <span class="label">{{ $t('appearance.font') }}</span>
              <select v-model="form.font" class="input" @change="onField">
                <option v-for="f in FONTS" :key="f" :value="f">{{ f }}</option>
              </select>
            </label>
          </div>
          <div class="mt-6 flex flex-wrap gap-2">
            <button class="btn btn-primary" :disabled="saving" @click="save">
              <Spinner v-if="saving" :size="18" /><template v-else><Check class="h-4 w-4" /> {{ $t('appearance.save') }}</template>
            </button>
            <button class="btn btn-outline" @click="resetDefault"><RotateCcw class="h-4 w-4" /> {{ $t('appearance.reset') }}</button>
          </div>
          <p class="mt-3 text-xs text-muted">{{ $t('appearance.liveHint') }}</p>
        </section>
      </div>

      <!-- Live preview -->
      <aside class="h-fit lg:sticky lg:top-24">
        <div class="card overflow-hidden">
          <div class="bg-primary-600 p-4 text-white">
            <p class="font-heading text-lg font-bold">{{ $t('appearance.previewTitle') }}</p>
          </div>
          <div class="space-y-4 bg-lightbg p-5">
            <div class="rounded-xl border border-slate-200 bg-white p-4">
              <div class="flex items-center justify-between">
                <span class="font-heading font-semibold text-ink">{{ $t('appearance.sampleProduct') }}</span>
                <span class="text-lg font-bold text-primary-600">250 EGP</span>
              </div>
              <div class="mt-1 flex text-primary-600"><Star v-for="n in 5" :key="n" class="h-4 w-4 fill-primary-600" /></div>
              <div class="mt-3 flex gap-2">
                <button class="btn btn-primary btn-sm flex-1"><ShoppingCart class="h-4 w-4" /> {{ $t('product.addToCart') }}</button>
                <button class="grid h-9 w-9 place-items-center rounded-full border border-slate-200 text-primary-600"><Heart class="h-4 w-4" /></button>
              </div>
            </div>
            <div class="flex flex-wrap gap-2">
              <span class="chip border-0 bg-primary-50 text-primary-700">{{ $t('appearance.tagPrimary') }}</span>
              <span class="chip border-0 bg-secondary-500 text-white">{{ $t('appearance.tagSale') }}</span>
            </div>
            <button class="btn btn-secondary btn-sm w-full">{{ $t('appearance.tagSale') }}</button>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>
