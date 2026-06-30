// Registry of backend resources surfaced in the admin.
//
// Each entry drives both a sidebar menu item and a generic list page
// (see views/resource/ResourcePage + components/ResourceTable). `columns` is
// optional — when omitted the table auto-derives columns from the API response.

const money = (v, row) => (v == null ? '—' : `${v} ${row.currency || ''}`.trim());
const bool = (v) => (v ? 'Yes' : 'No');
const date = (v) => (v ? String(v).slice(0, 10) : '—');

export const RESOURCE_GROUPS = [
  {
    id: 'catalog',
    title: 'Catalog',
    iconname: 'inventory_2',
    resources: [
      {
        key: 'products',
        label: 'Products',
        endpoint: '/catalog/products/',
        columns: [
          { key: 'name', label: 'Name' },
          { key: 'status', label: 'Status', badge: true },
          { key: 'product_type', label: 'Type' },
          { key: 'created_at', label: 'Created', format: date }
        ]
      },
      { key: 'categories', label: 'Categories', endpoint: '/catalog/categories/' },
      { key: 'brands', label: 'Brands', endpoint: '/catalog/brands/' },
      { key: 'attributes', label: 'Attributes', endpoint: '/catalog/attributes/' }
    ]
  },
  {
    id: 'sales',
    title: 'Sales',
    iconname: 'receipt_long',
    resources: [
      {
        key: 'orders',
        label: 'Orders',
        endpoint: '/orders/',
        columns: [
          { key: 'number', label: 'Number' },
          { key: 'status', label: 'Status', badge: true },
          { key: 'total', label: 'Total', format: money },
          { key: 'created_at', label: 'Placed', format: date }
        ]
      },
      {
        key: 'payments',
        label: 'Payments',
        endpoint: '/payments/',
        columns: [
          { key: 'gateway', label: 'Gateway' },
          { key: 'amount', label: 'Amount', format: money },
          { key: 'status', label: 'Status', badge: true },
          { key: 'created_at', label: 'Created', format: date }
        ]
      },
      {
        key: 'returns',
        label: 'Returns (RMA)',
        endpoint: '/returns/',
        columns: [
          { key: 'status', label: 'Status', badge: true },
          { key: 'resolution', label: 'Resolution' },
          { key: 'refund_amount', label: 'Refund' },
          { key: 'created_at', label: 'Created', format: date }
        ]
      }
    ]
  },
  {
    id: 'inventory',
    title: 'Inventory',
    iconname: 'warehouse',
    resources: [
      { key: 'warehouses', label: 'Warehouses', endpoint: '/inventory/warehouses/' },
      {
        key: 'stock',
        label: 'Stock levels',
        endpoint: '/inventory/stock/',
        columns: [
          { key: 'variant', label: 'Variant' },
          { key: 'quantity', label: 'On hand' },
          { key: 'available_quantity', label: 'Available' },
          { key: 'is_low_stock', label: 'Low?', format: bool, badge: true }
        ]
      },
      {
        key: 'movements',
        label: 'Stock movements',
        endpoint: '/inventory/movements/',
        columns: [
          { key: 'movement_type', label: 'Type', badge: true },
          { key: 'quantity_change', label: 'Δ Qty' },
          { key: 'resulting_quantity', label: 'Result' },
          { key: 'created_at', label: 'When', format: date }
        ]
      }
    ]
  },
  {
    id: 'procurement',
    title: 'Procurement',
    iconname: 'local_shipping',
    resources: [
      { key: 'suppliers', label: 'Suppliers', endpoint: '/procurement/suppliers/' },
      {
        key: 'purchase-orders',
        label: 'Purchase orders',
        endpoint: '/procurement/purchase-orders/',
        columns: [
          { key: 'number', label: 'Number' },
          { key: 'status', label: 'Status', badge: true },
          { key: 'subtotal', label: 'Subtotal' },
          { key: 'created_at', label: 'Created', format: date }
        ]
      },
      {
        key: 'batches',
        label: 'Batches / lots',
        endpoint: '/procurement/batches/',
        columns: [
          { key: 'batch_number', label: 'Batch' },
          { key: 'quantity', label: 'Qty' },
          { key: 'expiry_date', label: 'Expiry', format: date }
        ]
      },
      { key: 'serials', label: 'Serial numbers', endpoint: '/procurement/serials/' },
      { key: 'boms', label: 'Bills of materials', endpoint: '/procurement/boms/' },
      {
        key: 'work-orders',
        label: 'Work orders',
        endpoint: '/procurement/work-orders/',
        columns: [
          { key: 'number', label: 'Number' },
          { key: 'status', label: 'Status', badge: true },
          { key: 'quantity', label: 'Qty' },
          { key: 'created_at', label: 'Created', format: date }
        ]
      }
    ]
  },
  {
    id: 'marketing',
    title: 'Marketing',
    iconname: 'campaign',
    resources: [
      {
        key: 'coupons',
        label: 'Coupons',
        endpoint: '/promotions/coupons/',
        columns: [
          { key: 'code', label: 'Code' },
          { key: 'discount_type', label: 'Type' },
          { key: 'value', label: 'Value' },
          { key: 'used_count', label: 'Used' },
          { key: 'is_active', label: 'Active', format: bool, badge: true }
        ]
      },
      {
        key: 'campaigns',
        label: 'Campaigns',
        endpoint: '/promotions/campaigns/',
        columns: [
          { key: 'name', label: 'Name' },
          { key: 'campaign_type', label: 'Type', badge: true },
          { key: 'priority', label: 'Priority' },
          { key: 'is_active', label: 'Active', format: bool, badge: true }
        ]
      },
      { key: 'price-groups', label: 'Customer groups', endpoint: '/pricing/groups/' },
      { key: 'price-rules', label: 'Price rules', endpoint: '/pricing/rules/' }
    ]
  },
  {
    id: 'finance',
    title: 'Finance',
    iconname: 'payments',
    resources: [
      { key: 'tax-zones', label: 'Tax zones', endpoint: '/finance/tax-zones/' },
      { key: 'currencies', label: 'Currencies', endpoint: '/finance/currencies/' },
      { key: 'exchange-rates', label: 'Exchange rates', endpoint: '/finance/exchange-rates/' },
      {
        key: 'payouts',
        label: 'Payouts',
        endpoint: '/payouts/',
        columns: [
          { key: 'amount', label: 'Amount' },
          { key: 'status', label: 'Status', badge: true },
          { key: 'created_at', label: 'Created', format: date }
        ]
      },
      {
        key: 'ledger',
        label: 'Seller ledger',
        endpoint: '/payouts/ledger/',
        columns: [
          { key: 'entry_type', label: 'Type', badge: true },
          { key: 'net_amount', label: 'Net' },
          { key: 'balance_after', label: 'Balance' },
          { key: 'created_at', label: 'When', format: date }
        ]
      },
      { key: 'gift-cards', label: 'Gift cards', endpoint: '/rewards/gift-cards/' }
    ]
  },
  {
    id: 'engagement',
    title: 'Customers',
    iconname: 'reviews',
    resources: [
      {
        key: 'reviews',
        label: 'Reviews (moderation)',
        endpoint: '/reviews/moderation/',
        columns: [
          { key: 'rating', label: 'Rating' },
          { key: 'status', label: 'Status', badge: true },
          { key: 'is_verified_purchase', label: 'Verified', format: bool },
          { key: 'created_at', label: 'Created', format: date }
        ]
      }
    ]
  },
  {
    id: 'operations',
    title: 'Operations',
    iconname: 'tune',
    resources: [
      { key: 'shipping-zones', label: 'Shipping zones', endpoint: '/shipping/zones/' },
      {
        key: 'fraud',
        label: 'Fraud review',
        endpoint: '/fraud/checks/',
        columns: [
          { key: 'order_number', label: 'Order' },
          { key: 'score', label: 'Score' },
          { key: 'decision', label: 'Decision', badge: true },
          { key: 'resolution', label: 'Resolution' }
        ]
      },
      {
        key: 'analytics-events',
        label: 'Analytics events',
        endpoint: '/analytics/events/',
        columns: [
          { key: 'event_type', label: 'Event', badge: true },
          { key: 'occurred_at', label: 'When', format: date }
        ]
      }
    ]
  }
];

export const RESOURCES = Object.fromEntries(
  RESOURCE_GROUPS.flatMap((g) => g.resources.map((r) => [r.key, { ...r, group: g.id }]))
);

export const findResource = (key) => RESOURCES[key];
