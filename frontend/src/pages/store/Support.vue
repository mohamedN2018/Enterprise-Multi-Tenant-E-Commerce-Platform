<script setup>
import { ref, computed } from 'vue';
import {
  Search,
  Truck,
  Undo2,
  CreditCard,
  ShieldCheck,
  Store as StoreIcon,
  ChevronDown,
  Mail,
  Phone,
  Clock,
  MessageCircle,
  Send
} from 'lucide-vue-next';
import PageHero from '@/components/ui/PageHero.vue';
import FormField from '@/components/ui/FormField.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import { useUiStore } from '@/stores/ui';
import { t } from '@/i18n';

const ui = useUiStore();

// No backend ticketing endpoint exists, so the contact form composes an email
// via the user's mail client and we surface direct channels instead.
const SUPPORT_EMAIL = 'support@q-shop.example';
const SUPPORT_PHONE = '+20 100 000 0000';
const SUPPORT_WHATSAPP = '201000000000';

const categories = computed(() => [
  { icon: Truck, title: t('support.catOrders'), desc: t('support.catOrdersDesc') },
  { icon: Undo2, title: t('support.catReturns'), desc: t('support.catReturnsDesc') },
  { icon: CreditCard, title: t('support.catPayments'), desc: t('support.catPaymentsDesc') },
  { icon: ShieldCheck, title: t('support.catAccount'), desc: t('support.catAccountDesc') },
  { icon: StoreIcon, title: t('support.catStores'), desc: t('support.catStoresDesc') }
]);

const query = ref('');
const openIndex = ref(0);

const allFaqs = computed(() => {
  const v = t('support.faqs');
  return Array.isArray(v) ? v : [];
});
const filteredFaqs = computed(() => {
  const q = query.value.trim().toLowerCase();
  if (!q) return allFaqs.value;
  return allFaqs.value.filter((f) => `${f.q} ${f.a}`.toLowerCase().includes(q));
});

const toggle = (i) => (openIndex.value = openIndex.value === i ? -1 : i);

const form = ref({ name: '', email: '', subject: '', message: '' });
const submit = () => {
  const body = `${form.value.message}\n\n— ${form.value.name} (${form.value.email})`;
  const href = `mailto:${SUPPORT_EMAIL}?subject=${encodeURIComponent(form.value.subject)}&body=${encodeURIComponent(body)}`;
  window.location.href = href;
  ui.success(t('support.sent'));
};
</script>

