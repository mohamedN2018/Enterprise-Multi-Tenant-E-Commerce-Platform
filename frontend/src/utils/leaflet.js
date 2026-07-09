// Leaflet setup — bundled locally (no CDN). Uses free OpenStreetMap tiles.
// The marker icon images are imported from the package so Vite fingerprints and
// serves them from our own origin (Leaflet's CSS otherwise points at missing paths).
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import iconUrl from 'leaflet/dist/images/marker-icon.png';
import iconRetinaUrl from 'leaflet/dist/images/marker-icon-2x.png';
import shadowUrl from 'leaflet/dist/images/marker-shadow.png';

L.Icon.Default.mergeOptions({ iconUrl, iconRetinaUrl, shadowUrl });

// A default map centre (Cairo) for stores that haven't pinned anything yet.
export const DEFAULT_CENTER = { lat: 30.0444, lng: 31.2357 };

export const osmTiles = () =>
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap'
  });

export { L };
