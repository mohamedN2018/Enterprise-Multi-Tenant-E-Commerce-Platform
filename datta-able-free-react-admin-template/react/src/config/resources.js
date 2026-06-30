// Registry of backend resources surfaced in the admin.
//
// Each entry drives both a sidebar menu item and a generic page set:
//   - list   : components/ResourceTable (columns optional — auto-derived if omitted)
//   - create/edit : components/ResourceForm, driven by `fields`
//   - detail : views/resource/ResourceDetail, with domain `actions`
//
// Field types: text | textarea | number | money | checkbox | select | date | datetime | email
// Select fields may use `options` (static) or `optionsEndpoint` (async FK picker).
// Actions are POST calls to a row-scoped endpoint; they return the updated record.

const money = (v, row) => (v == null ? '—' : `${v} ${row.currency || ''}`.trim());
const bool = (v) => (v ? 'Yes' : 'No');
const date = (v) => (v ? String(v).slice(0, 10) : '—');

// Shared choice sets (mirrors the DRF serializers).
const PRODUCT_TYPE = ['physical', 'digital'];
const PRODUCT_KIND = ['simple', 'configurable', 'bundle', 'kit', 'composite'];
const PRODUCT_STATUS = ['draft', 'published', 'archived'];
const DISCOUNT_TYPE = ['percentage', 'fixed'];
const CAMPAIGN_TYPE = ['flash_sale', 'buy_x_get_y', 'order_discount', 'free_shipping'];

const META_FIELDS = [
  { name: 'meta_title', label: 'Meta title' },
  { name: 'meta_keywords', label: 'Meta keywords' },
  { name: 'meta_description', label: 'Meta description', type: 'textarea' }
];

