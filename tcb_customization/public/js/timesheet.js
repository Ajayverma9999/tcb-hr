frappe.ui.form.on('Timesheet', {
    onload: function(frm) {
        if (!frm.doc.employee) {
            frappe.call({
                method: 'frappe.client.get_list',
                args: {
                    doctype: 'Employee',
                    filters: { user_id: frappe.session.user, status: 'Active' },
                    fields: ['name'],
                    limit_page_length: 1
                },
                callback: function(r) {
                    if (r.message && r.message.length) {
                        frm.set_value('employee', r.message[0].name);
                    }
                }
            });
        }
    },

    refresh: function(frm) {
        // Ensure description column is visible in the time_logs grid
        if (frm.fields_dict && frm.fields_dict['time_logs'] && frm.fields_dict['time_logs'].grid) {
            try {
                frm.fields_dict['time_logs'].grid.update_docfield_property('description', 'hidden', 0);
                frm.fields_dict['time_logs'].grid.update_docfield_property('description', 'read_only', 0);
            } catch (e) {
                // ignore if field missing
            }
        }
    },

    validate: function(frm) {
        var missing = [];
        (frm.doc.time_logs || []).forEach(function(row, i) {
            if (!row.description || !row.description.toString().trim()) {
                missing.push(i + 1);
            }
        });

        if (missing.length) {
            frappe.msgprint(__('Each Timesheet row must have a description. Missing in rows: ') + missing.join(', '));
            frappe.validated = false;
        }
    }
});
