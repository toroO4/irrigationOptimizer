"use client"

import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { CloudRain, Thermometer, Wind, Droplets } from "lucide-react"
import { Skeleton } from "@/components/ui/skeleton"

export function WeatherWidget() {
  const { data: weather, isLoading, isError } = useQuery({
    queryKey: ["weather"],
    queryFn: async () => {
      const res = await api.get("/weather/live")
      return res.data
    },
    refetchInterval: 300000, // Refresh every 5 mins
  })

  return (
    <Card>
      <CardHeader>
        <CardTitle>Microclimate Data</CardTitle>
        <CardDescription>{weather?.location || "Loading..."}</CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-4">
            <Skeleton className="h-6 w-full" />
            <Skeleton className="h-6 w-full" />
            <Skeleton className="h-6 w-full" />
            <Skeleton className="h-6 w-full" />
          </div>
        ) : isError ? (
          <div className="text-red-500 text-sm">Failed to load weather data.</div>
        ) : (
          <div className="grid grid-cols-2 gap-4">
            <div className="flex items-center gap-2">
              <Thermometer className="h-5 w-5 text-orange-500" />
              <div className="flex flex-col">
                <span className="text-sm font-medium">{weather.temperature_c}°C</span>
                <span className="text-xs text-muted-foreground">{weather.condition}</span>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <CloudRain className="h-5 w-5 text-blue-400" />
              <div className="flex flex-col">
                <span className="text-sm font-medium">{weather.rain_probability_percent}% Rain</span>
                <span className="text-xs text-muted-foreground">Probability</span>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <Wind className="h-5 w-5 text-slate-400" />
              <div className="flex flex-col">
                <span className="text-sm font-medium">{weather.wind_speed_kmh} km/h</span>
                <span className="text-xs text-muted-foreground">Wind</span>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <Droplets className="h-5 w-5 text-blue-500" />
              <div className="flex flex-col">
                <span className="text-sm font-medium">{weather.evapotranspiration_mm} mm</span>
                <span className="text-xs text-muted-foreground">Evapotranspiration</span>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