export const RESOURCE_GROUPS = [
  {
    id: 'catalog',
    title: 'Catalog',
    iconname: 'inventory_2',
    resources: [
      {
        key: 'products',
        label: 'Products',
        singular: 'Product',
        endpoint: '/catalog/products/',
        detail: true,
        columns: [
          { key: 'name', label: 'Name' },
          { key: 'status', label: 'Status', badge: true },
          { key: 'product_type', label: 'Type' },
          { key: 'created_at', label: 'Created', format: date }
        ],
        fields: [
          { name: 'name', label: 'Name', required: true },
          { name: 'product_type', label: 'Type', type: 'select', options: PRODUCT_TYPE, default: 'physical' },
          { name: 'kind', label: 'Kind', type: 'select', options: PRODUCT_KIND, default: 'simple' },
          { name: 'status', label: 'Status', type: 'select', options: PRODUCT_STATUS, default: 'draft' },
          { name: 'category', label: 'Category', type: 'select', optionsEndpoint: '/catalog/categories/' },
          { name: 'brand', label: 'Brand', type: 'select', optionsEndpoint: '/catalog/brands/' },
          { name: 'is_active', label: 'Active', type: 'checkbox', default: true },
          { name: 'description', label: 'Description', type: 'textarea' },
          ...META_FIELDS
        ]
      },
      {
        key: 'categories',
        label: 'Categories',
        singular: 'Category',
        endpoint: '/catalog/categories/',
        fields: [
          { name: 'name', label: 'Name', required: true },
          { name: 'parent', label: 'Parent category', type: 'select', optionsEndpoint: '/catalog/categories/' },
          { name: 'position', label: 'Position', type: 'number', default: 0 },
          { name: 'is_active', label: 'Active', type: 'checkbox', default: true },
          { name: 'description', label: 'Description', type: 'textarea' },
          ...META_FIELDS
        ]
      },
      {
        key: 'brands',
        label: 'Brands',
        singular: 'Brand',
        endpoint: '/catalog/brands/',
        fields: [
          { name: 'name', label: 'Name', required: true },
          { name: 'is_active', label: 'Active', type: 'checkbox', default: true },
          { name: 'description', label: 'Description', type: 'textarea' },
          ...META_FIELDS
        ]
      },
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
        singular: 'Order',
        endpoint: '/orders/',
        detail: true,
        itemEndpoint: (id) => `/orders/${id}/`,
        columns: [
          { key: 'number', label: 'Number' },
          { key: 'status', label: 'Status', badge: true },
          { key: 'total', label: 'Total', format: money },
          { key: 'created_at', label: 'Placed', format: date }
        ],
        actions: [
          {
            key: 'confirm',
            label: 'Confirm',
            variant: 'success',
            path: (row) => `/orders/${row.id}/confirm/`,
            confirm: 'Confirm this order?',
            show: (row) => !['confirmed', 'cancelled', 'completed'].includes(row.status)
          },
          {
            key: 'cancel',
            label: 'Cancel',
            variant: 'danger',
            path: (row) => `/orders/${row.id}/cancel/`,
            confirm: 'Cancel this order? This cannot be undone.',
            show: (row) => !['cancelled', 'completed'].includes(row.status)
          }
        ]
      },
      {
        key: 'payments',
        label: 'Payments',
        singular: 'Payment',
        endpoint: '/payments/',
        detail: true,
        itemEndpoint: (id) => `/payments/${id}/`,
        columns: [
          { key: 'gateway', label: 'Gateway' },
          { key: 'amount', label: 'Amount', format: money },
          { key: 'status', label: 'Status', badge: true },
          { key: 'created_at', label: 'Created', format: date }
        ],
        actions: [
          {
            key: 'capture',
            label: 'Capture',
            variant: 'success',
            path: (row) => `/payments/${row.id}/capture/`,
            confirm: 'Capture this payment?',
            show: (row) => !['captured', 'refunded', 'failed'].includes(row.status)
          }
        ]
      },
      {
        key: 'returns',
        label: 'Returns (RMA)',
        singular: 'Return',
        endpoint: '/returns/',
        detail: true,
        itemEndpoint: (id) => `/returns/${id}/`,
        columns: [
          { key: 'status', label: 'Status', badge: true },
          { key: 'resolution', label: 'Resolution' },
          { key: 'refund_amount', label: 'Refund' },
          { key: 'created_at', label: 'Created', format: date }
        ],
        actions: [
          {
            key: 'approve',
            label: 'Approve',
            variant: 'success',
            path: (row) => `/returns/${row.id}/approve/`,
            confirm: 'Approve this return?'
          },
          {
            key: 'reject',
            label: 'Reject',
            variant: 'danger',
            path: (row) => `/returns/${row.id}/reject/`,
            prompt: { field: 'reason', label: 'Rejection reason' }
          },
          {
            key: 'refund',
            label: 'Refund',
            variant: 'primary',
            path: (row) => `/returns/${row.id}/refund/`,
            confirm: 'Issue the refund for this return?'
          }
        ]
      }
    ]
  },
  {
    id: 'inventory',
    title: 'Inventory',
    iconname: 'warehouse',
    resources: [
      {
        key: 'warehouses',
        label: 'Warehouses',
        singular: 'Warehouse',
        endpoint: '/inventory/warehouses/',
        fields: [
          { name: 'name', label: 'Name', required: true },
          { name: 'code', label: 'Code', required: true },
          { name: 'city', label: 'City' },
          { name: 'country', label: 'Country' },
          { name: 'is_default', label: 'Default warehouse', type: 'checkbox' },
          { name: 'is_active', label: 'Active', type: 'checkbox', default: true },
          { name: 'address', label: 'Address', type: 'textarea' }
        ]
      },
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
      {
        key: 'suppliers',
        label: 'Suppliers',
        singular: 'Supplier',
        endpoint: '/procurement/suppliers/',
        fields: [
          { name: 'name', label: 'Name', required: true },
          { name: 'email', label: 'Email', type: 'email', required: true },
          { name: 'code', label: 'Code' },
          { name: 'phone', label: 'Phone' },
          { name: 'is_active', label: 'Active', type: 'checkbox', default: true },
          { name: 'address', label: 'Address', type: 'textarea' }
        ]
      },
      {
        key: 'purchase-orders',
        label: 'Purchase orders',
        singular: 'Purchase order',
        endpoint: '/procurement/purchase-orders/',
        detail: true,
        itemEndpoint: (id) => `/procurement/purchase-orders/${id}/`,
        columns: [
          { key: 'number', label: 'Number' },
          { key: 'status', label: 'Status', badge: true },
          { key: 'subtotal', label: 'Subtotal' },
          { key: 'created_at', label: 'Created', format: date }
        ],
        actions: [
          {
            key: 'submit',
            label: 'Submit',
            variant: 'primary',
            path: (row) => `/procurement/purchase-orders/${row.id}/submit/`,
            confirm: 'Submit this purchase order to the supplier?',
            show: (row) => row.status === 'draft'
          },
          {
            key: 'receive',
            label: 'Receive (all)',
            variant: 'success',
            path: (row) => `/procurement/purchase-orders/${row.id}/receive/`,
            confirm: 'Receive all outstanding lines for this PO?',
            show: (row) => ['submitted', 'partial'].includes(row.status)
          }
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
        singular: 'Work order',
        endpoint: '/procurement/work-orders/',
        detail: true,
        itemEndpoint: (id) => `/procurement/work-orders/${id}/`,
        columns: [
          { key: 'number', label: 'Number' },
          { key: 'status', label: 'Status', badge: true },
          { key: 'quantity', label: 'Qty' },
          { key: 'created_at', label: 'Created', format: date }
        ],
        actions: [
          {
            key: 'complete',
            label: 'Complete',
            variant: 'success',
            path: (row) => `/procurement/work-orders/${row.id}/complete/`,
            confirm: 'Mark this work order complete and post the finished goods?',
            show: (row) => row.status !== 'completed'
          }
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
        singular: 'Coupon',
        endpoint: '/promotions/coupons/',
        columns: [
          { key: 'code', label: 'Code' },
          { key: 'discount_type', label: 'Type' },
          { key: 'value', label: 'Value' },
          { key: 'used_count', label: 'Used' },
          { key: 'is_active', label: 'Active', format: bool, badge: true }
        ],
        fields: [
          { name: 'code', label: 'Code', required: true },
          { name: 'discount_type', label: 'Discount type', type: 'select', options: DISCOUNT_TYPE, required: true },
          { name: 'value', label: 'Value', type: 'money', required: true, help: 'Percentage (≤100) or fixed amount.' },
          { name: 'min_spend', label: 'Minimum spend', type: 'money' },
          { name: 'max_discount', label: 'Max discount', type: 'money' },
          { name: 'usage_limit', label: 'Total usage limit', type: 'number' },
          { name: 'per_user_limit', label: 'Per-user limit', type: 'number' },
          { name: 'starts_at', label: 'Starts at', type: 'datetime' },
          { name: 'ends_at', label: 'Ends at', type: 'datetime' },
          { name: 'is_active', label: 'Active', type: 'checkbox', default: true },
          { name: 'description', label: 'Description', type: 'textarea' }
        ]
      },
      {
        key: 'campaigns',
        label: 'Campaigns',
        singular: 'Campaign',
        endpoint: '/promotions/campaigns/',
        columns: [
          { key: 'name', label: 'Name' },
          { key: 'campaign_type', label: 'Type', badge: true },
          { key: 'priority', label: 'Priority' },
          { key: 'is_active', label: 'Active', format: bool, badge: true }
        ],
        fields: [
          { name: 'name', label: 'Name', required: true },
          { name: 'campaign_type', label: 'Campaign type', type: 'select', options: CAMPAIGN_TYPE, required: true },
          { name: 'discount_type', label: 'Discount type', type: 'select', options: DISCOUNT_TYPE },
          { name: 'discount_value', label: 'Discount value', type: 'money' },
          { name: 'max_discount', label: 'Max discount', type: 'money' },
          { name: 'min_spend', label: 'Minimum spend', type: 'money' },
          { name: 'buy_quantity', label: 'Buy quantity', type: 'number', help: 'For buy X get Y.' },
          { name: 'get_quantity', label: 'Get quantity', type: 'number', help: 'For buy X get Y.' },
          { name: 'get_discount_percent', label: 'Get discount %', type: 'number' },
          { name: 'priority', label: 'Priority', type: 'number', default: 0 },
          { name: 'stackable', label: 'Stackable', type: 'checkbox' },
          { name: 'starts_at', label: 'Starts at', type: 'datetime' },
          { name: 'ends_at', label: 'Ends at', type: 'datetime' },
          { name: 'is_active', label: 'Active', type: 'checkbox', default: true },
          { name: 'description', label: 'Description', type: 'textarea' }
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
        singular: 'Payout',
        endpoint: '/payouts/',
        detail: true,
        itemEndpoint: (id) => `/payouts/${id}/`,
        columns: [
          { key: 'amount', label: 'Amount' },
          { key: 'status', label: 'Status', badge: true },
          { key: 'created_at', label: 'Created', format: date }
        ],
        actions: [
          {
            key: 'mark-paid',
            label: 'Mark paid',
            variant: 'success',
            path: (row) => `/payouts/${row.id}/mark-paid/`,
            confirm: 'Mark this payout as paid?',
            show: (row) => row.status !== 'paid'
          }
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
        singular: 'Review',
        endpoint: '/reviews/moderation/',
        detail: true,
        itemEndpoint: (id) => `/reviews/${id}/`,
        columns: [
          { key: 'rating', label: 'Rating' },
          { key: 'status', label: 'Status', badge: true },
          { key: 'is_verified_purchase', label: 'Verified', format: bool },
          { key: 'created_at', label: 'Created', format: date }
        ],
        actions: [
          {
            key: 'approve',
            label: 'Approve',
            variant: 'success',
            path: (row) => `/reviews/${row.id}/approve/`,
            confirm: 'Approve this review?',
            show: (row) => row.status !== 'approved'
          },
          {
            key: 'reject',
            label: 'Reject',
            variant: 'danger',
            path: (row) => `/reviews/${row.id}/reject/`,
            confirm: 'Reject this review?',
            show: (row) => row.status !== 'rejected'
          }
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
        singular: 'Fraud check',
        endpoint: '/fraud/checks/',
        detail: true,
        itemEndpoint: (id) => `/fraud/checks/${id}/`,
        columns: [
          { key: 'order_number', label: 'Order' },
          { key: 'score', label: 'Score' },
          { key: 'decision', label: 'Decision', badge: true },
          { key: 'resolution', label: 'Resolution' }
        ],
        actions: [
          {
            key: 'clear',
            label: 'Clear',
            variant: 'success',
            path: (row) => `/fraud/checks/${row.id}/clear/`,
            confirm: 'Clear this order of fraud suspicion?'
          },
          {
            key: 'reject',
            label: 'Reject',
            variant: 'danger',
            path: (row) => `/fraud/checks/${row.id}/reject/`,
            confirm: 'Reject (block) this order as fraudulent?'
          }
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

export const RESOURCES = Object.fromEntries(RESOURCE_GROUPS.flatMap((g) => g.resources.map((r) => [r.key, { ...r, group: g.id }])));

export const findResource = (key) => RESOURCES[key];
