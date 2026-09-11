frappe.pages["attendance-leave-das"].on_page_load = function (wrapper) {
    new AttendanceLeaveDashboard(wrapper);
};

class AttendanceLeaveDashboard {
    constructor(wrapper) {
        this.page = frappe.ui.make_app_page({
            parent: wrapper,
            title: "Attendance & Leave Dashboard",
            single_column: true
        });

        this.year = new Date().getFullYear();
        this.month = new Date().getMonth() + 1;

        this.make();
        this.load_employees();
    }

    make() {
        this.page.main.html(`
            <div class="attendance-leave-dashboard">

                <div class="ald-header">
                    <div>
                        <h2>Attendance & Leave Dashboard</h2>
                        <div class="ald-subtitle">
                            Employee Attendance & Leave Overview
                        </div>
                    </div>

                    <div class="ald-filters">
                        <div class="employee-filter"></div>
                    </div>
                </div>

                <div class="employee-info"></div>

                <div class="ald-layout">

                    <div class="calendar-card">

                        <div class="calendar-header">
                            <button class="btn btn-default prev-month">‹</button>

                            <h3 class="month-title"></h3>

                            <button class="btn btn-default next-month">›</button>
                        </div>

                        <div class="calendar-grid weekdays">
                            <div>Mon</div>
                            <div>Tue</div>
                            <div>Wed</div>
                            <div>Thu</div>
                            <div>Fri</div>
                            <div>Sat</div>
                            <div>Sun</div>
                        </div>

                        <div class="calendar-grid calendar-days"></div>

                        <div class="legend">
                            <span><b class="legend-present"></b> Present</span>
                            <span><b class="legend-absent"></b> Absent</span>
                            <span><b class="legend-leave"></b> Leave</span>
                            <span><b class="legend-weekend"></b> Weekend</span>
                        </div>

                    </div>

                    <div class="balance-card">
                        <h3>Leave Balance</h3>
                        <div class="balance-list"></div>
                    </div>

                </div>
            </div>
        `);

        this.setup_employee_filter();

        this.page.main.find(".prev-month").on("click", () => {
            this.change_month(-1);
        });

        this.page.main.find(".next-month").on("click", () => {
            this.change_month(1);
        });
    }

    setup_employee_filter() {
        this.employee_control = frappe.ui.form.make_control({
            parent: this.page.main.find(".employee-filter"),
            df: {
                fieldtype: "Select",
                label: "Employee",
                fieldname: "employee",
                options: []
            },
            render_input: true
        });

        this.employee_control.$input.on("change", () => {
            const value = this.employee_control.get_value();

            if (!value) return;

            this.selected_employee = value.split(" - ")[0];
            this.load_dashboard();
        });
    }

    load_employees() {
        frappe.call({
            method:
                "tcb_customization.tcb.api.attendance-leave-das.get_employees",

            callback: (r) => {
                const employees = r.message || [];

                const options = employees.map(
                    e => `${e.name} - ${e.employee_name}`
                );

                this.employee_control.df.options = options;
                this.employee_control.refresh();

                if (employees.length) {
                    this.selected_employee = employees[0].name;

                    this.employee_control.set_value(
                        options[0]
                    );

                    this.load_dashboard();
                }
            }
        });
    }

    load_dashboard() {
        frappe.call({
            method:
                "tcb_customization.tcb.api.attendance-leave-das.get_dashboard_data",

            args: {
                employee: this.selected_employee,
                year: this.year,
                month: this.month
            },

            freeze: true,
            freeze_message: "Loading attendance...",

            callback: (r) => {
                if (r.message) {
                    this.render(r.message);
                }
            }
        });
    }

    change_month(direction) {
        this.month += direction;

        if (this.month > 12) {
            this.month = 1;
            this.year++;
        }

        if (this.month < 1) {
            this.month = 12;
            this.year--;
        }

        this.load_dashboard();
    }

    render(data) {
        this.page.main.find(".month-title").text(
            `${data.month_name} ${data.year}`
        );

        this.page.main.find(".employee-info").html(`
            <div class="employee-name">
                ${data.employee_name || ""}
            </div>

            <div class="employee-details">
                ${data.employee || ""}
                ${data.department ? " • " + data.department : ""}
                ${data.designation ? " • " + data.designation : ""}
            </div>
        `);

        this.render_calendar(data);
        this.render_balance(data.leave_balance || []);
    }

    render_calendar(data) {
        const container = this.page.main.find(".calendar-days");
        container.empty();

        const firstDay = new Date(
            data.year,
            data.month - 1,
            1
        );

        let start = firstDay.getDay();
        start = start === 0 ? 6 : start - 1;

        for (let i = 0; i < start; i++) {
            container.append(
                `<div class="calendar-cell empty"></div>`
            );
        }

        data.calendar.forEach(day => {
            const date = new Date(
                data.year,
                data.month - 1,
                day.day
            );

            const weekday = date.getDay();

            let css = "calendar-cell";

            if (day.status === "Present") {
                css += " present";
            } else if (day.status === "Absent") {
                css += " absent";
            } else if (day.status === "Leave") {
                css += " leave";
            } else if (weekday === 0 || weekday === 6) {
                css += " weekend";
            }

            const label = day.short_code || "";

            container.append(`
                <div class="${css}">
                    <div class="date-number">${day.day}</div>
                    <div class="status-code">${label}</div>
                </div>
            `);
        });
    }

    render_balance(balances) {
        const container = this.page.main.find(".balance-list");
        container.empty();

        if (!balances.length) {
            container.html(
                `<div class="no-balance">No leave balance found</div>`
            );
            return;
        }

        balances.forEach(row => {
            container.append(`
                <div class="balance-row">
                    <div>
                        <span class="balance-code">
                            ${row.short_code}
                        </span>
                        <span>${row.leave_type}</span>
                    </div>

                    <strong>${row.balance}</strong>
                </div>
            `);
        });
    }
}
