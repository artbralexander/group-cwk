<template>
  <div class="container py-4">
    <div class="mb-3">
      <RouterLink to="/groups" class="text-decoration-none">
        ← Back to groups
      </RouterLink>
    </div>

    <div v-if="groupError" class="alert alert-danger">
      {{ groupError }}
    </div>
    <div v-else-if="loadingGroup" class="text-center py-5">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>
    <div v-else-if="group">
      <div class="card mb-4">
        <div class="card-body">
          <div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
            <h3 class="card-title mb-0">{{ group.name }}</h3>
            <div class="d-flex align-items-center gap-2">
              <span class="badge text-bg-light border">{{ group.currency }}</span>
              <button
                v-if="isOwner"
                class="btn btn-outline-secondary btn-sm"
                type="button"
                @click="toggleGroupSettings"
              >
                {{ showGroupSettings ? "Close editor" : "Edit group" }}
              </button>
            </div>
          </div>
          <p class="text-muted mb-4">
            {{ group.members.length }} member{{ group.members.length === 1 ? "" : "s" }}
          </p>

          <div v-if="isOwner && showGroupSettings" class="border rounded p-3 mb-4">
            <form class="row g-3" @submit.prevent="saveGroupSettings">
              <div class="col-12 col-md-8">
                <label class="form-label" for="groupSettingsName">Group name</label>
                <input
                  id="groupSettingsName"
                  v-model.trim="groupSettingsForm.name"
                  type="text"
                  class="form-control"
                  required
                />
              </div>
              <div class="col-12 col-md-4">
                <label class="form-label" for="groupSettingsCurrency">Currency</label>
                <select id="groupSettingsCurrency" v-model="groupSettingsForm.currency" class="form-select">
                  <option v-for="option in currencyOptions" :key="option" :value="option">{{ option }}</option>
                </select>
              </div>
              <div class="col-12" v-if="groupSettingsError">
                <div class="alert alert-danger py-2 mb-0">{{ groupSettingsError }}</div>
              </div>
              <div class="col-12 d-flex gap-2 justify-content-end">
                <button class="btn btn-outline-secondary" type="button" @click="toggleGroupSettings">
                  Cancel
                </button>
                <button class="btn btn-primary" type="submit" :disabled="savingGroupSettings">
                  <span v-if="savingGroupSettings" class="spinner-border spinner-border-sm me-2"></span>
                  Save changes
                </button>
              </div>
            </form>
          </div>

          <h5>Members</h5>
          <ul class="list-group list-group-flush">
            <li v-for="member in group.members" :key="member.id" class="list-group-item">
              <div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
                <div>
                  <div class="d-flex align-items-center gap-2">
                    <span class="fw-semibold">{{ displayMemberName(member.username) }}</span>
                    <span v-if="member.role === 'owner'" class="badge text-bg-primary">Owner</span>
                  </div>
                  <small class="text-muted d-block">{{ member.email }}</small>
                </div>
                <small class="text-muted">{{ member.role === "owner" ? "Group owner" : "Member" }}</small>
              </div>
            </li>
          </ul>
          <div class="d-flex justify-content-between align-items-center flex-wrap gap-2 mt-3">
            <small class="text-muted mb-0" v-if="isOwner">
              Owners can’t leave. Delete the group once all balances are settled.
            </small>
            <small class="text-muted mb-0" v-else>Leaving removes your access once all balances are clear.</small>
            <button
              v-if="isOwner"
              class="btn btn-danger btn-sm"
              type="button"
              :disabled="deletingGroup"
              @click="handleDeleteGroup"
            >
              <span v-if="deletingGroup" class="spinner-border spinner-border-sm me-2"></span>
              Delete group
            </button>
            <button
              v-else
              class="btn btn-outline-danger btn-sm"
              type="button"
              :disabled="leavingGroup"
              @click="handleLeaveGroup"
            >
              <span v-if="leavingGroup" class="spinner-border spinner-border-sm me-2"></span>
              Leave group
            </button>
          </div>
          <p v-if="!isOwner && leaveError" class="text-danger small mt-2 mb-0">{{ leaveError }}</p>
          <p v-if="isOwner && deleteGroupError" class="text-danger small mt-2 mb-0">{{ deleteGroupError }}</p>
        </div>
      </div>

      <div class="row g-4">
        <div class="col-lg-6">
          <div class="card h-100">
            <div class="card-body d-flex flex-column">
              <h5 class="card-title">Add expense</h5>
              <p class="text-muted flex-grow-1">
                Record new group expenses, split them equally or customize shares, and edit or delete them later.
              </p>
              <button class="btn btn-success mt-3" type="button" @click="openExpenseModal()">
                Add expense
              </button>
            </div>
          </div>
        </div>
        <div class ='col-lg-6'>
          <div class="card h-100">
            <div class="card-body d-flex flex-column">
              <h5 class="card-title">Add category</h5>
              <p class="text-muted flex-grow-1">
                Record new group expense categories, split them equally or customize shares, and edit or delete them later.
              </p>
              <button class="btn btn-success mt-3" type="button" @click="openCategoryModal()">
                Add category
              </button>
            </div>
          </div>
        </div>
      </div>
      <div class="card mt-4">
        <div class="card-body">
          <div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
            <h5 class="card-title mb-0">Subscriptions</h5>
            <button class="btn btn-success btn-sm" type="button" @click="openSubscriptionModal()">Add subscription</button>
          </div>

          <div v-if="subscriptionsError" class="alert alert-danger mt-3">{{ subscriptionsError }}</div>
          <div v-else-if="subscriptionsLoading" class="text-center py-3">
            <div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>
          </div>
          <div v-else-if="subscriptions.length === 0" class="alert alert-secondary mt-3 mb-0">
            No subscriptions yet.
          </div>
          <div v-else class="list-group mt-3">
            <div v-for="sub in subscriptions" :key="sub.id" class="list-group-item">
              <div class="d-flex justify-content-between align-items-start">
                <div>
                  <div class="fw-semibold">{{ sub.name }}</div>
                  <small class="text-muted">
                    {{ sub.cadence }} • next due {{ sub.next_due_date }} • {{ sub.status }}
                  </small>
                  <ul class="small text-muted mb-0 mt-2">
                    <li v-for="m in sub.members" :key="m.username + sub.id">
                      {{ m.username }} pays {{ Number(m.amount).toFixed(2) }}
                    </li>
                  </ul>
                </div>
                <div class="text-end">
                  <div class="fw-bold">{{ sub.amount_display || Number(sub.amount).toFixed(2) }}</div>
                  <div class="btn-group btn-group-sm mt-2">
                    <button class="btn btn-outline-primary" type="button" @click="handlePaySubscription(sub)">Pay now</button>
                    <button class="btn btn-outline-secondary" type="button" @click="openSubscriptionModal(sub)">Edit</button>
                    <button class="btn btn-outline-danger" type="button" @click="handleDeleteSubscription(sub)">Delete</button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>  
      
      <div class="row g-4">
        <div class="col-lg-6">
          <div class="card h-100">
            <div class="card-body">
              <h5 class="card-title">Invite a member</h5>

              <form class="row g-3" @submit.prevent="sendInvite">
                <div class="col-12 col-md-8">
                  <input
                    v-model.trim="inviteForm.username"
                    type="text"
                    class="form-control"
                    placeholder="Enter username"
                    required
                  />
                </div>
                <div class="col-12 col-md-4 d-grid d-md-block">
                  <button class="btn btn-primary" type="submit" :disabled="inviteLoading">
                    <span v-if="inviteLoading" class="spinner-border spinner-border-sm me-2"></span>
                    Send invite
                  </button>
                </div>
              </form>

              <p v-if="inviteSuccess" class="text-success mt-3 mb-0">{{ inviteSuccess }}</p>
              <p v-if="inviteErrorMessage" class="text-danger mt-3 mb-0">{{ inviteErrorMessage }}</p>
            </div>
          </div>
        </div>
      </div>

      <div class="card mt-4">
        <div class="card-body">
          <div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
            <h5 class="card-title mb-0">Categories</h5>
          </div>
          <div v-if="categoriesError" class="alert alert-danger">{{ categoryError }}</div>
          <div v-else-if="loadingCategories" class="text-center py-3">
            <div class="spinner-border text-primary" role="status">
              <span class="visually-hidden">Loading...</span>
            </div>
          </div>
          <div v-else-if="categories.length === 0" class="alert alert-secondary mb-0">
            No categories recorded yet.
          </div>
          <div v-else class="list-group">
            <div v-for="category in categories" :key="category.id" class="list-group-item">
              <div class="d-flex justify-content-between align-items-start">
                <div class="d-flex align-items-center">
                  <div class="fw-semibold">{{ category.name }}</div>
                </div>
                <div class="d-flex flex-column align-items-end gap-1">
                  <RouterLink
                    v-if="route.params.id"
                    class="btn btn-outline-secondary btn-sm"
                    :to="{ name: 'CategoryStats', params: { id: route.params.id, categoryId: category.id } }"
                  >View insights</RouterLink>
                  <div class="btn-group btn-group-sm">
                    <button v-if="isOwner" class="btn btn-outline-secondary" type="button" @click="handleEditCategory(category)">
                      Edit
                    </button>
                    <button class="btn btn-outline-danger" type="button" @click="handleDeleteExpense(expense)">
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="card mt-4">
        <div class="card-body">
          <div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
            <h5 class="card-title mb-0">Expenses</h5>
            <div class="d-flex gap-2">
              <button
                class="btn btn-outline-secondary btn-sm"
                type="button"
                :disabled="expenses.length === 0"
                @click="exportExpensesCsv"
              >
                Export CSV
              </button>
              <RouterLink
                v-if="route.params.id"
                class="btn btn-outline-secondary btn-sm"
                :to="{ name: 'GroupStats', params: { id: route.params.id } }"
              >
                View insights
              </RouterLink>
            </div>
          </div>
          <div v-if="expensesError" class="alert alert-danger">{{ expensesError }}</div>
          <div v-else-if="loadingExpenses" class="text-center py-3">
            <div class="spinner-border text-primary" role="status">
              <span class="visually-hidden">Loading...</span>
            </div>
          </div>
          <div v-else-if="expenses.length === 0" class="alert alert-secondary mb-0">
            No expenses recorded yet.
          </div>
          <div v-else class="list-group">
            <div v-for="expense in expenses" :key="expense.id" class="list-group-item">
              <div class="d-flex justify-content-between align-items-start">
                <div>
                  <div class="fw-semibold">{{ expense.description }}</div>
                  <small class="text-muted">
                    Paid by {{ expense.paid_by }} · {{ new Date(expense.created_at).toLocaleString() }}
                  </small>
                </div>
                <div class="text-end">
                <span class="fw-bold d-block">{{ currencySymbol }}{{ Number(expense.amount).toFixed(2) }}</span>
                  <div class="btn-group btn-group-sm mt-2">
                    <button class="btn btn-outline-secondary" type="button" @click="handleEditExpense(expense)">
                      Edit
                    </button>
                    <button class="btn btn-outline-danger" type="button" @click="handleDeleteExpense(expense)">
                      Delete
                    </button>
                  </div>
                </div>
              </div>
              <ul class="small text-muted mb-0 mt-2">
                <li v-for="split in expense.splits" :key="split.username + expense.id">
                  {{ split.username }} owes {{ currencySymbol }}{{ Number(split.amount).toFixed(2) }}
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>


      <div class="card mt-4">
        <div class="card-body">
          <h5 class="card-title">Settlements</h5>
          <div v-if="settlementsError" class="alert alert-danger">{{ settlementsError }}</div>
          <div v-else-if="loadingSettlements" class="text-center py-3">
            <div class="spinner-border text-primary" role="status">
              <span class="visually-hidden">Loading...</span>
            </div>
          </div>
          <div v-else-if="settlements.length === 0" class="alert alert-success mb-0">
            Everyone is settled up!
          </div>
          <div v-else class="list-group">
            <div v-for="transfer in settlements" :key="transfer.payer + transfer.receiver + transfer.amount" class="list-group-item">
              <div class="d-flex justify-content-between align-items-center">
                <div>
                  <div>
                    <strong>{{ transfer.payer }}</strong> pays
                    <strong>{{ transfer.receiver }}</strong>
                  </div>
                </div>
                <div class="text-end">
                  <span class="fw-bold d-block">{{ currencySymbol }}{{ Number(transfer.amount).toFixed(2) }}</span>
                  <button
                    v-if="currentUsername === transfer.payer"
                    class="btn btn-outline-primary btn-sm mt-2"
                    type="button"
                    :disabled="recordingSettlementKey === recommendationKey(transfer)"
                    @click="handleRecordSettlement(transfer)"
                  >
                    <span
                      v-if="recordingSettlementKey === recommendationKey(transfer)"
                      class="spinner-border spinner-border-sm me-2"
                    ></span>
                    Mark as paid
                  </button>
                </div>
              </div>
            </div>
          </div>
          <div v-if="settlementActionError" class="alert alert-danger mt-3 mb-0">
            {{ settlementActionError }}
          </div>
        </div>
      </div>

      <div class="card mt-4">
        <div class="card-body">
          <h5 class="card-title">Recorded settlements</h5>
          <div v-if="settlementRecords.length === 0" class="alert alert-secondary mb-0">
            No settlement records yet.
          </div>
          <div v-else class="list-group">
            <div v-for="record in settlementRecords" :key="record.id" class="list-group-item">
              <div class="d-flex justify-content-between align-items-center">
                <div>
                  <div>
                    <strong>{{ record.payer }}</strong> paid
                    <strong>{{ record.receiver }}</strong>
                  </div>
                  <small class="text-muted">
                    Status:
                    <span v-if="record.status === 'complete'">Confirmed</span>
                    <span v-else>Waiting for receiver</span>
                  </small>
                </div>
                <div class="text-end">
                  <span class="fw-bold d-block">{{ currencySymbol }}{{ Number(record.amount).toFixed(2) }}</span>
                  <button
                    v-if="currentUsername === record.receiver && record.status !== 'complete'"
                    class="btn btn-success btn-sm mt-2"
                    type="button"
                    :disabled="confirmingSettlementId === record.id"
                    @click="handleConfirmSettlement(record)"
                  >
                    <span
                      v-if="confirmingSettlementId === record.id"
                      class="spinner-border spinner-border-sm me-2"
                    ></span>
                    Confirm received
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div v-if="showExpenseModal">
      <div class="modal-backdrop fade show"></div>
      <div class="modal d-block" tabindex="-1">
        <div class="modal-dialog modal-lg modal-dialog-centered">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">{{ isEditingExpense ? "Edit expense" : "Add expense" }}</h5>
              <button type="button" class="btn-close" @click="closeExpenseModal"></button>
            </div>
            <div class="modal-body">
              <form class="row g-3" @submit.prevent="saveExpense">
                <div class="col-12">
                  <label class="form-label" for="modalExpenseDescription">Description</label>
                  <input
                    id="modalExpenseDescription"
                    v-model.trim="expenseForm.description"
                    class="form-control"
                    required
                  />
                </div>

                <div class="col-6">
                  <label class="form-label" for="modalExpenseAmount">Amount</label>
                  <input
                    id="modalExpenseAmount"
                    v-model.number="expenseForm.amount"
                    type="number"
                    min="0"
                    step="0.01"
                    class="form-control"
                    required
                  />
                </div>

                <div class="col-6">
                  <label class="form-label" for="modalExpensePaidBy">Paid by</label>
                  <select id="modalExpensePaidBy" v-model="expenseForm.paidBy" class="form-select" required>
                    <option v-for="member in group.members" :key="member.id" :value="member.username">
                      {{ displayMemberName(member.username) }}
                    </option>
                  </select>
                </div>

                <div class="col-6">
                  <label class="form-label" for="modalExpenseCategory">Category</label>
                  <select id="modalExpenseCategory" v-model="expenseForm.category_id" class="form-select">
                    <option :value="null">Other</option>
                    <option v-for="category in categories":key="category.id":value="category.id">{{ category.name }}</option>
                  </select>
                  <small class="text-muted">Optional - if selected, splits follow category rules</small>
                </div>

                <div class="col-12">
                  <label class="form-label">Split type</label>
                  <div class="btn-group w-100">
                    <button
                      type="button"
                      class="btn"
                      :class="expenseForm.splitMode === 'equal' ? 'btn-primary' : 'btn-outline-primary'"
                      @click="expenseForm.splitMode = 'equal'"
                    >
                      Equal
                    </button>
                    <button
                      type="button"
                      class="btn"
                      :class="expenseForm.splitMode === 'custom' ? 'btn-primary' : 'btn-outline-primary'"
                      @click="expenseForm.splitMode = 'custom'"
                    >
                      Custom
                    </button>
                  </div>
                </div>

                <div class="col-12" v-if="expenseForm.splitMode === 'equal'">
                  <label class="form-label d-flex justify-content-between align-items-center">
                    <span>Split between</span>
                    <button class="btn btn-link btn-sm p-0" type="button" @click="selectAllEqualMembers">
                      Select all
                    </button>
                  </label>
                  <div class="d-flex flex-wrap gap-3">
                    <label v-for="member in group.members" :key="member.id" class="form-check m-0">
                      <input
                        class="form-check-input me-1"
                        type="checkbox"
                        :checked="isEqualSelected(member.username)"
                        @change="toggleEqualMember(member.username)"
                      />
                      <span class="form-check-label">{{ displayMemberName(member.username) }}</span>
                    </label>
                  </div>
                  <p class="small text-muted mt-2 mb-0">
                    Selected members split the amount equally. Others won’t owe anything.
                  </p>
                </div>

                <div class="col-12" v-if="expenseForm.splitMode === 'custom'">
                  <div class="table-responsive">
                    <table class="table table-sm align-middle">
                      <thead>
                        <tr>
                          <th>Member</th>
                          <th class="text-end">Amount</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="split in customSplits" :key="split.username">
                          <td>{{ displayMemberName(split.username) }}</td>
                          <td>
                            <input
                              type="number"
                              class="form-control text-end"
                              min="0"
                              step="0.01"
                              v-model.number="split.amount"
                            />
                          </td>
                        </tr>
                      </tbody>
                      <tfoot>
                        <tr>
                          <th>Total</th>
                          <th class="text-end">{{ customTotalDisplay }}</th>
                        </tr>
                      </tfoot>
                    </table>
                  </div>
                  <p
                    class="small"
                    :class="customTotalMatches ? 'text-success' : 'text-danger'"
                  >
                    Splits {{ customTotalMatches ? 'match' : 'must equal' }} total amount
                  </p>
                </div>

                <div class="col-12">
                  <div v-if="expenseError" class="alert alert-danger py-2">{{ expenseError }}</div>
                  <button class="btn btn-success w-100" :disabled="savingExpense">
                    <span v-if="savingExpense" class="spinner-border spinner-border-sm me-2"></span>
                    {{ isEditingExpense ? "Save changes" : "Add expense" }}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div v-if="showCategoryModal">
      <div class="modal-backdrop fade show"></div>
      <div class="modal d-block" tabindex="-1">
        <div class="modal-dialog modal-lg modal-dialog-centered">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">{{ isEditingCategory ? "Edit Category" : "Add Category" }}</h5>
              <button type="button" class="btn-close" @click="closeCategoryModal"></button>
            </div>
            <div class="modal-body">
              <form class="row g-3" @submit.prevent="saveCategory">
                <div class="col-12">
                  <label class="form-label">Name</label>
                  <input v-model.trim="categoryForm.name" class="form-control" required />
                </div>
                <div class="col-12">
                  <label class="form-label">Description</label>
                  <textarea v-model.trim="categoryForm.description" class="form-control"></textarea>
                </div>
                <div class="col-6">
                  <label class="form-label">Budget</label>
                  <input v-model.number="categoryForm.budget" type="number" min="0" step="0.01" class="form-control"/>
                </div>
                <div class="col-12">
                  <label class="form-label">Split Shares</label>
                  <table class="table table-sm">
                    <thead>
                      <tr>
                        <th>Member</th>
                        <th class="text-end">Share</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="split in categoryForm.splits" :key="split.username">
                        <td>{{ displayMemberName(split.username) }}</td>
                        <td>
                          <input type="number" min="1" step="1" class="form-control text-end" v-model.number="split.share"/>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                  <small class="text-muted">
                    Shares are in ratios (e.g. 2 = pays twice as much as 1).
                  </small>
                </div>
                <div class="col-12">
                  <div v-if="categoryError" class="alert alert-danger py-2">
                    {{ categoryError }}
                  </div>
                  <button class="btn btn-success w-100" :disabled="creatingCategory">
                    <span v-if="creatingCategory" class="spinner-border spinner-border-sm me-2"></span>
                    {{ isEditingCategory ? "Save Changes" : "Create Category"}}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div v-if="showSubscriptionModal">
    <div class="modal-backdrop fade show"></div>
    <div class="modal d-block" tabindex="-1">
      <div class="modal-dialog modal-lg modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
           <h5 class="modal-title">{{ editingSubscriptionId ? "Edit subscription" : "Add subscription" }}</h5>
           <button type="button" class="btn-close" @click="closeSubscriptionModal"></button>
          </div>
          <div class="modal-body">
           <form class="row g-3" @submit.prevent="saveSubscription">
            <div class="col-12">
              <label class="form-label">Name</label>
              <input v-model.trim="subscriptionForm.name" class="form-control" required />
            </div>
            <div class="col-6">
              <label class="form-label">Amount</label>
              <input v-model.number="subscriptionForm.amount" type="number" min="0" step="0.01" class="form-control" required />
            </div>
            <div class="col-6">
              <label class="form-label">Cadence</label>
              <select v-model="subscriptionForm.cadence" class="form-select">
                <option value="monthly">Monthly</option>
                <option value="quarterly">Quarterly</option>
                <option value="yearly">Yearly</option>
              </select>
            </div>
            <div class="col-6">
              <label class="form-label">Next due date</label>
              <input v-model="subscriptionForm.next_due_date" type="date" class="form-control" required />
            </div>
            <div class="col-12">
              <label class="form-label">Notes</label>
              <textarea v-model="subscriptionForm.notes" class="form-control" rows="2"></textarea>
            </div>
            <div class="col-12">
              <label class="form-label">Member shares (ratios)</label>
              <table class="table table-sm mb-0">
                <tbody>
                  <tr v-for="m in subscriptionForm.members" :key="m.username">
                    <td>{{ displayMemberName(m.username) }}</td>
                    <td style="width: 140px;">
                      <input v-model.number="m.share" type="number" min="1" step="1" class="form-control text-end" />
                    </td>
                  </tr>
                </tbody>
              </table>
              <small class="text-muted">Shares are relative weights (e.g., 2 pays twice as much as 1).</small>
            </div>
            <div class="col-12">
              <div v-if="subscriptionError" class="alert alert-danger py-2">{{ subscriptionError }}</div>
              <button class="btn btn-success w-100">
                <span v-if="subscriptionsLoading" class="spinner-border spinner-border-sm me-2"></span>
                {{ editingSubscriptionId ? "Save changes" : "Create subscription" }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</div>
</template>

<script setup>
import { computed, onMounted, watch, reactive, ref, nextTick } from "vue"
import { useRoute, useRouter, RouterLink } from "vue-router"
import { useGroups } from "../composables/useGroups"
import { useExpenses } from "../composables/useExpenses"
import { useAuth } from "../composables/useAuth"
import { useCategories } from "../composables/useCategories"
import { useSubscriptions } from "../composables/useSubscriptions"


const route = useRoute()
const router = useRouter()
const groupId = computed(() => route.params.id)
const{
  categories,
  loadingCategories,
  categoriesError,
  fetchCategories,
  createCategory,
  updateCategory
} = useCategories(groupId)
const {
  loading: subscriptionsLoading,
  error: subscriptionsError,
  list: listSubscriptions,
  create: createSubscription,
  update: updateSubscription,
  remove: removeSubscription,
  pay: paySubscription
} = useSubscriptions()
const {
  activeGroup: group,
  loadingGroup,
  groupError,
  fetchGroup,
  fetchGroups,
  updateGroup,
  deleteGroup,
  connectToGroupUpdates
} = useGroups()
const { currentUser } = useAuth()
const inviteForm = reactive({ username: "" })
const inviteLoading = ref(false)
const inviteSuccess = ref("")
const inviteErrorMessage = ref("")
const {
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
} = useExpenses()
const expenseForm = reactive({
  description: "",
  amount: 0,
  paidBy: "",
  splitMode: "equal",
  category_id:null
})
const categoryForm=reactive({
  name:"",
  description:"",
  budget:0,
  splits:[]
})

const showCategoryModal = ref(false)
const creatingCategory = ref(false)
const categoryError = ref("")
const customSplits = reactive([])
const expenseError = ref("")
const showExpenseModal = ref(false)
const editingExpenseId = ref(null)
const editingCategoryID = ref(null)
const isEditingCategory = computed(() => editingCategoryID.value !== null)
const equalSelectedMembers = ref([])
const settlementActionError = ref("")
const recordingSettlementKey = ref("")
const confirmingSettlementId = ref(null)
const leavingGroup = ref(false)
const leaveError = ref("")
const deletingGroup = ref(false)
const deleteGroupError = ref("")
const showGroupSettings = ref(false)
const savingGroupSettings = ref(false)
const groupSettingsError = ref("")
const groupSettingsForm = reactive({
  name: "",
  currency: "GBP"
})
const subscriptions = ref([])
const showSubscriptionModal = ref(false)
const subscriptionError = ref("")
const editingSubscriptionId = ref(null)
const subscriptionForm = reactive({
  name: "",
  amount: 0,
  cadence: "monthly",
  next_due_date: "",
  notes: "",
  members: []
})

const currencySymbols = {
  GBP: "£",
  USD: "$",
  EUR: "€",
  CAD: "$",
  AUD: "$",
  JPY: "¥"
}
const currencyOptions = ["GBP", "USD", "EUR", "CAD", "AUD", "JPY"]
const currencyCode = computed(() => group.value?.currency || "GBP")
const currencySymbol = computed(() => currencySymbols[currencyCode.value] || currencyCode.value + " ")
const currentUsername = computed(() => currentUser.value?.username || "")
const isOwner = computed(
  () => Boolean(group.value && currentUser.value && group.value.owner_id === currentUser.value.id)
)

function displayMemberName(username) {
  if (!username) {
    return "Unknown"
  }
  return username === currentUsername.value ? `${username} (you)` : username
}

function resetGroupSettingsForm() {
  if (group.value) {
    groupSettingsForm.name = group.value.name
    groupSettingsForm.currency = group.value.currency
  } else {
    groupSettingsForm.name = ""
    groupSettingsForm.currency = "GBP"
  }
}
async function openCategoryModal(category = null){
  categoryError.value = ""
  if (category){
    editingCategoryID.value = category.id
    categoryForm.name = category.name
    categoryForm.description = category.description || ""
    categoryForm.budget = category.budget || 0
    categoryForm.splits = group.value.members.map(member => {
      const existing = category.splits?.find(
        split => split.username === member.username
      )
      return {
        username: member.username,
        share: existing?.share ?? 1
      }
    })
  }
  else{
    editingCategoryID.value = null
    categoryForm.name=""
    categoryForm.description=""
    categoryForm.budget=0

    categoryForm.splits = group.value.members.map(member => ({
      username:member.username,
      share:1
    }))
  }
  
  showCategoryModal.value = true
}

function closeCategoryModal(){
  showCategoryModal.value = false
  categoryError.value = ""
  categoryForm.name = ""
  categoryForm.description=""
  categoryForm.budget = 0
}

async function saveCategory(){
  if (!route.params.id) return
  categoryError.value = ""

  if (!categoryForm.name.trim()){
    categoryError.value ="Category name is required"
    return
  }
  const payload = {
    name: categoryForm.name.trim(),
    description: categoryForm.description || null,
    budget: categoryForm.budget ? Math.round(Number(categoryForm.budget)*100):null,
    splits: categoryForm.splits.map(split => ({
      username: split.username,
      share : split.share
    }))
  }

  creatingCategory.value = true
  try{
    if (isEditingCategory.value){
      await updateCategory(editingCategoryID.value,payload)
    }
    else{
      await createCategory(payload)
    }
    closeCategoryModal()
    await fetchCategories()
  }
  catch (err){
    categoryError.value = err.message || "Failed to create category"
  } finally{
    editingCategoryID.value = null
    creatingCategory.value = false
  }
}

function toggleGroupSettings() {
  groupSettingsError.value = ""
  if (!showGroupSettings.value) {
    resetGroupSettingsForm()
    showGroupSettings.value = true
  } else {
    showGroupSettings.value = false
    resetGroupSettingsForm()
  }
}

async function saveGroupSettings() {
  if (!route.params.id) return
  groupSettingsError.value = ""
  if (!groupSettingsForm.name.trim()) {
    groupSettingsError.value = "Group name is required"
    return
  }
  savingGroupSettings.value = true
  try {
    await updateGroup(route.params.id, {
      name: groupSettingsForm.name.trim(),
      currency: groupSettingsForm.currency
    })
    showGroupSettings.value = false
  } catch (err) {
    groupSettingsError.value = err.message || "Failed to update group"
  } finally {
    savingGroupSettings.value = false
  }
}

function exportExpensesCsv() {
  const header = ["Description", "Amount", "Paid By", "Created At", "Splits"]
  const rows = expenses.value.map((expense) => {
    const splits = (expense.splits || [])
      .map((split) => `${split.username}: ${Number(split.amount).toFixed(2)}`)
      .join("; ")
    return [
      expense.description || "",
      Number(expense.amount || 0).toFixed(2),
      expense.paid_by || "",
      expense.created_at ? new Date(expense.created_at).toLocaleString() : "",
      splits
    ]
  })
  const csvLines = [header, ...rows]
    .map((row) =>
      row
        .map((value) => {
          const str = String(value ?? "")
          return `"${str.replace(/"/g, '""')}"`
        })
        .join(",")
    )
    .join("\n")

  const blob = new Blob([csvLines], { type: "text/csv;charset=utf-8;" })
  const url = URL.createObjectURL(blob)
  const link = document.createElement("a")
  link.href = url
  link.setAttribute("download", `${group.value?.name || "group"}-expenses.csv`)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

function setDefaultPaidBy(members) {
  const memberList = members || group.value?.members || []
  if (!memberList.length) {
    expenseForm.paidBy = ""
    return
  }
  const ownEntry = memberList.find((member) => member.username === currentUsername.value)
  expenseForm.paidBy = ownEntry ? ownEntry.username : memberList[0].username
}

function loadGroup() {
  if (route.params.id) {
    fetchGroup(route.params.id)
    fetchExpenses(route.params.id)
    fetchSettlements(route.params.id)
    loadSubscriptions()
  }
}

async function sendInvite() {
  if (!route.params.id) return
  inviteLoading.value = true
  inviteSuccess.value = ""
  inviteErrorMessage.value = ""

  try {
    const res = await fetch(`/api/groups/${route.params.id}/invite`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ username: inviteForm.username })
    })

    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      throw new Error(body.detail || "Failed to send invite")
    }

    inviteSuccess.value = `Invitation sent to ${inviteForm.username}.`
    inviteForm.username = ""
  } catch (err) {
    inviteErrorMessage.value = err.message || "Failed to send invite"
  } finally {
    inviteLoading.value = false
  }
}