<template>
  <div>
    <PageHero :title="$t('support.title')" :items="[{ label: $t('support.title') }]" />

    <div class="container py-10">
      <!-- Intro + search -->
      <div class="mx-auto max-w-2xl text-center">
        <p class="text-muted">{{ $t('support.subtitle') }}</p>
        <div class="relative mt-5">
          <Search class="pointer-events-none absolute start-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />
          <input
            v-model="query"
            type="search"
            :placeholder="$t('support.searchPlaceholder')"
            class="input h-12 rounded-full ps-12 text-base shadow-sm"
          />
        </div>
      </div>

      <!-- Topic categories -->
      <h2 class="section-title mt-12">{{ $t('support.browseTopics') }}</h2>
      <div class="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div v-for="c in categories" :key="c.title" class="card flex items-start gap-4 p-5">
          <span class="grid h-12 w-12 shrink-0 place-items-center rounded-xl bg-primary-50 text-primary-600">
            <component :is="c.icon" class="h-6 w-6" />
          </span>
          <div>
            <p class="font-heading font-semibold text-ink">{{ c.title }}</p>
            <p class="mt-1 text-sm text-muted">{{ c.desc }}</p>
          </div>
        </div>
      </div>

      <!-- FAQ + Contact -->
      <div class="mt-12 grid gap-8 lg:grid-cols-[1fr_380px]">
        <!-- FAQ accordion -->
        <div>
          <h2 class="section-title mb-5">{{ $t('support.popularQuestions') }}</h2>
          <div v-if="filteredFaqs.length" class="space-y-3">
            <div v-for="(f, i) in filteredFaqs" :key="i" class="card overflow-hidden">
              <button
                class="flex w-full items-center justify-between gap-4 p-4 text-start transition hover:bg-slate-50"
                @click="toggle(i)"
              >
                <span class="font-medium text-ink">{{ f.q }}</span>
                <ChevronDown class="h-5 w-5 shrink-0 text-slate-400 transition" :class="openIndex === i ? 'rotate-180' : ''" />
              </button>
              <div v-if="openIndex === i" class="border-t border-slate-100 p-4 pt-3 text-sm leading-7 text-muted">
                {{ f.a }}
              </div>
            </div>
          </div>
          <EmptyState v-else :title="$t('support.noResults')" :message="$t('support.noResultsMsg')" />
        </div>

        <!-- Contact -->
        <aside class="space-y-4">
          <!-- Direct channels -->
          <div class="card p-5">
            <a :href="`mailto:${SUPPORT_EMAIL}`" class="flex items-center gap-3 rounded-lg p-2 transition hover:bg-slate-50">
              <span class="grid h-10 w-10 place-items-center rounded-lg bg-primary-50 text-primary-600"><Mail class="h-5 w-5" /></span>
              <span><span class="block text-xs text-muted">{{ $t('support.emailUs') }}</span><span class="block text-sm font-semibold text-ink">{{ SUPPORT_EMAIL }}</span></span>
            </a>
            <a :href="`tel:${SUPPORT_PHONE.replace(/\s/g, '')}`" class="flex items-center gap-3 rounded-lg p-2 transition hover:bg-slate-50">
              <span class="grid h-10 w-10 place-items-center rounded-lg bg-emerald-50 text-emerald-600"><Phone class="h-5 w-5" /></span>
              <span><span class="block text-xs text-muted">{{ $t('support.callUs') }}</span><span class="block text-sm font-semibold text-ink" dir="ltr">{{ SUPPORT_PHONE }}</span></span>
            </a>
            <a :href="`https://wa.me/${SUPPORT_WHATSAPP}`" target="_blank" rel="noopener" class="flex items-center gap-3 rounded-lg p-2 transition hover:bg-slate-50">
              <span class="grid h-10 w-10 place-items-center rounded-lg bg-green-50 text-green-600"><MessageCircle class="h-5 w-5" /></span>
              <span><span class="block text-xs text-muted">{{ $t('support.whatsapp') }}</span><span class="block text-sm font-semibold text-ink" dir="ltr">{{ SUPPORT_PHONE }}</span></span>
            </a>
            <div class="flex items-center gap-3 rounded-lg p-2">
              <span class="grid h-10 w-10 place-items-center rounded-lg bg-slate-100 text-slate-500"><Clock class="h-5 w-5" /></span>
              <span><span class="block text-xs text-muted">{{ $t('support.workingHours') }}</span><span class="block text-sm font-semibold text-ink">{{ $t('support.hoursValue') }}</span></span>
            </div>
          </div>

          <!-- Contact form -->
          <div class="card p-5">
            <h3 class="font-heading font-semibold text-ink">{{ $t('support.contactTitle') }}</h3>
            <p class="mt-1 text-sm text-muted">{{ $t('support.contactSubtitle') }}</p>
            <form class="mt-4 space-y-3" @submit.prevent="submit">
              <FormField v-model="form.name" :label="$t('support.yourName')" required />
              <FormField v-model="form.email" :label="$t('common.email')" type="email" placeholder="you@example.com" required />
              <FormField v-model="form.subject" :label="$t('support.subject')" required />
              <div>
                <label class="label">{{ $t('support.message') }}</label>
                <textarea v-model="form.message" rows="4" class="input" required></textarea>
              </div>
              <button type="submit" class="btn btn-primary w-full"><Send class="h-4 w-4" /> {{ $t('support.send') }}</button>
              <p class="text-center text-xs text-slate-400">{{ $t('support.responseTime') }}</p>
            </form>
          </div>
        </aside>
      </div>
    </div>
  </div>
</template>
