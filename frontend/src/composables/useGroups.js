import { ref } from "vue"

const groups = ref([])
const loadingGroups = ref(false)
const groupsError = ref("")
const activeGroup = ref(null)
const loadingGroup = ref(false)
const groupError = ref("")
const creatingGroup = ref(false)
const createGroupError = ref("")

async function fetchGroups() {
  loadingGroups.value = true
  groupsError.value = ""

  try {
    const res = await fetch("/api/groups", {
      credentials: "include"
    })

    if (!res.ok) {
      throw new Error("Unable to load groups")
    }

    groups.value = await res.json()
  } catch (err) {
    groupsError.value = err.message || "Failed to load groups"
    groups.value = []
  } finally {
    loadingGroups.value = false
  }
}

async function fetchGroup(groupId) {
  loadingGroup.value = true
  groupError.value = ""

  try {
    const res = await fetch(`/api/groups/${groupId}`, {
      credentials: "include"
    })

    if (!res.ok) {
      if (res.status === 404) {
        throw new Error("Group not found")
      }
      if (res.status === 403) {
        throw new Error("You do not have access to this group")
      }
      throw new Error("Unable to load group")
    }

    activeGroup.value = await res.json()
  } catch (err) {
    groupError.value = err.message || "Failed to load group"
    activeGroup.value = null
  } finally {
    loadingGroup.value = false
  }
}

async function createGroup(payload) {
  creatingGroup.value = true
  createGroupError.value = ""
  try {
    const res = await fetch("/api/groups", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(payload)
    })

    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      throw new Error(body.detail || "Unable to create group")
    }

    const created = await res.json()
    groups.value = [created, ...groups.value]
    return created
  } catch (err) {
    createGroupError.value = err.message || "Failed to create group"
    throw err
  } finally {
    creatingGroup.value = false
  }
}

async function updateGroup(groupId, payload) {
  try {
    const res = await fetch(`/api/groups/${groupId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(payload)
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      throw new Error(body.detail || "Unable to update group")
    }
    const updated = await res.json()
    if (activeGroup.value && activeGroup.value.id === updated.id) {
      activeGroup.value = updated
    }
    groups.value = groups.value.map((group) => (group.id === updated.id ? updated : group))
    return updated
  } catch (err) {
    throw err
  }
}

export function useGroups() {
  return {
    groups,
    loadingGroups,
    groupsError,
    activeGroup,
    loadingGroup,
    groupError,
    creatingGroup,
    createGroupError,
    fetchGroups,
    fetchGroup,
    createGroup,
    updateGroup
  }
}
