frappe.pages['hr-console'] = frappe.pages['hr-console'] || {};

frappe.pages['hr-console'].on_page_load = function(wrapper) {
    const page = frappe.ui.make_app_page({parent: wrapper, title: 'HR Console', single_column: false});

    const statsBar = $("<div class='hr-stats' style='display:flex; gap:16px; padding:0 18px 18px 18px;'></div>");
    const headcountCard = $(`<div class='stat-card' style='flex:1; padding:14px 18px; border:1px solid #eee; border-radius:8px; background:#fafafa;'><div style='font-size:12px; color:#888;'>Active Headcount</div><div style='font-size:24px; font-weight:700;' id='stat-headcount'>—</div></div>`);
    const pendingCard = $(`<div class='stat-card' style='flex:1; padding:14px 18px; border:1px solid #eee; border-radius:8px; background:#fff8e6;'><div style='font-size:12px; color:#888;'>Pending Attendance Reviews</div><div style='font-size:24px; font-weight:700;' id='stat-pending'>—</div></div>`);
    statsBar.append(headcountCard).append(pendingCard);
    page.main.append(statsBar);

    frappe.call({
        method: 'tcb_customization.api.hr_console.get_overview',
        callback: function(r) {
            const data = r.message || {};
            $('#stat-headcount').text(data.headcount !== undefined ? data.headcount : '—');
            $('#stat-pending').text(data.pending_attendance_reviews !== undefined ? data.pending_attendance_reviews : '—');
        }
    });

    const content = $("<div class='hr-console row' style='padding:18px;'></div>");
    page.main.append(content);

    const left = $("<div class='col-md-4 hr-left'><div class='hr-actions'></div><div class='hr-list' style='margin-top:12px'></div></div>");
    const right = $("<div class='col-md-8 hr-right'><div class='hr-overview'><p>Loading...</p></div></div>");
    content.append(left).append(right);

    const actions = left.find('.hr-actions');
    const setupBtn = $(`<button class='btn btn-primary'>Setup Roles & Permissions</button>`);
    setupBtn.on('click', function() {
        frappe.confirm('Requires System Manager. Continue?', function() {
            frappe.call({method: 'tcb_customization.api.roles.run_ensure_roles', callback: r => frappe.msgprint(JSON.stringify(r.message))});
            frappe.call({method: 'tcb_customization.api.permissions.apply_attendance_permissions', callback: r => frappe.msgprint(JSON.stringify(r.message))});
        });
    });
    const refreshBtn = $(`<button class='btn btn-default' style='margin-left:8px'>Refresh</button>`);
    refreshBtn.on('click', function() { loadEmployees(0); });
    actions.append(setupBtn).append(refreshBtn);
    const reviewBtn = $(`<button class='btn btn-warning' style='margin-left:8px'>Open Attendance Review Queue</button>`);
    reviewBtn.on('click', openReviewQueue);
    actions.append(reviewBtn);

    const list = left.find('.hr-list');
    // filters
    const filterBar = $(`<div style='margin-top:8px; display:flex; gap:8px; align-items:center'></div>`);
    const searchInput = $(`<input class='form-control' placeholder='Search employee name or ID' style='flex:1'/>`);
    const deptSelect = $(`<select class='form-control' style='width:180px'><option value=''>All Departments</option></select>`);
    filterBar.append(searchInput).append(deptSelect);
    left.find('.hr-actions').after(filterBar);

    let currentPage = 0;
    const pageSize = 50;
    const pager = $(`<div style='margin-top:8px; display:flex; gap:8px; align-items:center'><button class='btn btn-default' id='prev-page'>Prev</button><span id='page-info'>Page 1</span><button class='btn btn-default' id='next-page'>Next</button></div>`);
    list.after(pager);
    const detail = right.find('.hr-overview');

    function loadEmployees(page = 0) {
        currentPage = page;
        const start = page * pageSize;
        list.html('<p>Loading employees...</p>');
        const search = searchInput.val() || '';
        const dept = deptSelect.val() || '';
        frappe.call({
            method: 'tcb_customization.api.hr_console.get_employee_list',
            args: {start: start, limit: pageSize, search: search, department: dept},
            callback: function(r) {
                list.empty();
                const rows = r.message || [];
                if (!rows.length) {
                    list.html('<p>No employees found.</p>');
                    $('#page-info').text(`Page ${currentPage+1}`);
                    return;
                }
                rows.forEach(emp => {
                    const row = $(`<div class='employee-row' style='padding:6px; border-bottom:1px solid #eee; cursor:pointer;'><strong>${emp.employee_name}</strong><div style='font-size:12px;color:#666'>${emp.designation || ''} — ${emp.department || ''}</div></div>`);
                    row.on('click', () => loadEmployeeDetail(emp.name, emp.employee_name));
                    list.append(row);
                });
                $('#page-info').text(`Page ${currentPage+1}`);
            }
        });
    }

    function loadEmployeeDetail(employee, label) {
        detail.html('<p>Loading employee detail...</p>');
        const now = new Date();
        const from = new Date(now.getFullYear(), now.getMonth(), 1);
        const to = new Date(now.getFullYear(), now.getMonth() + 1, 0);
        const from_s = from.toISOString().slice(0,10);
        const to_s = to.toISOString().slice(0,10);

        frappe.call({method: 'tcb_customization.api.hr_console.get_employee_detail', args: {employee: employee, from_date: from_s, to_date: to_s}, callback: function(r) {
            detail.empty();
            detail.append(`<h4>${label}</h4>`);
            const att = r.message.attendance || [];
            const attMap = {};
            att.forEach(a => { attMap[a.attendance_date] = a.status; });

            const table = $('<table class="table table-condensed" style="width:100%"><thead><tr><th>Date</th><th>Status</th></tr></thead><tbody></tbody></table>');
            const tbody = table.find('tbody');
            let cur = new Date(from);
            while (cur <= to) {
                const d = cur.toISOString().slice(0,10);
                const status = attMap[d] || 'Pending';
                tbody.append(`<tr><td>${d}</td><td>${status}</td></tr>`);
                cur.setDate(cur.getDate()+1);
            }
            detail.append('<h5>Attendance (month)</h5>');
            detail.append(table);

            // Calendar toggle
            const calBtn = $(`<button class='btn btn-default' style='margin-top:8px; margin-bottom:8px'>Toggle Calendar View</button>`);
            detail.prepend(calBtn);
            let calShown = false;
            calBtn.on('click', function() {
                calShown = !calShown;
                if (calShown) {
                    const cal = renderCalendar(from, to, attMap);
                    table.hide();
                    detail.append(cal);
                    calBtn.text('Hide Calendar');
                } else {
                    detail.find('.hr-calendar').remove();
                    table.show();
                    calBtn.text('Toggle Calendar View');
                }
            });

            detail.append('<h5 style="margin-top:12px">Salary Slips</h5>');
            const slips = r.message.salary_slips || [];
            if (slips.length === 0) {
                detail.append('<div>No salary slips for this period.</div>');
            } else {
                const slipList = $('<ul></ul>');
                slips.forEach(s => slipList.append(`<li>${s.name}: ${s.start_date} → ${s.end_date} — Net: ${s.net_pay}</li>`));
                detail.append(slipList);
            }
        }});
    }

    function renderCalendar(from, to, attMap) {
        const container = $('<div class="hr-calendar" style="margin-top:8px"></div>');
        let cur = new Date(from);
        const end = new Date(to);
        const table = $('<table class="table table-bordered" style="width:100%"><thead></thead><tbody></tbody></table>');
        const tbody = table.find('tbody');
        // simple week rows
        let week = $('<tr></tr>');
        // align start to weekday
        const startWeekday = cur.getDay();
        for (let i=0;i<startWeekday;i++) week.append('<td></td>');
        while (cur <= end) {
            const d = cur.toISOString().slice(0,10);
            const status = attMap[d] || 'Pending';
            const cell = $(`<td style='min-width:80px; vertical-align:top'><div style='font-size:12px'>${d}</div><div style='font-weight:600'>${status}</div></td>`);
            week.append(cell);
            if (week.find('td').length >= 7) {
                tbody.append(week);
                week = $('<tr></tr>');
            }
            cur.setDate(cur.getDate()+1);
        }
        if (week.find('td').length) tbody.append(week);
        container.append(table);
        return container;
    }

    // pagination handlers
    pager.find('#prev-page').on('click', function() { if (currentPage>0) loadEmployees(currentPage-1); });
    pager.find('#next-page').on('click', function() { loadEmployees(currentPage+1); });

    // debounce search
    let searchTimer = null;
    searchInput.on('input', function() {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(() => loadEmployees(0), 350);
    });
    deptSelect.on('change', function() { loadEmployees(0); });

    // load departments for filter
    frappe.call({method: 'tcb_customization.api.hr_console.get_departments', callback: function(r) {
        const depts = r.message || [];
        depts.forEach(d => deptSelect.append(`<option value='${d}'>${d}</option>`));
    }});

    loadEmployees();
}

