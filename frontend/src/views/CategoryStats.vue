<template>
  <div class="container py-4">
    <RouterLink :to="`/groups/${groupId}`" class="text-decoration-none">
      Back to Group
    </RouterLink>
    <h3 class="mt-3">{{ category?.name }} - Insights</h3>
    <div v-if="loading">Loading...</div>

    <div v-else>
      <div class="row g-4">
        <div class="col-md-6">
          <div class="card">
            <div class="card-body">
              <h5>Total Spent</h5>
              <p class="fs-4 fw-bold">
                £{{ totalSpent.toFixed(2) }}
              </p>
            </div>
          </div>
        </div>
        <div class="col-md-6">
          <div class="card">
            <div class="card-body">
              <h5>Spending Split</h5>
              <div v-if="totalSpent>0" class="pie-wrapper">
                <div class="pie-chart" :style="pieStyle"></div>
                <div class="pie-center">
                  <div class="fw-bold">£{{ totalSpent.toFixed(2) }}</div>
                  <small class="text-muted">Total</small>
                </div>
              </div>
              <ul class="list-group mt-3">
                <li v-for="entry in coloredTotals" :key="entry.username" class="list-group-item d-flex justify-content-between align-items-center">
                  <div class="d-flex align-items-center gap-2">
                    <span class="legend-dot" :style="{backgroundColor: entry.color}"></span>
                    <span class="fw-semibold">{{ entry.username }}</span>
                  </div>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
      <div class="card mt-4">
        <div class="card-body">
          <h5>Expenses in this category</h5>
          <ul class="list-group list-group-flush">
            <li v-for="expense in categoryExpenses" :key="expense.id" class="list-group-item">
              {{ expense.description }}
              £{{ expense.amount.toFixed(2) }}
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { useExpenses } from '../composables/useExpenses';
import { useCategories } from '../composables/useCategories';

const route = useRoute()
const groupId = computed(() => route.params.id)
const categoryId = computed(() => Number(route.params.categoryId))
const {expensesByGroup, fetchExpenses} = useExpenses()
const {categories, fetchCategories, loadingCategories} = useCategories(groupId)

onMounted(async () => {
  await fetchCategories()
  console.log("Categories:", categories.value)
  console.log("categoryId:", categoryId)
  await fetchExpenses(groupId.value)
})

const category = computed(() => categories.value.find(c => c.id === categoryId.value))
const categoryExpenses = computed(() => (expensesByGroup.value[groupId.value] || []).filter(
  e => e.category_id === categoryId.value
))
const perUserTotals = computed(() => {
  const totals = {}
  categoryExpenses.value.forEach(expense => {
    expense.splits.forEach(split => {
      if (!totals[split.username]){
        totals[split.username] = 0
      }
      totals[split.username] += Number(split.amount)||0
    })
  })
  return Object.entries(totals).map(([username,amount]) => ({username,amount}))
})
const sortedTotals = computed(() => [...perUserTotals.value].sort((a,b) => b.amount-a.amount))
const loading = computed(() => loadingCategories.value)

//Pie chart colours same as group stats
const chartColors = ["#6366f1", "#22d3ee", "#10b981", "#f97316", "#ef4444", "#a855f7", "#14b8a6"]
const coloredTotals = computed(() =>
  sortedTotals.value.map((entry, index) => ({
    ...entry,
    color: chartColors[index % chartColors.length]
  }))
)
const totalSpent = computed(()=> coloredTotals.value.reduce((sum,e) => sum+e.amount,0))
const sharePercent = (amount) => {
  if (!totalSpent.value) return "0.0"
  return ((amount/totalSpent.value)*100).toFixed(1)
}

const chartSegments = computed(() => {
  const total = totalSpent.value
  if (!total) {
    return []
  }
  let cumulative = 0
  return coloredTotals.value
    .filter((entry) => entry.amount > 0)
    .map((entry) => {
      const start = cumulative
      const percentage = entry.amount/ total
      cumulative += percentage
      return {
        ...entry,
        start: start * 100,
        end: cumulative * 100
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