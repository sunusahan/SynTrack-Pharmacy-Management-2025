from odoo import fields, models, api


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    product_type = fields.Selection([('insurance', 'Insurance'), ('non_insurance', 'Non Insurance')], string='Product Type', compute='_compute_insurance_type_id')
    product_code = fields.Char(related='product_id.default_code', string='Internal Reference')
    barcode = fields.Char(related='product_id.barcode', string='Barcode')
    sub_total = fields.Float(string='Subtotal', compute='_compute_qty_price', readonly=1)
    ins_disc_percentage = fields.Float(string='Ins Disc(%)', related='order_id.ins_disc', readonly=1)
    ins_disc_amount = fields.Float(string='Ins Disc Amount', compute='_compute_qty_price', readonly=1)
    subtotal_after_ins_disc_amt = fields.Float(string='Subtotal After Ins Disc Amt', readonly=1)
    copay = fields.Float(string='Copay(%)')
    patient_share_amount = fields.Float(string='Patient Share Amount', compute='_compute_qty_price', readonly=1)
    insurance_amount = fields.Float(string='Insurance Amount', compute='_compute_qty_price', readonly=1)
    available_qty = fields.Float(string='Available Qty', related='product_id.qty_available')
    # insurance_type_name = fields.Char( store=True)
    # insurance_type_name = fields.Char(related='order_id.insurance_type_name', store=True)



    # @api.depends('order_id.type_of_order')
    # def _compute_is_insurance_order(self):
    #     print('line.is_insurance_order', self.is_insurance_order)
    #     for line in self:
    #         line.is_insurance_order = line.order_id.type_of_order.name == 'Insurance' if line.order_id.type_of_order else False
    #         print('line.is_insurance_order1111111111', self.is_insurance_order)


    @api.depends('price_subtotal', 'total_cost')
    def _compute_margin(self):
        for line in self:
            if line.product_id.type != 'combo':
                line.currency_id = self.env.company.currency_id
        res = super()._compute_margin()
        return res

    @api.depends('qty', 'price_unit', 'ins_disc_percentage', 'ins_disc_amount', 'copay', 'patient_share_amount', 'product_id')
    def _compute_qty_price(self):
        for rec in self:
            rec.sub_total = rec.qty * rec.price_unit
            rec.ins_disc_percentage = rec.order_id.ins_disc
            rec.copay = rec.order_id.copay
            rec.ins_disc_amount = (rec.sub_total * rec.ins_disc_percentage)/100
            rec.subtotal_after_ins_disc_amt = rec.sub_total - rec.ins_disc_amount
            rec.patient_share_amount = (rec.subtotal_after_ins_disc_amt * rec.copay)/100
            rec.insurance_amount = rec.subtotal_after_ins_disc_amt - rec.patient_share_amount
            rec.tax_ids_after_fiscal_position = rec.product_id.taxes_id

    @api.depends('order_id.type_of_order')
    def _compute_insurance_type_id(self):
        for rec in self:
            # Set the product_type based on the order's type_of_order
            print('rec.order_id.type_of_order', rec.order_id.type_of_order)
            if rec.order_id.type_of_order.name == 'Insurance':
                rec.product_type = 'insurance'
            else:
                rec.product_type = 'non_insurance'
            print('rec.product_type1111111111111', rec.product_type)
            print('rrrrrrrrrrrrrrrrrrrrrr', rec.order_id.fiscal_position_id, rec.tax_ids_after_fiscal_position, rec.tax_ids)
            # rec.tax_ids_after_fiscal_position = rec.order_id.fiscal_position_id.map_tax(rec.tax_ids)


    # @api.onchange("order_id.type_of_order")
    # def _compute_insurance_type_id(self):
    #     """Find the ID of the 'Insurance' order type"""
    #     for rec in self:
    #         # Ensure that the type of order is mapped to a valid selection value
    #         print('rec.order_id.type_of_order', rec.order_id.type_of_order)
    #         if rec.order_id.type_of_order.name == 'Insurance':
    #             rec.product_type = 'insurance'
    #         else:
    #             rec.product_type = 'non_insurance'
    #         print('rec.product_type22222222222222', rec.product_type)
