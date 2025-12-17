<template>
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <div>
        <h2 class="mb-0">Your Groups</h2>
        <p class="text-muted mb-0">Track shared expenses with friends and family.</p>
      </div>
      <button class="btn btn-primary btn-sm" type="button" @click="openCreateModal">
        Create group
      </button>
    </div>

    <section class="mb-4">
      <h5 class="mb-3">Invitations</h5>
      <div v-if="inviteError" class="alert alert-danger">
        {{ inviteError }}
      </div>
      <div v-else-if="loadingInvites" class="text-center py-3">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
      </div>
      <div v-else-if="invites.length === 0" class="alert alert-secondary mb-0">
        No pending invitations.
      </div>
      <div v-else class="list-group">
        <div
          v-for="invite in invites"
          :key="invite.id"
          class="list-group-item d-flex justify-content-between align-items-center"
        >
          <div>
            <div class="fw-semibold">{{ invite.group_name }}</div>
            <small class="text-muted">Invited by {{ invite.inviter_username }}</small>
          </div>
          <button
            class="btn btn-success btn-sm"
            type="button"
            :disabled="acceptingInviteId === invite.id"
            @click="handleAcceptInvite(invite.id)"
          >
            <span v-if="acceptingInviteId === invite.id" class="spinner-border spinner-border-sm me-2"></span>
            Accept
          </button>
        </div>
      </div>
    </section>

    <div v-if="groupsError" class="alert alert-danger">
      {{ groupsError }}
    </div>

    <div v-else-if="loadingGroups" class="text-center py-5">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>

    <div v-else>
      <div v-if="groups.length === 0" class="alert alert-info">
        You haven’t joined any groups yet. Create one to get started.
      </div>

      <div v-else class="row g-3">
        <div v-for="group in groups" :key="group.id" class="col-12 col-md-6 col-lg-4">
          <div class="card h-100">
            <div class="card-body d-flex flex-column">
              <div class="d-flex justify-content-between align-items-start mb-2">
                <h5 class="card-title mb-0">{{ group.name }}</h5>
                <span class="badge text-bg-light border">{{ group.currency }}</span>
              </div>
              <p class="text-muted small mb-2">
                {{ group.members.length }} member{{ group.members.length === 1 ? "" : "s" }}
              </p>

              <ul class="list-group list-group-flush flex-grow-1 mb-3">
                <li
                  v-for="member in group.members"
                  :key="member.id"
                  class="list-group-item d-flex justify-content-between align-items-center"
                >
                  <div>
                    <div class="d-flex align-items-center gap-2">
                      <span>{{ member.username }}</span>
                      <span v-if="member.role === 'owner'" class="badge text-bg-primary">Owner</span>
                    </div>
                    <small class="text-muted d-block">{{ member.email }}</small>
                  </div>
                  <small class="text-muted">{{ member.role === "owner" ? "Owner" : "Member" }}</small>
                </li>
              </ul>

              <RouterLink
                class="btn btn-outline-secondary btn-sm mt-auto"
                :to="{ name: 'GroupDetails', params: { id: group.id } }"
              >
                View details
              </RouterLink>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div v-if="showCreateModal">
      <div class="modal-backdrop fade show"></div>
      <div class="modal d-block" tabindex="-1">
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">Create new group</h5>
              <button type="button" class="btn-close" @click="closeCreateModal"></button>
            </div>
            <div class="modal-body">
              <form @submit.prevent="submitCreateGroup">
                <div class="mb-3">
                  <label for="groupName" class="form-label">Group name</label>
                  <input id="groupName" v-model.trim="createForm.name" type="text" class="form-control" required />
                </div>

                <div class="mb-3">
                  <label for="groupCurrency" class="form-label">Currency</label>
                  <select id="groupCurrency" v-model="createForm.currency" class="form-select">
                    <option v-for="option in currencyOptions" :key="option" :value="option">{{ option }}</option>
                  </select>
                </div>

                <div class="mb-3">
                  <label for="groupMembers" class="form-label">Invite members (usernames)</label>
                  <input
                    id="groupMembers"
                    v-model="createForm.members"
                    type="text"
                    class="form-control"
                    placeholder="Comma-separated usernames"
                  />
                  <div class="form-text">You’re added automatically. Members receive invites immediately.</div>
                </div>

                <div v-if="createFormError || createGroupError" class="alert alert-danger py-2">
                  {{ createFormError || createGroupError }}
                </div>

                <button class="btn btn-primary w-100" :disabled="creatingGroup">
                  <span v-if="creatingGroup" class="spinner-border spinner-border-sm me-2"></span>
                  Create group
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue"
import { RouterLink } from "vue-router"
import { useGroups } from "../composables/useGroups"
import { useInvites } from "../composables/useInvites"

const {
  groups,
  loadingGroups,
  groupsError,
  fetchGroups,
  createGroup,
  creatingGroup,
  createGroupError
} = useGroups()
const {
  invites,
  loadingInvites,
  inviteError,
  acceptingInviteId,
  fetchInvites,
  acceptInvite,
  connectToInviteSocket
} = useInvites()

const showCreateModal = ref(false)
const createForm = reactive({
  name: "",
  currency: "GBP",
  members: ""
})
const createFormError = ref("")
const currencyOptions = ["GBP", "USD", "EUR", "CAD", "AUD", "JPY"]

async function handleAcceptInvite(inviteId) {
  try {
    await acceptInvite(inviteId)
    await fetchGroups()
  } catch {
    // errors already surfaced through inviteError
  }
}

function openCreateModal() {
  createFormError.value = ""
  showCreateModal.value = true
}

function closeCreateModal() {
  showCreateModal.value = false
  createFormError.value = ""
  createForm.name = ""
  createForm.members = ""
  createForm.currency = "GBP"
}

async function submitCreateGroup() {
  createFormError.value = ""
  if (!createForm.name) {
    createFormError.value = "Group name is required"
    return
  }

  const members = createForm.members
    .split(",")
    .map((m) => m.trim())
    .filter((m) => m.length > 0)

  try {
    await createGroup({
      name: createForm.name,
      currency: createForm.currency,
      members
    })
    closeCreateModal()
    await fetchGroups()
  } catch (err) {
    createFormError.value = err.message || "Failed to create group"
  }
}

onMounted(() => {
  fetchGroups()
  fetchInvites()
  connectToInviteSocket()
})
</script>
