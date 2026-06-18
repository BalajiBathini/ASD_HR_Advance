/** @odoo-module */
import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";

export class TimeOffPage extends Component {
    static template = "owl_self_service.TimeOffPage";
    static props = {};

    setup() {
        this.rpc = rpc;
        this.notification = useService("notification");

        const now = new Date();
        this.state = useState({
            loading: true,
            employeeFound: true,
            activeTab: "balance",
            balances: [],
            history: [],
            historyPage: 1,
            historyTotalPages: 1,
            showModal: false,
            modalLoading: false,
            leaveTypes: [],
            form: {
                holiday_status_id: "",
                date_from: "",
                date_to: "",
                description: "",
                attachment: null,       // File object
                attachmentName: "",
            },
            formErrors: {},
            // Calendar
            calView: "month",
            calYear: now.getFullYear(),
            calMonth: now.getMonth(),
            calDay: now.getDate(),
            calEvents: [],
            confirmDialog: { show: false, title: "", message: "", loading: false },
        });

        onWillStart(() => this._loadAll());
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

    async _loadAll() {
        this.state.loading = true;
        try {
            await Promise.all([
                this._loadBalance(),
                this._loadHistory(1),
                this._loadCalEvents(),
            ]);
        } finally {
            this.state.loading = false;
        }
    }

    async _loadBalance() {
        const data = await this.rpc("/ess/timeoff/balance");
        if (data.error === "no_employee") { this.state.employeeFound = false; return; }
        this.state.balances = data.balances;
    }

    async _loadHistory(page = 1) {
        const data = await this.rpc("/ess/timeoff/history", { page, limit: 10 });
        if (data.error === "no_employee") { this.state.employeeFound = false; return; }
        this.state.history = data.records;
        this.state.historyPage = page;
        this.state.historyTotalPages = Math.ceil(data.total / 10) || 1;
    }

    async _loadCalEvents() {
        const data = await this.rpc("/ess/timeoff/calendar_events");
        if (data.error) return;
        this.state.calEvents = data.events || [];
    }

    // ── Calendar: view ─────────────────────────────────────

    setCalView(view) { this.state.calView = view; }

    goToday() {
        const now = new Date();
        this.state.calYear = now.getFullYear();
        this.state.calMonth = now.getMonth();
        this.state.calDay = now.getDate();
    }

    calPrev() {
        if (this.state.calView === "month") {
            let m = this.state.calMonth - 1, y = this.state.calYear;
            if (m < 0) { m = 11; y--; }
            this.state.calMonth = m; this.state.calYear = y;
        } else if (this.state.calView === "week") {
            const d = new Date(this.state.calYear, this.state.calMonth, this.state.calDay);
            d.setDate(d.getDate() - 7);
            this.state.calYear = d.getFullYear(); this.state.calMonth = d.getMonth(); this.state.calDay = d.getDate();
        } else {
            const d = new Date(this.state.calYear, this.state.calMonth, this.state.calDay);
            d.setDate(d.getDate() - 1);
            this.state.calYear = d.getFullYear(); this.state.calMonth = d.getMonth(); this.state.calDay = d.getDate();
        }
    }

    calNext() {
        if (this.state.calView === "month") {
            let m = this.state.calMonth + 1, y = this.state.calYear;
            if (m > 11) { m = 0; y++; }
            this.state.calMonth = m; this.state.calYear = y;
        } else if (this.state.calView === "week") {
            const d = new Date(this.state.calYear, this.state.calMonth, this.state.calDay);
            d.setDate(d.getDate() + 7);
            this.state.calYear = d.getFullYear(); this.state.calMonth = d.getMonth(); this.state.calDay = d.getDate();
        } else {
            const d = new Date(this.state.calYear, this.state.calMonth, this.state.calDay);
            d.setDate(d.getDate() + 1);
            this.state.calYear = d.getFullYear(); this.state.calMonth = d.getMonth(); this.state.calDay = d.getDate();
        }
    }

    get calLabel() {
        const { calView, calYear, calMonth, calDay } = this.state;
        if (calView === "month") {
            return new Date(calYear, calMonth, 1)
                .toLocaleDateString([], { month: "long", year: "numeric" });
        }
        if (calView === "week") {
            const days = this._weekDays();
            const fmt = d => d.toLocaleDateString([], { day: "numeric", month: "short" });
            return `${fmt(days[0])} – ${fmt(days[6])}, ${calYear}`;
        }
        return new Date(calYear, calMonth, calDay)
            .toLocaleDateString([], { weekday: "long", day: "numeric", month: "long", year: "numeric" });
    }

    // ── Calendar: computed ─────────────────────────────────

    _dateStr(d) {
        return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
    }

    _eventsForDate(dateStr) {
        return this.state.calEvents.filter(ev => ev.date_from <= dateStr && dateStr <= ev.date_to);
    }

    _weekDays() {
        const pivot = new Date(this.state.calYear, this.state.calMonth, this.state.calDay);
        const sunday = new Date(pivot);
        sunday.setDate(pivot.getDate() - pivot.getDay());
        return Array.from({ length: 7 }, (_, i) => {
            const d = new Date(sunday);
            d.setDate(sunday.getDate() + i);
            return d;
        });
    }

    get calDays() {
        const { calYear, calMonth } = this.state;
        const todayStr = this._dateStr(new Date());
        const firstDow = new Date(calYear, calMonth, 1).getDay();
        const daysInMonth = new Date(calYear, calMonth + 1, 0).getDate();
        const cells = [];
        for (let i = 0; i < firstDow; i++) cells.push({ day: null, dateStr: null, events: [] });
        for (let d = 1; d <= daysInMonth; d++) {
            const dateStr = `${calYear}-${String(calMonth + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
            cells.push({ day: d, dateStr, isToday: dateStr === todayStr, events: this._eventsForDate(dateStr) });
        }
        return cells;
    }

    get calWeekDays() {
        const todayStr = this._dateStr(new Date());
        return this._weekDays().map(d => {
            const dateStr = this._dateStr(d);
            return {
                date: d, dateStr,
                label: d.toLocaleDateString([], { weekday: "short" }),
                dayNum: d.getDate(),
                isToday: dateStr === todayStr,
                events: this._eventsForDate(dateStr),
            };
        });
    }

    get calDayStr() {
        return `${this.state.calYear}-${String(this.state.calMonth + 1).padStart(2, "0")}-${String(this.state.calDay).padStart(2, "0")}`;
    }

    get calDayEvents() {
        return this._eventsForDate(this.calDayStr);
    }

    // 24 hour labels: 00:00 – 23:00
    get hours24() {
        return Array.from({ length: 24 }, (_, i) => `${String(i).padStart(2, "0")}:00`);
    }

    clickDayCell(dateStr) {
        if (!dateStr) return;
        const d = new Date(dateStr + "T00:00:00");
        this.state.calYear = d.getFullYear();
        this.state.calMonth = d.getMonth();
        this.state.calDay = d.getDate();
        this.state.calView = "day";
    }

    // ── Tab ────────────────────────────────────────────────

    setTab(tab) { this.state.activeTab = tab; }

    // ── Modal ──────────────────────────────────────────────

    get selectedLeaveType() {
        if (!this.state.form.holiday_status_id) return null;
        return this.state.leaveTypes.find(lt => lt.id == this.state.form.holiday_status_id) || null;
    }

    // hour options matching Odoo's selection (07:00–18:00 range for work hours)
    get hourOptions() {
        const opts = [];
        for (let h = 7; h <= 18; h++) {
            opts.push({ value: String(h), label: `${String(h).padStart(2, "0")}:00` });
            if (h < 18) {
                opts.push({ value: String(h + 0.5), label: `${String(h).padStart(2, "0")}:30` });
            }
        }
        return opts;
    }

    async openModal() {
        if (!this.state.leaveTypes.length) {
            const data = await this.rpc("/ess/timeoff/leave_types");
            this.state.leaveTypes = data.types || [];
        }
        const today = new Date().toISOString().slice(0, 10);
        this.state.form = {
            holiday_status_id: this.state.leaveTypes[0]?.id || "",
            date_from: today,
            date_to: today,
            description: "",
            attachment: null,
            attachmentName: "",
            // half_day / hour fields
            half_day_period: "am",
            hour_from: "8",
            hour_to: "17",
        };
        this.state.formErrors = {};
        this.state.showModal = true;
    }

    closeModal() { this.state.showModal = false; }

    onFormInput(field) {
        return (ev) => {
            this.state.form[field] = ev.target.value;
            if (this.state.formErrors[field]) delete this.state.formErrors[field];
        };
    }

    onFileChange(ev) {
        const file = ev.target.files[0] || null;
        this.state.form.attachment = file;
        this.state.form.attachmentName = file ? file.name : "";
    }

    removeAttachment() {
        this.state.form.attachment = null;
        this.state.form.attachmentName = "";
    }

    _validateForm() {
        const errors = {};
        const lt = this.selectedLeaveType;
        const unit = lt?.request_unit || "day";
        if (!this.state.form.holiday_status_id) errors.holiday_status_id = "Required";
        if (!this.state.form.date_from) errors.date_from = "Required";
        if (unit === "day" && !this.state.form.date_to) errors.date_to = "Required";
        if (unit === "day" && this.state.form.date_from && this.state.form.date_to &&
            this.state.form.date_from > this.state.form.date_to) {
            errors.date_to = "End date must be after start date";
        }
        if (unit === "hour") {
            if (!this.state.form.hour_from) errors.hour_from = "Required";
            if (!this.state.form.hour_to) errors.hour_to = "Required";
            if (this.state.form.hour_from && this.state.form.hour_to &&
                parseFloat(this.state.form.hour_from) >= parseFloat(this.state.form.hour_to)) {
                errors.hour_to = "End time must be after start time";
            }
        }
        return errors;
    }

    async onSubmitForm() {
        const errors = this._validateForm();
        if (Object.keys(errors).length) { this.state.formErrors = errors; return; }

        this.state.modalLoading = true;
        const f = this.state.form;
        const lt = this.selectedLeaveType;
        const unit = lt?.request_unit || "day";
        const isEdit = !!f._editId;

        try {
            let attachmentData = null;
            if (f.attachment) {
                attachmentData = await new Promise((resolve, reject) => {
                    const reader = new FileReader();
                    reader.onload = () => resolve(reader.result.split(",")[1]);
                    reader.onerror = reject;
                    reader.readAsDataURL(f.attachment);
                });
            }

            const payload = {
                holiday_status_id: f.holiday_status_id,
                date_from: f.date_from,
                date_to: unit === "day" ? f.date_to : f.date_from,
                description: f.description.trim(),
                attachment_b64: attachmentData,
                attachment_name: f.attachmentName || "",
                request_unit: unit,
                half_day_period: f.half_day_period,
                hour_from: unit === "hour" ? f.hour_from : null,
                hour_to: unit === "hour" ? f.hour_to : null,
            };
            const result = await this.rpc(
                isEdit ? "/ess/timeoff/update" : "/ess/timeoff/request",
                isEdit ? { leave_id: f._editId, ...payload } : payload
            );

            if (result && result.error) {
                this.state.formErrors._server = result.error;
                return;
            }
            this.state.showModal = false;
            this.notification.add(
                isEdit ? "Time off request updated." : "Time off request submitted.",
                { type: "success" }
            );
            await Promise.all([this._loadBalance(), this._loadHistory(1), this._loadCalEvents()]);

        } catch (e) {
            this.state.formErrors._server = e.message || "An error occurred.";
        } finally {
            this.state.modalLoading = false;
        }
    }

    async onEdit(leave) {
        if (!this.state.leaveTypes.length) {
            const data = await this.rpc("/ess/timeoff/leave_types");
            this.state.leaveTypes = data.types || [];
        }
        this.state.form = {
            holiday_status_id: leave.holiday_status_id || "",
            date_from: leave.date_from || "",
            date_to: leave.date_to || "",
            description: leave.description || "",
            attachment: null,
            attachmentName: "",
            half_day_period: "am",
            hour_from: "8",
            hour_to: "17",
            _editId: leave.id,
        };
        this.state.formErrors = {};
        this.state.showModal = true;
    }

    async onCancel(leaveId) {
        const ok = await this._confirm("Cancel Request", "Are you sure you want to cancel this time off request?");
        if (!ok) return;
        const result = await this.rpc("/ess/timeoff/cancel", { leave_id: leaveId });
        if (result.error) {
            this.notification.add(result.error, { title: "Error", type: "danger" });
            return;
        }
        this.notification.add("Request cancelled.", { type: "success" });
        await Promise.all([this._loadBalance(), this._loadHistory(this.state.historyPage), this._loadCalEvents()]);
    }

    async onPageChange(page) {
        if (page < 1 || page > this.state.historyTotalPages) return;
        await this._loadHistory(page);
    }

    // ── Formatters ─────────────────────────────────────────

    formatDate(dateStr) {
        if (!dateStr) return "—";
        return new Date(dateStr + "T00:00:00").toLocaleDateString([], {
            day: "numeric", month: "short", year: "numeric",
        });
    }

    balancePercent(balance) {
        if (!balance.max_leaves) return 0;
        return Math.min(100, Math.round(((balance.leaves_taken || 0) / balance.max_leaves) * 100));
    }
}
