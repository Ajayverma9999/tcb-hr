frappe.pages["employee-attendance"].on_page_load = function (wrapper) {
    new MyAttendance(wrapper);
};

class MyAttendance {
    constructor(wrapper) {
        this.page = frappe.ui.make_app_page({
            parent: wrapper,
            title: "My Attendance",
            single_column: true
        });

        const now = new Date();
        this.year = now.getFullYear();
        this.month = now.getMonth() + 1;

        this.render();
        this.render_basic_calendar();
        this.load_data();
    }

    render() {
        $(this.page.body).html(`
            <div class="my-attendance">


                <div class="employee-card">

                    <div>
                        <h2 id="employee-name">Loading...</h2>
                        <div id="employee-meta"></div>
                        <div id="employee-id"></div>
                    </div>
                </div>

                <div class="attendance-layout">

                    <div class="calendar-card">

                        <div class="calendar-header">
                            <button class="month-btn prev-month">
                                <i class="fa fa-chevron-left"></i>
                            </button>

                            <h2 class="month-title">Loading...</h2>

                            <button class="month-btn next-month">
                                <i class="fa fa-chevron-right"></i>
                            </button>
                        </div>

                        <div class="weekdays">
                            <div>Sun</div>
                            <div>Mon</div>
                            <div>Tue</div>
                            <div>Wed</div>
                            <div>Thu</div>
                            <div>Fri</div>
                            <div>Sat</div>
                        </div>

                        <div class="calendar-grid">
                            <div class="loading">Loading attendance...</div>
                        </div>

                        <div class="legend">
                            <span>
                                <i class="dot present"></i>
                                Present
                            </span>

                            <span>
                                <i class="dot absent"></i>
                                Absent
                            </span>

                            <span>
                                <i class="dot leave"></i>
                                Leave (CL/SL/LWP)
                            </span>

                            <span>
                                <i class="dot norecord"></i>
                                No Record
                            </span>
                        </div>

                    </div>

                    <div class="leave-card">

                        <div class="leave-heading">
                            <i class="fa fa-calendar"></i>
                            <h2>Leave Balance</h2>
                        </div>

                        <div class="leave-list">
                            <div class="loading">
                                Loading...
                            </div>
                        </div>

                    </div>

                </div>

                <div class="attendance-note">
                    <i class="fa fa-info-circle"></i>
                    <span>
                        <b>Note:</b>
                        Attendance is updated based on approved records.
                        For any discrepancy, please contact HR.
                    </span>
                </div>

            </div>
        `);

        $(this.page.body).find(".prev-month").on("click", () => {
            this.change_month(-1);
        });

        $(this.page.body).find(".next-month").on("click", () => {
            this.change_month(1);
        });
    }

    change_month(value) {
        this.month += value;

        if (this.month > 12) {
            this.month = 1;
            this.year++;
        }

        if (this.month < 1) {
            this.month = 12;
            this.year--;
        }

        this.load_data();
    }

    render_basic_calendar() {
        const daysInMonth = new Date(
            this.year,
            this.month,
            0
        ).getDate();

        const firstDay = new Date(
            this.year,
            this.month - 1,
            1
        ).getDay();

        let html = "";

        for (let i = 0; i < firstDay; i++) {
            html += `<div class="calendar-day empty"></div>`;
        }

        for (let day = 1; day <= daysInMonth; day++) {
            html += `
                <div class="calendar-day norecord">
                    <span class="day-number">${day}</span>
                </div>
            `;
        }

        $(".calendar-grid").html(html);

        const monthNames = [
            "January", "February", "March", "April",
            "May", "June", "July", "August",
            "September", "October", "November", "December"
        ];

        $(".month-title").text(
            `${monthNames[this.month - 1]} ${this.year}`
        );
    }

    load_data() {
        $(".month-title").text("Loading...");

        frappe.call({
            method:
                "tcb_customization.tcb.api.my_attendance.get_my_attendance",

            args: {
                year: this.year,
                month: this.month
            },

            callback: (r) => {
                if (!r.message) {
                    return;
                }

                this.data = r.message;

                this.render_employee();
                this.render_calendar();
                this.render_leave_balance();
            },

            error: () => {
                $(".calendar-grid").html(`
                    <div class="loading">
                        Unable to load attendance.
                    </div>
                `);
            }
        });
    }

    render_employee() {
        const d = this.data;

        const initials = (d.employee_name || "Employee")
            .split(" ")
            .map(x => x.charAt(0))
            .slice(0, 2)
            .join("")
            .toUpperCase();

        $("#employee-name").text(d.employee_name);

        $("#employee-meta").text(
            `${d.department || "-"}  •  ${d.designation || "-"}`
        );

        $("#employee-id").text(
            `Employee ID: ${d.employee}`
        );

        $(".month-title").text(
            `${d.month_name} ${d.year}`
        );
    }

    render_calendar() {
        const d = this.data;
        const days = d.calendar || [];

        const firstDay = new Date(
            d.year,
            d.month - 1,
            1
        ).getDay();

        let html = "";

        for (let i = 0; i < firstDay; i++) {
            html += `<div class="calendar-day empty"></div>`;
        }

        days.forEach(day => {
            let cls = "norecord";
            let content = "";
            let title = "No Record";

            if (day.status === "Present") {
                cls = "present";
                content = `<span class="status-dot"></span>`;
                title = "Present";
            }

            if (day.status === "Absent") {
                cls = "absent";
                content = `<span class="status-dot"></span>`;
                title = "Absent";
            }

            if (day.status === "Leave") {
                cls = "leave";
                content = `
                    <span class="leave-code">
                        ${day.short_code || "L"}
                    </span>
                `;
                title = day.leave_type || "Leave";
            }

            html += `
                <div class="calendar-day ${cls}" title="${title}">
                    <span class="day-number">${day.day}</span>
                    ${content}
                </div>
            `;
        });

        $(".calendar-grid").html(html);
    }

    render_leave_balance() {
        const balances = this.data.leave_balance || [];

        if (!balances.length) {
            $(".leave-list").html(`
                <div class="loading">
                    No leave balance found.
                </div>
            `);
            return;
        }

        let html = "";

        balances.forEach(item => {
            html += `
                <div class="leave-row">

                    <div class="leave-code-box">
                        ${item.short_code || "LV"}
                    </div>

                    <div class="leave-details">
                        <div class="leave-name">
                            ${item.leave_type}
                        </div>

                        <div class="leave-subtitle">
                            days remaining
                        </div>
                    </div>

                    <div class="leave-count">
                        ${item.balance}
                    </div>

                </div>
            `;
        });

        $(".leave-list").html(html);
    }
}
