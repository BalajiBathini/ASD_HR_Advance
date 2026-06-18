/** @odoo-module */
import { registry } from "@web/core/registry";
import { Root } from "./root";

// Register as a public component instead of mounting manually
registry.category("public_components").add("owl_self_service.Root", Root);
