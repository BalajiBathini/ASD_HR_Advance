/** @odoo-module */
import { Component, useState, onWillStart, onMounted, onWillUnmount } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { AttendancePage } from "./attendance/attendance";
import { ExpensePage } from "./expense/expense";
import { ContractPage } from "./contract/contract";
import { TimeOffPage } from "./timeoff/timeoff";
import { PayslipPage } from "./payslip/payslip";
import { rpc } from "@web/core/network/rpc";
import { user } from "@web/core/user";

export class Root extends Component {
    static template = "owl_self_service.Root";
    static props = {};
    static components = { AttendancePage, ExpensePage, ContractPage, TimeOffPage, PayslipPage };

    setup() {
        this.user = user;
        this.rpc = rpc;
        this.notification = useService("notification");

        this.menus = [
            {
                id: "attendance",
                icon: "fa fa-sign-in",
                iconActive: "fa fa-sign-in",
                label: "My Attendance",
                description: "Check in, check out, and view history",
            },
            {
                id: "timeoff",
                icon: "fa fa-calendar-o",
                iconActive: "fa fa-calendar",
                label: "My Time Off",
                description: "Submit and track your leave requests",
            },
            {
                id: "expenses",
                icon: "fa fa-credit-card",
                iconActive: "fa fa-credit-card",
                label: "My Expenses",
                description: "Submit and track your expense reports",
            },
            {
                id: "payslips",
                icon: "fa fa-money",
                iconActive: "fa fa-money",
                label: "My Payslips",
                description: "View and download your monthly payslips",
            },
            {
                id: "contracts",
                icon: "fa fa-pencil-square-o",
                iconActive: "fa fa-pencil-square-o",
                label: "My Contracts",
                description: "View your employment contracts",
            },
        ];

        const initialMenu = window.location.hash.slice(1) || "attendance";

        this.state = useState({
            activeMenu: initialMenu,
            avatarUrl: null,
            avatarUploading: false,
            displayName: this.user.name || this.user.userName || "User",
            profileTab: "info",
            pwForm: { old_password: "", new_password: "", confirm_password: "" },
            pwErrors: {},
            pwLoading: false,
            pwSuccess: false,
            infoForm: { name: "", work_phone: "", mobile_phone: "", company_name: "", vat: "", street: "", city: "", zip: "", country_id: "" },
            infoOriginal: {},
            infoMeta: { email: "", work_email: "", job_title: "", department: "", has_employee: false },
            infoEditing: false,
            infoLoading: false,
            infoSaving: false,
            infoSuccess: false,
            infoError: "",
            countries: [],
        });

        this._onHashChange = () => {
            const menu = window.location.hash.slice(1) || "attendance";
            this.state.activeMenu = menu;
        };

        this._successTimer = null;

        onMounted(() => {
            window.addEventListener("hashchange", this._onHashChange);
        });

        onWillUnmount(() => {
            window.removeEventListener("hashchange", this._onHashChange);
            if (this._successTimer) clearTimeout(this._successTimer);
        });

        onWillStart(async () => {
            try {
                const result = await this.rpc("/ess/account/avatar_info");
                if (result.has_avatar) {
                    const ts = new Date().getTime();
                    if (result.source === 'employee' && result.employee_id) {
                        this.state.avatarUrl = `/web/image/hr.employee/${result.employee_id}/image_128?t=${ts}`;
                    } else if (result.partner_id) {
                        this.state.avatarUrl = `/web/image/res.partner/${result.partner_id}/image_128?t=${ts}`;
                    }
                }
            } catch (_) { }
            try {
                const countries = await this.rpc("/ess/account/countries");
                this.state.countries = countries || [];
            } catch (_) { }
            if (initialMenu === "profile") {
                await this._loadProfileInfo();
            }
        });
    }

    get userName() {
        return this.state.displayName;
    }

    get userInitial() {
        return this.userName.charAt(0).toUpperCase();
    }

    get userEmail() {
        return this.user.userName || "";
    }

    get userCompany() {
        return odoo.__session_info__?.company_name || "";
    }

    get userAvatarUrl() {
        return this.state.avatarUrl;
    }

    get activeMenu() {
        return this.state.activeMenu;
    }

    get activeMenuLabel() {
        if (this.state.activeMenu === "profile") return "My Profile";
        return this.menus.find((m) => m.id === this.state.activeMenu)?.label || "";
    }

    logout() {
        window.location.href = "/web/session/logout?redirect=/ess";
    }

    setProfileTab(tab) {
        this.state.profileTab = tab;
        this.state.pwErrors = {};
        this.state.pwSuccess = false;
        this.state.infoEditing = false;
        if (tab === "info") this._loadProfileInfo();
    }

    setActive(menuId) {
        this.state.activeMenu = menuId;
        window.location.hash = menuId;
        if (menuId === "profile") {
            this.state.pwForm = { old_password: "", new_password: "", confirm_password: "" };
            this.state.pwErrors = {};
            this.state.pwSuccess = false;
            this._loadProfileInfo();
        }
    }

