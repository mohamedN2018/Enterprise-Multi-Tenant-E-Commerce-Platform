import { t } from '@/i18n';

// Fulfillment steps shown on the tracking timeline (cancelled is a separate,
// terminal state and isn't part of the linear flow).
export const ORDER_STEPS = ['pending', 'confirmed', 'processing', 'shipped', 'out_for_delivery', 'delivered'];

// The next status(es) a seller may set from the current one — mirrors the
// backend FULFILLMENT_NEXT so the UI never offers an invalid transition.
export const NEXT_STATUS = {
  confirmed: ['processing'],
  processing: ['shipped'],
  shipped: ['out_for_delivery', 'delivered'],
  out_for_delivery: ['delivered']
};

export const statusLabel = (s) => t(`status.${s}`);
