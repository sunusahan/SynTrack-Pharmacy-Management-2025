from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    # @api.depends('quantity', 'discount', 'price_unit', 'tax_ids', 'currency_id')
    # def _compute_totals(self):
    #     res = super()._compute_totals()
    #     for line in self:
    #         if line.move_id.pos_order_id.is_insurance_order:
    #             base_line = line.move_id._prepare_product_base_line_for_taxes_computation(line)
    #             line.price_subtotal = base_line['tax_details']['raw_total_excluded_currency']
    #             line.price_total = base_line['tax_details']['raw_total_included_currency']