import "leaflet/dist/leaflet.css";
import { MapContainer, TileLayer, CircleMarker, Polyline, Tooltip } from "react-leaflet";

const RISK_COLOR = { Critical: "#EF4444", High: "#F97316", Moderate: "#F59E0B", Low: "#10B981" };

export default function WorldMap({ shipments = [], ports = [], height = 420 }) {
  return (
    <div data-testid="world-map" className="overflow-hidden rounded-lg border border-border/60" style={{ height }}>
      <MapContainer center={[25, 30]} zoom={2} minZoom={2} scrollWheelZoom={false} style={{ height: "100%", width: "100%" }} worldCopyJump>
        <TileLayer
          attribution='&copy; OpenStreetMap'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />
        {ports.map((p) => {
          const lat = p.lat ?? p.latitude;
          const lng = p.lng ?? p.lon ?? p.longitude;
          if (lat == null || lng == null || isNaN(lat) || isNaN(lng)) return null;
          return (
            <CircleMarker key={p.code || p.name} center={[lat, lng]} radius={4}
              pathOptions={{ color: "#0EA5E9", fillColor: "#0EA5E9", fillOpacity: 0.7, weight: 1 }}>
              <Tooltip>{p.name} · congestion {p.congestion || 15}%</Tooltip>
            </CircleMarker>
          );
        })}
        {shipments.map((s) => {
          const orig = s.origin_coords;
          const dest = s.dest_coords;
          if (!Array.isArray(orig) || !Array.isArray(dest)) return null;
          if (orig.length < 2 || dest.length < 2) return null;
          if (orig[0] == null || orig[1] == null || dest[0] == null || dest[1] == null) return null;
          const color = RISK_COLOR[s.risk_category] || "#10B981";
          return (
            <Polyline key={s.shipment_id || Math.random()} positions={[orig, dest]}
              pathOptions={{ color, weight: 1.4, opacity: 0.55 }}>
              <Tooltip>{s.shipment_id}: {s.origin} → {s.destination} · {s.risk_category}</Tooltip>
            </Polyline>
          );
        })}
        {shipments.map((s) => {
          const dest = s.dest_coords;
          if (!Array.isArray(dest) || dest.length < 2 || dest[0] == null || dest[1] == null) return null;
          return (
            <CircleMarker key={`d-${s.shipment_id}`} center={dest} radius={3}
              pathOptions={{ color: RISK_COLOR[s.risk_category] || "#10B981", fillOpacity: 0.9, weight: 0 }} />
          );
        })}
      </MapContainer>
    </div>
  );
}
