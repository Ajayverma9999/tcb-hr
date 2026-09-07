frappe.pages["hr-console"].on_page_load = function (wrapper) {
    new HRConsoleDashboard(wrapper);
};

class HRConsoleDashboard {
    constructor(wrapper) {
        this.wrapper = wrapper;

        this.page = frappe.ui.make_app_page({
            parent: wrapper,
            title: "",
            single_column: true
        });

        this.currentData = null;
        this.activeSection = null;

        this.render();
        this.setupFilters();
        this.loadDashboard();
    }

    render() {
        $(this.wrapper).find(".layout-main-section").html(`
            <style>
                .hr-dashboard {
                    padding: 14px 6px 45px;
                    font-family: Inter, -apple-system, BlinkMacSystemFont,
                        "Segoe UI", sans-serif;
                    background:
                        radial-gradient(circle at 0% 0%, rgba(99,102,241,.10), transparent 28%),
                        radial-gradient(circle at 100% 10%, rgba(14,165,233,.10), transparent 25%),
                        #f8fafc;
                    min-height: calc(100vh - 80px);
                }

                /* ================= HEADER ================= */

                .hr-dashboard-header {
                    position: relative;
                    overflow: hidden;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    gap: 24px;
                    margin-bottom: 22px;
                    padding: 24px 26px;
                    border-radius: 22px;
                    background:
                        linear-gradient(135deg, #ffffff 0%, #f8faff 100%);
                    border: 1px solid rgba(148,163,184,.18);
                    box-shadow:
                        0 10px 35px rgba(15,23,42,.07);
                }

                .hr-dashboard-header::before {
                    content: "";
                    position: absolute;
                    width: 220px;
                    height: 220px;
                    border-radius: 50%;
                    right: -90px;
                    top: -120px;
                    background: rgba(99,102,241,.08);
                    pointer-events: none;
                }

                .hr-dashboard-header::after {
                    content: "";
                    position: absolute;
                    width: 150px;
                    height: 150px;
                    border-radius: 50%;
                    left: 42%;
                    bottom: -115px;
                    background: rgba(14,165,233,.07);
                    pointer-events: none;
                }

                .hr-title-wrap {
                    position: relative;
                    z-index: 1;
                    display: flex;
                    align-items: center;
                    gap: 15px;
                }

                .hr-title-icon {
                    width: 56px;
                    height: 56px;
                    border-radius: 17px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background:
                        linear-gradient(135deg, #4f46e5, #7c3aed);
                    color: white;
                    font-size: 23px;
                    box-shadow:
                        0 10px 22px rgba(79,70,229,.28);
                }

                .hr-title {
                    font-size: 26px;
                    font-weight: 800;
                    color: #172033;
                    margin: 0;
                    letter-spacing: -.4px;
                }

                .hr-subtitle {
                    color: #64748b;
                    font-size: 13px;
                    margin-top: 5px;
                    font-weight: 500;
                }

                /* ================= FILTERS ================= */

                .hr-filters {
                    position: relative;
                    z-index: 2;
                    display: flex;
                    align-items: flex-end;
                    gap: 10px;
                    flex-wrap: wrap;
                }

                .hr-filter {
                    min-width: 125px;
                }

                .hr-filter label {
                    display: block;
                    font-size: 10px;
                    font-weight: 800;
                    color: #64748b;
                    margin: 0 0 6px 3px;
                    text-transform: uppercase;
                    letter-spacing: .7px;
                }

                .hr-filter select {
                    height: 41px;
                    min-width: 125px;
                    border: 1px solid #dbe3ee;
                    border-radius: 11px;
                    padding: 0 12px;
                    background: #ffffff;
                    color: #1e293b;
                    font-weight: 650;
                    outline: none;
                    box-shadow: 0 3px 10px rgba(15,23,42,.035);
                    transition: .2s ease;
                }

                .hr-filter select:hover {
                    border-color: #a5b4fc;
                }

                .hr-filter select:focus {
                    border-color: #6366f1;
                    box-shadow:
                        0 0 0 3px rgba(99,102,241,.10);
                }

                .hr-refresh {
                    height: 41px;
                    padding: 0 18px;
                    border: none;
                    border-radius: 11px;
                    background:
                        linear-gradient(135deg, #4f46e5, #7c3aed);
                    color: white;
                    font-weight: 750;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    transition: .22s ease;
                    box-shadow:
                        0 7px 18px rgba(79,70,229,.22);
                }

                .hr-refresh:hover {
                    transform: translateY(-2px);
                    box-shadow:
                        0 11px 24px rgba(79,70,229,.30);
                }

                .hr-refresh:active {
                    transform: translateY(0);
                }

                /* ================= CARDS ================= */

                .hr-cards {
                    display: grid;
                    grid-template-columns: repeat(4, minmax(180px, 1fr));
                    gap: 15px;
                    margin-bottom: 22px;
                    width: 100%;
                }

                .hr-card {
                    min-width: 0;
                    width: 100%;
                    box-sizing: border-box;
                }

                .hr-card-label {
                    white-space: normal;
                    overflow-wrap: anywhere;
                    line-height: 1.35;
                }

                .hr-card-value {
                    white-space: nowrap;
                }

                .hr-card {
                    --card-color: #6366f1;
                    --card-light: #eef2ff;
                    --card-shadow: rgba(99,102,241,.20);

                    position: relative;
                    overflow: hidden;
                    min-height: 158px;
                    padding: 21px;
                    border-radius: 19px;
                    border: 1px solid rgba(148,163,184,.20);
                    background: #ffffff;
                    cursor: pointer;
                    transition: all .25s ease;
                    box-shadow:
                        0 7px 25px rgba(15,23,42,.055);
                }

                .hr-card:nth-child(1) {
                    --card-color: #6366f1;
                    --card-light: #eef2ff;
                    --card-shadow: rgba(99,102,241,.22);
                }

                .hr-card:nth-child(2) {
                    --card-color: #10b981;
                    --card-light: #ecfdf5;
                    --card-shadow: rgba(16,185,129,.22);
                }

                .hr-card:nth-child(3) {
                    --card-color: #ef4444;
                    --card-light: #fef2f2;
                    --card-shadow: rgba(239,68,68,.20);
                }

                .hr-card:nth-child(4) {
                    --card-color: #f59e0b;
                    --card-light: #fffbeb;
                    --card-shadow: rgba(245,158,11,.23);
                }

                .hr-card:nth-child(5) {
                    --card-color: #06b6d4;
                    --card-light: #ecfeff;
                    --card-shadow: rgba(6,182,212,.22);
                }

                .hr-card:nth-child(6) {
                    --card-color: #8b5cf6;
                    --card-light: #f5f3ff;
                    --card-shadow: rgba(139,92,246,.22);
                }

                .hr-card:nth-child(7) {
                    --card-color: #ec4899;
                    --card-light: #fdf2f8;
                    --card-shadow: rgba(236,72,153,.22);
                }

                .hr-card:nth-child(8) {
                    --card-color: #14b8a6;
                    --card-light: #f0fdfa;
                    --card-shadow: rgba(20,184,166,.22);
                }

                .hr-card:hover {
                    transform: translateY(-5px);
                    border-color: var(--card-color);
                    box-shadow:
                        0 15px 34px var(--card-shadow);
                }

                .hr-card.active {
                    border: 2px solid var(--card-color);
                    transform: translateY(-3px);
                    box-shadow:
                        0 13px 30px var(--card-shadow);
                }

                .hr-card::before {
                    content: "";
                    position: absolute;
                    width: 125px;
                    height: 125px;
                    border-radius: 50%;
                    right: -48px;
                    bottom: -58px;
                    background: var(--card-light);
                    transition: .25s ease;
                }

                .hr-card:hover::before {
                    transform: scale(1.25);
                }

                .hr-card::after {
                    content: "";
                    position: absolute;
                    width: 7px;
                    height: 48px;
                    left: 0;
                    top: 22px;
                    border-radius: 0 6px 6px 0;
                    background: var(--card-color);
                    opacity: .9;
                }

                .hr-card-icon {
                    position: relative;
                    z-index: 1;
                    width: 44px;
                    height: 44px;
                    border-radius: 13px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 18px;
                    margin-bottom: 14px;
                    background: var(--card-light);
                    color: var(--card-color);
                    transition: .25s ease;
                }

                .hr-card:hover .hr-card-icon {
                    transform: scale(1.07);
                }

                .hr-card-label {
                    position: relative;
                    z-index: 1;
                    color: #64748b;
                    font-size: 11px;
                    font-weight: 800;
                    text-transform: uppercase;
                    letter-spacing: .65px;
                }

                .hr-card-value {
                    position: relative;
                    z-index: 1;
                    color: var(--card-color);
                    font-size: 32px;
                    line-height: 1;
                    font-weight: 850;
                    margin-top: 7px;
                    letter-spacing: -1px;
                }

                .hr-card-arrow {
                    position: absolute;
                    z-index: 2;
                    right: 17px;
                    top: 18px;
                    width: 28px;
                    height: 28px;
                    border-radius: 9px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: var(--card-color);
                    background: var(--card-light);
                    font-size: 13px;
                    transition: .2s ease;
                }

                .hr-card:hover .hr-card-arrow {
                    transform: translateX(3px);
                }

                /* ================= CONTENT ================= */

                .hr-content {
                    position: relative;
                    background: #ffffff;
                    border: 1px solid rgba(148,163,184,.18);
                    border-radius: 20px;
                    min-height: 280px;
                    box-shadow:
                        0 8px 28px rgba(15,23,42,.05);
                    overflow: hidden;
                }

                .hr-content-header {
                    position: relative;
                    padding: 18px 22px;
                    border-bottom: 1px solid #edf1f6;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    background:
                        linear-gradient(135deg, #ffffff, #f8faff);
                }

                .hr-content-header::before {
                    content: "";
                    position: absolute;
                    left: 0;
                    top: 0;
                    width: 100%;
                    height: 3px;
                    background:
                        linear-gradient(
                            90deg,
                            #6366f1,
                            #8b5cf6,
                            #06b6d4
                        );
                }

                .hr-content-title {
                    font-size: 17px;
                    font-weight: 800;
                    color: #172033;
                }

                .hr-content-count {
                    padding: 6px 11px;
                    border-radius: 20px;
                    font-size: 11px;
                    font-weight: 750;
                    color: #6366f1;
                    background: #eef2ff;
                }

                /* ================= LIST ================= */

                .hr-list {
                    padding: 8px 14px 14px;
                }

                .hr-list-row {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    gap: 15px;
                    padding: 13px 11px;
                    border-bottom: 1px solid #f0f3f7;
                    border-radius: 11px;
                    transition: .18s ease;
                }

                .hr-list-row:last-child {
                    border-bottom: none;
                }

                .hr-list-row:hover {
                    background:
                        linear-gradient(
                            90deg,
                            #f8faff,
                            #ffffff
                        );
                    transform: translateX(2px);
                }

                .hr-employee {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    min-width: 0;
                }

                .hr-avatar {
                    width: 40px;
                    height: 40px;
                    flex-shrink: 0;
                    border-radius: 12px;
                    background:
                        linear-gradient(135deg, #eef2ff, #f3e8ff);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 12px;
                    font-weight: 850;
                    color: #6366f1;
                    border: 1px solid #e0e7ff;
                }

                .hr-employee-name {
                    font-size: 14px;
                    font-weight: 750;
                    color: #1e293b;
                }

                .hr-employee-meta {
                    color: #94a3b8;
                    font-size: 11px;
                    margin-top: 3px;
                }

                .hr-status {
                    padding: 6px 11px;
                    border-radius: 20px;
                    background: #eef2ff;
                    color: #6366f1;
                    font-size: 10px;
                    font-weight: 800;
                    text-transform: uppercase;
                    letter-spacing: .3px;
                    white-space: nowrap;
                }

                /* Status colors */

                .hr-list-row:has(.hr-status) .hr-status {
                    transition: .15s ease;
                }

                .hr-timesheet-row {
                    cursor: pointer;
                }

                .hr-timesheet-row:hover {
                    background: #fffbeb;
                }

                .hr-timesheet-open {
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    padding: 7px 11px;
                    border-radius: 9px;
                    color: #d97706;
                    background: #fffbeb;
                    font-size: 11px;
                    font-weight: 800;
                    transition: .2s ease;
                }

                .hr-timesheet-row:hover .hr-timesheet-open {
                    background: #fef3c7;
                    transform: translateX(2px);
                }

                /* ================= EMPTY ================= */

                .hr-empty {
                    padding: 62px 20px;
                    text-align: center;
                    color: #94a3b8;
                }

                .hr-empty-icon {
                    width: 58px;
                    height: 58px;
                    margin: 0 auto 13px;
                    border-radius: 17px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 25px;
                    color: #6366f1;
                    background: #eef2ff;
                }

                .hr-empty-title {
                    font-weight: 800;
                    color: #64748b;
                    font-size: 14px;
                }

                .hr-empty-text {
                    font-size: 12px;
                    margin-top: 5px;
                    color: #94a3b8;
                }

                .hr-loading {
                    padding: 65px 20px;
                    text-align: center;
                    color: #64748b;
                }

                /* ================= RESPONSIVE ================= */

                @media (max-width: 1250px) {
                    .hr-cards {
                        grid-template-columns: repeat(3, 1fr);
                    }

                    .hr-dashboard-header {
                        flex-direction: column;
                        align-items: flex-start;
                    }

                    .hr-filters {
                        width: 100%;
                    }
                }

                @media (max-width: 700px) {
                    .hr-cards {
                        grid-template-columns: repeat(2, 1fr);
                    }

                    .hr-filters {
                        display: grid;
                        grid-template-columns: 1fr 1fr;
                        width: 100%;
                    }

                    .hr-filter,
                    .hr-filter select {
                        width: 100%;
                        min-width: 0;
                    }

                    .hr-refresh {
                        width: 100%;
                        justify-content: center;
                    }
                }

                @media (max-width: 480px) {
                    .hr-dashboard {
                        padding: 8px 3px 30px;
                    }

                    .hr-dashboard-header {
                        padding: 20px;
                    }

                    .hr-title {
                        font-size: 21px;
                    }

                    .hr-cards {
                        grid-template-columns: 1fr;
                    }

                    .hr-filters {
                        grid-template-columns: 1fr;
                    }

                    .hr-card {
                        min-height: 145px;
                    }
                }
            </style>

            <div class="hr-dashboard">

                <div class="hr-dashboard-header">

                    <div class="hr-title-wrap">

                        <div class="hr-title-icon">
                            <i class="fa fa-users"></i>
                        </div>

                        <div>
                            <div class="hr-title">
                                HR Console Dashboard
                            </div>

                            <div class="hr-subtitle">
                                Employee attendance overview by year and month
                            </div>
                        </div>

                    </div>

                    <div class="hr-filters">

                        <div class="hr-filter">
                            <label>Year</label>
                            <select id="hr-year"></select>
                        </div>

                        <div class="hr-filter">
                            <label>Month</label>

                            <select id="hr-month">
                                <option value="1">January</option>
                                <option value="2">February</option>
                                <option value="3">March</option>
                                <option value="4">April</option>
                                <option value="5">May</option>
                                <option value="6">June</option>
                                <option value="7">July</option>
                                <option value="8">August</option>
                                <option value="9">September</option>
                                <option value="10">October</option>
                                <option value="11">November</option>
                                <option value="12">December</option>
                            </select>
                        </div>

                        <button class="hr-refresh" id="hr-refresh">
                            <i class="fa fa-refresh"></i>
                            Refresh
                        </button>

                    </div>

                </div>

                <div class="hr-cards">

                    <div class="hr-card" data-section="active">

                        <div class="hr-card-arrow">
                            <i class="fa fa-angle-right"></i>
                        </div>

                        <div class="hr-card-icon">
                            <i class="fa fa-users"></i>
                        </div>

                        <div class="hr-card-label">
                            Active Headcount
                        </div>

                        <div class="hr-card-value" id="count-active">
                            0
                        </div>

                    </div>

                    <div class="hr-card" data-section="present">

                        <div class="hr-card-arrow">
                            <i class="fa fa-angle-right"></i>
                        </div>

                        <div class="hr-card-icon">
                            <i class="fa fa-check"></i>
                        </div>

                        <div class="hr-card-label">
                            Present
                        </div>

                        <div class="hr-card-value" id="count-present">
                            0
                        </div>

                    </div>

                    <div class="hr-card" data-section="absent">

                        <div class="hr-card-arrow">
                            <i class="fa fa-angle-right"></i>
                        </div>

                        <div class="hr-card-icon">
                            <i class="fa fa-times"></i>
                        </div>

                        <div class="hr-card-label">
                            Absent
                        </div>

                        <div class="hr-card-value" id="count-absent">
                            0
                        </div>

                    </div>

                    <div class="hr-card" data-section="pending">

                        <div class="hr-card-arrow">
                            <i class="fa fa-angle-right"></i>
                        </div>

                        <div class="hr-card-icon">
                            <i class="fa fa-clock-o"></i>
                        </div>

                        <div class="hr-card-label">
                            Pending Attendance
                        </div>

                        <div class="hr-card-value" id="count-pending">
                            0
                        </div>

                    </div>

                    <div class="hr-card" data-section="on_leave">

                        <div class="hr-card-arrow">
                            <i class="fa fa-angle-right"></i>
                        </div>

                        <div class="hr-card-icon">
                            <i class="fa fa-plane"></i>
                        </div>

                        <div class="hr-card-label">
                            On Leave
                        </div>

                        <div class="hr-card-value" id="count-on-leave">
                            0
                        </div>

                    </div>

                <div class="hr-card" data-section="work_from_home">

                    <div class="hr-card-arrow">
                        <i class="fa fa-angle-right"></i>
                    </div>

                    <div class="hr-card-icon">
                        <i class="fa fa-home"></i>
                    </div>

                    <div class="hr-card-label">
                        Work From Home
                    </div>

                    <div class="hr-card-value" id="count-work-from-home">
                        0
                    </div>

                </div>

                <div class="hr-card" data-section="leave_applications">

                    <div class="hr-card-arrow">
                        <i class="fa fa-angle-right"></i>
                    </div>

                    <div class="hr-card-icon">
                        <i class="fa fa-calendar"></i>
                    </div>

                    <div class="hr-card-label">
                        Leave Applications
                    </div>

                    <div class="hr-card-value" id="count-leave-applications">
                        0
                    </div>

                </div>

                <div class="hr-card" data-section="expense_claims">

                    <div class="hr-card-arrow">
                        <i class="fa fa-angle-right"></i>
                    </div>

                    <div class="hr-card-icon">
                        <i class="fa fa-money"></i>
                    </div>

                    <div class="hr-card-label">
                        Expense Claims
                    </div>

                    <div class="hr-card-value" id="count-expense-claims">
                        0
                    </div>

                </div>

                </div>

                <div class="hr-content" id="hr-content">

                    <div class="hr-empty">

                        <div class="hr-empty-icon">
                            <i class="fa fa-hand-pointer-o"></i>
                        </div>

                        <div class="hr-empty-title">
                            Select a card
                        </div>

                        <div class="hr-empty-text">
                            Click any card above to view employees.
                        </div>

                    </div>

                </div>

            </div>
        `);

        this.$main = $(this.wrapper);
    }

