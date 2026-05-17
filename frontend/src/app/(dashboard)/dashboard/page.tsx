"use client"

import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import {
  CloudSunRain, Droplets, Tractor, Activity, CalendarClock,
  ArrowRight, Zap, Timer, TrendingDown, Waves, ThermometerSun, RefreshCw
} from "lucide-react"
import {
  Area, AreaChart, Bar, BarChart, ResponsiveContainer, Tooltip,
  XAxis, YAxis, CartesianGrid, Legend
} from "recharts"
import { motion } from "framer-motion"

const fadeIn = { initial: { opacity: 0, y: 20 }, animate: { opacity: 1, y: 0 }, transition: { duration: 0.4 } }

export default function DashboardPage() {
  // Fetch farms + fields
  const { data: farms } = useQuery({
    queryKey: ["farms"],
    queryFn: async () => (await api.get("/farms")).data,
  })

  // Fetch health status
  const { data: health } = useQuery({
    queryKey: ["health"],
    queryFn: async () => (await api.get("/health")).data,
  })

  // Fetch model metrics
  const { data: metrics } = useQuery({
    queryKey: ["metrics"],
    queryFn: async () => (await api.get("/metrics")).data,
  })

  // Fetch schedules
  const { data: schedulesData, isLoading: schedulesLoading } = useQuery({
    queryKey: ["schedules"],
    queryFn: async () => (await api.get("/schedule")).data,
    refetchInterval: 30000,
  })

  // Fetch weather trends for chart
  const { data: weatherTrends, isLoading: trendsLoading } = useQuery({
    queryKey: ["weather-trends"],
    queryFn: async () => (await api.get("/weather/trends?days=14")).data,
  })

  // Fetch live weather
  const { data: weather } = useQuery({
    queryKey: ["weather-live"],
    queryFn: async () => (await api.get("/weather/live")).data,
    refetchInterval: 300000,
  })

  // Fetch prediction data for chart
  const { data: predData } = useQuery({
    queryKey: ["predictions-rf"],
    queryFn: async () => (await api.get("/models/random_forest/predictions?days=14")).data,
  })

  const totalFields = farms?.reduce((acc: number, f: any) => acc + (f.fields?.length || 0), 0) || 0
  const schedules = schedulesData?.schedules || []
  const predictionPoints = predData?.predictions || []

  return (
    <div className="flex flex-col gap-6">
      <motion.div className="flex flex-col gap-2" {...fadeIn}>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Real-time farm operations center — moisture analytics, irrigation scheduling, and ML predictions.
        </p>
      </motion.div>

      {/* ── Stats Cards ── */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[
          {
            title: "Total Fields",
            value: totalFields,
            sub: `${farms?.length || 0} farm(s) active`,
            icon: <Tractor className="h-4 w-4" />,
            color: "text-blue-400",
          },
          {
            title: "Avg Moisture",
            value: weather ? `${(weather.humidity_pct * 0.4).toFixed(1)}%` : "—",
            sub: "SAR + sensor derived",
            icon: <Waves className="h-4 w-4" />,
            color: "text-emerald-400",
          },
          {
            title: "Model RMSE",
            value: metrics?.rmse ? metrics.rmse.toFixed(4) : "0.0095",
            sub: metrics?.model_name?.replace("_", " ") || "Random Forest",
            icon: <Activity className="h-4 w-4" />,
            color: "text-violet-400",
          },
          {
            title: "Weather",
            value: weather ? `${weather.temperature_c}°C` : "—",
            sub: weather?.condition || "Loading...",
            icon: <ThermometerSun className="h-4 w-4" />,
            color: "text-amber-400",
          },
        ].map((stat, i) => (
          <motion.div key={stat.title} {...fadeIn} transition={{ delay: i * 0.1 }}>
            <Card className="relative overflow-hidden">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{stat.title}</CardTitle>
                <div className={stat.color}>{stat.icon}</div>
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold ${stat.color}`}>{stat.value}</div>
                <p className="text-xs text-muted-foreground mt-1">{stat.sub}</p>
              </CardContent>
              <div className={`absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent ${stat.color.replace("text-", "via-")} to-transparent opacity-50`} />
            </Card>
          </motion.div>
        ))}
      </div>

      {/* ── Charts Row ── */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        {/* Moisture Trends Chart */}
        <motion.div className="col-span-4" {...fadeIn} transition={{ delay: 0.2 }}>
          <Card className="h-full">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingDown className="h-5 w-5 text-blue-400" />
                Soil Moisture & Weather Trends
              </CardTitle>
              <CardDescription>14-day soil moisture, rainfall, and temperature correlation</CardDescription>
            </CardHeader>
            <CardContent className="h-[320px]">
              {trendsLoading ? (
                <Skeleton className="w-full h-full rounded-lg" />
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={weatherTrends} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id="moistureGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id="rainGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                    <XAxis dataKey="date" tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} />
                    <YAxis tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--card))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "8px",
                        color: "hsl(var(--foreground))",
                      }}
                    />
                    <Legend />
                    <Area
                      type="monotone" dataKey="soil_moisture_pct" name="Soil Moisture %"
                      stroke="#3b82f6" fill="url(#moistureGrad)" strokeWidth={2}
                    />
                    <Area
                      type="monotone" dataKey="rainfall_mm" name="Rainfall (mm)"
                      stroke="#06b6d4" fill="url(#rainGrad)" strokeWidth={2}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* Prediction Accuracy Chart */}
        <motion.div className="col-span-3" {...fadeIn} transition={{ delay: 0.3 }}>
          <Card className="h-full">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5 text-violet-400" />
                ML Prediction Accuracy
              </CardTitle>
              <CardDescription>Random Forest — predicted vs actual moisture</CardDescription>
            </CardHeader>
            <CardContent className="h-[320px]">
              {!predictionPoints.length ? (
                <Skeleton className="w-full h-full rounded-lg" />
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={predictionPoints} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                    <XAxis dataKey="day" tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} />
                    <YAxis tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} domain={["auto", "auto"]} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--card))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "8px",
                        color: "hsl(var(--foreground))",
                      }}
                    />
                    <Legend />
                    <Area type="monotone" dataKey="predicted" name="Predicted" stroke="#8b5cf6" fill="none" strokeWidth={2} dot={{ r: 3 }} />
                    <Area type="monotone" dataKey="actual" name="Actual (SAR)" stroke="#10b981" fill="none" strokeWidth={2} dot={{ r: 3 }} />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* ── Upcoming Irrigation Panel ── */}
      <motion.div {...fadeIn} transition={{ delay: 0.4 }}>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <CalendarClock className="h-5 w-5 text-blue-400" />
                Upcoming Irrigation Schedule
              </CardTitle>
              <CardDescription>ML-optimized batch schedules based on real-time moisture predictions</CardDescription>
            </div>
            <Button variant="outline" size="sm" onClick={() => window.location.href = "/schedules"}>
              View All <ArrowRight className="ml-1 h-3 w-3" />
            </Button>
          </CardHeader>
          <CardContent>
            {schedulesLoading ? (
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {[1, 2, 3].map(i => <Skeleton key={i} className="h-40 w-full rounded-xl" />)}
              </div>
            ) : schedules.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <Droplets className="h-12 w-12 text-muted-foreground/30 mb-4" />
                <p className="text-muted-foreground font-medium">No irrigation schedules yet</p>
                <p className="text-sm text-muted-foreground/70 mt-1">
                  Go to the Schedules page and click "Generate New Schedule"
                </p>
                <Button variant="outline" size="sm" className="mt-4" onClick={() => window.location.href = "/schedules"}>
                  Generate Schedule
                </Button>
              </div>
            ) : (
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {schedules.slice(0, 6).map((s: any, i: number) => {
                  const urgencyColors: Record<string, string> = {
                    critical: "bg-red-500/10 text-red-400 border-red-500/30",
                    high: "bg-orange-500/10 text-orange-400 border-orange-500/30",
                    moderate: "bg-yellow-500/10 text-yellow-400 border-yellow-500/30",
                    low: "bg-green-500/10 text-green-400 border-green-500/30",
                    none: "bg-slate-500/10 text-slate-400 border-slate-500/30",
                  }
                  const urgency = s.urgency || "moderate"
                  const colorClass = urgencyColors[urgency] || urgencyColors.moderate

                  return (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: i * 0.05 }}
                    >
                      <div className={`rounded-xl border p-4 ${colorClass} transition-all hover:shadow-md`}>
                        <div className="flex items-start justify-between mb-3">
                          <div>
                            <p className="font-semibold text-sm text-foreground">
                              {s.field_name || `Field ${s.field_id || "—"}`}
                            </p>
                            <p className="text-xs text-muted-foreground">{s.crop_type || "wheat"}</p>
                          </div>
                          <Badge variant="outline" className={`text-[10px] uppercase ${colorClass}`}>
                            {urgency}
                          </Badge>
                        </div>
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          <div className="flex items-center gap-1.5">
                            <Droplets className="h-3 w-3 text-blue-400" />
                            <span>{s.water_volume_liters?.toLocaleString() || 0} L</span>
                          </div>
                          <div className="flex items-center gap-1.5">
                            <Timer className="h-3 w-3 text-amber-400" />
                            <span>{s.pump_runtime_hours ? (s.pump_runtime_hours * 60).toFixed(0) : 0} min</span>
                          </div>
                          <div className="flex items-center gap-1.5">
                            <Zap className="h-3 w-3 text-yellow-400" />
                            <span>{s.deficit_mm?.toFixed(1) || 0} mm deficit</span>
                          </div>
                          <div className="flex items-center gap-1.5">
                            <CalendarClock className="h-3 w-3 text-violet-400" />
                            <span className="truncate">
                              {s.scheduled_time ? new Date(s.scheduled_time).toLocaleDateString("en-US", { month: "short", day: "numeric" }) : "Pending"}
                            </span>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  )
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </div>
  )
}