async function handleLeaveGroup() {
  if (!route.params.id) return
  const confirmed = window.confirm("Are you sure you want to leave this group? This cannot be undone.")
  if (!confirmed) {
    return
  }
  leaveError.value = ""
  leavingGroup.value = true
  try {
    const res = await fetch(`/api/groups/${route.params.id}/leave`, {
      method: "POST",
      credentials: "include"
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      throw new Error(body.detail || "Unable to leave group")
    }
    group.value = null
    await fetchGroups()
    router.push("/groups")
  } catch (err) {
    leaveError.value = err.message || "Failed to leave group"
  } finally {
    leavingGroup.value = false
  }
}

async function handleDeleteGroup() {
  if (!route.params.id) return
  const confirmed = window.confirm(
    "Delete this group? This removes all expense history once everyone is settled."
  )
  if (!confirmed) {
    return
  }
  deleteGroupError.value = ""
  deletingGroup.value = true
  try {
    await deleteGroup(route.params.id)
    await fetchGroups()
    router.push("/groups")
  } catch (err) {
    deleteGroupError.value = err.message || "Failed to delete group"
  } finally {
    deletingGroup.value = false
  }
}

const expenses = computed(() => expensesByGroup.value[route.params.id] || [])
const settlementsSummary = computed(() => settlementsByGroup.value[route.params.id] || { recommendations: [], records: [] })
const settlements = computed(() => settlementsSummary.value.recommendations || [])
const settlementRecords = computed(() => settlementsSummary.value.records || [])
const isEditingExpense = computed(() => Boolean(editingExpenseId.value))

function resetSplitsEqual() {
  if (!group.value || group.value.members.length === 0) return
  const selected = equalSelectedMembers.value.length
    ? equalSelectedMembers.value
    : group.value.members.map((member) => member.username)
  const count = selected.length
  if (count === 0) return
  const totalCents = Math.round(Number(expenseForm.amount || 0) * 100)
  const base = Math.floor(totalCents / count)
  let remainder = totalCents - base * count
  customSplits.forEach((split) => {
    if (selected.includes(split.username)) {
      let cents = base
      if (remainder > 0) {
        cents += 1
        remainder -= 1
      }
      split.amount = Number((cents / 100).toFixed(2))
    } else {
      split.amount = 0
    }
  })
}

watch(
  () => group.value,
  (val) => {
    deleteGroupError.value = ""
    resetGroupSettingsForm()
    if (val && val.members.length > 0) {
      setDefaultPaidBy(val.members)
      customSplits.splice(0, customSplits.length)
      val.members.forEach((member) => {
        customSplits.push({ username: member.username, amount: 0 })
      })
      equalSelectedMembers.value = val.members.map((member) => member.username)
      if (expenseForm.splitMode === "equal") {
        resetSplitsEqual()
      }
    }
  },
  { immediate: true }
)

watch(
  () => group.value,
  (val) => {
    if (!val) return
    categoryForm.splits = val.members.map((member) => ({
      username: member.username,
      share:1
    }))
  },{immediate: true}
)

watch(
  () => expenseForm.amount,
  () => {
    if (expenseForm.splitMode === "equal") {
      resetSplitsEqual()
    }
  }
)

watch(
  () => expenseForm.splitMode,
  (mode) => {
    if (mode === "equal") {
      resetSplitsEqual()
    }
  }
)

watch(
  () => equalSelectedMembers.value,
  () => {
    if (expenseForm.splitMode === "equal") {
      resetSplitsEqual()
    }
  },
  { deep: true }
)
watch(
  () => route.params.id,
  (id) => {
    if (id) {
      fetchCategories()
    }
  }, {immediate: true}
)

watch(
  () => currentUsername.value,
  () => {
    if (!isEditingExpense.value && group.value?.members?.length) {
      setDefaultPaidBy(group.value.members)
    }
  }
)

const customTotalCents = computed(() =>
  customSplits.reduce((total, split) => total + Math.round(Number(split.amount || 0) * 100), 0)
)
const customTotalMatches = computed(
  () => customTotalCents.value === Math.round(Number(expenseForm.amount || 0) * 100)
)
const customTotalDisplay = computed(() => (customTotalCents.value / 100).toFixed(2))

async function saveExpense() {
  expenseError.value = ""
  if (!expenseForm.description || !expenseForm.amount || expenseForm.amount <= 0) {
    expenseError.value = "Description and positive amount required"
    return
  }

  let splitsPayload = []
  if (expenseForm.splitMode === "equal") {
    const selected =
      equalSelectedMembers.value.length > 0
        ? equalSelectedMembers.value
        : group.value?.members.map((member) => member.username) || []
    if (!selected.length) {
      expenseError.value = "Select at least one member to split between"
      return
    }
    const selectedSet = new Set(selected)
    splitsPayload = customSplits
      .filter((split) => selectedSet.has(split.username))
      .map((split) => ({
        username: split.username,
        amount: Number(split.amount || 0)
      }))
  } else {
    if (!customTotalMatches.value) {
      expenseError.value = "Custom splits must equal total amount"
      return
    }
    splitsPayload = customSplits.map((split) => ({
      username: split.username,
      amount: Number(split.amount || 0)
    }))
  }

  try {
    const payload = {
      description: expenseForm.description,
      amount: Number(expenseForm.amount),
      paid_by: expenseForm.paidBy,
      splits: splitsPayload,
      category_id: expenseForm.category_id
    }

    if (isEditingExpense.value) {
      await updateExpense(route.params.id, editingExpenseId.value, payload)
    } else {
      await createExpense(route.params.id, payload)
    }
    expenseForm.description = ""
    expenseForm.amount = 0
    expenseError.value = ""
    if (expenseForm.splitMode === "equal") {
      resetSplitsEqual()
    }
    closeExpenseModal()
    await fetchExpenses(route.params.id)
    await fetchSettlements(route.params.id)
  } catch (err) {
    expenseError.value = err.message || "Failed to save expense"
  }
}

function closeExpenseModal() {
  showExpenseModal.value = false
  editingExpenseId.value = null
  if (group.value) {
    equalSelectedMembers.value = group.value.members.map((member) => member.username)
  } else {
    equalSelectedMembers.value = []
  }
}


async function openExpenseModal(expense = null) {
  expenseError.value = ""
  if (!group.value) return
  if (expense) {
    editingExpenseId.value = expense.id
    expenseForm.description = expense.description
    expenseForm.amount = Number(expense.amount)
    expenseForm.paidBy = expense.paid_by
    expenseForm.splitMode = "custom"
    expenseForm.category_id= expense.category_id ?? null
    await nextTick()
    customSplits.forEach((split) => {
      const match = expense.splits.find((s) => s.username === split.username)
      split.amount = match ? Number(match.amount) : 0
    })
  } else {
    editingExpenseId.value = null
    expenseForm.description = ""
    expenseForm.amount = 0
    setDefaultPaidBy(group.value.members)
    expenseForm.category_id = null
    expenseForm.splitMode = "equal"
    equalSelectedMembers.value = group.value.members.map((member) => member.username)
    await nextTick()
    resetSplitsEqual()
  }
  showExpenseModal.value = true
}

function handleEditExpense(expense) {
  openExpenseModal(expense)
}

function handleEditCategory(category){
  openCategoryModal(category)
}

async function handleDeleteExpense(expense) {
  if (!route.params.id) return
  const confirmed = window.confirm("Delete this expense?")
  if (!confirmed) return
  try {
    await deleteExpense(route.params.id, expense.id)
    expenseError.value = ""
    await fetchSettlements(route.params.id)
  } catch (err) {
    expenseError.value = err.message || "Failed to delete expense"
  }
}

function isEqualSelected(username) {
  return equalSelectedMembers.value.includes(username)
}

function toggleEqualMember(username) {
  const set = new Set(equalSelectedMembers.value)
  if (set.has(username)) {
    set.delete(username)
  } else {
    set.add(username)
  }
  equalSelectedMembers.value = Array.from(set)
}

function selectAllEqualMembers() {
  if (!group.value) return
  equalSelectedMembers.value = group.value.members.map((member) => member.username)
  resetSplitsEqual()
}

function recommendationKey(transfer) {
  return `${transfer.payer}-${transfer.receiver}-${transfer.amount}`
}

async function handleRecordSettlement(transfer) {
  if (!route.params.id || !currentUser.value?.username) return
  settlementActionError.value = ""
  const key = recommendationKey(transfer)
  recordingSettlementKey.value = key
  try {
    await recordSettlement(route.params.id, {
      receiver: transfer.receiver,
      amount: Number(transfer.amount)
    })
    await fetchSettlements(route.params.id)
  } catch (err) {
    settlementActionError.value = err.message || "Failed to record settlement"
  } finally {
    recordingSettlementKey.value = ""
  }
}

async function handleConfirmSettlement(record) {
  if (!route.params.id) return
  settlementActionError.value = ""
  confirmingSettlementId.value = record.id
  try {
    await confirmSettlement(route.params.id, record.id)
    await fetchSettlements(route.params.id)
  } catch (err) {
    settlementActionError.value = err.message || "Failed to confirm settlement"
  } finally {
    confirmingSettlementId.value = null
  }
}

function resetSubscriptionForm() {
  subscriptionError.value = ""
  editingSubscriptionId.value = null
  subscriptionForm.name = ""
  subscriptionForm.amount = 0
  subscriptionForm.cadence = "monthly"
  subscriptionForm.next_due_date = ""
  subscriptionForm.notes = ""
  subscriptionForm.members = group.value
    ? group.value.members.map((m) => ({ username: m.username, share: 1 }))
    : []
}

function openSubscriptionModal(sub = null) {
  subscriptionError.value = ""
  if (sub) {
    editingSubscriptionId.value = sub.id
    subscriptionForm.name = sub.name
    subscriptionForm.amount = Number(sub.amount)
    subscriptionForm.cadence = sub.cadence
    subscriptionForm.next_due_date = sub.next_due_date
    subscriptionForm.notes = sub.notes || ""
    // reuse member order from group; fall back to share=1
    subscriptionForm.members = group.value
      ? group.value.members.map((m) => {
          const match = (sub.members || []).find((x) => x.username === m.username)
          return { username: m.username, share: match ? match.share : 1 }
        })
      : []
  } else {
    resetSubscriptionForm()
  }
  showSubscriptionModal.value = true
}

function closeSubscriptionModal() {
  showSubscriptionModal.value = false
  resetSubscriptionForm()
}

async function loadSubscriptions() {
  if (!route.params.id) return
  try {
    subscriptions.value = await listSubscriptions(route.params.id)
  } catch (err) {
    // subscriptionsError is already set by composable
    console.error(err)
  }
}

async function saveSubscription() {
  if (!route.params.id) return
  subscriptionError.value = ""
  if (!subscriptionForm.name.trim() || !subscriptionForm.amount || subscriptionForm.amount <= 0 || !subscriptionForm.next_due_date) {
    subscriptionError.value = "Name, positive amount, and due date are required"
    return
  }
  const payload = {
    name: subscriptionForm.name.trim(),
    amount: Number(subscriptionForm.amount),
    cadence: subscriptionForm.cadence,
    next_due_date: subscriptionForm.next_due_date,
    notes: subscriptionForm.notes || "",
    category_id: null,
    members: subscriptionForm.members.map((m) => ({ username: m.username, share: Number(m.share) || 1 }))
  }
  try {
    if (editingSubscriptionId.value) {
      await updateSubscription(route.params.id, editingSubscriptionId.value, payload)
    } else {
      await createSubscription(route.params.id, payload)
    }
    await loadSubscriptions()
    closeSubscriptionModal()
  } catch (err) {
    subscriptionError.value = err.message || "Failed to save subscription"
  }
}

async function handleDeleteSubscription(sub) {
  if (!route.params.id) return
  if (!window.confirm("Delete this subscription?")) return
  try {
    await removeSubscription(route.params.id, sub.id)
    await loadSubscriptions()
  } catch (err) {
    subscriptionError.value = err.message || "Failed to delete subscription"
  }
}

async function handlePaySubscription(sub) {
  if (!route.params.id) return
  try {
    await paySubscription(route.params.id, sub.id)
    await Promise.all([loadSubscriptions(), fetchExpenses(route.params.id), fetchSettlements(route.params.id)])
  } catch (err) {
    subscriptionError.value = err.message || "Failed to record payment"
  }
}

onMounted(() => {
  connectToGroupUpdates()
  connectToExpenseNotifications()
  loadGroup()
})
watch(
  () => route.params.id,
  () => loadGroup()
)
</script>