    setupFilters() {
        const currentYear = new Date().getFullYear();
        const currentMonth = new Date().getMonth() + 1;

        let years = "";

        for (
            let year = currentYear;
            year >= currentYear - 5;
            year--
        ) {
            years += `
                <option value="${year}">
                    ${year}
                </option>
            `;
        }

        this.$main.find("#hr-year").html(years);
        this.$main.find("#hr-year").val(currentYear);
        this.$main.find("#hr-month").val(currentMonth);

        this.$main.find("#hr-refresh").on("click", () => {
            this.loadDashboard();
        });

        this.$main.find("#hr-year, #hr-month").on("change", () => {
            this.loadDashboard();
        });

        this.$main.find(".hr-card").on("click", (e) => {
            const section = $(e.currentTarget).data("section");

            this.$main.find(".hr-card").removeClass("active");
            $(e.currentTarget).addClass("active");

            this.activeSection = section;

            this.renderSection(section);
        });
    }

    loadDashboard() {
        const year = this.$main.find("#hr-year").val();
        const month = this.$main.find("#hr-month").val();

        this.$main.find("#hr-refresh i")
            .addClass("fa-spin");

        frappe.call({
            method:
                "tcb_customization.tcb.page.hr_console.hr_console.get_dashboard_data",

            args: {
                year: year,
                month: month
            },

            callback: (r) => {

                this.$main.find("#hr-refresh i")
                    .removeClass("fa-spin");

                if (!r.message) {
                    frappe.msgprint(
                        "Unable to load HR dashboard."
                    );
                    return;
                }

                this.currentData = r.message;

                this.$main.find("#count-active")
                    .text(r.message.counts.active);

                this.$main.find("#count-present")
                    .text(r.message.counts.present);

                this.$main.find("#count-absent")
                    .text(r.message.counts.absent);

                this.$main.find("#count-pending")
                    .text(r.message.counts.pending);

                this.$main.find("#count-on-leave")
                    .text(r.message.counts.on_leave);

                this.$main.find("#count-work-from-home")
                    .text(r.message.counts.work_from_home);

                this.$main.find("#count-leave-applications")
                    .text(r.message.counts.leave_applications);

                this.$main.find("#count-expense-claims")
                    .text(r.message.counts.expense_claims);

                if (this.activeSection) {
                    this.renderSection(
                        this.activeSection
                    );
                }
            },

            error: () => {
                this.$main.find("#hr-refresh i")
                    .removeClass("fa-spin");
            }
        });
    }

