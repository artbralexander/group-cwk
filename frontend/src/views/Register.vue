<template>
  <div class="container py-5">
    <div class="row justify-content-center">
      <div class="col-md-6 col-lg-5">
        <div class="card shadow-sm">
          <div class="card-body">
            <h3 class="card-title mb-4 text-center">Create your account</h3>

            <form @submit.prevent="registerUser">
              <div class="mb-3">
                <label for="email" class="form-label">Email</label>
                <input
                  id="email"
                  v-model.trim="form.email"
                  type="email"
                  class="form-control"
                  required
                  autocomplete="email"
                />
              </div>

              <div class="mb-3">
                <label for="username" class="form-label">Username</label>
                <input
                  id="username"
                  v-model.trim="form.username"
                  type="text"
                  class="form-control"
                  required
                  autocomplete="username"
                />
              </div>

              <div class="mb-3">
                <label for="password" class="form-label">Password</label>
                <input
                  id="password"
                  v-model="form.password"
                  type="password"
                  class="form-control"
                  required
                  autocomplete="new-password"
                />
                <div class="mt-2">
                  <div class="progress" style="height: 6px;">
                    <div
                      class="progress-bar"
                      role="progressbar"
                      :class="`bg-${passwordStrength.variant}`"
                      :style="{ width: `${passwordStrength.score}%` }"
                      aria-label="Password strength"
                    ></div>
                  </div>
                  <small :class="`text-${passwordStrength.variant}`">
                    {{ passwordStrength.label }}
                  </small>
                </div>
              </div>

              <div class="mb-3">
                <label for="confirmPassword" class="form-label">Confirm password</label>
                <input
                  id="confirmPassword"
                  v-model="form.confirmPassword"
                  type="password"
                  class="form-control"
                  required
                  autocomplete="new-password"
                />
                <small v-if="form.confirmPassword && !passwordsMatch" class="text-danger">
                  Passwords do not match
                </small>
              </div>

              <div class="mb-3">
                <p class="mb-1 small text-muted">Password requirements:</p>
                <ul class="small list-unstyled mb-0">
                  <li :class="requirementClass(requirements.hasMinLength)">
                    • At least 8 characters
                  </li>
                  <li :class="requirementClass(requirements.hasMaxLength)">
                    • No more than 64 characters
                  </li>
                </ul>
              </div>

              <div v-if="error" class="alert alert-danger py-2">
                {{ error }}
              </div>

              <button
                type="submit"
                class="btn btn-primary w-100"
                :disabled="loading || !canSubmit"
              >
                <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
                Create account
              </button>
            </form>

            <hr class="my-4" />

            <div class="text-center">
              <small class="text-muted">
                Already have an account?
                <RouterLink to="/login">Sign in</RouterLink>
              </small>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from "vue"
import { useRouter, RouterLink } from "vue-router"
import { useAuth } from "../composables/useAuth"

const router = useRouter()
const { fetchCurrentUser } = useAuth()

const form = reactive({
  email: "",
  username: "",
  password: "",
  confirmPassword: ""
})

const loading = ref(false)
const error = ref("")

const requirements = computed(() => ({
  hasMinLength: form.password.length >= 8,
  hasMaxLength: form.password.length <= 64,
  hasBonusLength: form.password.length >= 32
}))

const strengthScore = computed(() => {
  let score = 0
  const length = form.password.length
  if (requirements.value.hasMinLength) score += 40
  if (length >= 12) score += 20
  if (length >= 20) score += 20
  if (requirements.value.hasBonusLength) score += 20
  return Math.min(score, 100)
})

const passwordStrength = computed(() => {
  if (!form.password) return { label: "Start typing a password", variant: "secondary", score: 5 }

  if (strengthScore.value < 40) {
    return { label: "Too weak — add more length", variant: "danger", score: strengthScore.value }
  }
  if (strengthScore.value < 70) {
    return { label: "Decent — longer is safer", variant: "warning", score: strengthScore.value }
  }
  return { label: "Strong password!", variant: "success", score: strengthScore.value }
})

const passwordsMatch = computed(
  () =>
    Boolean(form.password) &&
    Boolean(form.confirmPassword) &&
    form.password === form.confirmPassword
)

const canSubmit = computed(
  () => requirements.value.hasMinLength && requirements.value.hasMaxLength && passwordsMatch.value
)

function requirementClass(satisfied) {
  return satisfied ? "text-success" : "text-muted"
}

async function registerUser() {
  if (!canSubmit.value) return

  loading.value = true
  error.value = ""

  try {
    const res = await fetch("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({
        email: form.email,
        username: form.username,
        password: form.password,
        confirm_password: form.confirmPassword
      })
    })

    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      throw new Error(body.detail || "Registration failed")
    }

    await fetchCurrentUser()
    router.push("/")
  } catch (err) {
    error.value = err.message || "Registration failed"
  } finally {
    loading.value = false
  }
}
</script>
