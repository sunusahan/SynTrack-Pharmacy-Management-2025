from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import clean_context, OrderedSet, groupby
from odoo.tools.float_utils import float_compare, float_is_zero, float_round


class ProductProduct(models.Model):
    _inherit = 'product.product'

    moh_price = fields.Float('MOH Price', company_dependent=True, digits='Product Price', groups="base.group_user",
                             help="""MOH Price for product.""")

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    moh_price = fields.Float('MOH Price', company_dependent=True, digits='Product Price', groups="base.group_user",
                             help="""MOH Price for product.""")

