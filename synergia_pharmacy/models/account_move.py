from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    pos_order_id = fields.Many2one('pos.order', string="POS Order")
    insurance_amount = fields.Monetary(string='Insurance Amount', readonly=1)
    copay_amount = fields.Monetary(string='Copay Amount', readonly=1)
    insurance_discount = fields.Monetary(string='Insurance Discount', readonly=1)
    total_payable_amount = fields.Monetary(string="Insurance Amount", compute='_compute_total_payable_amount',
                                           store=True, readonly=1)

    @api.depends('amount_tax')
    def _compute_total_payable_amount(self):
        for record in self:
            record.total_payable_amount = record.amount_tax + (record.total_payable_amount or 0.0)

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    insurance_discount_percentage = fields.Float(string='Insurance Discount Percentage')
    copay_percentage = fields.Float(string='Copay Percentage')
    subtotal_after_ins_disc_amt = fields.Float(string='Subtotal After Ins. Disc. Amt')
    patient_share_amount = fields.Float(string='Patient Share Amount')

    # @api.onchange()

