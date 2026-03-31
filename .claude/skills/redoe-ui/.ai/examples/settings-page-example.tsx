// GOLD STANDARD: Settings page. Copy this pattern for any settings/config screen.

"use client"

import { useState } from "react"
import { Bell, Shield, Wrench } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { Separator } from "@/components/ui/separator"
import { FormField, toast } from "@/components/redoe"
import { SettingsPage } from "@/components/layouts/settings-page"

// ---------------------------------------------------------------------------
// Nav items — icon + href for each settings section
// ---------------------------------------------------------------------------
const navItems = [
  { label: "Notifications", href: "/settings/notifications", icon: Bell },
  { label: "Shop Floor",    href: "/settings/shop-floor",    icon: Wrench },
  { label: "Security",      href: "/settings/security",      icon: Shield },
]

// ---------------------------------------------------------------------------
// State shape — one boolean per toggle
// ---------------------------------------------------------------------------
interface NotificationSettings {
  emailWorkOrderUpdates: boolean
  emailDailyDigest: boolean
  smsShopFloorAlerts: boolean
  smsCriticalOnly: boolean
  pushWorkOrderStatus: boolean
  pushOperationComplete: boolean
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------
export default function NotificationSettingsPage() {
  const [settings, setSettings] = useState<NotificationSettings>({
    emailWorkOrderUpdates: true,
    emailDailyDigest: false,
    smsShopFloorAlerts: true,
    smsCriticalOnly: true,
    pushWorkOrderStatus: true,
    pushOperationComplete: false,
  })

  function toggle(key: keyof NotificationSettings) {
    setSettings((prev) => ({ ...prev, [key]: !prev[key] }))
  }

  function saveSection(section: string) {
    // In real code: call server action / Supabase update
    toast.success("Settings saved", {
      description: `${section} preferences updated.`,
    })
  }

  return (
    <SettingsPage title="Settings" navItems={navItems}>
      <div className="space-y-8">
        {/* ---- Section: Email Notifications ---- */}
        <section className="space-y-4">
          <div>
            <h2 className="text-[16px] font-semibold text-foreground">
              Email Notifications
            </h2>
            <p className="text-[13px] text-muted-foreground">
              Control which emails you receive from Redoe OS.
            </p>
          </div>

          {/* Pattern: FormField + Switch — label left, toggle right */}
          <FormField
            label="Work Order Updates"
            description="Receive an email when a work order you own changes status."
          >
            <Switch
              checked={settings.emailWorkOrderUpdates}
              onCheckedChange={() => toggle("emailWorkOrderUpdates")}
            />
          </FormField>

          <FormField
            label="Daily Digest"
            description="Summary of all shop floor activity sent each morning at 7 AM."
          >
            <Switch
              checked={settings.emailDailyDigest}
              onCheckedChange={() => toggle("emailDailyDigest")}
            />
          </FormField>

          {/* Pattern: Save per section, not one global save */}
          <div className="flex justify-end">
            <Button size="sm" onClick={() => saveSection("Email")}>
              Save Email Settings
            </Button>
          </div>
        </section>

        <Separator />

        {/* ---- Section: SMS Alerts ---- */}
        <section className="space-y-4">
          <div>
            <h2 className="text-[16px] font-semibold text-foreground">
              SMS Alerts
            </h2>
            <p className="text-[13px] text-muted-foreground">
              Text message alerts for time-sensitive shop floor events.
            </p>
          </div>

          <FormField
            label="Shop Floor Alerts"
            description="Receive SMS when a machine goes down or an operation is blocked."
          >
            <Switch
              checked={settings.smsShopFloorAlerts}
              onCheckedChange={() => toggle("smsShopFloorAlerts")}
            />
          </FormField>

          <FormField
            label="Critical Only"
            description="Limit SMS to critical-severity alerts (machine down, safety stop)."
          >
            <Switch
              checked={settings.smsCriticalOnly}
              onCheckedChange={() => toggle("smsCriticalOnly")}
            />
          </FormField>

          <div className="flex justify-end">
            <Button size="sm" onClick={() => saveSection("SMS")}>
              Save SMS Settings
            </Button>
          </div>
        </section>

        <Separator />

        {/* ---- Section: Push Notifications ---- */}
        <section className="space-y-4">
          <div>
            <h2 className="text-[16px] font-semibold text-foreground">
              Push Notifications
            </h2>
            <p className="text-[13px] text-muted-foreground">
              In-app and browser push notifications.
            </p>
          </div>

          <FormField
            label="Work Order Status Changes"
            description="Get notified when a work order moves to a new stage."
          >
            <Switch
              checked={settings.pushWorkOrderStatus}
              onCheckedChange={() => toggle("pushWorkOrderStatus")}
            />
          </FormField>

          <FormField
            label="Operation Complete"
            description="Get notified when an operation on your jobs is marked complete."
          >
            <Switch
              checked={settings.pushOperationComplete}
              onCheckedChange={() => toggle("pushOperationComplete")}
            />
          </FormField>

          <div className="flex justify-end">
            <Button size="sm" onClick={() => saveSection("Push")}>
              Save Push Settings
            </Button>
          </div>
        </section>
      </div>
    </SettingsPage>
  )
}