function openReviewQueue() {
    const modal = new frappe.ui.Dialog({
        title: 'Attendance Review Queue',
        width: 800,
        fields: [
            {fieldname: 'rows_html', fieldtype: 'HTML'},
            {fieldname: 'action', fieldtype: 'Select', options: 'accept\nreject', label: 'Action'},
            {fieldname: 'reason', fieldtype: 'Small Text', label: 'Reason (required for reject)'},
            {fieldname: 'submit', fieldtype: 'Button', label: 'Process'}
        ]
    });

    const $rows = $('<div style="max-height:400px; overflow:auto"></div>');

    // controls: from/to/company
    const controls = $(`<div style='display:flex; gap:8px; align-items:center; margin-bottom:8px'></div>`);
    const fromInput = $(`<input type='date' class='form-control' style='width:150px'/>`);
    const toInput = $(`<input type='date' class='form-control' style='width:150px'/>`);
    const companySelect = $(`<select class='form-control' style='width:200px'><option value=''>All Companies</option></select>`);
    controls.append('<div style="font-size:12px; color:#666">From</div>').append(fromInput).append('<div style="font-size:12px; color:#666">To</div>').append(toInput).append(companySelect);

    modal.set_value('rows_html', $('<div></div>').append(controls).append($rows));

    modal.show();

    modal.get_field('action').$input.on('change', function() {
        const v = $(this).val();
        if (v === 'reject') {
            modal.get_field('reason').toggle(true);
        } else {
            modal.get_field('reason').toggle(false);
        }
    });

    // default dates = yesterday
    const yd = new Date(); yd.setDate(yd.getDate()-1);
    const yd_s = yd.toISOString().slice(0,10);
    fromInput.val(yd_s); toInput.val(yd_s);

    // load companies
    frappe.call({method: 'tcb_customization.api.hr_console.get_companies', callback: function(r) {
        const comps = r.message || [];
        comps.forEach(c => companySelect.append(`<option value='${c}'>${c}</option>`));
    }});

    let rows = [];

    function fetchAndRender() {
        const from = fromInput.val();
        const to = toInput.val();
        const company = companySelect.val();
        $rows.html('<div>Loading...</div>');
        frappe.call({method: 'tcb_customization.api.hr_console.get_pending_reviews', args: {from_date: from, to_date: to}, callback: function(r) {
            rows = r.message || [];
            if (company) rows = rows.filter(x => x.company === company);
            if (rows.length === 0) {
                $rows.html('<div>No pending attendance reviews.</div>');
                return;
            }
            const table = $('<table class="table table-condensed" style="width:100%"><thead><tr><th><input type="checkbox" id="select_all_rows"></th><th>Employee</th><th>Date</th><th>Company</th></tr></thead><tbody></tbody></table>');
            const tbody = table.find('tbody');
            rows.forEach(function(rr, idx) {
                const id = 'r_' + idx;
                const tr = $(`<tr><td><input type='checkbox' data-idx='${idx}' id='${id}'></td><td>${rr.employee_name} (${rr.employee})</td><td>${rr.date}</td><td>${rr.company}</td></tr>`);
                tbody.append(tr);
            });
            $rows.empty().append(table);

            // select-all handler
            $rows.find('#select_all_rows').on('change', function() {
                const checked = $(this).is(':checked');
                $rows.find('input[type=checkbox]').prop('checked', checked);
            });

            modal.get_field('submit').$input.off('click').on('click', function() {
                const action = modal.get_value('action');
                const reason = modal.get_value('reason');
                const selected = [];
                $rows.find('input[type=checkbox]:checked').each(function() {
                    const idx = $(this).data('idx');
                    selected.push(rows[idx]);
                });
                if (!selected.length) { frappe.msgprint('Select at least one row'); return; }
                if (action === 'reject' && !reason) { frappe.msgprint('Reason is required for reject'); return; }

                const payload = selected.map(s => ({employee: s.employee, date: s.date, action: action, reason: reason}));
                frappe.call({method: 'tcb_customization.api.hr_console.bulk_review', args: {data: JSON.stringify({rows: payload})}, callback: function(res) {
                    frappe.msgprint('Bulk review submitted: ' + JSON.stringify(res.message));
                    modal.hide();
                }});
            });

            // ensure undo button wired
            modal.wrapper.find('.dialog-footer').find('.btn-undo').remove();
            const undoBtn = $(`<button class='btn btn-default btn-undo' style='margin-left:8px'>Undo Selected</button>`);
            modal.wrapper.find('.dialog-footer').prepend(undoBtn);
            undoBtn.off('click').on('click', function() {
                const selected = [];
                $rows.find('input[type=checkbox]:checked').each(function() {
                    const idx = $(this).data('idx');
                    selected.push(rows[idx]);
                });
                if (!selected.length) { frappe.msgprint('Select at least one row to undo'); return; }
                frappe.confirm('Cancel submitted Attendance for selected rows? This cannot be undone.', function() {
                    const results = [];
                    const promises = selected.map(s => new Promise((resolve) => {
                        frappe.call({method: 'tcb_customization.api.attendance_job.undo_attendance', args: {employee: s.employee, date: s.date}, callback: function(r) {
                            results.push({row: s, result: r.message});
                            resolve();
                        }, error: function(e) { results.push({row: s, error: e}); resolve(); }});
                    }));
                    Promise.all(promises).then(() => {
                        frappe.msgprint('Undo completed: ' + JSON.stringify(results));
                        modal.hide();
                    });
                });
            });
        }});
    }

    fromInput.on('change', fetchAndRender);
    toInput.on('change', fetchAndRender);
    companySelect.on('change', fetchAndRender);

    fetchAndRender();
}
