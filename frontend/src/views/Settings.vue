<template>
  <div class="container py-4">
    <div class="row justify-content-center">
      <div class="col-lg-6">
        <div class="card">
          <div class="card-body">
            <h3 class="card-title mb-4">Account settings</h3>

            <form @submit.prevent="saveSettings">
              <div class="mb-3">
                <label class="form-label">Username</label>
                <input type="text" class="form-control" :value="currentUser?.username" disabled />
              </div>

              <div class="mb-3">
                <label for="email" class="form-label">Email</label>
                <input
                  id="email"
                  v-model.trim="form.email"
                  type="email"
                  class="form-control"
                  required
                />
              </div>

              <div class="border rounded p-3 mb-3">
                <h6 class="fw-semibold mb-3">Change password</h6>
                <div class="mb-3">
                  <label for="currentPassword" class="form-label">Current password</label>
                  <input
                    id="currentPassword"
                    v-model="form.currentPassword"
                    type="password"
                    class="form-control"
                    :required="Boolean(form.newPassword)"
                    autocomplete="current-password"
                  />
                </div>
                <div class="mb-3">
                  <label for="newPassword" class="form-label">New password</label>
                  <input
                    id="newPassword"
                    v-model="form.newPassword"
                    type="password"
                    class="form-control"
                    autocomplete="new-password"
                  />
                  <div class="form-text">Leave blank to keep your current password.</div>
                </div>
                <div>
                  <label for="confirmPassword" class="form-label">Confirm new password</label>
                  <input
                    id="confirmPassword"
                    v-model="form.confirmPassword"
                    type="password"
                    class="form-control"
                    :disabled="!form.newPassword"
                    autocomplete="new-password"
                  />
                </div>
                <div class="mt-3" v-if="form.newPassword">
                  <p class="small text-muted mb-1">Password requirements:</p>
                  <ul class="list-unstyled small mb-0">
                    <li :class="requirementClass(passwordRequirements.hasMinLength)">
                      • At least 8 characters
                    </li>
                    <li :class="requirementClass(passwordRequirements.hasMaxLength)">
                      • No more than 64 characters
                    </li>
                    <li :class="requirementClass(passwordRequirements.matches)">
                      • Matches confirmation
                    </li>
                  </ul>
                </div>
              </div>

              <div v-if="error" class="alert alert-danger py-2">{{ error }}</div>
              <div v-if="success" class="alert alert-success py-2">{{ success }}</div>

              <button class="btn btn-primary w-100" type="submit" :disabled="loading">
                <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
                Save changes
              </button>
            </form>
          </div>
        </div>
        <div class="card mt-4">
          <div class="card-body">
            <h3 class="card-title mb-4">Spending summary</h3>

            <div v-if="loadingSummary">Loading…</div>
            <div v-else-if="summaryError" class="alert alert-danger py-2">{{ summaryError }}</div>

            <div v-else-if="summary">
              <div class="row g-3 mb-3">
                <div class="col-md-4">
                  <div class="border rounded p-3">
                    <div class="text-muted">Total paid</div>
                    <div class="fs-5">{{ summary.overall_paid.toFixed(2) }}</div>
                  </div>
                </div>
                <div class="col-md-4">
                  <div class="border rounded p-3">
                    <div class="text-muted">Total owed</div>
                    <div class="fs-5">{{ summary.overall_owed.toFixed(2) }}</div>
                  </div>
                </div>
                <div class="col-md-4">
                  <div class="border rounded p-3">
                    <div class="text-muted">Net</div>
                    <div class="fs-5">{{ summary.overall_net.toFixed(2) }}</div>
                  </div>
                </div>
              </div>

              <div v-if="summary.groups.length === 0" class="text-muted">
                You are not in any groups yet.
              </div>

              <div v-else class="table-responsive">
                <table class="table table-sm align-middle mb-0">
                  <thead>
                    <tr>
                      <th>Group</th>
                      <th class="text-end">Paid</th>
                      <th class="text-end">Owed</th>
                      <th class="text-end">Net</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="g in summary.groups" :key="g.group_id">
                      <td>
                        <router-link :to="`/groups/${g.group_id}`">{{ g.group_name }}</router-link>
                        <span class="text-muted ms-2">{{ g.currency }}</span>
                      </td>
                      <td class="text-end">{{ g.paid.toFixed(2) }}</td>
                      <td class="text-end">{{ g.owed.toFixed(2) }}</td>
                      <td class="text-end">{{ g.net.toFixed(2) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <hr class="my-4" />
                <div class="d-flex justify-content-between align-items-center mb-2">
                  <h5 class="mb-0">Spending overview</h5>
                  <button
                    class="btn btn-outline-primary btn-sm"
                    type="button"
                    :disabled="loadingSummaryText"
                    @click="fetchSpendingSummaryText"
                  >
                    <span
                      v-if="loadingSummaryText"
                      class="spinner-border spinner-border-sm me-2"
                    ></span>
                    Generate summary
                  </button>
                </div>

                <div v-if="summaryTextError" class="alert alert-danger py-2">
                  {{ summaryTextError }}
                </div>

                <div
                  v-else-if="summaryText"
                  class="border rounded p-3"
                >
                  {{ summaryText }}
                </div>

                <div v-else class="text-muted small">
                  Click “Generate summary” to get a short overview of your spending habits.
                </div>

            </div>

            <div v-else class="text-muted">
              No summary available.
            </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from "vue"
import { useAuth } from "../composables/useAuth"
import { useProfile } from "../composables/useProfile"

const { currentUser, fetchCurrentUser } = useAuth()
const {
  summary,
  loadingSummary,
  summaryError,
  fetchSpendingSummary,
  summaryText,
  loadingSummaryText,
  summaryTextError,
  fetchSpendingSummaryText
} = useProfile()

const form = reactive({
  email: "",
  currentPassword: "",
  newPassword: "",
  confirmPassword: ""
})

const loading = ref(false)
const error = ref("")
const success = ref("")

const passwordRequirements = computed(() => {
  const length = form.newPassword.length
  return {
    hasMinLength: length >= 8,
    hasMaxLength: length <= 64,
    matches: length > 0 && form.newPassword === form.confirmPassword
  }
})

function requirementClass(satisfied) {
  return satisfied ? "text-success" : "text-muted"
}

watch(
  () => currentUser.value,
  (user) => {
    if (user) {
      form.email = user.email || ""
    }
  },
  { immediate: true }
)

async function saveSettings() {
  error.value = ""
  success.value = ""

  if (!form.email) {
    error.value = "Email is required"
    return
  }

  const payload = {}
  const currentEmail = currentUser.value?.email || ""
  if (form.email !== currentEmail) {
    payload.email = form.email
  }

  if (form.newPassword) {
    if (form.newPassword !== form.confirmPassword) {
      error.value = "New passwords do not match"
      return
    }
    if (form.newPassword.length < 8 || form.newPassword.length > 64) {
      error.value = "Password must be between 8 and 64 characters"
      return
    }
    if (!form.currentPassword) {
      error.value = "Current password is required to set a new one"
      return
    }
    payload.current_password = form.currentPassword
    payload.new_password = form.newPassword
  }

  if (!payload.email && !payload.new_password) {
    success.value = "No changes to save"
    return
  }

  loading.value = true
  try {
    const res = await fetch("/api/auth/me", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(payload)
    })

    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      throw new Error(body.detail || "Unable to update settings")
    }

    await fetchCurrentUser()
    form.currentPassword = ""
    form.newPassword = ""
    form.confirmPassword = ""
    success.value = "Profile updated"
  } catch (err) {
    error.value = err.message || "Failed to update settings"
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  if (!currentUser.value) {
    await fetchCurrentUser()
  }
  fetchSpendingSummary()
})
</script>
