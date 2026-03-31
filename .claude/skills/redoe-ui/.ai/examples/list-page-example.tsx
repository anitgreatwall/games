/**
 * GOLD STANDARD: List Page (Pattern 1)
 * Tool list with filter bar, data table, and pagination.
 * Copy this structure when building any list/table view.
 */

import { Plus } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  PageHeader,
  FilterBar,
  DataTable,
  StatusBadge,
  EntityBadge,
  type Column,
} from "@/components/redoe"

// Types match Supabase schema — never hand-write
interface Tool {
  id: string
  job_number: string
  customer: string
  program: string
  status: "active" | "at-risk" | "complete" | "pending"
  entity: "redoe-windsor" | "redoe-hunan"
  revenue: number
  due_date: string
}

const columns: Column<Tool>[] = [
  {
    key: "job_number",
    header: "Job #",
    render: (row) => (
      <span className="font-mono text-muted-foreground">{row.job_number}</span>
    ),
  },
  { key: "customer", header: "Customer" },
  { key: "program", header: "Program" },
  {
    key: "status",
    header: "Status",
    render: (row) => <StatusBadge status={row.status} size="sm" />,
  },
  {
    key: "entity",
    header: "Entity",
    render: (row) => <EntityBadge entity={row.entity} />,
  },
  {
    key: "revenue",
    header: "Revenue",
    numeric: true,
    render: (row) =>
      new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        maximumFractionDigits: 0,
      }).format(row.revenue),
  },
  {
    key: "due_date",
    header: "Due Date",
    render: (row) => (
      <span className="font-mono text-muted-foreground">{row.due_date}</span>
    ),
  },
]

export default function ToolListPage() {
  // In real code: const { data, isLoading } = useJobs(filters)
  const tools: Tool[] = [] // Replace with real data

  return (
    <div className="space-y-4">
      {/* Pattern: PageHeader with title + primary action */}
      <PageHeader
        title="Tools"
        description="Redoe Windsor · 42 active tools"
        actions={
          <Button>
            <Plus className="size-4 mr-1.5" />
            Create Work Order
          </Button>
        }
      />

      {/* Pattern: FilterBar — search + filters + export on one line */}
      <FilterBar
        searchPlaceholder="Search tools..."
        onExport={() => {/* export logic */}}
      />

      {/* Pattern: DataTable with typed columns, empty state built in */}
      <DataTable
        columns={columns}
        data={tools}
        keyExtractor={(row) => row.id}
        onRowClick={(row) => {/* router.push(`/tools/${row.id}`) */}}
        emptyTitle="No tools found"
        emptyDescription="Tools matching your filters will appear here."
        emptyAction={
          <Button>
            <Plus className="size-4 mr-1.5" />
            Create Work Order
          </Button>
        }
      />

      {/* Pattern: Pagination at bottom */}
      <div className="flex items-center justify-between text-[13px] text-muted-foreground">
        <span>Showing 1-25 of 42 results</span>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" disabled>Previous</Button>
          <Button variant="outline" size="sm">Next</Button>
        </div>
      </div>
    </div>
  )
}
