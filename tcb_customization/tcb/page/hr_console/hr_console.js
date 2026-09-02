frappe.pages["hr-console"] = frappe.pages["hr-console"] || {};

Object.assign(frappe.pages["hr-console"], {
	on_page_load(wrapper) {
		const page = frappe.ui.make_app_page({
			parent: wrapper,
			title: "HR Console",
			single_column: true,
		});

		const $main = $(page.main);

		// ==================================================
		// STATE
		// ==================================================

		let currentPage = 0;
		let currentStatus = "Active";
		let selectedDate = frappe.datetime.get_today();
		let fromDate = frappe.datetime.get_today();
		let toDate = frappe.datetime.get_today();
		let selectedEmployee = null;

		const pageSize = 50;

		// ==================================================
		// HTML
		// ==================================================

		$main.html(`
			<div class="hr-console">

				<style>

					/* ==================================================
					   MAIN
					================================================== */

					.hr-console {
						--hr-primary: #4f46e5;
						--hr-primary-light: #eef2ff;
						--hr-text: #172033;
						--hr-muted: #7b8497;
						--hr-border: #e8ebf2;
						--hr-bg: #f6f8fc;

						padding: 24px;
						min-height: calc(100vh - 80px);
						background:
							linear-gradient(
								180deg,
								#f8faff 0%,
								#f6f8fc 45%,
								#ffffff 100%
							);
						color: var(--hr-text);
					}

					.hr-console * {
						box-sizing: border-box;
					}

					/* ==================================================
					   HEADER
					================================================== */

					.hr-header {
						display: flex;
						justify-content: space-between;
						align-items: center;
						gap: 20px;
						margin-bottom: 24px;
						flex-wrap: wrap;
					}

					.hr-header-title {
						display: flex;
						align-items: center;
						gap: 14px;
					}

					.hr-header-icon {
						width: 48px;
						height: 48px;
						border-radius: 14px;
						display: flex;
						align-items: center;
						justify-content: center;
						background: linear-gradient(
							135deg,
							#4f46e5,
							#7c3aed
						);
						color: #fff;
						font-size: 21px;
						box-shadow:
							0 8px 22px rgba(79,70,229,.20);
					}

					.hr-title {
						font-size: 25px;
						font-weight: 700;
						line-height: 1.2;
						margin: 0;
						letter-spacing: -0.4px;
					}

					.hr-subtitle {
						color: var(--hr-muted);
						font-size: 13px;
						margin-top: 5px;
					}

					.hr-date-panel {
						display: flex;
						align-items: flex-end;
						gap: 10px;
						flex-wrap: wrap;
					}

					.hr-date-field {
						min-width: 155px;
					}

					.hr-date-field label {
						display: block;
						font-size: 11px;
						font-weight: 700;
						text-transform: uppercase;
						letter-spacing: .4px;
						color: #737b8c;
						margin-bottom: 6px;
					}

					.hr-date-field input {
						height: 40px !important;
						border-radius: 10px !important;
						border-color: #dfe4ee !important;
						background: #fff !important;
						box-shadow: 0 2px 7px rgba(20,30,55,.03) !important;
					}

					.hr-refresh-btn {
						height: 40px !important;
						border: 0 !important;
						border-radius: 10px !important;
						padding: 0 18px !important;
						font-weight: 600 !important;
						background: linear-gradient(
							135deg,
							#4f46e5,
							#6366f1
						) !important;
						box-shadow:
							0 7px 16px rgba(79,70,229,.20);
					}

					.hr-refresh-btn:hover {
						transform: translateY(-1px);
						box-shadow:
							0 10px 20px rgba(79,70,229,.25);
					}

					/* ==================================================
					   SUMMARY
					================================================== */

					.hr-summary-grid {
						display: grid;
						grid-template-columns:
							repeat(8, minmax(0, 1fr));
						gap: 13px;
						margin-bottom: 22px;
					}

					.hr-stat-card {
						position: relative;
						overflow: hidden;
						min-height: 112px;
						padding: 17px;
						border: 1px solid var(--hr-border);
						border-radius: 16px;
						background: rgba(255,255,255,.92);
						cursor: pointer;
						box-shadow:
							0 4px 15px rgba(27,39,70,.045);
						transition:
							transform .18s ease,
							box-shadow .18s ease,
							border-color .18s ease;
					}

					.hr-stat-card::after {
						content: "";
						position: absolute;
						right: -25px;
						bottom: -30px;
						width: 80px;
						height: 80px;
						border-radius: 50%;
						background: rgba(99,102,241,.055);
						pointer-events: none;
					}

					.hr-stat-card:hover {
						transform: translateY(-3px);
						border-color: #d8ddf0;
						box-shadow:
							0 12px 28px rgba(27,39,70,.09);
					}

					.hr-stat-card.active-card {
						border-color: #818cf8;
						background:
							linear-gradient(
								145deg,
								#ffffff,
								#f8f8ff
							);
						box-shadow:
							0 0 0 3px rgba(99,102,241,.10),
							0 12px 28px rgba(79,70,229,.10);
					}

					.hr-stat-label {
						display: flex;
						align-items: center;
						gap: 7px;
						font-size: 11px;
						font-weight: 700;
						color: #737b8c;
						text-transform: uppercase;
						letter-spacing: .3px;
						line-height: 1.35;
					}

					.hr-stat-value {
						font-size: 27px;
						font-weight: 750;
						letter-spacing: -1px;
						margin-top: 12px;
						color: #182033;
					}

					.hr-stat-dot {
						width: 8px;
						height: 8px;
						border-radius: 50%;
						background: #6366f1;
						flex: 0 0 auto;
					}

					.hr-stat-card[data-status="Present"]
						.hr-stat-dot {
						background: #10b981;
					}

					.hr-stat-card[data-status="Absent"]
						.hr-stat-dot {
						background: #ef4444;
					}

					.hr-stat-card[data-status="Pending"]
						.hr-stat-dot {
						background: #f59e0b;
					}

					.hr-stat-card[data-status="On Leave"]
						.hr-stat-dot {
						background: #8b5cf6;
					}

					.hr-action-card {
						cursor: pointer;
					}

					.hr-action-card .hr-stat-dot {
						background: #06b6d4;
					}

					/* ==================================================
					   CONTENT
					================================================== */

					.hr-content-grid {
						display: grid;
						grid-template-columns:
							minmax(330px, .72fr)
							minmax(500px, 1.28fr);
						gap: 20px;
						align-items: start;
					}

					.hr-panel {
						background: #fff;
						border: 1px solid var(--hr-border);
						border-radius: 18px;
						box-shadow:
							0 5px 20px rgba(27,39,70,.055);
						overflow: hidden;
					}

					.hr-panel-header {
						padding: 18px 20px;
						border-bottom: 1px solid #edf0f5;
						background:
							linear-gradient(
								180deg,
								#ffffff,
								#fbfcff
							);
					}

					.hr-panel-title-row {
						display: flex;
						align-items: center;
						justify-content: space-between;
						gap: 10px;
					}

					.hr-panel-title {
						font-size: 16px;
						font-weight: 700;
						margin: 0;
					}

					.hr-panel-caption {
						font-size: 12px;
						color: var(--hr-muted);
						margin-top: 4px;
					}

					.hr-panel-body {
						padding: 18px 20px;
					}

					/* ==================================================
					   SEARCH
					================================================== */

					.hr-filter-row {
						display: grid;
						grid-template-columns:
							minmax(0, 1fr)
							180px;
						gap: 10px;
						margin-bottom: 15px;
					}

					.hr-search-wrap {
						position: relative;
					}

					.hr-search-icon {
						position: absolute;
						left: 13px;
						top: 50%;
						transform: translateY(-50%);
						color: #9aa2b1;
						font-size: 13px;
						pointer-events: none;
					}

					.hr-search-input {
						height: 42px !important;
						padding-left: 36px !important;
						border-radius: 11px !important;
						border-color: #e0e5ee !important;
						background: #fbfcfe !important;
					}

					.hr-department-select {
						height: 42px !important;
						border-radius: 11px !important;
						border-color: #e0e5ee !important;
						background: #fbfcfe !important;
					}

					/* ==================================================
					   EMPLOYEE ROW
					================================================== */

					.hr-employee-list {
						max-height: 590px;
						overflow-y: auto;
						padding-right: 2px;
					}

					.hr-employee-list::-webkit-scrollbar {
						width: 6px;
					}

					.hr-employee-list::-webkit-scrollbar-thumb {
						background: #d8ddea;
						border-radius: 10px;
					}

					.hr-employee-row {
						position: relative;
						display: flex;
						align-items: center;
						gap: 12px;
						padding: 12px 11px;
						margin-bottom: 5px;
						border: 1px solid transparent;
						border-radius: 12px;
						cursor: pointer;
						transition:
							background .15s ease,
							border-color .15s ease,
							transform .15s ease;
					}

					.hr-employee-row:hover {
						background: #f8f9fd !important;
						border-color: #edf0f6;
						transform: translateX(2px);
					}

					.hr-employee-row.selected {
						background: #f2f4ff !important;
						border-color: #dfe2ff;
					}

					.hr-avatar {
						width: 39px;
						height: 39px;
						flex: 0 0 39px;
						display: flex;
						align-items: center;
						justify-content: center;
						border-radius: 12px;
						background:
							linear-gradient(
								135deg,
								#eef2ff,
								#e0e7ff
							);
						color: #4f46e5;
						font-size: 13px;
						font-weight: 750;
					}

					.hr-employee-main {
						min-width: 0;
						flex: 1;
					}

					.hr-employee-name {
						font-size: 13px;
						font-weight: 700;
						color: #252c3d;
						white-space: nowrap;
						overflow: hidden;
						text-overflow: ellipsis;
					}

					.hr-employee-meta {
						font-size: 11px;
						color: #8a92a3;
						margin-top: 3px;
						white-space: nowrap;
						overflow: hidden;
						text-overflow: ellipsis;
					}

					.hr-status-pill {
						display: inline-flex;
						align-items: center;
						gap: 5px;
						padding: 5px 8px;
						border-radius: 20px;
						font-size: 10px;
						font-weight: 700;
						white-space: nowrap;
						background: #f1f3f7;
						color: #687184;
					}

					.hr-status-pill::before {
						content: "";
						width: 5px;
						height: 5px;
						border-radius: 50%;
						background: currentColor;
					}

					.hr-status-present {
						background: #ecfdf5;
						color: #059669;
					}

					.hr-status-absent {
						background: #fef2f2;
						color: #dc2626;
					}

					.hr-status-leave {
						background: #f5f3ff;
						color: #7c3aed;
					}

					.hr-status-pending {
						background: #fffbeb;
						color: #d97706;
					}

					/* ==================================================
					   PAGINATION
					================================================== */

					.hr-pagination {
						display: flex;
						align-items: center;
						justify-content: space-between;
						gap: 10px;
						padding-top: 15px;
						margin-top: 10px;
						border-top: 1px solid #eef0f5;
					}

					.hr-pagination button {
						border-radius: 9px !important;
						font-weight: 600 !important;
					}

					.hr-page-label {
						font-size: 12px;
						font-weight: 600;
						color: #7d8596;
					}

					/* ==================================================
					   DETAIL
					================================================== */

					.hr-detail-panel {
						min-height: 650px;
					}

					.hr-detail-empty {
						min-height: 620px;
						display: flex;
						align-items: center;
						justify-content: center;
						text-align: center;
						padding: 40px;
					}

					.hr-empty-icon {
						width: 62px;
						height: 62px;
						margin: 0 auto 15px;
						border-radius: 18px;
						display: flex;
						align-items: center;
						justify-content: center;
						background: #f1f3ff;
						color: #6366f1;
						font-size: 25px;
					}

					.hr-empty-title {
						font-size: 15px;
						font-weight: 700;
						color: #303747;
					}

					.hr-empty-text {
						font-size: 12px;
						color: #8a92a3;
						margin-top: 5px;
					}

					/* ==================================================
					   DETAIL PROFILE
					================================================== */

					.hr-profile {
						display: flex;
						align-items: center;
						gap: 14px;
						padding-bottom: 17px;
						margin-bottom: 17px;
						border-bottom: 1px solid #edf0f5;
					}

					.hr-profile-avatar {
						width: 54px;
						height: 54px;
						flex: 0 0 54px;
						display: flex;
						align-items: center;
						justify-content: center;
						border-radius: 16px;
						background:
							linear-gradient(
								135deg,
								#4f46e5,
								#7c3aed
							);
						color: #fff;
						font-size: 17px;
						font-weight: 750;
						box-shadow:
							0 8px 18px rgba(79,70,229,.20);
					}

					.hr-profile-name {
						font-size: 18px;
						font-weight: 750;
						margin: 0;
					}

					.hr-profile-id {
						font-size: 11px;
						color: #8a92a3;
						margin-top: 4px;
					}

					.hr-detail-section-title {
						font-size: 13px;
						font-weight: 750;
						margin: 18px 0 10px;
						color: #303747;
					}

					.hr-info-grid {
						display: grid;
						grid-template-columns:
							repeat(2,minmax(0,1fr));
						gap: 10px;
					}

					.hr-info-item {
						padding: 12px;
						border: 1px solid #edf0f5;
						border-radius: 11px;
						background: #fbfcfe;
					}

					.hr-info-label {
						font-size: 10px;
						font-weight: 700;
						text-transform: uppercase;
						letter-spacing: .3px;
						color: #9299a8;
					}

					.hr-info-value {
						font-size: 12px;
						font-weight: 650;
						color: #303747;
						margin-top: 4px;
						word-break: break-word;
					}

					/* ==================================================
					   ATTENDANCE BOX
					================================================== */

					.hr-attendance-box {
						border: 1px solid #e9ecf3;
						border-radius: 13px;
						padding: 13px;
						background:
							linear-gradient(
								145deg,
								#fbfcff,
								#ffffff
							);
					}

					.hr-attendance-grid {
						display: grid;
						grid-template-columns:
							repeat(4,minmax(0,1fr));
						gap: 8px;
					}

					.hr-attendance-item {
						padding: 9px;
						border-radius: 9px;
						background: #f8f9fc;
					}

					.hr-attendance-label {
						font-size: 10px;
						color: #9098a7;
						font-weight: 650;
					}

					.hr-attendance-value {
						font-size: 12px;
						color: #303747;
						font-weight: 700;
						margin-top: 3px;
					}

					/* ==================================================
					   TABLE
					================================================== */

					.hr-table-wrap {
						max-height: 320px;
						overflow: auto;
						border: 1px solid #edf0f5;
						border-radius: 12px;
					}

					.hr-console table {
						margin-bottom: 0 !important;
					}

					.hr-console .table > thead > tr > th {
						background: #f8f9fc;
						border-bottom: 1px solid #e8ebf2;
						font-size: 10px;
						font-weight: 750;
						color: #737b8c;
						text-transform: uppercase;
						letter-spacing: .3px;
						padding: 10px;
						position: sticky;
						top: 0;
						z-index: 1;
					}

					.hr-console .table > tbody > tr > td {
						padding: 10px;
						font-size: 11px;
						vertical-align: middle;
						border-color: #eef0f4;
					}

					.hr-attendance-status {
						display: inline-flex;
						padding: 4px 7px;
						border-radius: 15px;
						font-size: 9px;
						font-weight: 700;
						background: #f1f3f7;
						color: #6b7280;
					}

					.hr-attendance-status.present {
						background: #ecfdf5;
						color: #059669;
					}

					.hr-attendance-status.absent {
						background: #fef2f2;
						color: #dc2626;
					}

					.hr-attendance-status.leave {
						background: #f5f3ff;
						color: #7c3aed;
					}

					.hr-attendance-status.pending {
						background: #fffbeb;
						color: #d97706;
					}

					/* ==================================================
					   PAYROLL
					================================================== */

					.hr-pay-card {
						padding: 15px;
						border: 1px solid #e9ecf3;
						border-radius: 13px;
						margin-bottom: 10px;
						background: #fff;
						transition: box-shadow .15s ease;
					}

					.hr-pay-card:hover {
						box-shadow:
							0 7px 18px rgba(27,39,70,.06);
					}

					.hr-pay-grid {
						display: grid;
						grid-template-columns:
							repeat(3,minmax(0,1fr));
						gap: 9px;
					}

					.hr-pay-item {
						padding: 9px;
						border-radius: 9px;
						background: #f8f9fc;
					}

					.hr-pay-label {
						font-size: 9px;
						font-weight: 700;
						text-transform: uppercase;
						color: #9299a8;
					}

					.hr-pay-value {
						font-size: 12px;
						font-weight: 700;
						color: #303747;
						margin-top: 3px;
					}

					.hr-net-pay {
						background:
							linear-gradient(
								135deg,
								#eef2ff,
								#f5f3ff
							);
						border: 1px solid #e2e4ff;
					}

					.hr-net-pay .hr-pay-value {
						color: #4f46e5;
						font-size: 14px;
					}

					/* ==================================================
					   LOADING / EMPTY
					================================================== */

					.hr-loading {
						padding: 45px 20px;
						text-align: center;
						color: #8b93a3;
						font-size: 12px;
					}

					.hr-loading-spinner {
						width: 25px;
						height: 25px;
						border: 3px solid #e8eafd;
						border-top-color: #6366f1;
						border-radius: 50%;
						margin: 0 auto 10px;
						animation: hrSpin .8s linear infinite;
					}

					@keyframes hrSpin {
						to {
							transform: rotate(360deg);
						}
					}

					.hr-no-data {
						padding: 45px 20px;
						text-align: center;
					}

					.hr-no-data-icon {
						font-size: 27px;
						color: #b4bbca;
						margin-bottom: 10px;
					}

					.hr-no-data-title {
						font-size: 13px;
						font-weight: 700;
						color: #60697a;
					}

					.hr-no-data-text {
						font-size: 11px;
						color: #9299a8;
						margin-top: 4px;
					}

					/* ==================================================
					   REVIEW BUTTON
					================================================== */

					.hr-review-btn {
						border: 1px solid #e3e6ef !important;
						background: #fff !important;
						border-radius: 9px !important;
						font-size: 11px !important;
						font-weight: 650 !important;
					}

					.hr-review-btn:hover {
						border-color: #cdd2e3 !important;
						background: #f8f9fc !important;
					}

					/* ==================================================
					   RESPONSIVE
					================================================== */

					@media (max-width: 1350px) {
						.hr-summary-grid {
							grid-template-columns:
								repeat(4,minmax(0,1fr));
						}
					}

					@media (max-width: 1050px) {
						.hr-content-grid {
							grid-template-columns: 1fr;
						}

						.hr-detail-panel {
							min-height: auto;
						}

						.hr-detail-empty {
							min-height: 300px;
						}
					}

					@media (max-width: 700px) {
						.hr-console {
							padding: 14px;
						}

						.hr-summary-grid {
							grid-template-columns:
								repeat(2,minmax(0,1fr));
						}

						.hr-filter-row {
							grid-template-columns: 1fr;
						}

						.hr-info-grid,
						.hr-pay-grid {
							grid-template-columns: 1fr;
						}

						.hr-attendance-grid {
							grid-template-columns:
								repeat(2,minmax(0,1fr));
						}

						.hr-date-panel {
							width: 100%;
						}

						.hr-date-field {
							flex: 1;
							min-width: 130px;
						}
					}

					@media (max-width: 450px) {
						.hr-summary-grid {
							grid-template-columns: 1fr;
						}

						.hr-header-icon {
							width: 42px;
							height: 42px;
						}

						.hr-title {
							font-size: 21px;
						}
					}

				</style>

				<!-- ==================================================
				     HEADER
				================================================== -->

				<div class="hr-header">

					<div class="hr-header-title">

						<div class="hr-header-icon">
							<i class="fa fa-users"></i>
						</div>

						<div>
							<h1 class="hr-title">
								HR Console
							</h1>

							<div class="hr-subtitle">
								Employee attendance, payroll & HR overview
							</div>
						</div>

					</div>

					<div class="hr-date-panel">

						<div class="hr-date-field">

							<label>From Date</label>

							<input
								type="date"
								id="hr-from-date"
								class="form-control"
								value="${selectedDate}"
							/>

						</div>

						<div class="hr-date-field">

							<label>To Date</label>

							<input
								type="date"
								id="hr-to-date"
								class="form-control"
								value="${selectedDate}"
							/>

						</div>

						<button
							class="btn btn-primary hr-refresh-btn"
							id="hr-refresh"
						>
							<i class="fa fa-refresh"
							   style="margin-right:6px;"></i>
							Refresh
						</button>

					</div>

				</div>

				<!-- ==================================================
				     SUMMARY CARDS
				================================================== -->

				<div class="hr-summary-grid">

					<div
						class="hr-stat-card active-card"
						data-status="Active"
					>
						<div class="hr-stat-label">
							<span class="hr-stat-dot"></span>
							Active Headcount
						</div>

						<div
							id="hr-headcount"
							class="hr-stat-value"
						>
							—
						</div>
					</div>

					<div
						class="hr-stat-card"
						data-status="Present"
					>
						<div class="hr-stat-label">
							<span class="hr-stat-dot"></span>
							Present
						</div>

						<div
							id="hr-present"
							class="hr-stat-value"
						>
							—
						</div>
					</div>

					<div
						class="hr-stat-card"
						data-status="Absent"
					>
						<div class="hr-stat-label">
							<span class="hr-stat-dot"></span>
							Absent
						</div>

						<div
							id="hr-absent"
							class="hr-stat-value"
						>
							—
						</div>
					</div>

					<div
						class="hr-stat-card"
						data-status="Pending"
					>
						<div class="hr-stat-label">
							<span class="hr-stat-dot"></span>
							Pending Attendance
						</div>

						<div
							id="hr-pending"
							class="hr-stat-value"
						>
							—
						</div>
					</div>

					<div
						class="hr-stat-card"
						data-status="On Leave"
					>
						<div class="hr-stat-label">
							<span class="hr-stat-dot"></span>
							On Leave
						</div>

						<div
							id="hr-leave"
							class="hr-stat-value"
						>
							—
						</div>
					</div>

					<div
						class="hr-stat-card hr-action-card"
						id="hr-wfh-apply"
					>
						<div class="hr-stat-label">
							<span class="hr-stat-dot"></span>
							Work From Home
						</div>

						<div
							id="hr-wfh-count"
							class="hr-stat-value"
						>
							—
						</div>
					</div>

					<div
						class="hr-stat-card hr-action-card"
						id="hr-leave-application"
					>
						<div class="hr-stat-label">
							<span class="hr-stat-dot"></span>
							Leave Applications
						</div>

						<div
							id="hr-leave-application-count"
							class="hr-stat-value"
						>
							—
						</div>
					</div>

					<div
						class="hr-stat-card hr-action-card"
						id="hr-expense-claim"
					>
						<div class="hr-stat-label">
							<span class="hr-stat-dot"></span>
							Expense Claims
						</div>

						<div
							id="hr-expense-claim-count"
							class="hr-stat-value"
						>
							—
						</div>
					</div>

				</div>

				<!-- ==================================================
				     CONTENT
				================================================== -->

				<div class="hr-content-grid">

					<!-- EMPLOYEE LIST -->

					<div class="hr-panel">

						<div class="hr-panel-header">

							<div class="hr-panel-title-row">

								<div>
									<div class="hr-panel-title">
										Employees
									</div>

									<div
										class="hr-panel-caption"
										id="hr-selected-status"
									>
										Active Employees
									</div>
								</div>

							</div>

						</div>

						<div class="hr-panel-body">

							<div class="hr-filter-row">

								<div class="hr-search-wrap">

									<i
										class="fa fa-search hr-search-icon"
									></i>

									<input
										id="hr-search"
										class="form-control hr-search-input"
										placeholder="Search employee..."
									/>

								</div>

							</div>

							<div
								id="hr-employee-list"
								class="hr-employee-list"
							>
								<div class="hr-loading">
									<div class="hr-loading-spinner"></div>
									Loading employees...
								</div>
							</div>

							<div class="hr-pagination">

								<button
									class="btn btn-default btn-sm"
									id="hr-prev"
								>
									<i
										class="fa fa-chevron-left"
										style="margin-right:5px;"
									></i>
									Previous
								</button>

								<span
									id="hr-page"
									class="hr-page-label"
								>
									Page 1
								</span>

								<button
									class="btn btn-default btn-sm"
									id="hr-next"
								>
									Next
									<i
										class="fa fa-chevron-right"
										style="margin-left:5px;"
									></i>
								</button>

							</div>

						</div>

					</div>

					<!-- EMPLOYEE DETAIL -->

					<div
						class="hr-panel hr-detail-panel"
						id="hr-detail-panel"
					>

						<div
							class="hr-panel-header"
						>
							<div class="hr-panel-title">
								Employee Details
							</div>

							<div class="hr-panel-caption">
								Select an employee to view attendance and payroll
							</div>
						</div>

						<div
							id="hr-detail"
							class="hr-panel-body"
						>

							<div class="hr-detail-empty">

								<div>

									<div class="hr-empty-icon">
										<i class="fa fa-user"></i>
									</div>

									<div class="hr-empty-title">
										No employee selected
									</div>

									<div class="hr-empty-text">
										Select an employee from the list
										to view their details.
									</div>

								</div>

							</div>

						</div>

					</div>

				</div>

			</div>
		`);

		// ==================================================
		// REFERENCES
		// ==================================================

		const $list = $main.find("#hr-employee-list");
		const $detail = $main.find("#hr-detail");
		const $search = $main.find("#hr-search");
		const $fromDate = $main.find("#hr-from-date");
		const $toDate = $main.find("#hr-to-date");

		// ==================================================
		// HELPERS
		// ==================================================

		function escape(value) {
			return frappe.utils.escape_html(
				value == null ? "" : String(value)
			);
		}

		function initials(name) {
			if (!name) {
				return "U";
			}

			const parts = String(name)
				.trim()
				.split(/\s+/)
				.filter(Boolean);

			if (parts.length === 1) {
				return parts[0].substring(0, 2).toUpperCase();
			}

			return (
				parts[0][0] +
				parts[parts.length - 1][0]
			).toUpperCase();
		}

		function statusClass(status) {
			switch (status) {
				case "Present":
					return "hr-status-present";

				case "Absent":
					return "hr-status-absent";

				case "On Leave":
					return "hr-status-leave";

				case "Pending":
					return "hr-status-pending";

				default:
					return "";
			}
		}

		function attendanceStatusClass(status) {
			switch (status) {
				case "Present":
					return "present";

				case "Absent":
					return "absent";

				case "On Leave":
					return "leave";

				case "Pending":
					return "pending";

				default:
					return "";
			}
		}

		function emptyDetail() {
			$detail.html(`
				<div class="hr-detail-empty">

					<div>

						<div class="hr-empty-icon">
							<i class="fa fa-user"></i>
						</div>

						<div class="hr-empty-title">
							No employee selected
						</div>

						<div class="hr-empty-text">
							Select an employee from the list
							to view their details.
						</div>

					</div>

				</div>
			`);
		}

		function loadingDetail() {
			$detail.html(`
				<div class="hr-detail-empty">

					<div>

						<div class="hr-loading-spinner"></div>

						<div class="hr-empty-title">
							Loading employee details...
						</div>

					</div>

				</div>
			`);
		}

		// ==================================================
		// STATUS LABEL
		// ==================================================

		function updateStatusLabel() {
			$main
				.find("#hr-selected-status")
				.text(
					`${currentStatus} Employees • ${selectedDate}`
				);
		}

		// ==================================================
		// OVERVIEW
		// ==================================================

		function loadOverview() {
			$main.find("#hr-headcount").text("...");
			$main.find("#hr-present").text("...");
			$main.find("#hr-absent").text("...");
			$main.find("#hr-pending").text("...");
			$main.find("#hr-leave").text("...");

			frappe.call({
				method:
					"tcb_customization.api.hr_console.get_overview",

				args: {
					from_date: fromDate,
					to_date: toDate,
				},

				callback(r) {
					const data = r.message || {};

					$main
						.find("#hr-headcount")
						.text(data.headcount ?? 0);

					$main
						.find("#hr-present")
						.text(data.present ?? 0);

					$main
						.find("#hr-absent")
						.text(data.absent ?? 0);

					$main
						.find("#hr-pending")
						.text(data.pending ?? 0);

					$main
						.find("#hr-leave")
						.text(data.on_leave ?? 0);
				},

				error(err) {
					console.error(
						"HR Console overview error",
						err
					);

					$main.find("#hr-headcount").text("—");
					$main.find("#hr-present").text("—");
					$main.find("#hr-absent").text("—");
					$main.find("#hr-pending").text("—");
					$main.find("#hr-leave").text("—");
				},
			});
		}

		// ==================================================
		// ACTION CARD COUNTS
		// ==================================================

		function loadActionCardCounts() {
			const from_date = $fromDate.val();
			const to_date = $toDate.val();

			if (!from_date || !to_date) {
				return;
			}

			$main.find("#hr-wfh-count").text("...");
			$main
				.find("#hr-leave-application-count")
				.text("...");
			$main
				.find("#hr-expense-claim-count")
				.text("...");

			frappe.db.count("Attendance Request", {
				filters: [
					[
						"Attendance Request",
						"reason",
						"=",
						"Work From Home",
					],
					[
						"Attendance Request",
						"from_date",
						"<=",
						to_date,
					],
					[
						"Attendance Request",
						"to_date",
						">=",
						from_date,
					],
					[
						"Attendance Request",
						"docstatus",
						"=",
						1,
					],
				],
			}).then((count) => {
				$main
					.find("#hr-wfh-count")
					.text(count || 0);
			});

			frappe.db.count("Leave Application", {
				filters: [
					[
						"Leave Application",
						"from_date",
						"<=",
						to_date,
					],
					[
						"Leave Application",
						"to_date",
						">=",
						from_date,
					],
					[
						"Leave Application",
						"docstatus",
						"=",
						1,
					],
				],
			}).then((count) => {
				$main
					.find("#hr-leave-application-count")
					.text(count || 0);
			});

			frappe.db.count("Expense Claim", {
				filters: [
					[
						"Expense Claim",
						"posting_date",
						">=",
						from_date,
					],
					[
						"Expense Claim",
						"posting_date",
						"<=",
						to_date,
					],
					[
						"Expense Claim",
						"docstatus",
						"=",
						1,
					],
				],
			}).then((count) => {
				$main
					.find("#hr-expense-claim-count")
					.text(count || 0);
			});
		}

		// ==================================================
		// EMPLOYEE LIST
		// ==================================================

		function loadEmployees(pageNumber = 0) {
			currentPage = Math.max(
				0,
				pageNumber
			);

			const start =
				currentPage * pageSize;

			$list.html(`
				<div class="hr-loading">
					<div class="hr-loading-spinner"></div>
					Loading ${escape(
				currentStatus
			).toLowerCase()} employees...
				</div>
			`);

			frappe.call({
				method:
					"tcb_customization.api.hr_console.get_attendance_employees",

				args: {
					from_date: fromDate,
					to_date: toDate,
					status: currentStatus,
					start: start,
					limit: pageSize,
					search: $search.val() || "",
				},

				callback(r) {
					const employees =
						r.message || [];

					$list.empty();

					if (!employees.length) {
						$list.html(`
							<div class="hr-no-data">

								<div class="hr-no-data-icon">
									<i class="fa fa-users"></i>
								</div>

								<div class="hr-no-data-title">
									No employees found
								</div>

								<div class="hr-no-data-text">
									No ${escape(
							currentStatus
						).toLowerCase()}
									employees found for
									${escape(selectedDate)}.
								</div>

							</div>
						`);

						updatePagination(
							employees.length
						);

						return;
					}

					employees.forEach(
						(employee) => {

							const name =
								escape(
									employee.employee_name ||
									""
								);

							const employeeId =
								escape(
									employee.name ||
									""
								);

							const designation =
								escape(
									employee.designation ||
									""
								);

							const department =
								escape(
									employee.department ||
									""
								);

							const status =
								escape(
									employee.attendance_status ||
									""
								);

							const isSelected =
								selectedEmployee ===
								employee.name;

							const $row = $(`
								<div
									class="
										hr-employee-row
										${isSelected ? "selected" : ""}
									"
								>

									<div class="hr-avatar">
										${escape(
								initials(
									employee.employee_name ||
									employee.name
								)
							)}
									</div>

									<div class="hr-employee-main">

										<div class="hr-employee-name">
											${name}
										</div>

										<div class="hr-employee-meta">
											${designation}
											${designation &&
									department
									? " • "
									: ""
								}
											${department}
										</div>

									</div>

									<div
										class="
											hr-status-pill
											${statusClass(status)}
										"
									>
										${status || "Pending"}
									</div>

								</div>
							`);

							$row.on(
								"click",
								function () {

									selectedEmployee =
										employee.name;

									$list
										.find(
											".hr-employee-row"
										)
										.removeClass(
											"selected"
										);

									$row.addClass(
										"selected"
									);

									if (currentStatus === "Pending") {
										const pendingDate =
											employee.pending_date ||
											employee.attendance_date ||
											employee.date ||
											selectedDate;

										loadPendingEmployeeTimesheet(
											employee.name,
											employee.employee_name,
											pendingDate
										);
									} else {
										loadEmployeeDetail(
											employee.name,
											employee.employee_name
										);
									}
								}
							);

							$list.append($row);
						}
					);

					updatePagination(
						employees.length
					);
				},

				error(err) {
					console.error(
						"Employee list error",
						err
					);

					$list.html(`
						<div class="hr-no-data">

							<div class="hr-no-data-icon">
								<i class="fa fa-exclamation-circle"></i>
							</div>

							<div class="hr-no-data-title">
								Failed to load employees
							</div>

							<div class="hr-no-data-text">
								Please refresh and try again.
							</div>

						</div>
					`);

					updatePagination(0);
				},
			});
		}

		// ==================================================
		// PAGINATION
		// ==================================================

		function updatePagination(resultLength) {
			$main
				.find("#hr-page")
				.text(
					`Page ${currentPage + 1}`
				);

			$main
				.find("#hr-prev")
				.prop(
					"disabled",
					currentPage === 0
				);

			$main
				.find("#hr-next")
				.prop(
					"disabled",
					resultLength < pageSize
				);
		}

		// ==================================================

		function loadPendingEmployeeTimesheet(employee, employeeName, pendingDate) {

			$detail.html(`
        <div style="padding:40px;text-align:center;color:#888;">
            <div style="font-size:30px;margin-bottom:10px;">⏳</div>
            <div style="font-size:16px;font-weight:600;color:#444;">
                Loading Timesheet...
            </div>
            <div style="margin-top:5px;font-size:12px;color:#999;">
                ${frappe.utils.escape_html(pendingDate)}
            </div>
        </div>
    `);

			frappe.db.get_list("Timesheet", {
				fields: [
					"name",
					"employee",
					"employee_name",
					"start_date",
					"end_date",
					"total_hours",
					"status"
				],
				filters: [
					["employee", "=", employee],
					["start_date", "<=", pendingDate],
					["end_date", ">=", pendingDate]
				],
				order_by: "start_date desc",
				limit_page_length: 50
			}).then(function (timesheets) {

				if (!timesheets || !timesheets.length) {
					$detail.html(`
                <div style="padding:40px;text-align:center;">
                    <div style="font-size:42px;margin-bottom:12px;">📋</div>

                    <h3 style="margin:0 0 8px;color:#333;">
                        No Timesheet Found
                    </h3>

                    <div style="color:#888;font-size:13px;">
                        No Timesheet found for
                        <strong>
                            ${frappe.utils.escape_html(employeeName || employee)}
                        </strong>
                        on
                        <strong>
                            ${frappe.utils.escape_html(pendingDate)}
                        </strong>.
                    </div>
                </div>
            `);

					return;
				}

				Promise.all(
					timesheets.map(function (ts) {
						return frappe.db.get_doc("Timesheet", ts.name);
					})
				).then(function (docs) {

					let matched = [];

					docs.forEach(function (doc) {

						const logs = (doc.time_logs || []).filter(function (log) {

							if (!log.from_time) {
								return false;
							}

							return String(log.from_time).substring(0, 10) === pendingDate;
						});

						if (logs.length) {
							matched.push({
								doc: doc,
								logs: logs
							});
						}
					});

					if (!matched.length) {
						$detail.html(`
                    <div style="padding:40px;text-align:center;">

                        <div style="font-size:42px;margin-bottom:12px;">
                            📋
                        </div>

                        <h3 style="margin:0 0 8px;color:#333;">
                            No Timesheet Found
                        </h3>

                        <div style="color:#888;font-size:13px;">
                            No Timesheet entries found for
                            <strong>
                                ${frappe.utils.escape_html(employeeName || employee)}
                            </strong>
                            on
                            <strong>
                                ${frappe.utils.escape_html(pendingDate)}
                            </strong>.
                        </div>

                    </div>
                `);

						return;
					}

					let html = `
                <div style="
                    margin-bottom:20px;
                    padding-bottom:15px;
                    border-bottom:1px solid #eee;
                ">

                    <div style="
                        display:flex;
                        justify-content:space-between;
                        align-items:flex-start;
                        gap:15px;
                        flex-wrap:wrap;
                    ">

                        <div>
                            <h3 style="
                                margin:0 0 5px;
                                font-weight:800;
                                color:#20283a;
                            ">
                                ${frappe.utils.escape_html(employeeName || employee)}
                            </h3>

                            <div style="
                                color:#888;
                                font-size:12px;
                            ">
                                ${frappe.utils.escape_html(employee)}
                            </div>
                        </div>

                        <div style="
                            padding:7px 12px;
                            border-radius:999px;
                            background:#eef2ff;
                            color:#4f46e5;
                            font-size:12px;
                            font-weight:700;
                        ">
                            Pending Attendance
                        </div>

                    </div>

                    <div style="
                        margin-top:14px;
                        padding:12px 14px;
                        border-radius:10px;
                        background:#f8fafc;
                        border:1px solid #e5e7eb;
                    ">

                        <span style="
                            color:#888;
                            font-size:12px;
                        ">
                            Attendance Date
                        </span>

                        <div style="
                            margin-top:3px;
                            font-size:15px;
                            font-weight:700;
                            color:#333;
                        ">
                            ${frappe.utils.escape_html(pendingDate)}
                        </div>

                    </div>

                </div>
            `;

					matched.forEach(function (item) {

						const doc = item.doc;
						const logs = item.logs;

						const totalHours = logs.reduce(function (sum, log) {
							return sum + (parseFloat(log.hours) || 0);
						}, 0);

						html += `
                    <div style="
                        border:1px solid #e5e7eb;
                        border-radius:14px;
                        background:white;
                        margin-bottom:18px;
                        overflow:hidden;
                        box-shadow:0 5px 18px rgba(16,24,40,.05);
                    ">

                        <div style="
                            padding:16px;
                            background:#fafbff;
                            border-bottom:1px solid #eee;
                        ">

                            <div style="
                                display:flex;
                                justify-content:space-between;
                                align-items:center;
                                gap:10px;
                                flex-wrap:wrap;
                            ">

                                <div>

                                    <div style="
                                        font-size:12px;
                                        color:#888;
                                    ">
                                        Timesheet
                                    </div>

                                    <div style="
                                        font-size:17px;
                                        font-weight:800;
                                        color:#20283a;
                                        margin-top:3px;
                                    ">
                                        ${frappe.utils.escape_html(doc.name || "")}
                                    </div>

                                </div>

                                <div style="
                                    display:flex;
                                    gap:8px;
                                    align-items:center;
                                ">

                                    <span style="
                                        padding:5px 9px;
                                        border-radius:999px;
                                        background:#eef2ff;
                                        color:#4f46e5;
                                        font-size:11px;
                                        font-weight:700;
                                    ">
                                        ${frappe.utils.escape_html(doc.status || "Draft")}
                                    </span>

                                    <span style="
                                        padding:5px 9px;
                                        border-radius:999px;
                                        background:#ecfdf3;
                                        color:#16834a;
                                        font-size:11px;
                                        font-weight:700;
                                    ">
                                        ${totalHours.toFixed(2)} hrs
                                    </span>

                                </div>

                            </div>

                            <div style="
                                display:flex;
                                gap:25px;
                                margin-top:12px;
                                flex-wrap:wrap;
                                font-size:12px;
                                color:#777;
                            ">

                                <div>
                                    <strong>Start:</strong>
                                    ${frappe.utils.escape_html(doc.start_date || "-")}
                                </div>

                                <div>
                                    <strong>End:</strong>
                                    ${frappe.utils.escape_html(doc.end_date || "-")}
                                </div>

                                <div>
                                    <strong>Day Hours:</strong>
                                    ${totalHours.toFixed(2)}
                                </div>

                            </div>

                        </div>

                        <div style="
                            padding:15px;
                            overflow-x:auto;
                        ">

                            <table style="
                                width:100%;
                                border-collapse:collapse;
                                font-size:12px;
                            ">

                                <thead>

                                    <tr style="background:#f8fafc;">

                                        <th style="padding:10px;text-align:left;border-bottom:1px solid #e5e7eb;">
                                            From
                                        </th>

                                        <th style="padding:10px;text-align:left;border-bottom:1px solid #e5e7eb;">
                                            To
                                        </th>

                                        <th style="padding:10px;text-align:left;border-bottom:1px solid #e5e7eb;">
                                            Hours
                                        </th>

                                        <th style="padding:10px;text-align:left;border-bottom:1px solid #e5e7eb;">
                                            Activity Type
                                        </th>

                                        <th style="padding:10px;text-align:left;border-bottom:1px solid #e5e7eb;">
                                            Project
                                        </th>

                                        <th style="padding:10px;text-align:left;border-bottom:1px solid #e5e7eb;">
                                            Description
                                        </th>

                                    </tr>

                                </thead>

                                <tbody>
            `;

						logs.forEach(function (log) {

							html += `
                        <tr>

                            <td style="padding:10px;border-bottom:1px solid #f0f0f0;">
                                ${frappe.utils.escape_html(log.from_time || "-")}
                            </td>

                            <td style="padding:10px;border-bottom:1px solid #f0f0f0;">
                                ${frappe.utils.escape_html(log.to_time || "-")}
                            </td>

                            <td style="padding:10px;border-bottom:1px solid #f0f0f0;font-weight:700;">
                                ${log.hours ?? 0}
                            </td>

                            <td style="padding:10px;border-bottom:1px solid #f0f0f0;">
                                ${frappe.utils.escape_html(log.activity_type || "-")}
                            </td>

                            <td style="padding:10px;border-bottom:1px solid #f0f0f0;">
                                ${frappe.utils.escape_html(log.project || "-")}
                            </td>

                            <td style="
                                padding:10px;
                                border-bottom:1px solid #f0f0f0;
                                min-width:220px;
                            ">
                                ${frappe.utils.escape_html(log.description || "-")}
                            </td>

                        </tr>
                    `;
						});

						html += `
                                </tbody>
                            </table>

                        </div>

                    </div>
                `;
					});

					$detail.html(html);

				}).catch(function (err) {

					console.error("Pending Timesheet error:", err);

					$detail.html(`
                <div style="padding:20px;color:#b91c1c;">
                    Failed to load Timesheet.
                </div>
            `);
				});

			}).catch(function (err) {

				console.error("Pending Timesheet list error:", err);

				$detail.html(`
            <div style="padding:20px;color:#b91c1c;">
                Failed to load Timesheet.
            </div>
        `);
			});
		}

		// ==================================================
		// EMPLOYEE LEAVE APPLICATIONS (for Leave Application action card)
		// ==================================================

		function loadEmployeeLeaveApplications(employee, employeeName) {

			loadingDetail();

			frappe.db.get_list("Leave Application", {
				fields: [
					"name",
					"employee",
					"employee_name",
					"leave_type",
					"from_date",
					"to_date",
					"total_leave_days",
					"status",
					"docstatus",
					"description",
					"posting_date",
				],
				filters: [
					["employee", "=", employee],
					["docstatus", "=", 1],
				],
				order_by: "from_date desc",
				limit_page_length: 0,
			}).then(function (applications) {

				if (!applications || !applications.length) {
					$detail.html(`
				<div class="hr-detail-empty">

					<div>

						<div class="hr-empty-icon">
							<i class="fa fa-calendar-times-o"></i>
						</div>

						<div class="hr-empty-title">
							No Leave Applications Found
						</div>

						<div class="hr-empty-text">
							No leave applications found for
							${escape(employeeName || employee)}.
						</div>

					</div>

				</div>
			`);

					return;
				}

				let html = `

			<div class="hr-profile">

				<div class="hr-profile-avatar">
					${escape(initials(employeeName || employee))}
				</div>

				<div>

					<h3 class="hr-profile-name">
						${escape(employeeName || employee)}
					</h3>

					<div class="hr-profile-id">
						${escape(employee)}
					</div>

				</div>

			</div>

			<div class="hr-detail-section-title">
				Leave Applications (${applications.length})
			</div>
		`;

				applications.forEach(function (app) {

					const statusColor =
						app.status === "Approved"
							? { bg: "#ecfdf5", color: "#059669" }
							: app.status === "Rejected"
								? { bg: "#fef2f2", color: "#dc2626" }
								: { bg: "#fffbeb", color: "#d97706" };

					html += `

				<div class="hr-pay-card">

					<div
						style="
							display:flex;
							justify-content:space-between;
							align-items:center;
							gap:10px;
							margin-bottom:11px;
						"
					>

						<div>

							<div
								style="
									font-size:12px;
									font-weight:750;
									color:#303747;
								"
							>
								${escape(app.leave_type || "Leave")}
							</div>

							<div
								style="
									font-size:10px;
									color:#9299a8;
									margin-top:3px;
								"
							>
								${escape(app.name || "")}
							</div>

						</div>

						<div
							style="
								font-size:10px;
								font-weight:700;
								color:${statusColor.color};
								background:${statusColor.bg};
								padding:5px 9px;
								border-radius:999px;
							"
						>
							${escape(app.status || "")}
						</div>

					</div>

					<div class="hr-pay-grid">

						<div class="hr-pay-item">

							<div class="hr-pay-label">
								From
							</div>

							<div class="hr-pay-value">
								${escape(app.from_date || "-")}
							</div>

						</div>

						<div class="hr-pay-item">

							<div class="hr-pay-label">
								To
							</div>

							<div class="hr-pay-value">
								${escape(app.to_date || "-")}
							</div>

						</div>

						<div class="hr-pay-item">

							<div class="hr-pay-label">
								Total Days
							</div>

							<div class="hr-pay-value">
								${escape(app.total_leave_days ?? "-")}
							</div>

						</div>

					</div>

					${app.description
							? `
						<div
							style="
								margin-top:10px;
								padding:10px;
								border-radius:9px;
								background:#f8f9fc;
								font-size:11px;
								color:#5b6272;
							"
						>
							${escape(app.description)}
						</div>
					`
							: ""
						}

				</div>
			`;
				});

				$detail.html(html);

			}).catch(function (err) {

				console.error("Leave Application list error", err);

				$detail.html(`
			<div class="hr-detail-empty">

				<div>

					<div
						class="hr-empty-icon"
						style="
							background:#fef2f2;
							color:#ef4444;
						"
					>
						<i class="fa fa-exclamation-circle"></i>
					</div>

					<div class="hr-empty-title">
						Failed to load leave applications
					</div>

					<div class="hr-empty-text">
						Please refresh and try again.
					</div>

				</div>

			</div>
		`);
			});
		}

		// EMPLOYEE DETAIL
		// ==================================================

		function loadEmployeeDetail(
			employee,
			employeeName
		) {
			loadingDetail();

			const selected =
				frappe.datetime.str_to_obj(
					selectedDate
				);

			const from =
				new Date(
					selected.getFullYear(),
					selected.getMonth(),
					1
				);

			const to =
				new Date(
					selected.getFullYear(),
					selected.getMonth() + 1,
					0
				);

			const detailFromDate =
				frappe.datetime.obj_to_str(from);

			const detailToDate =
				frappe.datetime.obj_to_str(to);

			frappe.call({
				method:
					"tcb_customization.api.hr_console.get_employee_detail",

				args: {
					employee: employee,
					from_date:
						detailFromDate,
					to_date:
						detailToDate,
				},

				callback(r) {

					const data =
						r.message || {};

					const employeeInfo =
						data.employee || {};

					const attendance =
						data.attendance || [];

					const salarySlips =
						data.salary_slips || [];

					const attendanceMap = {};

					attendance.forEach(
						(row) => {
							attendanceMap[
								row.attendance_date
							] = row;
						}
					);

					const selectedAttendance =
						attendanceMap[selectedDate];

					const selectedStatus =
						selectedAttendance?.status ||
						"Pending";

					const employeeDisplayName =
						employeeInfo.employee_name ||
						employeeName ||
						"Employee";

					let html = `

						<!-- PROFILE -->

						<div class="hr-profile">

							<div class="hr-profile-avatar">
								${escape(
						initials(
							employeeDisplayName
						)
					)}
							</div>

							<div>

								<h3 class="hr-profile-name">
									${escape(
						employeeDisplayName
					)}
								</h3>

								<div class="hr-profile-id">
									${escape(
						employeeInfo.name ||
						employee
					)}
								</div>

							</div>

						</div>

						<!-- EMPLOYEE INFO -->

						<div class="hr-detail-section-title">
							Employee Information
						</div>

						<div class="hr-info-grid">

							<div class="hr-info-item">
								<div class="hr-info-label">
									Department
								</div>

								<div class="hr-info-value">
									${escape(
						employeeInfo.department ||
						"-"
					)}
								</div>
							</div>

							<div class="hr-info-item">
								<div class="hr-info-label">
									Designation
								</div>

								<div class="hr-info-value">
									${escape(
						employeeInfo.designation ||
						"-"
					)}
								</div>
							</div>

							<div class="hr-info-item">
								<div class="hr-info-label">
									Company
								</div>

								<div class="hr-info-value">
									${escape(
						employeeInfo.company ||
						"-"
					)}
								</div>
							</div>

							<div class="hr-info-item">
								<div class="hr-info-label">
									Date of Joining
								</div>

								<div class="hr-info-value">
									${escape(
						employeeInfo.date_of_joining ||
						"-"
					)}
								</div>
							</div>

						</div>

						<!-- SELECTED DATE -->

						<div class="hr-detail-section-title">
							Attendance • ${escape(selectedDate)}
						</div>

						<div class="hr-attendance-box">

							<div class="hr-attendance-grid">

								<div class="hr-attendance-item">

									<div class="hr-attendance-label">
										Status
									</div>

									<div class="hr-attendance-value">
										<span
											class="
												hr-attendance-status
												${attendanceStatusClass(
						selectedStatus
					)}
											"
										>
											${escape(
						selectedStatus
					)}
										</span>
									</div>

								</div>

								<div class="hr-attendance-item">

									<div class="hr-attendance-label">
										In Time
									</div>

									<div class="hr-attendance-value">
										${escape(
						selectedAttendance?.in_time ||
						"-"
					)}
									</div>

								</div>

								<div class="hr-attendance-item">

									<div class="hr-attendance-label">
										Out Time
									</div>

									<div class="hr-attendance-value">
										${escape(
						selectedAttendance?.out_time ||
						"-"
					)}
									</div>

								</div>

								<div class="hr-attendance-item">

									<div class="hr-attendance-label">
										Working Hours
									</div>

									<div class="hr-attendance-value">
										${escape(
						selectedAttendance?.working_hours ??
						"-"
					)}
									</div>

								</div>

							</div>

						</div>

						<!-- MONTH ATTENDANCE -->

						<div class="hr-detail-section-title">
							Monthly Attendance
						</div>

						<div class="hr-table-wrap">

							<table class="table table-bordered">

								<thead>

									<tr>
										<th>Date</th>
										<th>Status</th>
										<th>In</th>
										<th>Out</th>
										<th>Hours</th>
									</tr>

								</thead>

								<tbody>
					`;

					let current =
						new Date(from);

					while (current <= to) {

						const dateString =
							frappe.datetime.obj_to_str(
								current
							);

						const row =
							attendanceMap[
							dateString
							];

						const status =
							row?.status ||
							"Pending";

						html += `

							<tr
								style="
									${dateString ===
								selectedDate
								? "font-weight:700;background:#f7f8ff;"
								: ""
							}
								"
							>

								<td>
									${escape(dateString)}
								</td>

								<td>

									<span
										class="
											hr-attendance-status
											${attendanceStatusClass(
								status
							)}
										"
									>
										${escape(status)}
									</span>

								</td>

								<td>
									${escape(
								row?.in_time ||
								"-"
							)}
								</td>

								<td>
									${escape(
								row?.out_time ||
								"-"
							)}
								</td>

								<td>
									${escape(
								row?.working_hours ??
								"-"
							)}
								</td>

							</tr>
						`;

						current.setDate(
							current.getDate() + 1
						);
					}

					html += `

								</tbody>

							</table>

						</div>

						<!-- PAYROLL -->

						<div class="hr-detail-section-title">
							Pay Summary
						</div>
					`;

					if (!salarySlips.length) {

						html += `

							<div class="hr-no-data"
								style="
									padding:28px;
									border:1px solid #edf0f5;
									border-radius:13px;
									background:#fbfcfe;
								"
							>

								<div class="hr-no-data-icon">
									<i class="fa fa-money"></i>
								</div>

								<div class="hr-no-data-title">
									Payroll not yet run
								</div>

								<div class="hr-no-data-text">
									No salary slips found for this employee.
								</div>

							</div>
						`;

					} else {

						salarySlips.forEach(
							(slip) => {

								html += `

									<div class="hr-pay-card">

										<div
											style="
												display:flex;
												justify-content:space-between;
												align-items:center;
												gap:10px;
												margin-bottom:11px;
											"
										>

											<div>

												<div
													style="
														font-size:12px;
														font-weight:750;
														color:#303747;
													"
												>
													Salary Slip
												</div>

												<div
													style="
														font-size:10px;
														color:#9299a8;
														margin-top:3px;
													"
												>
													${escape(
									slip.name ||
									""
								)}
												</div>

											</div>

											<div
												style="
													font-size:10px;
													font-weight:650;
													color:#737b8c;
													background:#f4f5f8;
													padding:5px 8px;
													border-radius:8px;
												"
											>
												${escape(
									slip.start_date ||
									""
								)}
												&nbsp;→&nbsp;
												${escape(
									slip.end_date ||
									""
								)}
											</div>

										</div>

										<div class="hr-pay-grid">

											<div class="hr-pay-item">

												<div class="hr-pay-label">
													Working Days
												</div>

												<div class="hr-pay-value">
													${escape(
									slip.total_working_days ??
									0
								)}
												</div>

											</div>

											<div class="hr-pay-item">

												<div class="hr-pay-label">
													Payment Days
												</div>

												<div class="hr-pay-value">
													${escape(
									slip.payment_days ??
									0
								)}
												</div>

											</div>

											<div class="hr-pay-item">

												<div class="hr-pay-label">
													Loss of Pay
												</div>

												<div class="hr-pay-value">
													${escape(
									slip.leave_without_pay ??
									0
								)}
												</div>

											</div>

											<div class="hr-pay-item">

												<div class="hr-pay-label">
													Absent Days
												</div>

												<div class="hr-pay-value">
													${escape(
									slip.absent_days ??
									0
								)}
												</div>

											</div>

											<div class="hr-pay-item">

												<div class="hr-pay-label">
													Gross Pay
												</div>

												<div class="hr-pay-value">
													${escape(
									slip.gross_pay ??
									0
								)}
												</div>

											</div>

											<div class="hr-pay-item">

												<div class="hr-pay-label">
													Total Deduction
												</div>

												<div class="hr-pay-value">
													${escape(
									slip.total_deduction ??
									0
								)}
												</div>

											</div>

											<div
												class="
													hr-pay-item
													hr-net-pay
												"
											>

												<div class="hr-pay-label">
													Net Pay
												</div>

												<div class="hr-pay-value">
													${escape(
									slip.net_pay ??
									0
								)}
												</div>

											</div>

										</div>

									</div>
								`;
							}
						);
					}

					$detail.html(html);
				},

				error(err) {
					console.error(
						"Employee detail error",
						err
					);

					$detail.html(`
						<div class="hr-detail-empty">

							<div>

								<div
									class="hr-empty-icon"
									style="
										background:#fef2f2;
										color:#ef4444;
									"
								>
									<i class="fa fa-exclamation-circle"></i>
								</div>

								<div class="hr-empty-title">
									Failed to load details
								</div>

								<div class="hr-empty-text">
									Please refresh and try again.
								</div>

							</div>

						</div>
					`);
				},
			});
		}

		// ==================================================
		// CARD CLICK
		// ==================================================

		$main
			.find(".hr-stat-card")
			.not(".hr-action-card")
			.on(
				"click",
				function () {

					currentStatus =
						$(this).data(
							"status"
						);

					currentPage = 0;

					$main
						.find(".hr-stat-card")
						.removeClass(
							"active-card"
						);

					$(this)
						.addClass(
							"active-card"
						);

					selectedEmployee = null;

					emptyDetail();

					updateStatusLabel();

					loadEmployees(0);
				}
			);

		// ==================================================
		// ACTION CARD EMPLOYEE LIST
		// ==================================================

		function loadActionEmployees(type) {

			currentPage = 0;
			selectedEmployee = null;

			$main
				.find(".hr-stat-card")
				.removeClass(
					"active-card"
				);

			$main
				.find(type.card)
				.addClass(
					"active-card"
				);

			emptyDetail();

			const from_date =
				$fromDate.val();

			const to_date =
				$toDate.val();

			$list.html(`
				<div class="hr-loading">

					<div class="hr-loading-spinner"></div>

					Loading ${escape(
				type.label
			)}...

				</div>
			`);

			let filters = [];

			if (
				type.doctype ===
				"Attendance Request"
			) {

				filters = [
					[
						"Attendance Request",
						"reason",
						"=",
						"Work From Home",
					],
					[
						"Attendance Request",
						"from_date",
						"<=",
						to_date,
					],
					[
						"Attendance Request",
						"to_date",
						">=",
						from_date,
					],
					[
						"Attendance Request",
						"docstatus",
						"=",
						1,
					],
				];

			} else if (
				type.doctype ===
				"Leave Application"
			) {

				filters = [
					[
						"Leave Application",
						"from_date",
						"<=",
						to_date,
					],
					[
						"Leave Application",
						"to_date",
						">=",
						from_date,
					],
					[
						"Leave Application",
						"docstatus",
						"=",
						1,
					],
				];

			} else if (
				type.doctype ===
				"Expense Claim"
			) {

				filters = [
					[
						"Expense Claim",
						"posting_date",
						">=",
						from_date,
					],
					[
						"Expense Claim",
						"posting_date",
						"<=",
						to_date,
					],
					[
						"Expense Claim",
						"docstatus",
						"=",
						1,
					],
				];
			}

			frappe.db.get_list(
				type.doctype,
				{
					fields: [
						"name",
						"employee",
						"employee_name",
					],

					filters: filters,

					limit_page_length: 0,
				}
			)
				.then(
					(records) => {

						$list.empty();

						if (!records.length) {

							$list.html(`
								<div class="hr-no-data">

									<div class="hr-no-data-icon">
										<i class="fa fa-check-circle"></i>
									</div>

									<div class="hr-no-data-title">
										No ${escape(
								type.label
							)} found
									</div>

									<div class="hr-no-data-text">
										There are no records
										for the selected period.
									</div>

								</div>
							`);

							updatePagination(0);

							return;
						}

						records.forEach(
							(record) => {

								const employeeName =
									escape(
										record.employee_name ||
										record.employee ||
										""
									);

								const employeeId =
									escape(
										record.employee ||
										""
									);

								const $row = $(`
									<div
										class="hr-employee-row"
									>

										<div class="hr-avatar">
											${escape(
									initials(
										record.employee_name ||
										record.employee
									)
								)}
										</div>

										<div class="hr-employee-main">

											<div class="hr-employee-name">
												${employeeName}
											</div>

											<div class="hr-employee-meta">
												${employeeId}
											</div>

										</div>

										<div
											class="
												hr-status-pill
											"
										>
											${escape(
									type.label
								)}
										</div>

									</div>
								`);

								$row.on(
									"click",
									function () {

										if (
											record.employee
										) {

											selectedEmployee =
												record.employee;

											$list
												.find(
													".hr-employee-row"
												)
												.removeClass(
													"selected"
												);

											$row.addClass(
												"selected"
											);

											if (
												type.doctype ===
												"Leave Application"
											) {

												loadEmployeeLeaveApplications(
													record.employee,
													record.employee_name
												);

											} else {

												loadEmployeeDetail(
													record.employee,
													record.employee_name
												);
											}
										}
									}
								);

								$list.append(
									$row
								);
							}
						);

						updatePagination(
							records.length
						);
					}
				)
				.catch(
					(err) => {

						console.error(
							"Action card employee list error",
							err
						);

						$list.html(`
							<div class="hr-no-data">

								<div
									class="hr-no-data-icon"
									style="color:#ef4444;"
								>
									<i class="fa fa-exclamation-circle"></i>
								</div>

								<div class="hr-no-data-title">
									Failed to load records
								</div>

							</div>
						`);

						updatePagination(0);
					}
				);
		}

		// ==================================================
		// ACTION CARD EVENTS
		// ==================================================

		$main
			.find("#hr-wfh-apply")
			.on(
				"click",
				function () {

					loadActionEmployees({
						card:
							"#hr-wfh-apply",

						label:
							"Work From Home requests",

						doctype:
							"Attendance Request",
					});
				}
			);

		$main
			.find("#hr-leave-application")
			.on(
				"click",
				function () {

					loadActionEmployees({
						card:
							"#hr-leave-application",

						label:
							"Leave Applications",

						doctype:
							"Leave Application",
					});
				}
			);

		$main
			.find("#hr-expense-claim")
			.on(
				"click",
				function () {

					loadActionEmployees({
						card:
							"#hr-expense-claim",

						label:
							"Expense Claims",

						doctype:
							"Expense Claim",
					});
				}
			);

		// ==================================================
		// PAGINATION
		// ==================================================

		$main
			.find("#hr-prev")
			.on(
				"click",
				function () {

					if (currentPage > 0) {

						loadEmployees(
							currentPage - 1
						);
					}
				}
			);

		$main
			.find("#hr-next")
			.on(
				"click",
				function () {

					loadEmployees(
						currentPage + 1
					);
				}
			);

		// ==================================================
		// SEARCH
		// ==================================================

		let searchTimer;

		$search.on(
			"input",
			function () {

				clearTimeout(
					searchTimer
				);

				searchTimer =
					setTimeout(
						function () {

							selectedEmployee =
								null;

							emptyDetail();

							loadEmployees(0);

						},
						400
					);
			}
		);

		// ==================================================
		// DATE CHANGE
		// ==================================================

		$fromDate.on(
			"change",
			function () {

				selectedDate =
					$fromDate.val() ||
					frappe.datetime.get_today();
			}
		);

		// ==================================================
		// REFRESH
		// ==================================================

		$main
			.find("#hr-refresh")
			.on(
				"click",
				function () {

					fromDate =
						$fromDate.val() ||
						frappe.datetime.get_today();

					toDate =
						$toDate.val() ||
						frappe.datetime.get_today();

					selectedDate =
						fromDate;

					currentPage = 0;
					selectedEmployee = null;

					$main
						.find(".hr-stat-card")
						.removeClass(
							"active-card"
						);

					$main
						.find(
							'.hr-stat-card[data-status="Active"]'
						)
						.addClass(
							"active-card"
						);

					currentStatus =
						"Active";

					updateStatusLabel();

					emptyDetail();

					loadOverview();

					loadActionCardCounts();

					loadEmployees(0);
				}
			);

		// ==================================================
		// INITIAL LOAD
		// ==================================================

		updateStatusLabel();

		loadOverview();

		loadActionCardCounts();

		loadEmployees(0);
	},
});