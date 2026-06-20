/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { DashboardAmcharts } from "@asd_cust_dashboard/js/dashboard_amcharts";
import { DashboardChartWrapper } from "@asd_cust_dashboard/js/dashboard_chart_wrapper";
import { Component, useState, useSubEnv } from "@odoo/owl";

function formatToDT(dateObj) {
    return dateObj.toISOString().split("T")[0];
}

let activeGlobalFilterValues = {};

export class DashboardGlobalFilter extends Component {
    static template = "asd_dashboard_global_filter.GlobalFilter";

    setup() {
        console.log("[DEBUG] DashboardGlobalFilter setup() executing...");
        this.state = useState({
            startDate: this.props.initialStart || "",
            endDate: this.props.initialEnd || "",
            quickFilter: this.props.initialFilterType || "none"
        });

        const { onMounted } = owl; // Ensure onMounted is available
        onMounted(() => {
            console.log("[DEBUG] DashboardGlobalFilter mounted() on DOM!");
        });
    }

    onQuickFilterChange(ev) {
        const val = ev.target.value;
        this.state.quickFilter = val;

        const today = new Date();
        let start = "";
        let end = "";

        switch (val) {
            case "today":
                start = formatToDT(today) + " 00:00:00";
                end = formatToDT(today) + " 23:59:59";
                break;
            case "yesterday":
                const yest = new Date(today);
                yest.setDate(yest.getDate() - 1);
                start = formatToDT(yest) + " 00:00:00";
                end = formatToDT(yest) + " 23:59:59";
                break;
            case "last_7_days":
                const l7 = new Date(today);
                l7.setDate(l7.getDate() - 6); // 7 days inclusive: today and 6 prior
                start = formatToDT(l7) + " 00:00:00";
                end = formatToDT(today) + " 23:59:59";
                break;
            case "last_30_days":
                const l30 = new Date(today);
                l30.setDate(l30.getDate() - 29);
                start = formatToDT(l30) + " 00:00:00";
                end = formatToDT(today) + " 23:59:59";
                break;
            case "this_week":
                const twStart = new Date(today);
                const day = twStart.getDay() || 7;
                if (day !== 1) twStart.setDate(twStart.getDate() - (day - 1));
                const twEnd = new Date(twStart);
                twEnd.setDate(twStart.getDate() + 6);
                start = formatToDT(twStart) + " 00:00:00";
                end = formatToDT(twEnd) + " 23:59:59";
                break;
            case "last_week":
                const lwEnd = new Date(today);
                const day2 = lwEnd.getDay() || 7;
                lwEnd.setDate(lwEnd.getDate() - day2);
                const lwStart = new Date(lwEnd);
                lwStart.setDate(lwStart.getDate() - 6);
                start = formatToDT(lwStart) + " 00:00:00";
                end = formatToDT(lwEnd) + " 23:59:59";
                break;
            case "this_month":
                const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
                const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0);
                start = formatToDT(firstDay) + " 00:00:00";
                end = formatToDT(lastDay) + " 23:59:59";
                break;
            case "last_month":
                const firstDayLm = new Date(today.getFullYear(), today.getMonth() - 1, 1);
                const lastDayLm = new Date(today.getFullYear(), today.getMonth(), 0);
                start = formatToDT(firstDayLm) + " 00:00:00";
                end = formatToDT(lastDayLm) + " 23:59:59";
                break;
            case "this_quarter":
                const q = Math.floor(today.getMonth() / 3);
                const firstDayQ = new Date(today.getFullYear(), q * 3, 1);
                const lastDayQ = new Date(today.getFullYear(), q * 3 + 3, 0);
                start = formatToDT(firstDayQ) + " 00:00:00";
                end = formatToDT(lastDayQ) + " 23:59:59";
                break;
            case "last_quarter":
                const lq = Math.floor(today.getMonth() / 3) - 1;
                const yearShift = lq < 0 ? -1 : 0;
                const lqSafe = lq < 0 ? 3 : lq;
                const firstDayLq = new Date(today.getFullYear() + yearShift, lqSafe * 3, 1);
                const lastDayLq = new Date(today.getFullYear() + yearShift, lqSafe * 3 + 3, 0);
                start = formatToDT(firstDayLq) + " 00:00:00";
                end = formatToDT(lastDayLq) + " 23:59:59";
                break;
            case "this_year":
                const firstDayYear = new Date(today.getFullYear(), 0, 1);
                const lastDayYear = new Date(today.getFullYear(), 11, 31);
                start = formatToDT(firstDayYear) + " 00:00:00";
                end = formatToDT(lastDayYear) + " 23:59:59";
                break;
            case "custom":
                return;
        }