    getInitials(name) {
        if (!name) {
            return "?";
        }

        const parts = name.trim().split(" ");

        if (parts.length === 1) {
            return parts[0]
                .substring(0, 2)
                .toUpperCase();
        }

        return (
            parts[0].charAt(0) +
            parts[parts.length - 1].charAt(0)
        ).toUpperCase();
    }

    renderSection(section) {
        if (!this.currentData) {
            return;
        }

        let title = "";
        let rows = [];
        let isTimesheet = false;

        if (section === "active") {
            title = "Active Employees";
            rows = this.currentData.employees.active;
        }

        if (section === "present") {
            title = "Present Employees";
            rows = this.currentData.employees.present;
        }

        if (section === "absent") {
            title = "Absent Employees";
            rows = this.currentData.employees.absent;
        }

        if (section === "on_leave") {
            title = "Employees On Leave";
            rows = this.currentData.employees.on_leave;
        }

        if (section === "work_from_home") {
            title = "Employees Working From Home";
            rows = this.currentData.employees.work_from_home;
        }

        if (section === "leave_applications") {
            title = "Leave Applications";
            rows = this.currentData.leave_applications;
        }

        if (section === "expense_claims") {
            title = "Expense Claims";
            rows = this.currentData.expense_claims;
        }

        if (section === "pending") {
            title = "Pending Attendance — Draft Timesheets";
            rows = this.currentData.timesheets;
            isTimesheet = true;
        }

        let html = `
            <div class="hr-content-header">

                <div class="hr-content-title">
                    ${title}
                </div>

                <div class="hr-content-count">
                    ${rows.length}
                    record${rows.length === 1 ? "" : "s"}
                </div>

            </div>
        `;

        if (!rows.length) {

            html += `
                <div class="hr-empty">

                    <div class="hr-empty-icon">
                        <i class="fa fa-folder-open-o"></i>
                    </div>

                    <div class="hr-empty-title">
                        No records found
                    </div>

                    <div class="hr-empty-text">
                        There is no data for the selected
                        month and year.
                    </div>

                </div>
            `;

            this.$main
                .find("#hr-content")
                .html(html);

            return;
        }

        html += `<div class="hr-list">`;

        rows.forEach((row) => {

            const name =
                row.employee_name ||
                row.employee ||
                row.name;

            const initials =
                this.getInitials(name);

            if (section === "expense_claims") {

                const amount =
                    row.total_claimed_amount != null
                    ? "₹ " + row.total_claimed_amount
                    : "";

                const expenseStatus =
                    row.approval_status || "Pending";

                html += `
                    <div class="hr-list-row">

                        <div class="hr-employee">

                            <div class="hr-avatar">
                                ${initials}
                            </div>

                            <div>

                                <div class="hr-employee-name">
                                    ${frappe.utils.escape_html(name)}
                                </div>

                                <div class="hr-employee-meta">

                                    Expense Claim:
                                    ${frappe.utils.escape_html(row.name || "")}

                                    &nbsp; • &nbsp;

                                    ${row.posting_date || ""}

                                    ${amount ? " • " + amount : ""}

                                </div>

                            </div>

                        </div>

                        <div class="hr-status">
                            ${frappe.utils.escape_html(expenseStatus)}
                        </div>

                    </div>
                `;

            } else if (section === "leave_applications") {

                const leaveStatus =
                    row.status || "Pending";

                const leaveDays =
                    row.total_leave_days
                    ? row.total_leave_days + " day(s)"
                    : "";

                html += `
                    <div class="hr-list-row">

                        <div class="hr-employee">

                            <div class="hr-avatar">
                                ${initials}
                            </div>

                            <div>

                                <div class="hr-employee-name">
                                    ${frappe.utils.escape_html(name)}
                                </div>

                                <div class="hr-employee-meta">

                                    ${frappe.utils.escape_html(
                                        row.leave_type || "Leave"
                                    )}

                                    &nbsp; • &nbsp;

                                    ${row.from_date || ""}

                                    ${row.to_date ? " → " + row.to_date : ""}

                                    ${leaveDays ? " • " + leaveDays : ""}

                                </div>

                            </div>

                        </div>

                        <div class="hr-status">
                            ${frappe.utils.escape_html(leaveStatus)}
                        </div>

                    </div>
                `;

            } else if (isTimesheet) {

                html += `
                    <div
                        class="hr-list-row hr-timesheet-row"
                        data-timesheet="${frappe.utils.escape_html(row.name)}"
                    >

                        <div class="hr-employee">

                            <div class="hr-avatar">
                                ${initials}
                            </div>

                            <div>

                                <div class="hr-employee-name">
                                    ${frappe.utils.escape_html(name)}
                                </div>

                                <div class="hr-employee-meta">
                                    Timesheet:
                                    ${frappe.utils.escape_html(row.name)}
                                    &nbsp; • &nbsp;
                                    ${row.start_date || ""}
                                </div>

                            </div>

                        </div>

                        <div class="hr-timesheet-open">
                            Open
                            <i class="fa fa-angle-right"></i>
                        </div>

                    </div>
                `;

            } else {

                let meta = "";

                if (row.department) {
                    meta += frappe.utils.escape_html(
                        row.department
                    );
                }

                if (row.designation) {

                    if (meta) {
                        meta += " • ";
                    }

                    meta += frappe.utils.escape_html(
                        row.designation
                    );
                }

                if (row.attendance_date) {

                    if (meta) {
                        meta += " • ";
                    }

                    meta += row.attendance_date;
                }

                html += `
                    <div class="hr-list-row">

                        <div class="hr-employee">

                            <div class="hr-avatar">
                                ${initials}
                            </div>

                            <div>

                                <div class="hr-employee-name">
                                    ${frappe.utils.escape_html(name)}
                                </div>

                                <div class="hr-employee-meta">
                                    ${meta || "Employee"}
                                </div>

                            </div>

                        </div>

                        <div class="hr-status">
                            ${
                                section === "active"
                                    ? "Active"
                                    : ""
                            }

                            ${
                                section === "present"
                                    ? "Present"
                                    : ""
                            }

                            ${
                                section === "absent"
                                    ? "Absent"
                                    : ""
                            }

                            ${
                                section === "on_leave"
                                    ? "On Leave"
                                    : ""
                            }
                            ${
                                section === "work_from_home"
                                    ? "Work From Home"
                                    : ""
                            }
                            ${
                                section === "leave_applications"
                                    ? frappe.utils.escape_html(
                                        row.status || "Pending"
                                    )
                                    : ""
                            }
                        </div>

                    </div>
                `;
            }
        });

        html += `</div>`;

        this.$main
            .find("#hr-content")
            .html(html);

        if (isTimesheet) {

            this.$main
                .find(".hr-timesheet-row")
                .on("click", function () {

                    const timesheet =
                        $(this).data("timesheet");

                    frappe.set_route(
                        "Form",
                        "Timesheet",
                        timesheet
                    );
                });
        }
    }
}