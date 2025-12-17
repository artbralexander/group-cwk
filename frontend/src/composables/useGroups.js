import { ref } from "vue"
import { subscribeToNotifications } from "../services/notifications"

const groups = ref([])
const loadingGroups = ref(false)
const groupsError = ref("")
const activeGroup = ref(null)
const loadingGroup = ref(false)
const groupError = ref("")
const creatingGroup = ref(false)
const createGroupError = ref("")
let groupUpdatesUnsubscribe = null

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
    applyGroupUpdate(updated)
    return updated
  } catch (err) {
    throw err
  }
}

function applyGroupUpdate(updatedGroup) {
  if (!updatedGroup || !updatedGroup.id) {
    return
  }
  if (activeGroup.value && activeGroup.value.id === updatedGroup.id) {
    activeGroup.value = { ...activeGroup.value, ...updatedGroup }
  }
  const existingIndex = groups.value.findIndex((group) => group.id === updatedGroup.id)
  if (existingIndex >= 0) {
    const updatedList = [...groups.value]
    updatedList[existingIndex] = { ...updatedList[existingIndex], ...updatedGroup }
    groups.value = updatedList
  }
}

async function deleteGroup(groupId) {
  try {
    const res = await fetch(`/api/groups/${groupId}`, {
      method: "DELETE",
      credentials: "include"
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      throw new Error(body.detail || "Unable to delete group")
    }
    groups.value = groups.value.filter((group) => group.id !== groupId)
    if (activeGroup.value && activeGroup.value.id === groupId) {
      activeGroup.value = null
    }
  } catch (err) {
    throw err
  }
}

function connectToGroupUpdates() {
  if (groupUpdatesUnsubscribe || typeof window === "undefined") {
    return
  }
  groupUpdatesUnsubscribe = subscribeToNotifications("group_updated", (data) => {
    if (data) {
      applyGroupUpdate(data)
    }
  })
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
    updateGroup,
    deleteGroup,
    connectToGroupUpdates
  }
}
