/**
 * GOLD STANDARD: Dashboard (Pattern 3)
 * KPI cards + filter bar + chart section + recent activity table.
 * Copy this structure when building any dashboard/overview page.
 */

import { Download } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  PageHeader,
  KPICard,
  FilterBar,
  ChartSection,
  DataTable,
  StatusBadge,
  type Column,
} from "@/components/redoe"

interface RecentActivity {
  id: string
  timestamp: string
  description: string
  status: "active" | "complete" | "warning"
}

const activityColumns: Column<RecentActivity>[] = [
  {
    key: "timestamp",
    header: "Time",
    render: (row) => (
      <span className="font-mono text-muted-foreground">{row.timestamp}</span>
    ),
  },
  { key: "description", header: "Activity" },
  {
    key: "status",
    header: "Status",
    render: (row) => <StatusBadge status={row.status} size="sm" />,
  },
]

export default function PlantDashboard() {
  const activities: RecentActivity[] = [] // Replace with real data

  return (
    <div className="space-y-6">
      {/* Pattern: PageHeader — title + date range + export */}
      <PageHeader
        title="Plant Overview"
        description="Redoe Windsor · March 2026"
        actions={
          <Button variant="outline" size="sm">
            <Download className="size-4 mr-1.5" />
            Export
          </Button>
        }
      />

      {/* Pattern: KPI cards — max 4, borderless, hero number + delta */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          label="Active Jobs"
          value={42}
          delta={8}
          deltaLabel="vs last month"
        />
        <KPICard
          label="On-Time Delivery"
          value="87%"
          delta={-2.3}
          deltaLabel="vs target 92%"
        />
        <KPICard
          label="Revenue MTD"
          value="$1.2M"
          delta={12}
          deltaLabel="vs last month"
        />
        <KPICard
          label="At Risk"
          value={3}
          delta={-1}
          deltaLabel="fewer than last month"
        />
      </div>

      {/* Pattern: Filter bar — time pills + scope */}
      <FilterBar
        searchPlaceholder="Search..."
      />

      {/* Pattern: Charts side-by-side on desktop, stacked on mobile */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartSection
          title="Revenue Trend"
          subtitle="Last 12 months"
          heroValue="$14.2M"
        >
          {/* <AreaChart data={revenueData} /> */}
          <div className="flex items-center justify-center h-full text-muted-foreground text-[13px]">
            Chart placeholder — use Recharts via shadcn wrappers
          </div>
        </ChartSection>

        <ChartSection
          title="Job Status Breakdown"
          subtitle="Current month"
        >
          {/* <BarChart data={statusData} /> */}
          <div className="flex items-center justify-center h-full text-muted-foreground text-[13px]">
            Chart placeholder — use Recharts via shadcn wrappers
          </div>
        </ChartSection>
      </div>

      {/* Pattern: Recent activity table — compact, max 10 rows */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-[13px] font-medium text-foreground">Recent Activity</h2>
          <Button variant="ghost" size="sm" className="text-[13px]">
            View all
          </Button>
        </div>
        <DataTable
          columns={activityColumns}
          data={activities}
          keyExtractor={(row) => row.id}
          emptyTitle="No recent activity"
          emptyDescription="Activity will appear here as work progresses."
        />
      </div>
    </div>
  )
}
