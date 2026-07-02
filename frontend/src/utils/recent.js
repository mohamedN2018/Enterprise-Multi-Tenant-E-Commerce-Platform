// "Recently viewed" products, persisted in localStorage (newest first).
const KEY = 'recently_viewed';
const MAX = 8;

export function getRecentlyViewed() {
  try {
    return JSON.parse(localStorage.getItem(KEY) || '[]');
  } catch {
    return [];
  }
}

export function pushRecentlyViewed(product) {
  if (!product?.id) return;
  const slim = {
    id: product.id,
    name: product.name,
    slug: product.slug,
    store: product.store,
    store_slug: product.store_slug,
    price: product.price,
    compare_at_price: product.compare_at_price,
    currency: product.currency,
    rating: product.rating,
    review_count: product.review_count
  };
  try {
    const list = getRecentlyViewed().filter((p) => p.id !== product.id);
    list.unshift(slim);
    localStorage.setItem(KEY, JSON.stringify(list.slice(0, MAX)));
  } catch {
    /* ignore quota/serialization errors */
  }
}
