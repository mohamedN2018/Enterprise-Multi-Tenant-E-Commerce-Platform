<script setup>
import { computed } from 'vue';
import { Quote, Star } from 'lucide-vue-next';
import PageHero from '@/components/ui/PageHero.vue';
import { locale } from '@/i18n';

// Bilingual customer reviews (self-contained; not part of the shared catalog).
const reviews = [
  { name: 'سارة م.', ar: 'شحن سريع وجودة المنتج فاقت توقعاتي. أصبح سوقي المفضل!', en: 'Fast shipping and the quality exceeded my expectations. My favorite marketplace now!' },
  { name: 'أحمد ك.', ar: 'أحب تنوّع المتاجر المستقلة. وجدت بالضبط ما أبحث عنه بسعر رائع.', en: 'I love the variety of independent stores. Found exactly what I wanted at a great price.' },
  { name: 'إيلينا ر.', ar: 'الدفع كان سلسًا وميزة المفضلة عملية جدًا. أنصح بـ q-shop بشدة.', en: 'Checkout was smooth and the wishlist is so handy. Highly recommend q-shop.' },
  { name: 'ياسمين ع.', ar: 'خدمة العملاء ردّت بسرعة وحلّت مشكلتي في دقائق. تجربة احترافية.', en: 'Support replied quickly and solved my issue in minutes. A professional experience.' },
  { name: 'كريم ن.', ar: 'التوصيل كان في الموعد والتغليف ممتاز. سأعود للشراء بالتأكيد.', en: 'Delivery was on time and the packaging was excellent. I will definitely buy again.' },
  { name: 'ليلى ف.', ar: 'أسعار منافسة وعروض حقيقية. أفضل مكان للتسوّق من بائعين موثوقين.', en: 'Competitive prices and real deals. The best place to shop from trusted sellers.' }
];

const list = computed(() =>
  reviews.map((r) => ({ name: r.name, text: locale.value === 'en' ? r.en : r.ar }))
);
</script>

<template>
  <div>
    <PageHero :title="$t('home.testimonials')" :items="[{ label: $t('home.testimonials') }]" />
    <div class="container py-12">
      <p class="mx-auto mb-10 max-w-2xl text-center text-muted">{{ $t('home.testimonialsSubtitle') }}</p>
      <div class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <div v-for="tm in list" :key="tm.name" class="card p-6">
          <Quote class="h-8 w-8 text-primary-200" />
          <p class="mt-3 leading-7 text-muted">{{ tm.text }}</p>
          <div class="mt-4 flex items-center gap-3">
            <span class="grid h-10 w-10 place-items-center rounded-full bg-primary-100 font-bold text-primary-700">{{ tm.name.charAt(0) }}</span>
            <div>
              <p class="font-semibold">{{ tm.name }}</p>
              <p class="flex items-center gap-1 text-xs text-muted"><Star class="h-3 w-3 fill-primary-600 text-primary-600" /> {{ $t('home.verifiedBuyer') }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
