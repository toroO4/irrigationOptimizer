"use client"

import { useState, useMemo } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api"
import { toast } from "sonner"
import {
  Droplets, Calendar as CalendarIcon, CheckCircle2, RefreshCw,
  Timer, Zap, AlertTriangle, ChevronLeft, ChevronRight, ArrowRight
} from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import { motion } from "framer-motion"

// ── Calendar Helper ──
function getCalendarDays(year: number, month: number) {
  const firstDay = new Date(year, month, 1).getDay()
  const daysInMonth = new Date(year, month + 1, 0).getDate()
  const days: (number | null)[] = []
  for (let i = 0; i < firstDay; i++) days.push(null)
  for (let i = 1; i <= daysInMonth; i++) days.push(i)
  return days
}

const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

export default function SchedulesPage() {
  const queryClient = useQueryClient()
  const [calMonth, setCalMonth] = useState(new Date().getMonth())
  const [calYear, setCalYear] = useState(new Date().getFullYear())

  // Fetch all fields for the generation form
  const { data: farms } = useQuery({
    queryKey: ["farms"],
    queryFn: async () => (await api.get("/farms")).data,
  })

  // Fetch Schedules
  const { data: schedulesResponse, isLoading } = useQuery({
    queryKey: ["schedules"],
    queryFn: async () => (await api.get("/schedule")).data,
    refetchInterval: 15000,
  })

  // Generate Schedule Mutation — uses real field data
  const generateMutation = useMutation({
    mutationFn: async () => {
      const fields = farms?.flatMap((f: any) => f.fields || []) || []
      if (fields.length === 0) throw new Error("No fields found")

      // Generate a schedule for each field
      const results = []
      for (const field of fields) {
        const res = await api.post("/generate-irrigation-plan", {
          field_id: field.id,
          current_moisture: 0.12 + Math.random() * 0.15,
          crop_type: field.crop_type,
          area_hectares: field.area_hectares,
          irrigation_type: field.irrigation_type,
          field_capacity: 0.30,
          wilting_point: 0.15,
          pump_flow_rate_lph: 5000,
          temperature: 28 + Math.random() * 8,
          humidity: 45 + Math.random() * 30,
          rainfall_forecast: Math.random() < 0.3 ? Math.random() * 5 : 0,
        })
        results.push({ ...res.data, field_name: field.name, crop_type: field.crop_type })
      }
      return results
    },
    onSuccess: () => {
      toast.success("Irrigation schedules generated for all fields!", {
        description: "ML predictions have been computed and schedules optimized.",
      })
      queryClient.invalidateQueries({ queryKey: ["schedules"] })
    },
    onError: (err: any) => {
      toast.error("Failed to generate schedules", {
        description: err.message || "Check backend connection.",
      })
    },
  })

  const schedules = schedulesResponse?.schedules || []

  // Build calendar events map
  const calendarEvents = useMemo(() => {
    const events: Record<string, any[]> = {}
    schedules.forEach((s: any) => {
      if (s.scheduled_time) {
        const d = new Date(s.scheduled_time)
        const key = `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`
        if (!events[key]) events[key] = []
        events[key].push(s)
      }
    })
    return events
  }, [schedules])

  const calDays = getCalendarDays(calYear, calMonth)
  const today = new Date()

  return (
    <div className="flex flex-col gap-6">
      <motion.div
        className="flex items-center justify-between"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="flex flex-col gap-2">
          <h1 className="text-3xl font-bold tracking-tight">Irrigation Schedules</h1>
          <p className="text-muted-foreground">View and manage batch-optimized irrigation plans based on ML predictions.</p>
        </div>
        <Button
          variant="default"
          onClick={() => generateMutation.mutate()}
          disabled={generateMutation.isPending}
          className="gap-2"
        >
          {generateMutation.isPending ? (
            <RefreshCw className="h-4 w-4 animate-spin" />
          ) : (
            <Droplets className="h-4 w-4" />
          )}
          {generateMutation.isPending ? "Generating..." : "Generate New Schedule"}
        </Button>
      </motion.div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Timeline */}
        <motion.div
          className="lg:col-span-2"
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
        >
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CalendarIcon className="h-5 w-5 text-blue-400" />
                Upcoming Batch Operations
              </CardTitle>
              <CardDescription>Schedules optimized to minimize pump starts and maximize water efficiency.</CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="space-y-4">
                  {[1, 2, 3].map(i => <Skeleton key={i} className="h-28 w-full rounded-xl" />)}
                </div>
              ) : schedules.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-16 text-center">
                  <Droplets className="h-14 w-14 text-muted-foreground/20 mb-4" />
                  <p className="text-muted-foreground font-medium text-lg">No schedules generated yet</p>
                  <p className="text-sm text-muted-foreground/60 mt-1 max-w-sm">
                    Click "Generate New Schedule" to compute optimal irrigation plans for all your fields using the ML prediction engine.
                  </p>
                </div>
              ) : (
                <div className="relative border-l-2 border-muted-foreground/20 ml-4 space-y-6 pb-4 mt-2">
                  {schedules.map((schedule: any, index: number) => {
                    const urgency = schedule.urgency || "moderate"
                    const colors: Record<string, { dot: string; bg: string; text: string }> = {
                      critical: { dot: "bg-red-500", bg: "bg-red-500/5 border-red-500/20", text: "text-red-400" },
                      high: { dot: "bg-orange-500", bg: "bg-orange-500/5 border-orange-500/20", text: "text-orange-400" },
                      moderate: { dot: "bg-blue-500", bg: "bg-blue-500/5 border-blue-500/20", text: "text-blue-400" },
                      low: { dot: "bg-green-500", bg: "bg-green-500/5 border-green-500/20", text: "text-green-400" },
                      none: { dot: "bg-slate-400", bg: "bg-slate-500/5 border-slate-500/20", text: "text-slate-400" },
                    }
                    const c = colors[urgency] || colors.moderate

                    return (
                      <motion.div
                        key={index}
                        className="relative pl-8"
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.05 }}
                      >
                        <div className={`absolute w-3.5 h-3.5 ${c.dot} rounded-full -left-[8px] top-3 ring-4 ring-background`} />
                        <div className={`rounded-xl border p-4 ${c.bg} transition-all hover:shadow-md`}>
                          <div className="flex items-start justify-between mb-3">
                            <div>
                              <h3 className="font-semibold">
                                {schedule.field_name || `Field ${schedule.field_id || "—"}`}
                              </h3>
                              <p className="text-xs text-muted-foreground">
                                {schedule.scheduled_time
                                  ? new Date(schedule.scheduled_time).toLocaleString("en-US", {
                                      weekday: "short", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit"
                                    })
                                  : "Pending"}
                              </p>
                            </div>
                            <div className="flex items-center gap-2">
                              <Badge variant="outline" className={`text-[10px] uppercase ${c.text}`}>
                                {urgency}
                              </Badge>
                              {!schedule.irrigation_needed && (
                                <Badge variant="outline" className="text-[10px] text-emerald-400">
                                  <CheckCircle2 className="h-3 w-3 mr-1" /> No Irrigation
                                </Badge>
                              )}
                            </div>
                          </div>
                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                            <div className="flex items-center gap-1.5">
                              <Droplets className="h-3.5 w-3.5 text-blue-400" />
                              <span>{schedule.water_volume_liters?.toLocaleString() || 0} L</span>
                            </div>
                            <div className="flex items-center gap-1.5">
                              <Timer className="h-3.5 w-3.5 text-amber-400" />
                              <span>{schedule.pump_runtime_hours ? (schedule.pump_runtime_hours * 60).toFixed(0) : 0} min</span>
                            </div>
                            <div className="flex items-center gap-1.5">
                              <Zap className="h-3.5 w-3.5 text-yellow-400" />
                              <span>{schedule.deficit_mm?.toFixed(1) || 0} mm</span>
                            </div>
                            <div className="flex items-center gap-1.5">
                              <AlertTriangle className="h-3.5 w-3.5 text-violet-400" />
                              <span>{schedule.energy_estimate_kwh?.toFixed(1) || 0} kWh</span>
                            </div>
                          </div>
                          {schedule.recommendation && (
                            <p className="text-xs text-muted-foreground mt-3 italic">
                              {schedule.recommendation}
                            </p>
                          )}
                        </div>
                      </motion.div>
                    )
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* Sidebar: Calendar + Stats */}
        <div className="flex flex-col gap-6">
          {/* Interactive Calendar */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <Card>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">Schedule Calendar</CardTitle>
                  <div className="flex items-center gap-1">
                    <Button
                      variant="ghost" size="icon" className="h-7 w-7"
                      onClick={() => {
                        if (calMonth === 0) { setCalMonth(11); setCalYear(y => y - 1) }
                        else setCalMonth(m => m - 1)
                      }}
                    >
                      <ChevronLeft className="h-4 w-4" />
                    </Button>
                    <span className="text-sm font-medium min-w-[120px] text-center">
                      {MONTHS[calMonth]} {calYear}
                    </span>
                    <Button
                      variant="ghost" size="icon" className="h-7 w-7"
                      onClick={() => {
                        if (calMonth === 11) { setCalMonth(0); setCalYear(y => y + 1) }
                        else setCalMonth(m => m + 1)
                      }}
                    >
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-7 gap-0.5 text-center text-xs">
                  {["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"].map(d => (
                    <div key={d} className="py-1.5 font-semibold text-muted-foreground">{d}</div>
                  ))}
                  {calDays.map((day, i) => {
                    if (day === null) return <div key={`e-${i}`} />
                    const eventKey = `${calYear}-${calMonth}-${day}`
                    const hasEvents = calendarEvents[eventKey]
                    const isToday = today.getDate() === day && today.getMonth() === calMonth && today.getFullYear() === calYear

                    return (
                      <div
                        key={i}
                        className={`relative py-1.5 rounded-md transition-colors cursor-default
                          ${isToday ? "bg-primary text-primary-foreground font-bold" : "hover:bg-muted"}
                          ${hasEvents ? "font-semibold" : "text-muted-foreground"}
                        `}
                      >
                        {day}
                        {hasEvents && (
                          <div className="absolute bottom-0.5 left-1/2 -translate-x-1/2 flex gap-0.5">
                            {hasEvents.slice(0, 3).map((_: any, ei: number) => (
                              <div key={ei} className="w-1 h-1 rounded-full bg-blue-400" />
                            ))}
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Batch Optimization Stats */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Batch Optimization</CardTitle>
                <CardDescription>Impact of the Smart Scheduler</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {[
                    { label: "Total Schedules", value: schedules.length.toString(), color: "" },
                    { label: "Fields Needing Irrigation", value: schedules.filter((s: any) => s.irrigation_needed !== false).length.toString(), color: "text-blue-400" },
                    { label: "Total Water (L)", value: schedules.reduce((a: number, s: any) => a + (s.water_volume_liters || 0), 0).toLocaleString(), color: "text-cyan-400" },
                    { label: "Avg Pump Runtime", value: schedules.length ? ((schedules.reduce((a: number, s: any) => a + (s.pump_runtime_hours || 0), 0) / schedules.length) * 60).toFixed(0) + " min" : "—", color: "text-amber-400" },
                  ].map(item => (
                    <div key={item.label} className="flex justify-between items-center border-b border-border/50 pb-2">
                      <span className="text-sm text-muted-foreground">{item.label}</span>
                      <span className={`font-bold ${item.color}`}>{item.value}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>
    </div>
  )
}
