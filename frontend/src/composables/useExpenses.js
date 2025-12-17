import { ref } from "vue"
import { subscribeToNotifications } from "../services/notifications"

const expensesByGroup = ref({})
const loadingExpenses = ref(false)
const expensesError = ref("")
const savingExpense = ref(false)
const settlementsByGroup = ref({})
const loadingSettlements = ref(false)
const settlementsError = ref("")
let settlementUnsubscribe = null
let expenseUnsubscribe = null

async function fetchExpenses(groupId) {
  loadingExpenses.value = true
  expensesError.value = ""

  try {
    const res = await fetch(`/api/groups/${groupId}/expenses`, { credentials: "include" })
    if (!res.ok) {
      throw new Error("Unable to load expenses")
    }
    const data = await res.json()
    expensesByGroup.value[groupId] = data
  } catch (err) {
    expensesError.value = err.message || "Failed to load expenses"
    expensesByGroup.value[groupId] = []
  } finally {
    loadingExpenses.value = false
  }
}

async function createExpense(groupId, payload) {
  savingExpense.value = true
  expensesError.value = ""
  try {
    const res = await fetch(`/api/groups/${groupId}/expenses`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(payload)
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      throw new Error(body.detail || "Unable to create expense")
    }
    const newExpense = await res.json()
    const current = expensesByGroup.value[groupId] || []
    expensesByGroup.value[groupId] = [newExpense, ...current]
    return newExpense
  } catch (err) {
    expensesError.value = err.message || "Failed to save expense"
    throw err
  } finally {
    savingExpense.value = false
  }
}

async function updateExpense(groupId, expenseId, payload) {
  savingExpense.value = true
  expensesError.value = ""
  try {
    const res = await fetch(`/api/groups/${groupId}/expenses/${expenseId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(payload)
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      throw new Error(body.detail || "Unable to update expense")
    }
    const updated = await res.json()
    const current = expensesByGroup.value[groupId] || []
    const idx = current.findIndex((e) => e.id === expenseId)
    if (idx >= 0) {
      current[idx] = updated
      expensesByGroup.value[groupId] = [...current]
    }
    return updated
  } catch (err) {
    expensesError.value = err.message || "Failed to save expense"
    throw err
  } finally {
    savingExpense.value = false
  }
}

async function deleteExpense(groupId, expenseId) {
  expensesError.value = ""
  try {
    const res = await fetch(`/api/groups/${groupId}/expenses/${expenseId}`, {
      method: "DELETE",
      credentials: "include"
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      throw new Error(body.detail || "Unable to delete expense")
    }
    const current = expensesByGroup.value[groupId] || []
    expensesByGroup.value[groupId] = current.filter((expense) => expense.id !== expenseId)
  } catch (err) {
    expensesError.value = err.message || "Failed to delete expense"
    throw err
  }
}

async function fetchSettlements(groupId) {
  loadingSettlements.value = true
  settlementsError.value = ""

  try {
    const res = await fetch(`/api/groups/${groupId}/settlements`, { credentials: "include" })
    if (!res.ok) {
      throw new Error("Unable to load settlements")
    }
    settlementsByGroup.value[groupId] = await res.json()
  } catch (err) {
    settlementsError.value = err.message || "Failed to load settlements"
    settlementsByGroup.value[groupId] = { recommendations: [], records: [] }
  } finally {
    loadingSettlements.value = false
  }
}

async function recordSettlement(groupId, payload) {
  settlementsError.value = ""
  try {
    const res = await fetch(`/api/groups/${groupId}/settlements`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(payload)
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      throw new Error(body.detail || "Unable to record settlement")
    }
    const record = await res.json()
    const summary = settlementsByGroup.value[groupId] || { recommendations: [], records: [] }
    settlementsByGroup.value[groupId] = {
      recommendations: summary.recommendations || [],
      records: [record, ...(summary.records || [])]
    }
    return record
  } catch (err) {
    settlementsError.value = err.message || "Failed to record settlement"
    throw err
  }
}

async function confirmSettlement(groupId, settlementId) {
  settlementsError.value = ""
  try {
    const res = await fetch(`/api/groups/${groupId}/settlements/${settlementId}/confirm`, {
      method: "POST",
      credentials: "include"
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      throw new Error(body.detail || "Unable to confirm settlement")
    }
    const updated = await res.json()
    const summary = settlementsByGroup.value[groupId] || { recommendations: [], records: [] }
    const records = (summary.records || []).map((record) => (record.id === updated.id ? updated : record))
    settlementsByGroup.value[groupId] = {
      recommendations: summary.recommendations || [],
      records
    }
    return updated
  } catch (err) {
    settlementsError.value = err.message || "Failed to confirm settlement"
    throw err
  }
}

function connectToExpenseNotifications() {
  if (typeof window === "undefined") {
    return
  }
  if (!settlementUnsubscribe) {
    settlementUnsubscribe = subscribeToNotifications("settlement_update", (data) => {
      if (data?.group_id) {
        fetchSettlements(data.group_id)
      }
    })
  }
  if (!expenseUnsubscribe) {
    expenseUnsubscribe = subscribeToNotifications("expenses_changed", (data) => {
      if (data?.group_id) {
        fetchExpenses(data.group_id)
        fetchSettlements(data.group_id)
      }
    })
  }
}

export function useExpenses() {
  return {
    expensesByGroup,
    loadingExpenses,
    expensesError,
    savingExpense,
    settlementsByGroup,
    loadingSettlements,
    settlementsError,
    fetchExpenses,
    fetchSettlements,
    createExpense,
    updateExpense,
    deleteExpense,
    recordSettlement,
    confirmSettlement,
    connectToExpenseNotifications
  }
}
