<script setup>
// A free OpenStreetMap map (Leaflet). Two jobs, driven by props:
//  • editable — click / drag a pin to choose a point (checkout location, zone centre)
//  • circles  — draw delivery zones (a centre + km radius) as circles on the map
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue';
import { L, osmTiles, DEFAULT_CENTER } from '@/utils/leaflet';

const props = defineProps({
  modelValue: { type: Object, default: null }, // { lat, lng } — the chosen pin
  center: { type: Object, default: () => DEFAULT_CENTER },
  zoom: { type: Number, default: 11 },
  editable: { type: Boolean, default: false }, // click/drag sets modelValue
  radiusKm: { type: [Number, String], default: 0 }, // circle drawn around the pin
  circles: { type: Array, default: () => [] }, // [{ lat, lng, radius_km, name, color }]
  height: { type: String, default: '320px' }
});
const emit = defineEmits(['update:modelValue']);

const el = ref(null);
let map = null;
let marker = null;
let editCircle = null;
let zoneLayers = [];

const num = (v) => (v === '' || v == null ? 0 : Number(v));

const drawEditCircle = (lat, lng) => {
  if (editCircle) {
    map.removeLayer(editCircle);
    editCircle = null;
  }
  if (num(props.radiusKm) > 0) {
    editCircle = L.circle([lat, lng], {
      radius: num(props.radiusKm) * 1000,
      color: '#F28B00',
      fillColor: '#F28B00',
      fillOpacity: 0.12,
      weight: 2
    }).addTo(map);
  }
};

const setMarker = (lat, lng) => {
  if (!map) return;
  if (!marker) {
    marker = L.marker([lat, lng], { draggable: props.editable }).addTo(map);
    if (props.editable) {
      marker.on('dragend', () => {
        const p = marker.getLatLng();
        emit('update:modelValue', { lat: p.lat, lng: p.lng });
      });
    }
  } else {
    marker.setLatLng([lat, lng]);
  }
  drawEditCircle(lat, lng);
};

const drawZones = () => {
  if (!map) return;
  zoneLayers.forEach((l) => map.removeLayer(l));
  zoneLayers = [];
  (props.circles || []).forEach((c) => {
    if (c.lat == null || c.lng == null) return;
    const color = c.color || '#0EA5A4';
    const layer = L.circle([Number(c.lat), Number(c.lng)], {
      radius: num(c.radius_km) * 1000,
      color,
      fillColor: color,
      fillOpacity: 0.1,
      weight: 2
    }).addTo(map);
    if (c.name) layer.bindTooltip(c.name);
    zoneLayers.push(layer);
  });
};

onMounted(async () => {
  await nextTick();
  const c = props.modelValue || props.center || DEFAULT_CENTER;
  map = L.map(el.value, { scrollWheelZoom: true }).setView([c.lat, c.lng], props.zoom);
  osmTiles().addTo(map);
  if (props.editable) {
    map.on('click', (e) => emit('update:modelValue', { lat: e.latlng.lat, lng: e.latlng.lng }));
  }
  if (props.modelValue) setMarker(props.modelValue.lat, props.modelValue.lng);
  drawZones();
  // Maps inside modals/tabs mount at zero size — recompute once laid out.
  setTimeout(() => map && map.invalidateSize(), 250);
});

watch(
  () => props.modelValue,
  (v) => {
    if (!map || !v) return;
    setMarker(v.lat, v.lng);
    map.panTo([v.lat, v.lng]);
  }
);
watch(
  () => props.radiusKm,
  () => props.modelValue && drawEditCircle(props.modelValue.lat, props.modelValue.lng)
);
watch(() => props.circles, drawZones, { deep: true });

onBeforeUnmount(() => {
  if (map) {
    map.remove();
    map = null;
  }
});

defineExpose({ invalidate: () => map && map.invalidateSize() });
</script>

<template>
  <div
    ref="el"
    :style="{ height, width: '100%' }"
    class="z-0 overflow-hidden rounded-xl border border-slate-200 dark:border-slate-700"
  ></div>
</template>
