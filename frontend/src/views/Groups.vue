<template>
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <div>
        <h2 class="mb-0">Your Groups</h2>
        <p class="text-muted mb-0">Track shared expenses with friends and family.</p>
      </div>
      <button class="btn btn-primary btn-sm" type="button">
        Create group
      </button>
    </div>

    <div class="row g-3">
      <div class="col-12 col-md-6 col-lg-4">
        <div class="card h-100">
          <div class="card-body d-flex flex-column">
            <h5 class="card-title">Sample Group</h5>
            <p class="card-text flex-grow-1">
              This is a placeholder for future group data. Soon you’ll see balances,
              recent expenses, and members here.
            </p>
            <button class="btn btn-outline-secondary btn-sm mt-3" type="button" disabled>
              View details
            </button>
          </div>
        </div>
      </div>

      <div class="col-12">
        <div class="alert alert-info mb-0">
          Real group data isn’t wired up yet.
        </div>
      </div>
    </div>
  </div>
</template>
