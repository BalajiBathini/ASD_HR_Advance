/** @odoo-module */
import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";

export class ContractPage extends Component {
    static template = "owl_self_service.ContractPage";
    static props = {};

    setup() {
        this.rpc = rpc;

        this.state = useState({
            loading: true,
            employeeFound: true,
            contract: null,
        });

        onWillStart(() => this._loadContract());
    }

    async _loadContract() {
        this.state.loading = true;
        try {
            const data = await this.rpc("/ess/contract/active");
            if (data.error === "no_employee") {
                this.state.employeeFound = false;
                return;
            }
            this.state.contract = data.contract || null;
        } finally {
            this.state.loading = false;
        }
    }

    formatDate(dateStr) {
        if (!dateStr) return "—";
        return new Date(dateStr + "T00:00:00").toLocaleDateString([], {
            day: "numeric", month: "long", year: "numeric",
        });
    }

    formatWage(amount, symbol) {
        if (!amount) return "—";
        return `${symbol}${Number(amount).toLocaleString(undefined, {
            minimumFractionDigits: 0, maximumFractionDigits: 0,
        })}`;
    }
}
