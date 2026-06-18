/** @odoo-module */
import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";

export class ExpensePage extends Component {
    static template = "owl_self_service.ExpensePage";
    static props = {};

    setup() {
        this.rpc = rpc;
        this.notification = useService("notification");

        this.state = useState({
            loading: true,
            employeeFound: true,
            records: [],
            currentPage: 1,
            totalPages: 1,
            filterby: "all",
            sortby: "date",
            dateFrom: "",
            dateTo: "",
            showModal: false,
            modalMode: "create",
            editingId: null,
            modalLoading: false,
            products: [],
            form: {
                name: "",
                product_id: "",
                total_amount: "",
                expense_date: "",
                description: "",
            },
            formErrors: {},
            confirmDialog: { show: false, title: "", message: "", loading: false },
        });

        onWillStart(() => this._loadData());
    }

    // ── Confirm dialog ─────────────────────────────────────

    _confirm(title, message) {
        return new Promise((resolve) => {
            this.state.confirmDialog = { show: true, title, message, loading: false, _resolve: resolve };
        });
    }

    async onConfirmOk() {
        const d = this.state.confirmDialog;
        if (d._resolve) d._resolve(true);
        this.state.confirmDialog = { show: false, title: "", message: "", loading: false };
    }

    onConfirmCancel() {
        const d = this.state.confirmDialog;
        if (d._resolve) d._resolve(false);
        this.state.confirmDialog = { show: false, title: "", message: "", loading: false };
    }

    // ── Data ───────────────────────────────────────────────

    async _loadData(page = 1) {
        this.state.loading = true;
        try {
            const params = {
                page,
                limit: 10,
                filterby: this.state.filterby,
                sortby: this.state.sortby,
                date_from: this.state.dateFrom || false,
                date_to: this.state.dateTo || false,
            };
            const data = await this.rpc("/ess/expense/list", params);
            if (data.error === "no_employee") {
                this.state.employeeFound = false;
                return;
            }
            this.state.records = data.records;
            this.state.currentPage = page;
            this.state.totalPages = Math.ceil(data.total / 10) || 1;
        } finally {
            this.state.loading = false;
        }
    }

    async _loadProducts() {
        if (this.state.products.length) return;
        const products = await this.rpc("/ess/expense/products");
        this.state.products = products;
    }

    // ── Filter / sort actions ──────────────────────────────

    async onFilterChange(ev) {
        this.state.filterby = ev.target.value;
        await this._loadData(1);
    }

    async onSortChange(ev) {
        this.state.sortby = ev.target.value;
        await this._loadData(1);
    }

    async onDateFromChange(ev) {
        this.state.dateFrom = ev.target.value;
        await this._loadData(1);
    }

    async onDateToChange(ev) {
        this.state.dateTo = ev.target.value;
        await this._loadData(1);
    }

    async onPageChange(page) {
        if (page < 1 || page > this.state.totalPages) return;
        await this._loadData(page);
    }

    // ── Modal ──────────────────────────────────────────────

    async openModal() {
        await this._loadProducts();
        this.state.modalMode = "create";
        this.state.editingId = null;
        this.state.form = {
            name: "",
            product_id: this.state.products[0]?.id || "",
            total_amount: "",
            expense_date: new Date().toISOString().slice(0, 10),
            description: "",
        };
        this.state.formErrors = {};
        this.state.showModal = true;
    }

    async openEditModal(row) {
        await this._loadProducts();
        this.state.modalMode = "edit";
        this.state.editingId = row.id;
        this.state.form = {
            name: row.name || "",
            product_id: row.product_id || (this.state.products[0]?.id || ""),
            total_amount: String(row.total_amount || ""),
            expense_date: row.date || new Date().toISOString().slice(0, 10),
            description: row.description || "",
        };
        this.state.formErrors = {};
        this.state.showModal = true;
    }

    closeModal() {
        this.state.showModal = false;
    }

    async onDelete(sheetId) {
        const ok = await this._confirm("Delete Expense", "Are you sure you want to delete this expense? This action cannot be undone.");
        if (!ok) return;
        try {
            const result = await this.rpc("/ess/expense/delete", { sheet_id: sheetId });
            if (result.error) {
                this.notification.add(result.error, { title: "Error", type: "danger" });
                return;
            }
            this.notification.add("Expense deleted.", { type: "success" });
            await this._loadData(this.state.currentPage);
        } catch {
            this.notification.add("Failed to delete expense.", { type: "danger" });
        }
    }

    onFormInput(field) {
        return (ev) => {
            this.state.form[field] = ev.target.value;
            if (this.state.formErrors[field]) {
                delete this.state.formErrors[field];
            }
        };
    }

    _validateForm() {
        const errors = {};
        if (!this.state.form.name.trim()) errors.name = "Required";
        if (!this.state.form.product_id) errors.product_id = "Required";
        const amt = parseFloat(this.state.form.total_amount);
        if (!this.state.form.total_amount || isNaN(amt) || amt <= 0) {
            errors.total_amount = "Must be a positive number";
        }
        if (!this.state.form.expense_date) errors.expense_date = "Required";
        return errors;
    }

    async onSubmitForm() {
        const errors = this._validateForm();
        if (Object.keys(errors).length) {
            this.state.formErrors = errors;
            return;
        }
        this.state.modalLoading = true;
        try {
            const f = this.state.form;
            const isEdit = this.state.modalMode === "edit";
            const endpoint = isEdit ? "/ess/expense/update" : "/ess/expense/create";
            const params = {
                name: f.name.trim(),
                product_id: f.product_id,
                total_amount: parseFloat(f.total_amount),
                expense_date: f.expense_date,
                description: f.description.trim(),
            };
            if (isEdit) params.sheet_id = this.state.editingId;

            const result = await this.rpc(endpoint, params);
            if (result.error) {
                this.state.formErrors._server = result.error;
                return;
            }
            this.notification.add(
                isEdit ? "Expense updated successfully." : "Expense submitted successfully.",
                { type: "success" }
            );
            this.state.showModal = false;
            await this._loadData(isEdit ? this.state.currentPage : 1);
        } catch (e) {
            this.state.formErrors._server = e.message || "An error occurred.";
        } finally {
            this.state.modalLoading = false;
        }
    }

    // ── Computed ───────────────────────────────────────────

    get isFilterActive() {
        return this.state.filterby !== "all"
            || this.state.sortby !== "date"
            || !!this.state.dateFrom
            || !!this.state.dateTo;
    }

    async onResetFilter() {
        this.state.filterby = "all";
        this.state.sortby = "date";
        this.state.dateFrom = "";
        this.state.dateTo = "";
        await this._loadData(1);
    }

    formatAmount(amount, symbol) {
        return `${symbol}${Number(amount).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }
}
