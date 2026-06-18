/** @odoo-module */
import { Component, useState, onWillStart, onWillUnmount } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { ConnectionLostError, rpc } from "@web/core/network/rpc";
import { user } from "@web/core/user";

export class AttendancePage extends Component {
    static template = "owl_self_service.AttendancePage";
    static props = {};

    setup() {
        this.rpc = rpc;
        this.notification = useService("notification");

        this.state = useState({
            activeTab: "dashboard",
            employeeFound: true,
            isCheckedIn: false,
            checkInTime: null,
            elapsed: "00:00:00",
            loading: true,
            actionLoading: false,
            history: [],
            currentPage: 1,
            totalPages: 1,
        });

        this._timer = null;
        this.todayLabel = new Date().toLocaleDateString([], {
            weekday: "long", day: "numeric", month: "long", year: "numeric",
        });

        onWillStart(() => this._loadAll());
        onWillUnmount(() => this._stopTimer());
    }

    // ── Data loading ───────────────────────────────────────

    async _loadAll() {
        this.state.loading = true;
        try {
            await Promise.all([
                this._fetchAttendanceState(),
                this._loadHistory(1),
            ]);
        } finally {
            this.state.loading = false;
        }
    }

    async _fetchAttendanceState() {
        const data = await this.rpc("/ess/attendance/status");
        if (data.error === "no_employee") {
            this.state.employeeFound = false;
            return;
        }
        this.state.employeeFound = true;
        if (data.attendance_state === "checked_in" && data.last_check_in) {
            this.state.isCheckedIn = true;
            this.state.checkInTime = new Date(data.last_check_in);
            this._startTimer();
        } else {
            this.state.isCheckedIn = false;
            this.state.checkInTime = null;
            this._stopTimer();
        }
    }

    async _loadHistory(page = 1) {
        const limit = 10;
        const data = await this.rpc("/ess/attendance/history", { page, limit });
        if (data.error === "no_employee") return;

        this.state.history = data.records.map((r) => ({
            id: r.id,
            employeeName: r.employee_name || "",
            checkIn: r.check_in ? new Date(r.check_in) : null,
            checkOut: r.check_out ? new Date(r.check_out) : null,
        }));
        this.state.currentPage = page;
        this.state.totalPages = Math.ceil(data.total / limit) || 1;
    }

    // ── Actions ────────────────────────────────────────────

    async _toggleAttendance() {
        if (this.state.actionLoading) return;
        this.state.actionLoading = true;
        try {
            const data = await this.rpc("/ess/attendance/toggle");
            if (data.error) {
                this.notification.add(data.error, { title: "Attendance Error", type: "danger" });
                return;
            }
            await Promise.all([
                this._fetchAttendanceState(),
                this._loadHistory(1),
            ]);
        } catch (error) {
            if (error instanceof ConnectionLostError) {
                this.notification.add(
                    "Connection lost. Attendance could not be recorded.",
                    { title: "Attendance Error", type: "danger" }
                );
            } else {
                throw error;
            }
        } finally {
            this.state.actionLoading = false;
        }
    }

    async onPageChange(page) {
        if (page < 1 || page > this.state.totalPages) return;
        await this._loadHistory(page);
    }

    setTab(tab) {
        this.state.activeTab = tab;
    }

    // ── Timer ──────────────────────────────────────────────

    _startTimer() {
        this._stopTimer();
        this._timer = setInterval(() => {
            if (!this.state.checkInTime) return;
            const diff = Math.floor((Date.now() - this.state.checkInTime.getTime()) / 1000);
            const h = String(Math.floor(diff / 3600)).padStart(2, "0");
            const m = String(Math.floor((diff % 3600) / 60)).padStart(2, "0");
            const s = String(diff % 60).padStart(2, "0");
            this.state.elapsed = `${h}:${m}:${s}`;
        }, 1000);
    }

    _stopTimer() {
        if (this._timer) {
            clearInterval(this._timer);
            this._timer = null;
        }
        this.state.elapsed = "00:00:00";
    }

    // ── Computed ───────────────────────────────────────────

    get lastRecord() {
        return this.state.history.length ? this.state.history[0] : null;
    }

    get historyByDate() {
        const groups = [];
        const seen = {};
        for (const row of this.state.history) {
            const dateKey = row.checkIn
                ? row.checkIn.toLocaleDateString([], { day: "2-digit", month: "short", year: "numeric" })
                : "Unknown";
            if (!seen[dateKey]) {
                seen[dateKey] = { date: dateKey, totalSeconds: 0, rows: [] };
                groups.push(seen[dateKey]);
            }
            seen[dateKey].rows.push(row);
            if (row.checkIn && row.checkOut) {
                seen[dateKey].totalSeconds += Math.floor((row.checkOut - row.checkIn) / 1000);
            }
        }
        return groups;
    }

    // ── Formatters ─────────────────────────────────────────

    formatTime(date) {
        if (!date) return "--:--";
        return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    }

    formatDate(date) {
        if (!date) return "-";
        return date.toLocaleDateString([], {
            weekday: "short", day: "numeric", month: "short", year: "numeric",
        });
    }

    formatDuration(checkIn, checkOut) {
        if (!checkIn || !checkOut) return "-";
        const diff = Math.floor((checkOut - checkIn) / 1000);
        const h = Math.floor(diff / 3600);
        const m = Math.floor((diff % 3600) / 60);
        return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")} hrs`;
    }

    formatTotalHours(seconds) {
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
    }

}
