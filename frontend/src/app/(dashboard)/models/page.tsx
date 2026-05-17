"use client"

import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api"
import { toast } from "sonner"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Progress } from "@/components/ui/progress"
import {
  Bar, BarChart, Line, LineChart, ResponsiveContainer, Tooltip,
  XAxis, YAxis, CartesianGrid, Legend, Area, AreaChart
} from "recharts"
import {
  Play, RefreshCw, Brain, Gauge, Timer, TrendingUp,
  CheckCircle2, AlertCircle, Cpu
} from "lucide-react"
import { motion } from "framer-motion"

export default function ModelsPage() {
  const queryClient = useQueryClient()
  const [retrainProgress, setRetrainProgress] = useState(0)
  const [isRetraining, setIsRetraining] = useState(false)
  const [selectedModel, setSelectedModel] = useState("random_forest")

  // Fetch trained models
  const { data: modelsResponse, isLoading } = useQuery({
    queryKey: ["models"],
    queryFn: async () => (await api.get("/models")).data,
  })

  // Fetch prediction comparison data
  const { data: predData } = useQuery({
    queryKey: ["predictions", selectedModel],
    queryFn: async () => (await api.get(`/models/${selectedModel}/predictions?days=14`)).data,
  })

  // Retrain Mutation with progress simulation
  const retrainMutation = useMutation({
    mutationFn: async () => {
      setIsRetraining(true)
      setRetrainProgress(0)

      // Simulate progress while backend processes
      const progressInterval = setInterval(() => {
        setRetrainProgress(prev => {
          if (prev >= 90) { clearInterval(progressInterval); return 90 }
          return prev + Math.random() * 15
        })
      }, 500)

      try {
        const res = await api.post("/retrain", { model_name: selectedModel })
        clearInterval(progressInterval)
        setRetrainProgress(100)
        return res.data
      } catch (err) {
        clearInterval(progressInterval)
        throw err
      }
    },
    onSuccess: (data) => {
      toast.success("Model retraining completed!", {
        description: data.message || `${selectedModel} has been retrained successfully.`,
      })
      setTimeout(() => {
        setIsRetraining(false)
        setRetrainProgress(0)
        queryClient.invalidateQueries({ queryKey: ["models"] })
      }, 1500)
    },
    onError: () => {
      toast.error("Retraining failed", {
        description: "Check backend logs for details.",
      })
      setIsRetraining(false)
      setRetrainProgress(0)
    },
  })

  const models = modelsResponse?.models || []
  const predPoints = predData?.predictions || []

  // Format model data for charts
  const comparisonData = models.map((m: any) => ({
    name: m.model_name?.replace("_", " ").toUpperCase() || "UNKNOWN",
    rmse: m.rmse || 0,
    mae: m.mae || 0,
    r2: m.r2_score || 0,
    time: m.training_duration_seconds || 0,
  }))

  return (
    <div className="flex flex-col gap-6">
      <motion.div
        className="flex items-center justify-between"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="flex flex-col gap-2">
          <h1 className="text-3xl font-bold tracking-tight">ML Models & Analytics</h1>
          <p className="text-muted-foreground">Compare model performance, view explainability metrics, and trigger retraining.</p>
        </div>
        <Button
          onClick={() => retrainMutation.mutate()}
          disabled={retrainMutation.isPending || isRetraining}
          className="gap-2"
        >
          {isRetraining ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
          {isRetraining ? "Retraining..." : "Retrain Models"}
        </Button>
      </motion.div>

      {/* Retraining Progress */}
      {isRetraining && (
        <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }}>
          <Card className="border-blue-500/30 bg-blue-500/5">
            <CardContent className="pt-6">
              <div className="flex items-center gap-4 mb-3">
                <Cpu className="h-5 w-5 text-blue-400 animate-pulse" />
                <div className="flex-1">
                  <p className="text-sm font-medium">Retraining {selectedModel.replace("_", " ")}...</p>
                  <p className="text-xs text-muted-foreground">Processing dataset, training model, evaluating metrics</p>
                </div>
                <span className="text-sm font-mono text-blue-400">{Math.round(retrainProgress)}%</span>
              </div>
              <Progress value={retrainProgress} className="h-2" />
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Model Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {isLoading ? (
          [1, 2, 3].map(i => <Skeleton key={i} className="h-44 rounded-xl" />)
        ) : (
          models.map((model: any, i: number) => {
            const isSelected = model.model_name === selectedModel
            return (
              <motion.div
                key={model.id}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.08 }}
              >
                <Card
                  className={`cursor-pointer transition-all hover:shadow-lg ${
                    isSelected ? "ring-2 ring-blue-500 bg-blue-500/5" : ""
                  }`}
                  onClick={() => setSelectedModel(model.model_name)}
                >
                  <CardContent className="pt-6">
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h3 className="font-semibold capitalize">{model.model_name?.replace("_", " ")}</h3>
                        <p className="text-xs text-muted-foreground">v{model.model_version}</p>
                      </div>
                      {isSelected && <Badge className="bg-blue-500 text-white">Selected</Badge>}
                    </div>
                    <div className="grid grid-cols-3 gap-3 text-center">
                      <div>
                        <p className="text-lg font-bold text-blue-400">{model.rmse?.toFixed(4) || "—"}</p>
                        <p className="text-[10px] text-muted-foreground uppercase tracking-wider">RMSE</p>
                      </div>
                      <div>
                        <p className="text-lg font-bold text-emerald-400">{model.mae?.toFixed(4) || "—"}</p>
                        <p className="text-[10px] text-muted-foreground uppercase tracking-wider">MAE</p>
                      </div>
                      <div>
                        <p className="text-lg font-bold text-violet-400">{model.r2_score?.toFixed(3) || "—"}</p>
                        <p className="text-[10px] text-muted-foreground uppercase tracking-wider">R²</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 mt-4 text-xs text-muted-foreground">
                      <Timer className="h-3 w-3" />
                      <span>{model.training_duration_seconds?.toFixed(1) || "—"}s training</span>
                      <span className="mx-1">•</span>
                      <span>{model.dataset_size?.toLocaleString() || "—"} samples</span>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )
          })
        )}
      </div>

      {/* Charts */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* RMSE Comparison */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Gauge className="h-5 w-5 text-blue-400" />
                Model Comparison (RMSE & MAE)
              </CardTitle>
              <CardDescription>Lower is better — shows error metrics for all models</CardDescription>
            </CardHeader>
            <CardContent className="h-[300px]">
              {isLoading ? (
                <Skeleton className="w-full h-full" />
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={comparisonData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                    <XAxis dataKey="name" tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} />
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
                    <Bar dataKey="rmse" fill="#3b82f6" radius={[4, 4, 0, 0]} name="RMSE" />
                    <Bar dataKey="mae" fill="#10b981" radius={[4, 4, 0, 0]} name="MAE" />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* R² Score Comparison */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-emerald-400" />
                R² Score & Training Time
              </CardTitle>
              <CardDescription>Higher R² is better — training efficiency comparison</CardDescription>
            </CardHeader>
            <CardContent className="h-[300px]">
              {isLoading ? (
                <Skeleton className="w-full h-full" />
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={comparisonData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                    <XAxis dataKey="name" tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} />
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
                    <Bar dataKey="r2" fill="#8b5cf6" radius={[4, 4, 0, 0]} name="R² Score" />
                    <Bar dataKey="time" fill="#f59e0b" radius={[4, 4, 0, 0]} name="Train Time (s)" />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Prediction Trend */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="h-5 w-5 text-violet-400" />
              Prediction Accuracy — {selectedModel.replace("_", " ")}
            </CardTitle>
            <CardDescription>Predicted vs actual SAR-derived soil moisture over 14 days</CardDescription>
          </CardHeader>
          <CardContent className="h-[350px]">
            {!predPoints.length ? (
              <Skeleton className="w-full h-full" />
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={predPoints} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                  <defs>
                    <linearGradient id="predGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.2} />
                      <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                  <XAxis dataKey="day" tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} />
                  <YAxis domain={["auto", "auto"]} tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "8px",
                      color: "hsl(var(--foreground))",
                    }}
                  />
                  <Legend />
                  <Area type="monotone" dataKey="predicted" name="Predicted" stroke="#8b5cf6" fill="url(#predGrad)" strokeWidth={2} dot={{ r: 3 }} />
                  <Area type="monotone" dataKey="actual" name="Actual (SAR)" stroke="#10b981" fill="none" strokeWidth={2} dot={{ r: 3 }} />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Model Version History */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6 }}>
        <Card>
          <CardHeader>
            <CardTitle>Model Version History</CardTitle>
            <CardDescription>All trained model records from the database</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border/50">
                    <th className="text-left py-3 px-2 text-muted-foreground font-medium">Model</th>
                    <th className="text-left py-3 px-2 text-muted-foreground font-medium">Version</th>
                    <th className="text-right py-3 px-2 text-muted-foreground font-medium">RMSE</th>
                    <th className="text-right py-3 px-2 text-muted-foreground font-medium">MAE</th>
                    <th className="text-right py-3 px-2 text-muted-foreground font-medium">R²</th>
                    <th className="text-right py-3 px-2 text-muted-foreground font-medium">Samples</th>
                    <th className="text-left py-3 px-2 text-muted-foreground font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {models.map((m: any) => (
                    <tr key={m.id} className="border-b border-border/30 hover:bg-muted/20 transition-colors">
                      <td className="py-3 px-2 font-medium capitalize">{m.model_name?.replace("_", " ")}</td>
                      <td className="py-3 px-2 font-mono text-xs">{m.model_version}</td>
                      <td className="py-3 px-2 text-right text-blue-400">{m.rmse?.toFixed(4) || "—"}</td>
                      <td className="py-3 px-2 text-right text-emerald-400">{m.mae?.toFixed(4) || "—"}</td>
                      <td className="py-3 px-2 text-right text-violet-400">{m.r2_score?.toFixed(3) || "—"}</td>
                      <td className="py-3 px-2 text-right">{m.dataset_size?.toLocaleString() || "—"}</td>
                      <td className="py-3 px-2">
                        <Badge variant="outline" className="text-emerald-400 border-emerald-500/30 text-[10px]">
                          <CheckCircle2 className="h-3 w-3 mr-1" /> Trained
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  )
}
