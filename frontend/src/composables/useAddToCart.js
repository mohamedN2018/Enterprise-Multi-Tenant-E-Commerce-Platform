import { ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { useCartStore } from '@/stores/cart';
import { useUiStore } from '@/stores/ui';
import { storefront } from '@/services/storefront';
import { errorMessage } from '@/services/http';
import { t } from '@/i18n';

// Adds a storefront product to the (store-scoped) cart. Resolves the default
// purchasable variant when the caller only has a list-level product.
export function useAddToCart() {
  const route = useRoute();
  const router = useRouter();
  const auth = useAuthStore();
  const cart = useCartStore();
  const ui = useUiStore();
  const adding = ref(null); // id of the product currently being added

  const pickVariant = (variants = []) =>
    variants.find((v) => v.is_default && v.in_stock !== false) ||
    variants.find((v) => v.in_stock !== false) ||
    variants[0] ||
    null;

  const scopeToStore = (product) => {
    cart.setShopStore({
      id: product.store,
      slug: product.store_slug,
      name: product.store_slug,
      currency: product.currency
    });
  };

  const add = async (product, { variant = null, quantity = 1 } = {}) => {
    if (!auth.isAuthenticated) {
      ui.info(t('product.signInToShop'));
      router.push({ name: 'login', query: { redirect: route.fullPath } });
      return false;
    }
    adding.value = product.id;
    try {
      scopeToStore(product);
      let chosen = variant;
      if (!chosen) {
        // List products carry no variants — fetch detail to find the default.
        const detail = product.variants ? product : (await storefront.product(product.id)).data;
        chosen = pickVariant(detail.variants);
      }
      if (!chosen) {
        ui.error(t('product.unavailableToast'));
        return false;
      }
      await cart.addItem(chosen.id, quantity);
      ui.success(t('product.addedToCart'));
      cart.openDrawer();
      return true;
    } catch (e) {
      ui.error(errorMessage(e));
      return false;
    } finally {
      adding.value = null;
    }
  };

  return { add, adding };
}
