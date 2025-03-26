from odoo import fields, models, api


class InsuranceLines(models.Model):
    _name = 'synergia.insurance.lines'

    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)], required=True, change_default=True)
    order_id = fields.Many2one('pos.order', string='Order Ref', ondelete='cascade', required=True, index=True)
    product_type = fields.Selection([('insurance', 'Insurance'), ('non_insurance', 'Non Insurance')],
                                    string='Product Type')
    product_code = fields.Char(related='product_id.default_code', string='Internal Reference')
    qty = fields.Float('Quantity', digits='Product Unit of Measure', default=1)
    product_uom_id = fields.Many2one('uom.uom', string='Product UoM', related='product_id.uom_id')
    price_unit = fields.Float(string='Unit Price', digits=0, related='product_id.list_price')
    sub_total = fields.Float(string='Subtotal', compute='_compute_qty_price', readonly=1)
    ins_disc_percentage = fields.Float(string='Ins Disc(%)', related='order_id.ins_disc', readonly=1)
    ins_disc_amount = fields.Float(string='Ins Disc Amount', compute='_compute_qty_price', readonly=1)
    subtotal_after_ins_disc_amt = fields.Float(string='Subtotal After Ins Disc Amt', readonly=1)
    copay = fields.Float(string='Copay(%)', related='order_id.copay')
    patient_share_amount = fields.Float(string='Patient Share Amount', compute='_compute_qty_price', readonly=1)
    insurance_amount = fields.Float(string='Insurance Amount', compute='_compute_qty_price', readonly=1)
    price_subtotal = fields.Float(string='Total Amount', readonly=True)
    total_insu_amt = fields.Float(string='Subtotal', readonly=1)
    price_subtotal_incl = fields.Float(string='Total Incl')
    discount = fields.Float(string='Discount(%)')
    tax_ids = fields.Many2many('account.tax', string='Taxes', readonly=True)
    tax_ids_after_fiscal_position = fields.Many2many('account.tax', compute='_get_tax_ids_after_fiscal_position',
                                                     string='Taxes to Apply')

    @api.depends('order_id', 'order_id.fiscal_position_id')
    def _get_tax_ids_after_fiscal_position(self):
        for line in self:
            line.tax_ids_after_fiscal_position = line.order_id.fiscal_position_id.map_tax(line.tax_ids)


    @api.onchange('qty', 'discount', 'price_unit', 'tax_ids')
    def _onchange_qty(self):
        if self.product_id:
            price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
            self.price_subtotal = self.price_subtotal_incl = price * self.qty
            if (self.tax_ids):
                taxes = self.tax_ids.compute_all(price, self.order_id.currency_id, self.qty, product=self.product_id,
                                                 partner=False)
                self.price_subtotal = taxes['total_excluded']
                self.price_subtotal_incl = taxes['total_included']
            self.total_insu_amt = self.price_subtotal - self.ins_disc_amount

    @api.depends('qty', 'price_unit', 'ins_disc_percentage', 'ins_disc_amount', 'copay', 'patient_share_amount',
                 'product_id')
    def _compute_qty_price(self):
        for rec in self:
            rec.sub_total = rec.qty * rec.price_unit
            rec.ins_disc_percentage = rec.order_id.ins_disc
            rec.copay = rec.order_id.copay
            rec.ins_disc_amount = (rec.sub_total * rec.ins_disc_percentage) / 100
            rec.subtotal_after_ins_disc_amt = rec.sub_total - rec.ins_disc_amount
            rec.patient_share_amount = (rec.subtotal_after_ins_disc_amt * rec.copay) / 100
            rec.insurance_amount = rec.subtotal_after_ins_disc_amt - rec.patient_share_amount
            rec.tax_ids = rec.product_id.taxes_id