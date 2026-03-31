/**
 * GOLD STANDARD: Detail Page (Pattern 2)
 * Tool detail with tabs: Overview, Details, Documents, History.
 * Copy this structure when building any single-entity view.
 */

import { ArrowLeft, Pencil, Download, MoreHorizontal } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  PageHeader,
  KPICard,
  StatusBadge,
  EntityBadge,
  DataTable,
  EmptyState,
  type Column,
} from "@/components/redoe"
import { FileText } from "lucide-react"

interface Document {
  id: string
  name: string
  type: string
  size: string
  uploaded: string
}

const docColumns: Column<Document>[] = [
  { key: "name", header: "Name" },
  { key: "type", header: "Type" },
  { key: "size", header: "Size", numeric: true },
  {
    key: "uploaded",
    header: "Uploaded",
    render: (row) => (
      <span className="font-mono text-muted-foreground">{row.uploaded}</span>
    ),
  },
]

export default function ToolDetailPage() {
  const documents: Document[] = [] // Replace with real data

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Pattern: PageHeader with back button + status inline + actions */}
      <PageHeader
        title="G-8232 CNC Housing"
        description="FNG · Truck Program · Redoe Windsor"
        breadcrumbs={
          <div className="flex items-center gap-2 text-muted-foreground">
            <Button variant="ghost" size="icon" className="size-7">
              <ArrowLeft className="size-4" />
            </Button>
            <span>Tools</span>
            <span>/</span>
            <span className="text-foreground">G-8232</span>
          </div>
        }
        actions={
          <div className="flex items-center gap-2">
            <StatusBadge status="active" size="lg" />
            <EntityBadge entity="redoe-windsor" />
            <Button variant="outline" size="sm">
              <Pencil className="size-4 mr-1.5" />
              Edit
            </Button>
            <Button variant="outline" size="sm">
              <Download className="size-4 mr-1.5" />
              Export
            </Button>
            <Button variant="ghost" size="icon" className="size-8">
              <MoreHorizontal className="size-4" />
            </Button>
          </div>
        }
      />

      {/* Pattern: Tabs — underline style, not boxed */}
      <Tabs defaultValue="overview">
        <TabsList className="border-b border-[var(--border-subtle)] bg-transparent rounded-none w-full justify-start gap-0 p-0">
          <TabsTrigger
            value="overview"
            className="rounded-none border-b-2 border-transparent data-[state=active]:border-foreground data-[state=active]:bg-transparent data-[state=active]:shadow-none px-4 py-2 text-[13px]"
          >
            Overview
          </TabsTrigger>
          <TabsTrigger
            value="details"
            className="rounded-none border-b-2 border-transparent data-[state=active]:border-foreground data-[state=active]:bg-transparent data-[state=active]:shadow-none px-4 py-2 text-[13px]"
          >
            Details
          </TabsTrigger>
          <TabsTrigger
            value="documents"
            className="rounded-none border-b-2 border-transparent data-[state=active]:border-foreground data-[state=active]:bg-transparent data-[state=active]:shadow-none px-4 py-2 text-[13px]"
          >
            Documents
          </TabsTrigger>
          <TabsTrigger
            value="history"
            className="rounded-none border-b-2 border-transparent data-[state=active]:border-foreground data-[state=active]:bg-transparent data-[state=active]:shadow-none px-4 py-2 text-[13px]"
          >
            History
          </TabsTrigger>
        </TabsList>

        {/* Tab: Overview — KPI cards + timeline */}
        <TabsContent value="overview" className="pt-6 space-y-6">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <KPICard label="Total Value" value="$45,200" />
            <KPICard label="Hours Logged" value="320h" delta={5} deltaLabel="ahead of estimate" />
            <KPICard label="Operations" value="12/18" comparison="67% complete" />
            <KPICard label="Days Remaining" value={22} />
          </div>

          {/* Timeline placeholder */}
          <div className="space-y-3">
            <h3 className="text-[13px] font-medium">Recent Activity</h3>
            <div className="border-l-2 border-[var(--border-subtle)] pl-4 space-y-4">
              {[
                { time: "2h ago", text: "Operation 7 (Rough CNC) marked complete by John Depatie" },
                { time: "Yesterday", text: "Design revision uploaded — Rev C" },
                { time: "3 days ago", text: "Status changed from Pending to Active" },
              ].map((entry, i) => (
                <div key={i} className="relative">
                  <div className="absolute -left-[21px] top-1.5 size-2.5 rounded-full bg-[var(--border-strong)]" />
                  <p className="text-[12px] font-mono text-muted-foreground">{entry.time}</p>
                  <p className="text-[13px] text-foreground">{entry.text}</p>
                </div>
              ))}
            </div>
          </div>
        </TabsContent>

        {/* Tab: Details — read-only fields in 2-column grid */}
        <TabsContent value="details" className="pt-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4">
            {[
              { label: "Job Number", value: "G-8232" },
              { label: "Customer", value: "Flex-N-Gate" },
              { label: "Program", value: "Truck Program" },
              { label: "Part Name", value: "CNC Housing" },
              { label: "Material", value: "P20 Steel" },
              { label: "Cavities", value: "2" },
              { label: "Estimated Hours", value: "480" },
              { label: "Start Date", value: "2026-01-15" },
              { label: "Due Date", value: "2026-04-20" },
              { label: "PM", value: "Dave Belanger" },
            ].map((field) => (
              <div key={field.label}>
                <p className="text-[12px] font-medium text-muted-foreground mb-0.5">
                  {field.label}
                </p>
                <p className="text-[13px] text-foreground">{field.value}</p>
              </div>
            ))}
          </div>
        </TabsContent>

        {/* Tab: Documents */}
        <TabsContent value="documents" className="pt-6">
          <DataTable
            columns={docColumns}
            data={documents}
            keyExtractor={(row) => row.id}
            emptyTitle="No documents"
            emptyDescription="Upload drawings, specs, or revision files."
            emptyAction={<Button>Upload Document</Button>}
          />
        </TabsContent>

        {/* Tab: History */}
        <TabsContent value="history" className="pt-6">
          <EmptyState
            icon={FileText}
            title="No history yet"
            description="Changes and comments will appear here as the tool progresses."
          />
        </TabsContent>
      </Tabs>
    </div>
  )
}