    async _loadProfileInfo() {
        if (this.state.infoLoading) return;
        this.state.infoLoading = true;
        this.state.infoError = "";
        try {
            const data = await this.rpc("/ess/account/profile");
            const form = {
                name: data.name || "",
                work_phone: data.work_phone || "",
                mobile_phone: data.mobile_phone || "",
                company_name: data.company_name || "",
                vat: data.vat || "",
                street: data.street || "",
                city: data.city || "",
                zip: data.zip || "",
                country_id: data.country_id || "",
                emergency_contact: data.emergency_contact || "",
                emergency_phone: data.emergency_phone || "",
                certificate: data.certificate || "",
                study_field: data.study_field || "",
                study_school: data.study_school || "",
                marital: data.marital || "",
                children: data.children || 0,
                spouse_complete_name: data.spouse_complete_name || "",
                spouse_birthdate: data.spouse_birthdate || "",
            };
            this.state.infoMeta = {
                email: data.email || "",
                work_email: data.work_email || "",
                job_title: data.job_title || "",
                department: data.department || "",
                has_employee: data.has_employee || false,
            };
            this.state.infoForm = { ...form };
            this.state.infoOriginal = { ...form };
            if (form.name) this.state.displayName = form.name;
        } catch (e) {
            this.state.infoError = "Failed to load profile data.";
        } finally {
            this.state.infoLoading = false;
        }
    }

    onAvatarChange(ev) {
        const file = ev.target.files[0];
        if (!file) return;
        const formData = new FormData();
        formData.append("avatar", file);
        this.state.avatarUploading = true;
        fetch("/ess/account/upload_avatar", {
            method: "POST",
            body: formData,
            headers: { "X-Requested-With": "XMLHttpRequest" },
        })
            .then((r) => r.json())
            .then((result) => {
                if (result.error) {
                    this.notification.add(result.error, { type: "danger" });
                } else {
                    this.state.avatarUrl = result.avatar_url;
                    this.notification.add("Photo updated.", { type: "success" });
                }
            })
            .catch(() => this.notification.add("Upload failed.", { type: "danger" }))
            .finally(() => {
                this.state.avatarUploading = false;
                ev.target.value = "";
            });
    }

    onInfoInput(field) {
        return (ev) => {
            const val = ev.target.value;
            this.state.infoForm[field] = field === "country_id" ? (val ? parseInt(val) : "") : val;
            this.state.infoSuccess = false;
            this.state.infoError = "";
        };
    }

    onInfoEdit() {
        this.state.infoEditing = true;
        this.state.infoSuccess = false;
        this.state.infoError = "";
    }

    onInfoDiscard() {
        this.state.infoForm = { ...this.state.infoOriginal };
        this.state.infoEditing = false;
        this.state.infoSuccess = false;
        this.state.infoError = "";
    }

    get infoIsDirty() {
        const f = this.state.infoForm;
        const o = this.state.infoOriginal;
        return Object.keys(f).some((k) => f[k] !== o[k]);
    }

    async onInfoSave() {
        if (!this.state.infoForm.name) {
            this.state.infoError = "Name is required.";
            return;
        }
        this.state.infoSaving = true;
        this.state.infoError = "";
        this.state.infoSuccess = false;
        try {
            const f = this.state.infoForm;
            const result = await this.rpc("/ess/account/profile/update", {
                name: f.name,
                company_name: f.company_name,
                vat: f.vat,
                street: f.street,
                city: f.city,
                zip: f.zip,
                country_id: f.country_id || false,
                work_phone: f.work_phone,
                mobile_phone: f.mobile_phone,
            });
            if (result && result.error) {
                this.state.infoError = result.error;
            } else {
                this.state.infoOriginal = { ...f };
                this.state.infoEditing = false;
                this.state.infoSuccess = true;
                if (f.name) this.state.displayName = f.name;
                if (this._successTimer) clearTimeout(this._successTimer);
                this._successTimer = setTimeout(() => { this.state.infoSuccess = false; }, 4000);
            }
        } catch (e) {
            this.state.infoError = e.data?.message || e.message || "Failed to save profile.";
        } finally {
            this.state.infoSaving = false;
        }
    }

    onPwInput(field) {
        return (ev) => {
            this.state.pwForm[field] = ev.target.value;
            if (this.state.pwErrors[field]) delete this.state.pwErrors[field];
            this.state.pwSuccess = false;
        };
    }

    async onChangePassword() {
        const f = this.state.pwForm;
        const errors = {};
        if (!f.old_password) errors.old_password = "Required";
        if (!f.new_password) errors.new_password = "Required";
        else if (f.new_password.length < 6) errors.new_password = "Minimum 6 characters";
        if (!f.confirm_password) errors.confirm_password = "Required";
        else if (f.new_password !== f.confirm_password) errors.confirm_password = "Passwords do not match";

        if (Object.keys(errors).length) { this.state.pwErrors = errors; return; }

        this.state.pwLoading = true;
        this.state.pwErrors = {};
        try {
            const result = await this.rpc("/ess/account/change_password", {
                old_password: f.old_password,
                new_password: f.new_password,
            });
            if (result && result.error) {
                this.state.pwErrors._server = result.error;
                return;
            }
            this.state.pwSuccess = true;
            this.state.pwForm = { old_password: "", new_password: "", confirm_password: "" };
            this.notification.add("Password changed successfully.", { type: "success" });
        } catch (e) {
            this.state.pwErrors._server = e.data?.message || e.message || "Failed to change password.";
        } finally {
            this.state.pwLoading = false;
        }
    }
}
