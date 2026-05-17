"use client"

import { useEffect, useState } from "react"
import { MapContainer, TileLayer, Polygon, Marker, Popup, Tooltip } from "react-leaflet"
import "leaflet/dist/leaflet.css"
import L from "leaflet"

// Fix for default marker icons in Leaflet with Next.js
const icon = L.icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
})

// Sample data for a Farm and its fields
const farmCenter: [number, number] = [19.0760, 72.8777]

const colors = ["#22c55e", "#eab308", "#3b82f6", "#ef4444", "#a855f7"]

function generateDummyCoords(index: number): [number, number][] {
  // Generate a small square offset from the center based on index
  const offset = index * 0.003
  return [
    [19.0770 - offset, 72.8767 + offset],
    [19.0770 - offset, 72.8787 + offset],
    [19.0755 - offset, 72.8787 + offset],
    [19.0755 - offset, 72.8767 + offset],
  ]
}

export default function FarmMap({ fields = [] }: { fields?: any[] }) {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) return <div className="h-full w-full bg-muted animate-pulse rounded-md"></div>

  return (
    <div className="h-full w-full rounded-md overflow-hidden border">
      <MapContainer center={farmCenter} zoom={15} style={{ height: "100%", width: "100%" }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        />
        
        {fields.map((field, index) => {
          const coords = field.coords || generateDummyCoords(index)
          const color = colors[index % colors.length]
          // Mock moisture for newly created fields in the demo
          const moisture = (20 + (index * 5.2)) % 40
          
          return (
            <Polygon 
              key={field.id} 
              positions={coords} 
              pathOptions={{ color: color, fillColor: color, fillOpacity: 0.4 }}
            >
              <Tooltip sticky>
                <div className="font-semibold">{field.name}</div>
                <div>Crop: <span className="capitalize">{field.crop_type}</span></div>
                <div>Moisture: {moisture.toFixed(1)}%</div>
              </Tooltip>
              <Popup>
                <div className="p-1">
                  <h3 className="font-bold">{field.name}</h3>
                  <p className="text-sm">SAR-derived moisture: {moisture.toFixed(1)}%</p>
                  <p className="text-sm">Area: {field.area_hectares} Ha</p>
                  <p className="text-sm font-medium mt-1 text-blue-500 cursor-pointer">Schedule Irrigation</p>
                </div>
              </Popup>
            </Polygon>
          )
        })}
        <Marker position={farmCenter} icon={icon}>
          <Popup>Farm Main Hub</Popup>
        </Marker>
      </MapContainer>
    </div>
  )
}
