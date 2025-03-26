from odoo import models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    pos_order_id = fields.Many2one('pos.order', string="POS Order")
    insurance_amount = fields.Monetary(string='Insurance Amount')

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    insurance_discount_percentage = fields.Float(string='Insurance Discount Percentage')
    copay_percentage = fields.Float(string='Copay Percentage')
    subtotal_after_ins_disc_amt = fields.Float(string='Subtotal After Ins. Disc. Amt')
    patient_share_amount = fields.Float(string='Patient Share Amount')

