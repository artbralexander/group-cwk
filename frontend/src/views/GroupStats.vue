<template>
  <div class="container py-4">
    <div class="mb-3">
      <RouterLink :to="{ name: 'GroupDetails', params: { id: route.params.id } }" class="text-decoration-none">
        ← Back to group
      </RouterLink>
    </div>

    <div class="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-4">
      <div>
        <h3 class="mb-1">{{ group?.name || "Group insights" }}</h3>
        <p class="text-muted mb-0">Visual breakdown of total expenses paid by each member.</p>
      </div>
      <div class="text-muted">
        Currency: <strong>{{ currencyCode }}</strong>
      </div>
    </div>

    <div v-if="insightError" class="alert alert-danger">
      {{ insightError }}
    </div>
    <div v-else-if="loadingState" class="text-center py-5">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>
    <div v-else>
      <div class="card mb-4">
        <div class="card-body">
          <div v-if="totalPaid > 0" class="d-flex flex-column flex-lg-row align-items-center gap-4">
            <div class="pie-wrapper">
              <div class="pie-chart" :style="pieStyle"></div>
              <div class="pie-center">
                <div class="fw-bold">{{ currencySymbol }}{{ totalPaid.toFixed(2) }}</div>
                <small class="text-muted">Total paid</small>
              </div>
            </div>
            <div class="flex-grow-1 w-100">
              <h5 class="mb-3">Contribution share</h5>
              <ul class="list-group">
                <li v-for="entry in coloredTotals" :key="entry.username" class="list-group-item d-flex justify-content-between align-items-center">
                  <div class="d-flex align-items-center gap-2">
                    <span class="legend-dot" :style="{ backgroundColor: entry.color }"></span>
                    <span class="fw-semibold">{{ entry.displayName }}</span>
                  </div>
                  <div class="text-end">
                    <div class="fw-bold">{{ currencySymbol }}{{ entry.paid.toFixed(2) }}</div>
                    <small class="text-muted">{{ sharePercent(entry.paid) }}% of total</small>
                  </div>
                </li>
              </ul>
            </div>
          </div>
          <div v-else class="alert alert-secondary mb-0">
            Record expenses in this group to unlock the pie chart insights.
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-body">
          <h5 class="card-title">Member contributions</h5>
          <div class="table-responsive">
            <table class="table table-sm align-middle mb-0">
              <thead>
                <tr>
                  <th scope="col">Member</th>
                  <th scope="col" class="text-end">Paid</th>
                  <th scope="col" class="text-end">Share</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="entry in coloredTotals" :key="entry.username">
                  <td>
                    <span class="legend-dot me-2" :style="{ backgroundColor: entry.color }"></span>
                    {{ entry.displayName }}
                  </td>
                  <td class="text-end">{{ currencySymbol }}{{ entry.paid.toFixed(2) }}</td>
                  <td class="text-end">{{ sharePercent(entry.paid) }}%</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, watch } from "vue"
import { useRoute, RouterLink } from "vue-router"
import { useGroups } from "../composables/useGroups"
import { useExpenses } from "../composables/useExpenses"
import { useAuth } from "../composables/useAuth"

const route = useRoute()
const { activeGroup: group, loadingGroup, groupError, fetchGroup } = useGroups()
const { expensesByGroup, loadingExpenses, expensesError, fetchExpenses } = useExpenses()
const { currentUser } = useAuth()

const currencySymbols = {
  GBP: "£",
  USD: "$",
  EUR: "€",
  CAD: "$",
  AUD: "$",
  JPY: "¥"
}

const currencyCode = computed(() => group.value?.currency || "GBP")
const currencySymbol = computed(() => currencySymbols[currencyCode.value] || currencyCode.value + " ")
const currentUsername = computed(() => currentUser.value?.username || "")
const expenses = computed(() => expensesByGroup.value[route.params.id] || [])

function displayMemberName(username) {
  if (!username) {
    return "Unknown"
  }
  return username === currentUsername.value ? "Me" : username
}

const contributionTotals = computed(() => {
  if (!group.value) {
    return []
  }
  const totals = {}
  group.value.members.forEach((member) => {
    totals[member.username] = { username: member.username, paid: 0 }
  })
  expenses.value.forEach((expense) => {
    const amount = Number(expense.amount) || 0
    const payer = expense.paid_by
    if (!totals[payer]) {
      totals[payer] = { username: payer, paid: 0 }
    }
    totals[payer].paid += amount
  })
  return Object.values(totals).map((entry) => ({
    ...entry,
    displayName: displayMemberName(entry.username)
  }))
})

const sortedTotals = computed(() => [...contributionTotals.value].sort((a, b) => b.paid - a.paid))
const chartColors = ["#6366f1", "#22d3ee", "#10b981", "#f97316", "#ef4444", "#a855f7", "#14b8a6"]
const coloredTotals = computed(() =>
  sortedTotals.value.map((entry, index) => ({
    ...entry,
    color: chartColors[index % chartColors.length]
  }))
)
const totalPaid = computed(() => coloredTotals.value.reduce((sum, entry) => sum + entry.paid, 0))
const chartSegments = computed(() => {
  const total = totalPaid.value
  if (!total) {
    return []
  }
  let cumulative = 0
  return coloredTotals.value
    .filter((entry) => entry.paid > 0)
    .map((entry) => {
      const start = cumulative
      const percentage = entry.paid / total
      cumulative += percentage
      return {
        ...entry,
        start: start * 100,
        end: cumulative * 100,
        percent: percentage * 100
      }
    })
})

const pieStyle = computed(() => {
  if (!chartSegments.value.length) {
    return {}
  }
  const segments = chartSegments.value.map(
    (segment) => `${segment.color} ${segment.start}% ${segment.end}%`
  )
  return { background: `conic-gradient(${segments.join(", ")})` }
})

const sharePercent = (amount) => {
  if (!totalPaid.value) {
    return "0.0"
  }
  return ((amount / totalPaid.value) * 100).toFixed(1)
}

const loadingState = computed(() => loadingGroup.value || loadingExpenses.value)
const insightError = computed(() => groupError.value || expensesError.value)

function loadData() {
  if (!route.params.id) return
  fetchGroup(route.params.id)
  fetchExpenses(route.params.id)
}

onMounted(() => {
  loadData()
})

watch(
  () => route.params.id,
  () => loadData()
)
</script>

<style scoped>
.pie-wrapper {
  position: relative;
  width: 260px;
  height: 260px;
  min-width: 220px;
  flex-shrink: 0;
}

.pie-chart {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: #f1f5f9;
  box-shadow: inset 0 0 30px rgba(15, 23, 42, 0.08);
}

.pie-center {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}

.legend-dot {
  width: 0.85rem;
  height: 0.85rem;
  border-radius: 50%;
  display: inline-block;
}
</style>
