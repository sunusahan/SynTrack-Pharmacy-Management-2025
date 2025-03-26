from odoo import models, fields
from odoo.tools import float_is_zero


class PosMakePayment(models.TransientModel):
    _inherit = 'pos.make.payment'

    amount = fields.Float(digits=0, required=True, default=lambda self: self._default_amount())

    def _default_amount(self):
        res = super()._default_amount()
        active_id = self.env.context.get('active_id')
        print('active_idactive_id', active_id)
        if active_id:
            order = self.env['pos.order'].browse(active_id)
            print('order.type_of_order order.type_of_order order.type_of_order',  order.type_of_order)
            if order.is_insurance_order:
                amount_total = order.patient_paid_amount
                # If we refund the entire order, we refund what was paid originally, else we refund the value of the items returned
                if float_is_zero(order.refunded_order_id.patient_paid_amount + order.patient_paid_amount,
                                 precision_rounding=order.currency_id.rounding):
                    amount_total = -order.refunded_order_id.amount_paid
                return amount_total - order.amount_paid
            else:
                return res
        return res