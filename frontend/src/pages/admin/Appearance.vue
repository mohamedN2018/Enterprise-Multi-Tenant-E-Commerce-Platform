<script setup>
import { ref, onMounted } from 'vue';
import { Palette, Check, RotateCcw, Sun, Moon, Type } from 'lucide-vue-next';
import PageHeader from '@/components/ui/PageHeader.vue';
import Spinner from '@/components/ui/Spinner.vue';
import ThemePreviewSample from '@/components/ThemePreviewSample.vue';
import { useUiStore } from '@/stores/ui';
import { seller } from '@/services/seller';
import { errorMessage } from '@/services/http';
import { applyBrand, brand } from '@/theme';
import { t } from '@/i18n';

const ui = useUiStore();

// Fonts bundled locally (Arabic-first + Latin).
const FONTS = ['Cairo', 'Tajawal', 'Almarai', 'Roboto', 'Open Sans'];
const DEFAULT = {
  preset: 'sunset', primary: '#F28B00', secondary: '#F92400',
  background: '#F7F4EF', font: 'Cairo', heading_font: 'Cairo'
};

// Curated, hand-balanced ready-made themes — each pairs a primary with a
// harmonious secondary, a matching soft background, and a fitting type pairing.
const PRESETS = [
  { key: 'sunset', primary: '#F28B00', secondary: '#F92400', background: '#F7F4EF', font: 'Cairo', heading_font: 'Cairo' },
  { key: 'ocean', primary: '#0EA5E9', secondary: '#2563EB', background: '#EFF6FC', font: 'Cairo', heading_font: 'Tajawal' },
  { key: 'forest', primary: '#16A34A', secondary: '#0D9488', background: '#F0F7F2', font: 'Cairo', heading_font: 'Cairo' },
  { key: 'grape', primary: '#7C3AED', secondary: '#DB2777', background: '#F6F3FC', font: 'Tajawal', heading_font: 'Tajawal' },
  { key: 'rose', primary: '#E11D48', secondary: '#F97316', background: '#FDF2F4', font: 'Cairo', heading_font: 'Almarai' },
  { key: 'royal', primary: '#4F46E5', secondary: '#0EA5E9', background: '#F1F2FD', font: 'Cairo', heading_font: 'Cairo' },
  { key: 'mint', primary: '#059669', secondary: '#10B981', background: '#ECFDF5', font: 'Tajawal', heading_font: 'Tajawal' },
  { key: 'sand', primary: '#B45309', secondary: '#D97706', background: '#FBF6EE', font: 'Almarai', heading_font: 'Almarai' },
  { key: 'charcoal', primary: '#334155', secondary: '#F97316', background: '#F1F5F9', font: 'Almarai', heading_font: 'Roboto' }
];

const form = ref({ ...DEFAULT });
const loading = ref(true);
const saving = ref(false);

const preview = () => applyBrand(form.value);

