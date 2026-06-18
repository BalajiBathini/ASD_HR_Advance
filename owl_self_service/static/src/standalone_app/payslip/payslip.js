/** @odoo-module */
import { Component, useState, onWillStart } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";

export class PayslipPage extends Component {
    static template = "owl_self_service.PayslipPage";
    static props = {};

    setup() {
        this.rpc = rpc;

        this.state = useState({
            loading: true,
            records: [],
            total: 0,
            currentPage: 1,
            totalPages: 1,
            error: null,
        });

        onWillStart(() => this._loadPayslips(1));
    }

    async _loadPayslips(page = 1) {
        this.state.loading = true;
        this.state.error = null;
        try {
            const limit = 10;
            const data = await this.rpc("/ess/payslips/list", { page, limit });

            if (data.error) {
                this.state.error = data.error;
            } else {
                this.state.records = data.records;
                this.state.currentPage = page;
                this.state.totalPages = Math.ceil(data.total / limit) || 1;
                this.state.total = data.total;
            }
        } catch (e) {
            this.state.error = "Failed to load payslips. Please try again.";
        } finally {
            this.state.loading = false;
        }
    }

    async onPageChange(page) {
        if (page < 1 || page > this.state.totalPages) return;
        await this._loadPayslips(page);
    }

    downloadPdf(id) {
        window.open(`/ess/payslips/download/${id}`, "_blank");
    }
}
