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
        {ports.map((p) => (
          <CircleMarker key={p.code || p.name} center={[p.lat, p.lng]} radius={4}
            pathOptions={{ color: "#0EA5E9", fillColor: "#0EA5E9", fillOpacity: 0.7, weight: 1 }}>
            <Tooltip>{p.name} · congestion {p.congestion}%</Tooltip>
          </CircleMarker>
        ))}
        {shipments.map((s) => {
          if (!s.origin_coords || !s.dest_coords) return null;
          const color = RISK_COLOR[s.risk_category] || "#10B981";
          return (
            <Polyline key={s.shipment_id} positions={[s.origin_coords, s.dest_coords]}
              pathOptions={{ color, weight: 1.4, opacity: 0.55 }}>
              <Tooltip>{s.shipment_id}: {s.origin} → {s.destination} · {s.risk_category}</Tooltip>
            </Polyline>
          );
        })}
        {shipments.map((s) =>
          s.dest_coords ? (
            <CircleMarker key={`d-${s.shipment_id}`} center={s.dest_coords} radius={3}
              pathOptions={{ color: RISK_COLOR[s.risk_category] || "#10B981", fillOpacity: 0.9, weight: 0 }} />
          ) : null
        )}
      </MapContainer>
    </div>
  );
}
