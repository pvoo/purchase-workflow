# Copyright 2024 ForgeFlow S.L. (https://www.forgeflow.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    original_date_planned = fields.Datetime(
        string="Original Expected Arrival",
        readonly=True,
        copy=False,
        help="Original expected arrival at PO confirmation.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines._set_original_date_planned()
        return lines

    def _set_original_date_planned(self):
        """Keep the first expected arrival of confirmed lines."""
        for line in self.filtered(
            lambda pol: pol.order_id.state == "purchase"
            and pol.date_planned
            and not pol.original_date_planned
        ):
            line.original_date_planned = line.date_planned
