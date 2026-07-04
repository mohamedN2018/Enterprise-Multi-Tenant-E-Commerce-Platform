<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import {
  Phone,
  ChevronDown,
  Search,
  Shuffle,
  Heart,
  ShoppingCart,
  User,
  LogOut,
  LayoutDashboard,
  Menu,
  X,
  Facebook,
  Twitter,
  Instagram,
  Linkedin,
  Mail,
  MapPin,
  LifeBuoy,
  Truck,
  Tag
} from 'lucide-vue-next';
import { useAuthStore } from '@/stores/auth';
import { useCartStore } from '@/stores/cart';
import { storefront } from '@/services/storefront';
import { useI18n } from '@/i18n';
import { useTheme } from '@/theme';
import CartFlyout from '@/components/CartFlyout.vue';
import SearchBox from '@/components/SearchBox.vue';

const router = useRouter();
const auth = useAuthStore();
const cart = useCartStore();
const { t } = useI18n();
const { theme } = useTheme();

// Support contact points (each shortcut has a distinct function).
const SUPPORT_PHONE = '+0121234567890';
const SUPPORT_EMAIL = 'support@q-shop.com';

const categories = ref([]);
const catOpen = ref(false);
const accountOpen = ref(false);
const mobileNav = ref(false);
const searchOpen = ref(false);

const nav = [
  { key: 'home', to: { name: 'home' } },
  { key: 'shop', to: { name: 'products' } },
  { key: 'stores', to: { name: 'stores' } },
  { key: 'deals', to: { name: 'products', query: { on_sale: 1 } } }
];

const cartCount = computed(() => cart.count);
const cartTotal = computed(() => cart.cart?.total || '0.00');
const currency = computed(() => cart.shopStore?.currency || 'USD');

const goCategory = (name) => {
  catOpen.value = false;
  mobileNav.value = false;
  router.push({ name: 'products', query: { category: name } });
};

// Close all menus whenever the route changes.
watch(
  () => router.currentRoute.value.fullPath,
  () => {
    mobileNav.value = false;
    catOpen.value = false;
    accountOpen.value = false;
    searchOpen.value = false;
  }
);

const logout = async () => {
  await auth.logout();
  accountOpen.value = false;
  router.push({ name: 'home' });
};

onMounted(async () => {
  if (auth.isAuthenticated) cart.refreshCart();
  try {
    const res = await storefront.categories();
    categories.value = res.data || [];
  } catch {
    categories.value = [];
  }
});
</script>