        if (val !== "custom" && val !== "none") {
            this.state.startDate = start;
            this.state.endDate = end;
            this.props.onChange(this.state);
        } else if (val === "none") {
            this.state.startDate = "";
            this.state.endDate = "";
            this.props.onChange(this.state);
        }
    }

    onCustomDateChange(ev) {
        if (this.state.quickFilter === 'custom') {
            if (this.state.startDate && this.state.endDate) {
                // Ensure proper datetime string format
                const startStr = this.state.startDate.includes(" ") ? this.state.startDate : this.state.startDate + " 00:00:00";
                const endStr = this.state.endDate.includes(" ") ? this.state.endDate : this.state.endDate + " 23:59:59";

                this.props.onChange({
                    quickFilter: "custom",
                    startDate: startStr,
                    endDate: endStr
                });
            }
        }
    }
}

patch(DashboardAmcharts.prototype, {
    setup() {
        console.log("[DEBUG] DashboardAmcharts patch setup() executing...");
        super.setup(...arguments);

        const cachedFilter = sessionStorage.getItem("dashboardGlobalFilter");
        let initialFilter = { filterType: "none", start: "", end: "" };

        if (cachedFilter) {
            try {
                initialFilter = JSON.parse(cachedFilter);
            } catch (e) { }
        }

        this.globalFilterState = useState(initialFilter);
    },

    async get_chart_details() {
        const payload = await this.orm.call("dashboard.dashboard", "get_charts_details", [
            this.props.action.params.record,
        ]);
        if (payload && payload.length >= 4) {
            this.auto_reload_duration = payload[0];
            this.state.charts = payload[1];
            this.state.name = payload[2];
            this.dashboard_user = payload[3];
            this.state.enable_global_filter = payload.length > 4 ? payload[4] : false;
            console.log("[DEBUG] get_chart_details payload:", payload);
            console.log("[DEBUG] enable_global_filter set to:", this.state.enable_global_filter);
        }
    },

    get isGlobalFilterEnabled() {
        console.log("[DEBUG] Evaluating isGlobalFilterEnabled:", this.state.enable_global_filter);
        return this.state.enable_global_filter || false;
    },

    onGlobalFilterChange(filterState) {
        this.globalFilterState.filterType = filterState.quickFilter;
        this.globalFilterState.start = filterState.startDate;
        this.globalFilterState.end = filterState.endDate;

        sessionStorage.setItem("dashboardGlobalFilter", JSON.stringify(this.globalFilterState));

        // Use setTimeout to debounce slightly if multiple events fire
        if (this.filterTimeout) {
            clearTimeout(this.filterTimeout);
        }
        this.filterTimeout = setTimeout(() => {
            this.applyGlobalFilter();
        }, 500);
    },

    applyGlobalFilter() {
        const hasDates = this.globalFilterState.start && this.globalFilterState.end;
        if (!hasDates && this.globalFilterState.filterType !== 'none') return;

        const overrideData = {};
        if (this.globalFilterState.filterType !== 'none') {
            overrideData.date_filter_option = "custom";
            overrideData.start_date = this.globalFilterState.start;
            overrideData.end_date = this.globalFilterState.end;
        }

        // Update the module-scoped filter object
        activeGlobalFilterValues = overrideData;

        // Force a synchronous reactivity reload to all child charts
        if (this.timer) clearTimeout(this.timer);
        if (this.reloadKey) {
            this.reloadKey.value += 1;
        }
        // Restart the standard polling interval
        this.update_timer();
    }
});

patch(DashboardChartWrapper.prototype, {
    async update_record_sets(recordId, chart_type, isDirty, name, data) {
        let actualIsDirty = isDirty;
        let actualData = data || {};

        // Inject global filter state if present
        if (Object.keys(activeGlobalFilterValues).length > 0) {
            if (actualData.name === "Object") actualData = {}; // Clear placeholder
            Object.assign(actualData, activeGlobalFilterValues);
        }

        return super.update_record_sets(recordId, chart_type, actualIsDirty, name, actualData);
    }
});

// VERY IMPORTANT: Add to parent components so it can be rendered!
if (!DashboardAmcharts.components) {
    DashboardAmcharts.components = {};
}
DashboardAmcharts.components.DashboardGlobalFilter = DashboardGlobalFilter;

