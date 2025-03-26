from odoo import models, fields, api, _
from odoo.exceptions import UserError

class StockLot(models.Model):

    _inherit = "stock.lot"

    def get_lot_level_barcode(self):
        barcode_list = {}
        barcode = self.name
        if not barcode and self.barcode:
            barcode = self.barcode
        lot_barcode_other_info = barcode
        company_name = self.env.user.company_id.name
        currency = self.env.user.company_id.currency_id
        phone = self.env.user.company_id.phone
        expiry = self.expiration_date.strftime('%m/%y')
        price = float(self.product_id.lst_price)
        vat_amount = sum(self.product_id.taxes_id.mapped('amount'))
        if vat_amount != 0.0:
            price += price * (vat_amount / 100)
            total_price = str(currency.name) + ' '+ str(price) + ' ' +'Inc.VAT'
        else:
            price = float(self.product_id.lst_price)
            total_price = str(price) + str(currency.name)
        if not barcode:
            raise UserError(_('Barcode is not available'))
        barcode_list = [self.product_id.name, company_name, phone, barcode, lot_barcode_other_info, expiry,total_price]
        return barcode_list