<template>
  <div class="flex min-h-screen flex-col bg-white text-ink">
    <!-- Top thin bar: support shortcuts + account (each item has a function) -->
    <div class="border-b border-slate-200 dark:border-slate-800">
      <div class="container flex h-11 items-center gap-4 text-sm">
        <div class="hidden items-center gap-4 text-muted lg:flex">
          <RouterLink :to="{ name: 'support' }" class="flex items-center gap-1.5 hover:text-primary-600"><LifeBuoy class="h-4 w-4" /> {{ t('nav.help') }}</RouterLink>
          <a :href="`tel:${SUPPORT_PHONE}`" class="flex items-center gap-1.5 hover:text-primary-600" dir="ltr"><Phone class="h-4 w-4" /> {{ t('nav.support') }}</a>
          <a :href="`mailto:${SUPPORT_EMAIL}`" class="flex items-center gap-1.5 hover:text-primary-600"><Mail class="h-4 w-4" /> {{ t('nav.contact') }}</a>
          <RouterLink :to="{ name: 'account' }" class="flex items-center gap-1.5 hover:text-primary-600"><Truck class="h-4 w-4" /> {{ t('nav.trackOrder') }}</RouterLink>
        </div>
        <div class="ms-auto flex items-center gap-3 text-muted">
          <div class="hidden items-center gap-1 lg:flex">
            <span class="text-ink">{{ t('nav.callUs') }}:</span>
            <a :href="`tel:${SUPPORT_PHONE}`" class="hover:text-primary-600" dir="ltr">(+012) 1234 567890</a>
          </div>
          <div class="relative">
            <button class="flex items-center gap-1 hover:text-primary-600" @click="accountOpen = !accountOpen">
              <User class="h-4 w-4" /> <span class="hidden sm:inline">{{ auth.isAuthenticated ? auth.displayName : t('nav.myAccount') }}</span>
              <ChevronDown class="h-3 w-3" />
            </button>
            <div
              v-if="accountOpen"
              class="absolute end-0 z-[100] mt-2 w-52 overflow-hidden rounded-lg border border-slate-200 bg-white py-1 shadow-pop dark:border-slate-700 dark:bg-slate-800"
              @click="accountOpen = false"
            >
              <template v-if="auth.isAuthenticated">
                <RouterLink :to="{ name: 'account' }" class="dropdown-item"><User class="h-4 w-4" /> {{ t('nav.myAccount') }}</RouterLink>
                <RouterLink :to="{ name: 'admin-dashboard' }" class="dropdown-item"><LayoutDashboard class="h-4 w-4" /> {{ t('nav.dashboard') }}</RouterLink>
                <RouterLink :to="{ name: 'cart' }" class="dropdown-item"><ShoppingCart class="h-4 w-4" /> {{ t('nav.myCart') }}</RouterLink>
                <button class="dropdown-item w-full text-secondary-500 hover:bg-secondary-500 hover:text-white" @click="logout">
                  <LogOut class="h-4 w-4" /> {{ t('nav.logout') }}
                </button>
              </template>
              <template v-else>
                <RouterLink :to="{ name: 'login' }" class="dropdown-item">{{ t('nav.login') }}</RouterLink>
                <RouterLink :to="{ name: 'register' }" class="dropdown-item">{{ t('nav.register') }}</RouterLink>
              </template>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Main header: logo + search + actions -->
    <div class="border-b border-slate-100 bg-white dark:bg-slate-900">
      <div class="container flex items-center gap-3 py-3 lg:gap-4 lg:py-4">
        <RouterLink :to="{ name: 'home' }" class="flex shrink-0 items-center">
          <img :src="theme === 'dark' ? '/brand/dark-logo.png' : '/brand/qtech-logo.png'" alt="q-shop" class="h-9 w-auto lg:h-12" />
        </RouterLink>

        <!-- Desktop interactive search -->
        <div class="hidden lg:block lg:flex-1 lg:max-w-2xl">
          <SearchBox />
        </div>

        <div class="ms-auto flex items-center gap-2 lg:gap-3">
          <!-- Mobile: tap the icon to open the search -->
          <button
            class="grid h-11 w-11 place-items-center rounded-full border border-slate-200 text-ink transition hover:border-primary-500 hover:text-primary-600 lg:hidden dark:border-slate-700"
            :title="t('common.search')"
            @click="searchOpen = !searchOpen"
          >
            <component :is="searchOpen ? X : Search" class="h-4 w-4" />
          </button>
          <RouterLink :to="{ name: 'products' }" class="hidden h-11 w-11 place-items-center rounded-full border border-slate-200 text-ink hover:border-primary-500 hover:text-primary-600 sm:grid dark:border-slate-700" :title="t('nav.compare')">
            <Shuffle class="h-4 w-4" />
          </RouterLink>
          <RouterLink :to="{ name: 'account' }" class="grid h-11 w-11 place-items-center rounded-full border border-slate-200 text-ink hover:border-primary-500 hover:text-primary-600 dark:border-slate-700" :title="t('nav.wishlist')">
            <Heart class="h-4 w-4" />
          </RouterLink>
          <div class="relative">
            <button class="flex items-center gap-2 text-ink hover:text-primary-600" :title="t('nav.myCart')" @click="cart.openDrawer()">
              <span class="relative grid h-11 w-11 place-items-center rounded-full border border-slate-200 dark:border-slate-700">
                <ShoppingCart class="h-4 w-4" />
                <span v-if="cartCount" class="absolute -end-1 -top-1 grid h-5 min-w-5 place-items-center rounded-full bg-secondary-500 px-1 text-[11px] font-bold text-white">{{ cartCount }}</span>
              </span>
              <span class="whitespace-nowrap text-sm font-semibold sm:text-base">{{ cartTotal }} {{ currency }}</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Mobile search bar (opens on tap) -->
      <div v-if="searchOpen" class="container pb-3 lg:hidden">
        <SearchBox autofocus @navigate="searchOpen = false" />
      </div>
    </div>

    <!-- Orange category nav bar (sticky: follows on scroll) -->
    <div class="sticky top-0 z-40 bg-primary-600 shadow-md">
      <div class="container flex items-stretch">
        <!-- All categories -->
        <div class="relative hidden w-64 shrink-0 lg:block">
          <button class="flex h-full w-full items-center gap-2 py-3.5 text-lg font-medium text-white" @click="catOpen = !catOpen">
            <Menu class="h-5 w-5" /> {{ t('nav.allCategories') }} <ChevronDown class="ms-auto h-4 w-4" />
          </button>
          <div v-if="catOpen" class="absolute start-0 top-full z-[100] w-64 rounded-b-lg bg-lightbg py-1 shadow-pop dark:border dark:border-slate-700">
            <button
              v-for="c in categories"
              :key="c.name"
              class="flex w-full items-center justify-between border-b border-black/5 px-4 py-2.5 text-sm text-ink transition last:border-0 hover:bg-primary-600 hover:text-white"
              @click="goCategory(c.name)"
            >
              <span>{{ c.name }}</span>
              <span class="text-xs opacity-70">({{ c.product_count }})</span>
            </button>
            <p v-if="!categories.length" class="px-4 py-3 text-sm text-muted">{{ t('categoriesPage.noCategories') }}</p>
          </div>
        </div>

        <!-- Horizontal nav -->
        <nav class="hidden flex-1 items-center lg:flex">
          <RouterLink
            v-for="item in nav"
            :key="item.key"
            :to="item.to"
            class="px-4 py-3.5 font-heading text-[17px] font-medium text-white/90 transition hover:text-white"
            active-class="text-white"
          >
            {{ t('nav.' + item.key) }}
          </RouterLink>
          <RouterLink :to="{ name: 'support' }" class="px-4 py-3.5 font-heading text-[17px] font-medium text-white/90 transition hover:text-white">{{ t('nav.support') }}</RouterLink>
          <RouterLink :to="{ name: 'account' }" class="px-4 py-3.5 font-heading text-[17px] font-medium text-white/90 transition hover:text-white">{{ t('nav.account') }}</RouterLink>
          <a :href="`tel:${SUPPORT_PHONE}`" class="btn btn-secondary ms-auto my-2 rounded-full" dir="ltr"><Phone class="h-4 w-4" /> (+012) 1234 567890</a>
        </nav>

        <!-- Mobile nav toggle -->
        <button class="ms-auto flex items-center gap-2 py-3 text-white lg:hidden" @click="mobileNav = !mobileNav">
          <component :is="mobileNav ? X : Menu" class="h-6 w-6" /> {{ t('nav.menu') }}
        </button>
      </div>

      <!-- Mobile nav -->
      <div v-if="mobileNav" class="max-h-[80vh] overflow-y-auto border-t border-white/10 bg-primary-600 lg:hidden">
        <div class="container space-y-1 py-3">
          <!-- Primary links -->
          <RouterLink v-for="item in nav" :key="item.label" :to="item.to" class="block rounded-lg px-3 py-2.5 font-heading font-medium text-white hover:bg-white/10" @click="mobileNav = false">{{ t('nav.' + item.key) }}</RouterLink>

          <!-- Account -->
          <div class="mt-2 space-y-1 border-t border-white/10 pt-2">
            <template v-if="auth.isAuthenticated">
              <RouterLink :to="{ name: 'account' }" class="flex items-center gap-2 rounded-lg px-3 py-2.5 font-medium text-white hover:bg-white/10" @click="mobileNav = false"><User class="h-4 w-4" /> {{ t('nav.myAccount') }}</RouterLink>
              <RouterLink :to="{ name: 'admin-dashboard' }" class="flex items-center gap-2 rounded-lg px-3 py-2.5 font-medium text-white hover:bg-white/10" @click="mobileNav = false"><LayoutDashboard class="h-4 w-4" /> {{ t('nav.dashboard') }}</RouterLink>
              <button class="flex w-full items-center gap-2 rounded-lg px-3 py-2.5 font-medium text-white hover:bg-white/10" @click="logout"><LogOut class="h-4 w-4" /> {{ t('nav.logout') }}</button>
            </template>
            <template v-else>
              <RouterLink :to="{ name: 'login' }" class="flex items-center gap-2 rounded-lg px-3 py-2.5 font-medium text-white hover:bg-white/10" @click="mobileNav = false"><User class="h-4 w-4" /> {{ t('nav.login') }}</RouterLink>
              <RouterLink :to="{ name: 'register' }" class="flex items-center gap-2 rounded-lg px-3 py-2.5 font-medium text-white hover:bg-white/10" @click="mobileNav = false"><ChevronDown class="h-4 w-4 rotate-[-90deg] rtl:rotate-90" /> {{ t('nav.register') }}</RouterLink>
            </template>
            <RouterLink :to="{ name: 'support' }" class="flex items-center gap-2 rounded-lg px-3 py-2.5 font-medium text-white hover:bg-white/10" @click="mobileNav = false"><Phone class="h-4 w-4" /> {{ t('nav.support') }}</RouterLink>
          </div>

          <!-- Categories -->
          <div v-if="categories.length" class="mt-2 border-t border-white/10 pt-2">
            <p class="px-3 pb-1 text-xs font-semibold uppercase tracking-wide text-white/70">{{ t('nav.categories') }}</p>
            <button v-for="c in categories" :key="c.name" class="flex w-full items-center justify-between rounded-lg px-3 py-2 text-sm text-white/90 hover:bg-white/10" @click="goCategory(c.name)">
              <span>{{ c.name }}</span>
              <span class="text-xs text-white/60">({{ c.product_count }})</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Content -->
    <main class="flex-1">
      <RouterView v-slot="{ Component }">
        <Transition name="page" mode="out-in">
          <component :is="Component" />
        </Transition>
      </RouterView>
    </main>

    <!-- Footer -->
    <footer class="bg-ink text-slate-300">
      <div class="container grid gap-8 py-14 sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <img src="/brand/dark-logo.png" alt="q-shop" class="mb-4 h-16 w-auto" />
          <p class="text-sm leading-7">{{ t('footer.about') }}</p>
          <div class="mt-4 flex gap-2">
            <a href="#" class="grid h-9 w-9 place-items-center rounded-full border border-white/20 hover:bg-primary-600 hover:text-white"><Facebook class="h-4 w-4" /></a>
            <a href="#" class="grid h-9 w-9 place-items-center rounded-full border border-white/20 hover:bg-primary-600 hover:text-white"><Twitter class="h-4 w-4" /></a>
            <a href="#" class="grid h-9 w-9 place-items-center rounded-full border border-white/20 hover:bg-primary-600 hover:text-white"><Instagram class="h-4 w-4" /></a>
            <a href="#" class="grid h-9 w-9 place-items-center rounded-full border border-white/20 hover:bg-primary-600 hover:text-white"><Linkedin class="h-4 w-4" /></a>
          </div>
        </div>
        <div>
          <h4 class="mb-4 font-heading text-lg font-semibold text-white">{{ t('footer.account') }}</h4>
          <ul class="space-y-2 text-sm">
            <li><RouterLink :to="{ name: 'account' }" class="text-slate-300 hover:text-primary-500 hover:tracking-wide">{{ t('footer.myAccount') }}</RouterLink></li>
            <li><RouterLink :to="{ name: 'account' }" class="text-slate-300 hover:text-primary-500 hover:tracking-wide">{{ t('footer.orderHistory') }}</RouterLink></li>
            <li><RouterLink :to="{ name: 'account' }" class="text-slate-300 hover:text-primary-500 hover:tracking-wide">{{ t('nav.wishlist') }}</RouterLink></li>
            <li><RouterLink :to="{ name: 'cart' }" class="text-slate-300 hover:text-primary-500 hover:tracking-wide">{{ t('nav.myCart') }}</RouterLink></li>
          </ul>
        </div>
        <div>
          <h4 class="mb-4 font-heading text-lg font-semibold text-white">{{ t('footer.quickLinks') }}</h4>
          <ul class="space-y-2 text-sm">
            <li><RouterLink :to="{ name: 'products' }" class="text-slate-300 hover:text-primary-500 hover:tracking-wide">{{ t('nav.shop') }}</RouterLink></li>
            <li><RouterLink :to="{ name: 'stores' }" class="text-slate-300 hover:text-primary-500 hover:tracking-wide">{{ t('nav.stores') }}</RouterLink></li>
            <li><RouterLink :to="{ name: 'seller-login' }" class="text-slate-300 hover:text-primary-500 hover:tracking-wide">{{ t('footer.sellOn') }}</RouterLink></li>
            <li><RouterLink :to="{ name: 'support' }" class="text-slate-300 hover:text-primary-500 hover:tracking-wide">{{ t('nav.support') }}</RouterLink></li>
            <li><RouterLink :to="{ name: 'account' }" class="text-slate-300 hover:text-primary-500 hover:tracking-wide">{{ t('nav.account') }}</RouterLink></li>
          </ul>
        </div>
        <div>
          <h4 class="mb-4 font-heading text-lg font-semibold text-white">{{ t('footer.newsletter') }}</h4>
          <p class="mb-3 text-sm">{{ t('footer.newsletterMsg') }}</p>
          <form class="flex overflow-hidden rounded-full bg-white" @submit.prevent>
            <input type="email" :placeholder="t('footer.yourEmail')" class="w-full border-0 bg-transparent px-4 py-2.5 text-sm text-ink focus:outline-none" />
            <button class="btn btn-primary rounded-none px-5"><Mail class="h-4 w-4" /></button>
          </form>
          <p class="mt-4 flex items-center gap-2 text-sm"><MapPin class="h-4 w-4 text-primary-500" /> 123 Market Street, Cairo</p>
        </div>
      </div>
      <div class="bg-primary-600">
        <div class="container flex flex-col items-center justify-between gap-2 py-4 text-sm text-white sm:flex-row">
          <p>{{ t('footer.rights') }}</p>
          <p class="opacity-90">{{ t('footer.builtOn') }}</p>
        </div>
      </div>
    </footer>

    <!-- Global slide-in cart -->
    <CartFlyout />
  </div>
</template>
