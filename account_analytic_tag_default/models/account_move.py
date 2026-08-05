# Copyright 2020 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # make standard field a stored, computed, editable field.
    analytic_tag_ids = fields.Many2many(
        compute="_compute_analytic_tag_ids",
        store=True,
        readonly=False,
    )

    @api.depends("analytic_account_id")
    def _compute_analytic_tag_ids(self):
        for rec in self:
            if not rec._origin and rec.analytic_tag_ids:
                continue
            if rec.analytic_account_id.default_analytic_tag_ids:
                rec.analytic_tag_ids = rec.analytic_account_id.default_analytic_tag_ids
            else:
                rec.analytic_tag_ids = False
        self._sync_analytic_dimension_fields()

    def _sync_analytic_dimension_fields(self):
        # analytic_tag_dimension fills its x_dimension_* fields only when
        # analytic_tag_ids arrives through create/write vals; values assigned
        # by this compute are flushed directly and bypass that hook, so
        # mirror the dimension fields here as well.
        dim_fields = [f for f in self._fields if f.startswith("x_dimension_")]
        if not dim_fields:
            return
        for rec in self:
            values = rec.analytic_tag_ids.get_dimension_values()
            for fname in dim_fields:
                rec[fname] = values.get(fname, False)

    @api.model_create_multi
    def create(self, vals_list):
        # This is needed to apply default tags when creating and invoice/entry
        # from an action in other model, for instance a SO.
        aa_model = self.env["account.analytic.account"]
        for vals in vals_list:
            if vals.get("analytic_account_id"):
                a_acc = aa_model.browse(vals.get("analytic_account_id"))
                tags_value = vals.get("analytic_tag_ids")
                is_tags_empty = not tags_value or (
                    isinstance(tags_value, list) and tags_value == [(6, 0, [])]
                )
                if a_acc.default_analytic_tag_ids and is_tags_empty:
                    vals["analytic_tag_ids"] = [
                        (6, 0, a_acc.default_analytic_tag_ids.ids)
                    ]

        return super().create(vals_list)
