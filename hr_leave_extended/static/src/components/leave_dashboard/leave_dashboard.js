import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, useState } from "@odoo/owl";

export class LeaveDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            pendingApprovals: [],
            teamBalances: [],
            upcomingLeaves: []
        });

        onWillStart(async () => {
            await this.fetchDashboardData();
        });
    }

    async fetchDashboardData() {
        // Fetch pending leaves
        const pendingLeaves = await this.orm.searchRead('hr.leave',
            [['state', '=', 'confirm']],
            ['employee_id', 'date_from', 'date_to', 'number_of_days', 'holiday_status_id']
        );

        // Fetch team balances 
        // Note: For simplicity we fetch leave allocation vs taken data
        // Odoo 17/18 has hr.leave.report but we can fetch allocations and leaves
        // Or simply display employees
        const employees = await this.orm.searchRead('hr.employee',
            [['parent_id', '!=', false]], // team members
            ['name']
        );

        this.state.pendingApprovals = pendingLeaves;
        this.state.teamBalances = employees; // Simplified for display
    }

    openLeave(id) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "hr.leave",
            res_id: id,
            views: [[false, "form"]],
            target: "current",
        });
    }
}

LeaveDashboard.template = "hr_leave_extended.LeaveDashboard";

registry.category("actions").add("hr_leave_extended.dashboard", LeaveDashboard);
