# Copyright 2024 ForgeFlow S.L. (https://www.forgeflow.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from datetime import datetime
from datetime import timedelta as td

from odoo import Command
from odoo.tests import new_test_user

from odoo.addons.base.tests.common import BaseCommon


class TestPoLineOriginalDate(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_1 = cls.env["product.product"].create({"name": "test"})
        cls.comparison_delta = td(seconds=1)
        cls.today = datetime.today()
        cls.tomorrow = cls.today + td(1)
        cls.day_2 = cls.today + td(2)

    @classmethod
    def create_purchase_order(cls, product, date_planned, qty=10.0):
        return cls.env["purchase.order"].create(
            {
                "partner_id": cls.partner.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": product.id,
                            "product_uom_id": product.uom_id.id,
                            "name": product.name,
                            "price_unit": 100.0,
                            "date_planned": date_planned,
                            "product_qty": qty,
                        }
                    )
                ],
            }
        )

    def test_01_original_date_planned_stored(self):
        po = self.create_purchase_order(self.product_1, self.tomorrow)
        self.assertTrue(po.date_planned)
        self.assertFalse(po.original_date_planned)
        line = po.order_line
        self.assertTrue(line.date_planned)
        self.assertFalse(line.original_date_planned)
        po.button_confirm()
        self.assertTrue(po.original_date_planned)
        self.assertEqual(
            po.date_planned.replace(microsecond=0), po.original_date_planned
        )
        self.assertTrue(line.original_date_planned)
        self.assertEqual(line.date_planned, line.original_date_planned)
        line.date_planned = self.day_2
        self.assertAlmostEqual(
            po.original_date_planned, self.tomorrow, delta=self.comparison_delta
        )
        self.assertAlmostEqual(po.date_planned, self.day_2, delta=self.comparison_delta)
        self.assertEqual(line.original_date_planned, self.tomorrow)
        self.assertEqual(line.date_planned, self.day_2)

    def test_02_reconfirm_keeps_original_date(self):
        po = self.create_purchase_order(self.product_1, self.tomorrow)
        po.button_confirm()
        line = po.order_line
        original = line.original_date_planned
        po.button_cancel()
        po.button_draft()
        line.date_planned = self.day_2
        po.button_confirm()
        self.assertEqual(po.state, "purchase")
        self.assertEqual(line.original_date_planned, original)

    def test_03_line_added_to_confirmed_po(self):
        po = self.create_purchase_order(self.product_1, self.tomorrow)
        po.button_confirm()
        new_line = self.env["purchase.order.line"].create(
            {
                "order_id": po.id,
                "product_id": self.product_1.id,
                "product_qty": 1.0,
                "price_unit": 100.0,
                "date_planned": self.day_2,
            }
        )
        self.assertEqual(new_line.original_date_planned, new_line.date_planned)

    def test_04_double_validation(self):
        self.env.company.write(
            {"po_double_validation": "two_step", "po_double_validation_amount": 0}
        )
        buyer = new_test_user(
            self.env, login="po_buyer", groups="purchase.group_purchase_user"
        )
        po = self.create_purchase_order(self.product_1, self.tomorrow)
        po.with_user(buyer).button_confirm()
        self.assertEqual(po.state, "to approve")
        self.assertFalse(po.order_line.original_date_planned)
        po.order_line.date_planned = self.day_2
        po.button_approve()
        self.assertEqual(po.state, "purchase")
        self.assertEqual(
            po.order_line.original_date_planned, po.order_line.date_planned
        )