const pickPreset = (p) => {
  form.value = { ...p, preset: p.key };
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
    form.value = { ...DEFAULT, ...(brand.value || {}) };
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
          <h2 class="mb-1 flex items-center gap-2 font-semibold"><Palette class="h-5 w-5 text-primary-600" /> {{ $t('appearance.presets') }}</h2>
          <p class="mb-4 text-sm text-muted">{{ $t('appearance.presetsHint') }}</p>
          <div class="grid grid-cols-2 gap-3 sm:grid-cols-3">
            <button
              v-for="p in PRESETS"
              :key="p.key"
              class="group relative overflow-hidden rounded-xl border p-3 text-start transition hover:-translate-y-0.5 hover:shadow-pop"
              :class="form.preset === p.key ? 'border-primary-500 ring-2 ring-primary-500/30' : 'border-slate-200 dark:border-slate-700'"
              @click="pickPreset(p)"
            >
              <!-- mini theme swatch: background + two brand chips + a sample button -->
              <div class="rounded-lg p-2.5" :style="{ background: p.background }">
                <div class="flex items-center gap-1.5">
                  <span class="h-7 w-7 rounded-md shadow-sm" :style="{ background: p.primary }"></span>
                  <span class="h-7 w-7 rounded-md shadow-sm" :style="{ background: p.secondary }"></span>
                  <span class="ms-auto rounded-full px-2 py-1 text-[10px] font-bold text-white" :style="{ background: p.primary }">Aa</span>
                </div>
              </div>
              <p class="mt-2 text-sm font-medium">{{ $t('appearance.theme_' + p.key) }}</p>
              <span v-if="form.preset === p.key" class="absolute end-2 top-2 grid h-5 w-5 place-items-center rounded-full bg-primary-600 text-white shadow"><Check class="h-3 w-3" /></span>
            </button>
          </div>
        </section>

        <!-- Full customization -->
        <section class="card p-6">
          <h2 class="mb-1 font-semibold">{{ $t('appearance.custom') }}</h2>
          <p class="mb-4 text-sm text-muted">{{ $t('appearance.customHint') }}</p>

          <!-- Colors -->
          <div class="grid gap-5 sm:grid-cols-3">
            <label class="block">
              <span class="label">{{ $t('appearance.primary') }}</span>
              <div class="flex items-center gap-2">
                <input v-model="form.primary" type="color" class="h-10 w-12 shrink-0 cursor-pointer rounded-lg border border-slate-200 bg-transparent" @input="onField" />
                <input v-model="form.primary" class="input font-mono uppercase" maxlength="7" @input="onField" />
              </div>
            </label>
            <label class="block">
              <span class="label">{{ $t('appearance.secondary') }}</span>
              <div class="flex items-center gap-2">
                <input v-model="form.secondary" type="color" class="h-10 w-12 shrink-0 cursor-pointer rounded-lg border border-slate-200 bg-transparent" @input="onField" />
                <input v-model="form.secondary" class="input font-mono uppercase" maxlength="7" @input="onField" />
              </div>
            </label>
            <label class="block">
              <span class="label">{{ $t('appearance.background') }}</span>
              <div class="flex items-center gap-2">
                <input v-model="form.background" type="color" class="h-10 w-12 shrink-0 cursor-pointer rounded-lg border border-slate-200 bg-transparent" @input="onField" />
                <input v-model="form.background" class="input font-mono uppercase" maxlength="7" @input="onField" />
              </div>
            </label>
          </div>

          <!-- Typography -->
          <div class="mt-5 grid gap-5 sm:grid-cols-2">
            <label class="block">
              <span class="label flex items-center gap-1.5"><Type class="h-3.5 w-3.5" /> {{ $t('appearance.headingFont') }}</span>
              <select v-model="form.heading_font" class="input" @change="onField">
                <option v-for="f in FONTS" :key="f" :value="f">{{ f }}</option>
              </select>
              <span class="mt-2 block text-lg font-bold" :style="{ fontFamily: form.heading_font }">{{ $t('appearance.fontSampleHeading') }}</span>
            </label>
            <label class="block">
              <span class="label flex items-center gap-1.5"><Type class="h-3.5 w-3.5" /> {{ $t('appearance.bodyFont') }}</span>
              <select v-model="form.font" class="input" @change="onField">
                <option v-for="f in FONTS" :key="f" :value="f">{{ f }}</option>
              </select>
              <span class="mt-2 block text-sm" :style="{ fontFamily: form.font }">{{ $t('appearance.fontSampleBody') }}</span>
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

      <!-- Live preview: light + dark, so harmony is visible in both modes -->
      <aside class="h-fit space-y-4 lg:sticky lg:top-24">
        <div class="flex items-center gap-2 text-sm font-semibold text-muted">
          <Palette class="h-4 w-4" /> {{ $t('appearance.previewTitle') }}
        </div>

        <!-- Light preview -->
        <div class="overflow-hidden rounded-2xl border border-slate-200 shadow-card dark:border-slate-700">
          <div class="flex items-center gap-1.5 bg-primary-600 px-3 py-1.5 text-[11px] font-medium text-white/90">
            <Sun class="h-3.5 w-3.5" /> {{ $t('appearance.previewLight') }}
          </div>
          <ThemePreviewSample />
        </div>

        <!-- Dark preview (scoped .dark so the dark tokens apply inside only) -->
        <div class="dark overflow-hidden rounded-2xl border shadow-card" style="border-color:#22304d">
          <div class="flex items-center gap-1.5 bg-primary-600 px-3 py-1.5 text-[11px] font-medium text-white/90">
            <Moon class="h-3.5 w-3.5" /> {{ $t('appearance.previewDark') }}
          </div>
          <ThemePreviewSample />
        </div>
      </aside>
    </div>
  </div>
</template>
