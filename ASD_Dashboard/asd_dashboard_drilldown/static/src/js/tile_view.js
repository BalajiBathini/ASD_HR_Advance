/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { TileView } from "@asd_cust_dashboard/components/TileView/TileView";
import { useService } from "@web/core/utils/hooks";

patch(TileView.prototype, {
    setup() {
        super.setup(...arguments);
        this.actionService = useService("action");
    },

    onTileClick(ev) {
        if (!this.state || !this.state.data) return;

        const data = this.state.data;
        const model = data.drilldown_model;
        const domain = data.drilldown_domain || [];
        const action_id = data.drilldown_action_id;

        if (!model) return;

        if (action_id) {
            this.actionService.doAction(action_id, {
                additionalContext: {
                    active_id: false,
                    active_ids: false,
                    active_model: false,
                }
            });
        } else {
            this.actionService.doAction({
                type: 'ir.actions.act_window',
                name: data.name || "Records",
                res_model: model,
                domain: domain,
                views: [[false, 'list'], [false, 'form']],
                target: 'current',
            });
        }
    }
});
