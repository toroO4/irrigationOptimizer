"use client"

import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import {
  CloudRain, Thermometer, Wind, Droplets, Sun, Eye,
  Gauge, CloudSun, Umbrella, ArrowUp, ArrowDown, Waves
} from "lucide-react"
import {
  Area, AreaChart, Bar, BarChart, ResponsiveContainer, Tooltip,
  XAxis, YAxis, CartesianGrid, Legend, Line, ComposedChart
} from "recharts"
import { motion } from "framer-motion"

const fadeIn = { initial: { opacity: 0, y: 20 }, animate: { opacity: 1, y: 0 } }

function conditionIcon(condition: string) {
  const c = condition?.toLowerCase() || ""
  if (c.includes("rain") || c.includes("drizzle") || c.includes("thunder")) return <CloudRain className="h-8 w-8 text-blue-400" />
  if (c.includes("cloud") || c.includes("overcast")) return <CloudSun className="h-8 w-8 text-slate-400" />
  return <Sun className="h-8 w-8 text-amber-400" />
}

export default function WeatherPage() {
  // Live weather
  const { data: weather, isLoading: weatherLoading, isError: weatherError } = useQuery({
    queryKey: ["weather-live"],
    queryFn: async () => (await api.get("/weather/live")).data,
    refetchInterval: 300000,
  })

  // 7-day forecast
  const { data: forecast, isLoading: forecastLoading } = useQuery({
    queryKey: ["weather-forecast"],
    queryFn: async () => (await api.get("/weather/forecast")).data,
  })

  // Weather trends
  const { data: trends, isLoading: trendsLoading } = useQuery({
    queryKey: ["weather-trends"],
    queryFn: async () => (await api.get("/weather/trends?days=14")).data,
  })

  return (
    <div className="flex flex-col gap-6">
      <motion.div className="flex flex-col gap-2" {...fadeIn}>
        <h1 className="text-3xl font-bold tracking-tight">Weather Insights</h1>
        <p className="text-muted-foreground">
          Real-time weather monitoring, forecasts, and irrigation impact analysis for your farm region.
        </p>
      </motion.div>

      {/* ── Current Weather Hero ── */}
      <motion.div {...fadeIn} transition={{ delay: 0.1 }}>
        {weatherLoading ? (
          <Skeleton className="h-48 w-full rounded-xl" />
        ) : weatherError ? (
          <Card className="border-red-500/30 bg-red-500/5">
            <CardContent className="pt-6 text-center text-red-400">
              Failed to load weather data. Check your backend connection.
            </CardContent>
          </Card>
        ) : weather ? (
          <Card className="relative overflow-hidden">
            <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-bl from-blue-500/10 to-transparent rounded-full -translate-y-16 translate-x-16" />
            <CardContent className="pt-6">
              <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
                {/* Main temp */}
                <div className="flex items-center gap-4 sm:col-span-2 lg:col-span-1">
                  {conditionIcon(weather.condition)}
                  <div>
                    <p className="text-4xl font-bold">{weather.temperature_c}°C</p>
                    <p className="text-sm text-muted-foreground">{weather.condition}</p>
                    <p className="text-xs text-muted-foreground">Feels like {weather.feels_like_c}°C</p>
                  </div>
                </div>

                {/* Key metrics */}
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { icon: <Droplets className="h-4 w-4 text-blue-400" />, label: "Humidity", value: `${weather.humidity_pct}%` },
                    { icon: <Wind className="h-4 w-4 text-slate-400" />, label: "Wind", value: `${weather.wind_speed_kmh} km/h ${weather.wind_direction}` },
                    { icon: <Umbrella className="h-4 w-4 text-cyan-400" />, label: "Rain Prob.", value: `${weather.rain_probability_percent}%` },
                    { icon: <Eye className="h-4 w-4 text-violet-400" />, label: "Visibility", value: `${weather.visibility_km} km` },
                  ].map(item => (
                    <div key={item.label} className="flex items-center gap-2">
                      {item.icon}
                      <div>
                        <p className="text-xs text-muted-foreground">{item.label}</p>
                        <p className="text-sm font-medium">{item.value}</p>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Pressure & UV */}
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { icon: <Gauge className="h-4 w-4 text-amber-400" />, label: "Pressure", value: `${weather.pressure_hpa} hPa` },
                    { icon: <Sun className="h-4 w-4 text-yellow-400" />, label: "UV Index", value: weather.uv_index },
                    { icon: <Waves className="h-4 w-4 text-emerald-400" />, label: "ET₀", value: `${weather.evapotranspiration_mm} mm` },
                    { icon: <Thermometer className="h-4 w-4 text-orange-400" />, label: "Dew Point", value: `${weather.dew_point_c}°C` },
                  ].map(item => (
                    <div key={item.label} className="flex items-center gap-2">
                      {item.icon}
                      <div>
                        <p className="text-xs text-muted-foreground">{item.label}</p>
                        <p className="text-sm font-medium">{item.value}</p>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Location */}
                <div className="flex flex-col justify-center">
                  <p className="text-xs text-muted-foreground mb-1">Location</p>
                  <p className="text-sm font-medium">{weather.location}</p>
                  <p className="text-xs text-muted-foreground mt-2">
                    Last updated: {new Date(weather.timestamp).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        ) : null}
      </motion.div>

      {/* ── 7-Day Forecast ── */}
      <motion.div {...fadeIn} transition={{ delay: 0.2 }}>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CloudSun className="h-5 w-5 text-blue-400" />
              7-Day Forecast
            </CardTitle>
            <CardDescription>Daily weather predictions for irrigation planning</CardDescription>
          </CardHeader>
          <CardContent>
            {forecastLoading ? (
              <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
                {[1, 2, 3, 4, 5, 6, 7].map(i => <Skeleton key={i} className="h-40 rounded-xl" />)}
              </div>
            ) : forecast ? (
              <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
                {forecast.map((day: any, i: number) => (
                  <motion.div
                    key={day.date}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className={`rounded-xl border p-3 text-center transition-all hover:shadow-md ${
                      i === 0 ? "bg-blue-500/5 border-blue-500/20" : "hover:bg-muted/30"
                    }`}
                  >
                    <p className="text-xs font-semibold text-muted-foreground mb-2">{day.day_name}</p>
                    <div className="flex justify-center mb-2">
                      {conditionIcon(day.condition)}
                    </div>
                    <p className="text-xs text-muted-foreground mb-1">{day.condition}</p>
                    <div className="flex items-center justify-center gap-1.5 text-sm">
                      <span className="flex items-center text-red-400">
                        <ArrowUp className="h-3 w-3" /> {day.temp_high_c}°
                      </span>
                      <span className="text-muted-foreground">/</span>
                      <span className="flex items-center text-blue-400">
                        <ArrowDown className="h-3 w-3" /> {day.temp_low_c}°
                      </span>
                    </div>
                    <div className="mt-2 flex items-center justify-center gap-1 text-[10px] text-muted-foreground">
                      <Umbrella className="h-3 w-3" />
                      <span>{day.rain_probability_pct}%</span>
                    </div>
                  </motion.div>
                ))}
              </div>
            ) : null}
          </CardContent>
        </Card>
      </motion.div>

      {/* ── Charts ── */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Temperature & Humidity Trends */}
        <motion.div {...fadeIn} transition={{ delay: 0.3 }}>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Thermometer className="h-5 w-5 text-orange-400" />
                Temperature & Humidity Trends
              </CardTitle>
              <CardDescription>14-day historical weather data</CardDescription>
            </CardHeader>
            <CardContent className="h-[320px]">
              {trendsLoading ? (
                <Skeleton className="w-full h-full rounded-lg" />
              ) : trends ? (
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={trends} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                    <XAxis dataKey="date" tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} />
                    <YAxis yAxisId="temp" tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} />
                    <YAxis yAxisId="hum" orientation="right" tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--card))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "8px",
                        color: "hsl(var(--foreground))",
                      }}
                    />
                    <Legend />
                    <Area yAxisId="temp" type="monotone" dataKey="temperature_c" name="Temp (°C)" stroke="#f59e0b" fill="none" strokeWidth={2} dot={{ r: 2 }} />
                    <Line yAxisId="hum" type="monotone" dataKey="humidity_pct" name="Humidity (%)" stroke="#3b82f6" strokeWidth={2} dot={{ r: 2 }} />
                  </ComposedChart>
                </ResponsiveContainer>
              ) : null}
            </CardContent>
          </Card>
        </motion.div>

        {/* Rainfall & ET */}
        <motion.div {...fadeIn} transition={{ delay: 0.4 }}>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CloudRain className="h-5 w-5 text-cyan-400" />
                Rainfall & Evapotranspiration
              </CardTitle>
              <CardDescription>Water balance analysis for irrigation decisions</CardDescription>
            </CardHeader>
            <CardContent className="h-[320px]">
              {trendsLoading ? (
                <Skeleton className="w-full h-full rounded-lg" />
              ) : trends ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={trends} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                    <XAxis dataKey="date" tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} />
                    <YAxis tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--card))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "8px",
                        color: "hsl(var(--foreground))",
                      }}
                    />
                    <Legend />
                    <Bar dataKey="rainfall_mm" name="Rainfall (mm)" fill="#06b6d4" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="evapotranspiration_mm" name="ET₀ (mm)" fill="#f97316" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : null}
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* ── Irrigation Impact Analysis ── */}
      <motion.div {...fadeIn} transition={{ delay: 0.5 }}>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Waves className="h-5 w-5 text-emerald-400" />
              Soil Moisture & Wind Trends
            </CardTitle>
            <CardDescription>Soil moisture correlation with weather conditions</CardDescription>
          </CardHeader>
          <CardContent className="h-[350px]">
            {trendsLoading ? (
              <Skeleton className="w-full h-full rounded-lg" />
            ) : trends ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trends} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="smGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                  <XAxis dataKey="date" tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} />
                  <YAxis tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "8px",
                      color: "hsl(var(--foreground))",
                    }}
                  />
                  <Legend />
                  <Area type="monotone" dataKey="soil_moisture_pct" name="Soil Moisture (%)" stroke="#10b981" fill="url(#smGrad)" strokeWidth={2} dot={{ r: 2 }} />
                  <Area type="monotone" dataKey="wind_speed_kmh" name="Wind (km/h)" stroke="#94a3b8" fill="none" strokeWidth={1.5} dot={{ r: 2 }} />
                </AreaChart>
              </ResponsiveContainer>
            ) : null}
          </CardContent>
        </Card>
      </motion.div>
    </div>
  )
}
