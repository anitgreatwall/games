// GOLD STANDARD: Create/edit form page. Copy this pattern for any form.

"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Briefcase } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import {
  PageHeader,
  Breadcrumbs,
  FormField,
  DateRangePicker,
  toast,
} from "@/components/redoe"
import { FormPage } from "@/components/layouts/form-page"

// ---------------------------------------------------------------------------
// Types — match Supabase schema, never hand-write
// ---------------------------------------------------------------------------
interface WorkOrderForm {
  jobNumber: string
  customer: string
  program: string
  partName: string
  material: string
  priority: "standard" | "rush" | "emergency"
  notes: string
  startDate: { from: Date; to: Date } | undefined
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------
export default function CreateWorkOrderPage() {
  const router = useRouter()

  const [form, setForm] = useState<WorkOrderForm>({
    jobNumber: "",
    customer: "",
    program: "",
    partName: "",
    material: "",
    priority: "standard",
    notes: "",
    startDate: undefined,
  })

  // Demonstrate error state pattern — in real code, validate on submit
  const [errors, setErrors] = useState<Partial<Record<keyof WorkOrderForm, string>>>({
    jobNumber: "Job number is required",
    customer: "Select a customer",
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    // In real code: validate → call server action / Supabase insert
    toast.success("Work Order created", {
      description: `${form.jobNumber || "New job"} added to the schedule.`,
    })
    router.push("/work-orders")
  }

  return (
    <form onSubmit={handleSubmit} className="h-full">
      {/* Pattern: FormPage — header slot for PageHeader, footer slot for sticky submit bar */}
      <FormPage
        header={
          <PageHeader
            title="Create Work Order"
            description="Fill in the details below to open a new work order."
            breadcrumbs={
              <Breadcrumbs
                items={[
                  { label: "Work Orders", href: "/work-orders", icon: Briefcase },
                  { label: "Create" },
                ]}
              />
            }
          />
        }
        footer={
          <>
            <Button
              type="button"
              variant="outline"
              onClick={() => router.back()}
            >
              Cancel
            </Button>
            <Button type="submit">Create Work Order</Button>
          </>
        }
      >
        {/* ---- Section: Identification ---- */}
        <div className="space-y-4">
          <h2 className="text-[14px] font-semibold text-foreground">Identification</h2>

          {/* Pattern: FormField wraps every input — label, required asterisk, error */}
          <FormField label="Job Number" required error={errors.jobNumber}>
            <Input
              placeholder="G-XXXX"
              value={form.jobNumber}
              onChange={(e) => setForm({ ...form, jobNumber: e.target.value })}
            />
          </FormField>

          <FormField label="Customer" required error={errors.customer}>
            <Select
              value={form.customer}
              onValueChange={(v) => setForm({ ...form, customer: v })}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select customer" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="fng">Flex-N-Gate</SelectItem>
                <SelectItem value="magna">Magna International</SelectItem>
                <SelectItem value="martinrea">Martinrea</SelectItem>
                <SelectItem value="abc-group">ABC Group</SelectItem>
              </SelectContent>
            </Select>
          </FormField>

          <FormField label="Program" description="Vehicle program this tool belongs to.">
            <Input
              placeholder="e.g. Truck Program"
              value={form.program}
              onChange={(e) => setForm({ ...form, program: e.target.value })}
            />
          </FormField>
        </div>

        {/* ---- Section: Tool Details ---- */}
        <div className="space-y-4">
          <h2 className="text-[14px] font-semibold text-foreground">Tool Details</h2>

          <FormField label="Part Name" required>
            <Input
              placeholder="e.g. CNC Housing"
              value={form.partName}
              onChange={(e) => setForm({ ...form, partName: e.target.value })}
            />
          </FormField>

          <FormField label="Material">
            <Select
              value={form.material}
              onValueChange={(v) => setForm({ ...form, material: v })}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select material" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="p20">P20 Steel</SelectItem>
                <SelectItem value="h13">H13 Steel</SelectItem>
                <SelectItem value="s136">S136 Stainless</SelectItem>
                <SelectItem value="nak80">NAK80</SelectItem>
              </SelectContent>
            </Select>
          </FormField>

          {/* Pattern: RadioGroup for small option sets (3-5 choices) */}
          <FormField label="Priority" required>
            <RadioGroup
              value={form.priority}
              onValueChange={(v) =>
                setForm({ ...form, priority: v as WorkOrderForm["priority"] })
              }
              className="flex gap-4"
            >
              {[
                { value: "standard", label: "Standard" },
                { value: "rush", label: "Rush" },
                { value: "emergency", label: "Emergency" },
              ].map((opt) => (
                <label
                  key={opt.value}
                  className="flex items-center gap-2 text-[13px] cursor-pointer"
                >
                  <RadioGroupItem value={opt.value} />
                  {opt.label}
                </label>
              ))}
            </RadioGroup>
          </FormField>

          {/* Pattern: DateRangePicker — single date via same range start/end */}
          <FormField label="Target Start Date">
            <DateRangePicker
              value={form.startDate}
              onChange={(range) => setForm({ ...form, startDate: range })}
              placeholder="Select date"
            />
          </FormField>

          {/* Pattern: Textarea for freeform notes */}
          <FormField label="Notes" description="Internal notes — not visible to customer.">
            <Textarea
              placeholder="Special instructions, design notes, etc."
              rows={4}
              value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
            />
          </FormField>
        </div>
      </FormPage>
    </form>
  )
}
