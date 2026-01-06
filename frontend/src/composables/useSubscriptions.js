import { ref } from "vue"

export function useSubscriptions() {
  const loading = ref(false)
  const error = ref("")

  async function request(url, options = {}) {
    loading.value = true
    error.value = ""
    try {
      const res = await fetch(url, { credentials: "include", ...options })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || "Request failed")
      }
      return await res.json()
    } catch (err) {
      error.value = err.message || "Request failed"
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    error,
    list(groupId) {
      return request(`/api/groups/${groupId}/subscriptions`)
    },
    create(groupId, payload) {
      return request(`/api/groups/${groupId}/subscriptions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      })
    },
    update(groupId, subId, payload) {
      return request(`/api/groups/${groupId}/subscriptions/${subId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      })
    },
    remove(groupId, subId) {
      return request(`/api/groups/${groupId}/subscriptions/${subId}`, { method: "DELETE" })
    },
    pay(groupId, subId) {
      return request(`/api/groups/${groupId}/subscriptions/${subId}/pay`, { method: "POST" })
    }
  }
}
