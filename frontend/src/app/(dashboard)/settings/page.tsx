"use client"

import { useState } from "react"
import { toast } from "sonner"
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Save } from "lucide-react"

export default function SettingsPage() {
  const [loading, setLoading] = useState(false)
  const [settings, setSettings] = useState({
    name: "Admin User",
    email: "admin@agrismart.io",
    notifications: true,
    autoSchedule: false,
    theme: "dark",
  })

  const handleSave = () => {
    setLoading(true)
    setTimeout(() => {
      setLoading(false)
      toast.success("Settings saved successfully.", {
        description: "Your preferences have been updated locally."
      })
    }, 1000)
  }

  return (
    <div className="flex flex-col gap-6 max-w-4xl">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">Manage your account settings, preferences, and API integrations.</p>
      </div>

      <div className="grid gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Profile Information</CardTitle>
            <CardDescription>Update your personal details and contact information.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Full Name</Label>
              <Input 
                id="name" 
                value={settings.name} 
                onChange={(e) => setSettings({...settings, name: e.target.value})} 
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email Address</Label>
              <Input 
                id="email" 
                type="email" 
                value={settings.email}
                onChange={(e) => setSettings({...settings, email: e.target.value})} 
              />
            </div>
          </CardContent>
          <CardFooter>
            <Button onClick={handleSave} disabled={loading}>
              <Save className="mr-2 h-4 w-4" /> {loading ? "Saving..." : "Save Profile"}
            </Button>
          </CardFooter>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Preferences</CardTitle>
            <CardDescription>Customize your platform experience.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Push Notifications</Label>
                <p className="text-sm text-muted-foreground">Receive alerts for critical irrigation events.</p>
              </div>
              <Switch 
                checked={settings.notifications}
                onCheckedChange={(c) => setSettings({...settings, notifications: c})}
              />
            </div>
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Auto-Scheduler</Label>
                <p className="text-sm text-muted-foreground">Automatically trigger irrigation without manual approval.</p>
              </div>
              <Switch 
                checked={settings.autoSchedule}
                onCheckedChange={(c) => setSettings({...settings, autoSchedule: c})}
              />
            </div>
          </CardContent>
          <CardFooter>
            <Button variant="outline" onClick={handleSave} disabled={loading}>
               {loading ? "Saving..." : "Update Preferences"}
            </Button>
          </CardFooter>
        </Card>
      </div>
    </div>
  )
}
