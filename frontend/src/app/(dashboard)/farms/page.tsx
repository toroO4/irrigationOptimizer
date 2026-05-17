"use client"

import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { MapWrapper } from "@/components/map-wrapper"
import { WeatherWidget } from "@/components/weather-widget"
import { AddFieldDialog } from "@/components/add-field-dialog"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Droplets, Thermometer, Wind, CloudRain, Sun, Sprout,
  Layers, Activity, Gauge
} from "lucide-react"
import { motion } from "framer-motion"

function MicroclimateCard({ farmId, field }: { farmId: string; field: any }) {
  const { data: micro, isLoading } = useQuery({
    queryKey: ["microclimate", farmId, field.id],
    queryFn: async () => {
      const res = await api.get(`/farms/${farmId}/fields/${field.id}/microclimate`)
      return res.data
    },
    refetchInterval: 120000, // Refresh every 2 minutes
  })

  if (isLoading) {
    return (
      <div className="space-y-2">
        <Skeleton className="h-4 w-24" />
        <div className="grid grid-cols-3 gap-2">
          {[1, 2, 3, 4, 5, 6].map(i => <Skeleton key={i} className="h-12" />)}
        </div>
      </div>
    )
  }

  if (!micro) return null

  const moistureStatus = micro.soil_moisture_pct > 30 ? "Optimal" : micro.soil_moisture_pct > 20 ? "Low" : "Critical"
  const moistureColor = moistureStatus === "Optimal" ? "text-emerald-400" : moistureStatus === "Low" ? "text-yellow-400" : "text-red-400"

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Microclimate</h4>
        <Badge variant="outline" className={`text-[10px] ${moistureColor}`}>{moistureStatus}</Badge>
      </div>
      <div className="grid grid-cols-3 gap-2">
        {[
          { icon: <Thermometer className="h-3.5 w-3.5 text-orange-400" />, label: "Temp", value: `${micro.temperature_c}°C` },
          { icon: <Droplets className="h-3.5 w-3.5 text-blue-400" />, label: "Humidity", value: `${micro.humidity_pct}%` },
          { icon: <CloudRain className="h-3.5 w-3.5 text-cyan-400" />, label: "Rain", value: `${micro.rainfall_mm}mm` },
          { icon: <Sun className="h-3.5 w-3.5 text-amber-400" />, label: "ET₀", value: `${micro.evapotranspiration_mm}mm` },
          { icon: <Wind className="h-3.5 w-3.5 text-slate-400" />, label: "Wind", value: `${micro.wind_speed_kmh}km/h` },
          { icon: <Gauge className="h-3.5 w-3.5 text-emerald-400" />, label: "Moisture", value: `${micro.soil_moisture_pct}%` },
        ].map((item) => (
          <div key={item.label} className="flex items-center gap-1.5 rounded-md bg-muted/30 px-2 py-1.5">
            {item.icon}
            <div className="flex flex-col">
              <span className="text-[10px] text-muted-foreground">{item.label}</span>
              <span className="text-xs font-medium">{item.value}</span>
            </div>
          </div>
        ))}
      </div>
      <div className="flex items-center gap-2 rounded-md bg-blue-500/5 border border-blue-500/20 px-3 py-2">
        <Activity className="h-3.5 w-3.5 text-blue-400" />
        <span className="text-xs text-muted-foreground">
          SAR Moisture: <span className="font-semibold text-blue-400">{micro.sar_moisture_pct}%</span>
        </span>
      </div>
    </div>
  )
}

export default function FarmsPage() {
  const { data: farms, isLoading } = useQuery({
    queryKey: ["farms"],
    queryFn: async () => {
      const res = await api.get("/farms")
      return res.data
    },
  })

  const farm = farms?.[0]
  const fields = farm?.fields || []

  return (
    <div className="flex flex-col gap-6">
      <motion.div
        className="flex items-center justify-between"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="flex flex-col gap-2">
          <h1 className="text-3xl font-bold tracking-tight">Farms & Fields</h1>
          <p className="text-muted-foreground">Manage your agricultural land, view SAR overlays, and monitor localized weather.</p>
        </div>
        {farm && <AddFieldDialog farmId={farm.id} />}
      </motion.div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Map */}
        <motion.div
          className="lg:col-span-2"
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="min-h-[500px] flex flex-col">
            <CardHeader>
              <CardTitle>Geospatial Overview</CardTitle>
              <CardDescription>Interactive map with Sentinel-1 SAR moisture overlays</CardDescription>
            </CardHeader>
            <CardContent className="flex-1 p-0 pb-6 px-6">
              <MapWrapper fields={fields} />
            </CardContent>
          </Card>
        </motion.div>

        {/* Sidebar */}
        <div className="flex flex-col gap-6">
          <WeatherWidget />

          {/* Field Cards */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Layers className="h-5 w-5 text-emerald-400" />
                  Field Details
                </CardTitle>
                <Badge variant="secondary">{fields.length} fields</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-5">
                {isLoading ? (
                  <div className="space-y-4">
                    <Skeleton className="h-32 w-full" />
                    <Skeleton className="h-32 w-full" />
                  </div>
                ) : fields.length === 0 ? (
                  <div className="text-center py-8">
                    <Sprout className="h-10 w-10 text-muted-foreground/30 mx-auto mb-3" />
                    <p className="text-muted-foreground font-medium">No fields added yet</p>
                    <p className="text-sm text-muted-foreground/70 mt-1">Click "Add Field" to get started</p>
                  </div>
                ) : (
                  fields.map((field: any, index: number) => (
                    <motion.div
                      key={field.id}
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className={index > 0 ? "border-t pt-5" : ""}
                    >
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <h3 className="font-semibold text-sm">{field.name}</h3>
                          <Badge variant="outline" className="text-[10px] capitalize">{field.irrigation_type}</Badge>
                        </div>
                        <div className="grid grid-cols-2 text-xs gap-1.5">
                          <span className="text-muted-foreground">Crop:</span>
                          <span className="capitalize font-medium">{field.crop_type}</span>
                          <span className="text-muted-foreground">Area:</span>
                          <span>{field.area_hectares} ha</span>
                          <span className="text-muted-foreground">Soil:</span>
                          <span className="capitalize">{field.soil_type?.replace("_", " ")}</span>
                        </div>
                        {/* Microclimate Data */}
                        {farm && <MicroclimateCard farmId={farm.id} field={field} />}
                      </div>
                    </motion.div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
