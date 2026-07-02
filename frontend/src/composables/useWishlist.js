import { ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { useCartStore } from '@/stores/cart';
import { useUiStore } from '@/stores/ui';
import { shop } from '@/services/shop';
import { storefront } from '@/services/storefront';
import { errorMessage } from '@/services/http';

// Adds a storefront product to the (store-scoped) wishlist, resolving the
// default variant when the caller only has a list-level product.
export function useWishlist() {
  const route = useRoute();
  const router = useRouter();
  const auth = useAuthStore();
  const cart = useCartStore();
  const ui = useUiStore();
  const saving = ref(null);

  const pickVariant = (variants = []) =>
    variants.find((v) => v.is_default) || variants[0] || null;

  const add = async (product, { variant = null } = {}) => {
    if (!auth.isAuthenticated) {
      ui.info('Please sign in to save items.');
      router.push({ name: 'login', query: { redirect: route.fullPath } });
      return false;
    }
    saving.value = product.id;
    try {
      // Wishlist is store-scoped; point the shop store at this product's store.
      cart.setShopStore({
        id: product.store,
        slug: product.store_slug,
        name: product.store_slug,
        currency: product.currency
      });
      let chosen = variant;
      if (!chosen) {
        const detail = product.variants ? product : (await storefront.product(product.id)).data;
        chosen = pickVariant(detail.variants);
      }
      if (!chosen) {
        ui.error('This product is currently unavailable.');
        return false;
      }
      await shop.addWishlist(cart.headers, { variant_id: chosen.id });
      ui.success('Saved to wishlist.');
      return true;
    } catch (e) {
      const msg = errorMessage(e);
      // A duplicate is a friendly "already saved", not an error.
      ui.info(/already|exist/i.test(msg) ? 'Already in your wishlist.' : msg);
      return false;
    } finally {
      saving.value = null;
    }
  };

  return { add, saving };
}
