import re


from odoo import models, fields, api, _
from num2words import num2words
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_round

class PosOrder(models.Model):
    _inherit = 'pos.order'

    type_of_order = fields.Many2one('synergia.customer.type', string="Type Of Order", store=True, required=True)
    patient_phone_no = fields.Char(string="Patient Phone No.")
    patient_name = fields.Char(string="Patient Name")
    patient_email = fields.Char(string='Patient Email')
    patient_eid = fields.Char(string="Patient EID", store=True)
    patient_eid_expiry = fields.Date(string="Patient EID Expiry")
    type_of_transaction = fields.Selection([('select', ''),('otc', 'OTC'), ('prescription', 'Prescription')],
                                           string="Type of Transaction", default='select')
    delivery_type = fields.Selection([('select', ''),('counter', 'Counter'), ('delivery', 'Delivery')],
                                           string="Delivery Type")

    insurance_plan = fields.Many2one('synergia.insurance.plan', tracking=True)
    ins_disc = fields.Float('Ins. Disco', tracking=True, store=True)
    copay = fields.Float('Copay(%)', tracking=True)
    partner_company_id = fields.Many2one('res.partner', string='Insurance Company', tracking=True)
    doctor = fields.Many2one('res.partner', string='Doctor', tracking=True)
    clinic = fields.Many2one('res.partner', string='Clinic', tracking=True)
    insurance_company_type = fields.Many2one(
        'synergia.insurance.company.type',
        string='Insurance Company Type', tracking=True

    )
    insurance_lines = fields.One2many('synergia.insurance.lines', 'order_id', string='Insurance Lines', copy=True, store=True)
    approval_code = fields.Char(string='Approval Code')
    approval_date = fields.Date(string='Approval Date')
    amount_return = fields.Monetary(string='Returned', readonly=True, required=False)

    is_insurance_order = fields.Boolean(compute="_compute_is_insurance_order", store=True)
    patient_paid_amount = fields.Monetary(string='Patient Total Payable Amount', readonly=True, compute='compute_patient_paid_amount')
    patient_share_amount = fields.Monetary(string='Patient Total Payable Amount', readonly=True, compute='compute_patient_paid_amount')
    total_before_discount = fields.Monetary(
        string='Total Before Discount',
        currency_field='currency_id', compute='compute_patient_paid_amount',
        readonly=True, store=True
    )
    total_untaxed_insurance_amount = fields.Monetary(string='Total Untaxed Amount', compute='compute_patient_paid_amount', readonly=True, store=True)
    insurance_disc_amount = fields.Monetary(string='Insurance Discount Amount', compute='compute_patient_paid_amount', readonly=True, store=True)
    insurance_amount = fields.Monetary(string='Insurance Discount Amount', compute='compute_patient_paid_amount', readonly=True, store=True)
    # partner_id = fields.Many2one('res.partner', required=False, string='Customer', index='btree_not_null', change_default=False, copy=False)
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string="Customer",
        required=True, change_default=True, index=True,
        tracking=1,
        check_company=True)
    account_move_ids = fields.One2many('account.move', 'pos_order_id', string='Invoices')
    invoice_count = fields.Integer(compute='_compute_invoice_count')

    @api.depends('account_move_ids', 'account_move_ids.state')
    def _compute_invoice_count(self):
        for order in self:
            order.invoice_count = len(order.account_move_ids)
            # order.failed_pickings = bool(order.picking_ids.filtered(lambda p: p.state != 'done'))

    def _is_pos_order_paid(self):
        if self.is_insurance_order:
            amount_total = self.patient_share_amount
            # If we are checking if a refund was paid and if it was a total refund, we take into account the amount paid on
            # the original order. For a pertial refund, we take into account the value of the items returned.
            if float_is_zero(self.refunded_order_id.amount_total + amount_total, precision_rounding=self.currency_id.rounding):
                amount_total = -self.refunded_order_id.amount_paid
            return float_is_zero(self._get_rounded_amount(amount_total) - self.amount_paid, precision_rounding=self.currency_id.rounding)
        else:
            super()._is_pos_order_paid()

    def action_pos_order_paid(self):
        if self.is_insurance_order:
            self.ensure_one()

            # TODO: add support for mix of cash and non-cash payments when both cash_rounding and only_round_cash_method are True
            if not self.config_id.cash_rounding \
               or self.config_id.only_round_cash_method \
               and not any(p.payment_method_id.is_cash_count for p in self.payment_ids):
                total = self.patient_share_amount
            else:
                total = float_round(self.patient_share_amount, precision_rounding=self.config_id.rounding_method.rounding, rounding_method=self.config_id.rounding_method.rounding_method)

            isPaid = float_is_zero(total - self.amount_paid, precision_rounding=self.currency_id.rounding)

            if not isPaid and not self.config_id.cash_rounding:
                raise UserError(_("Order %s is not fully paid.", self.name))
            elif not isPaid and self.config_id.cash_rounding:
                currency = self.currency_id
                if self.config_id.rounding_method.rounding_method == "HALF-UP":
                    maxDiff = currency.round(self.config_id.rounding_method.rounding / 2)
                else:
                    maxDiff = currency.round(self.config_id.rounding_method.rounding)

                diff = currency.round(self.patient_share_amount - self.amount_paid)
                if not abs(diff) <= maxDiff:
                    raise UserError(_("Order %s is not fully paid.", self.name))

            self.write({'state': 'paid'})

            return True
        else:
            super().action_pos_order_paid()

    @api.depends('lines.patient_share_amount', 'insurance_lines.price_subtotal', 'insurance_lines.patient_share_amount')
    def compute_patient_paid_amount(self):
        for order in self:
            patient_share_total = sum(order.lines.mapped('patient_share_amount'))
            insurance_total = sum(order.insurance_lines.mapped('price_subtotal'))
            order.patient_paid_amount = patient_share_total
            order.total_before_discount = insurance_total
            order.patient_share_amount = sum(order.insurance_lines.mapped('patient_share_amount'))
            order.total_untaxed_insurance_amount = sum(order.insurance_lines.mapped('total_insu_amt'))
            order.insurance_disc_amount = sum(order.insurance_lines.mapped('ins_disc_amount'))
            order.insurance_amount = sum(order.insurance_lines.mapped('insurance_amount'))

    @api.depends('type_of_order')
    def _compute_is_insurance_order(self):
        for order in self:
            order.is_insurance_order = order.type_of_order.name == 'Insurance' if order.type_of_order else False
        # for order_line in self.lines:
        #     order_line.is_insurance_order = order_line.order_id.type_of_order.name == 'Insurance' if order_line.order_id.type_of_order else False

    @api.onchange('insurance_plan')
    def onchange_insurance_plan(self):
        insurance_plan = self.env['synergia.insurance.plan'].search([('id', '=', self.insurance_plan.id)])
        if insurance_plan:
            self.ins_disc = insurance_plan.ins_disc
            self.copay = insurance_plan.copay

    @api.onchange("type_of_order")
    def _compute_insurance_type_id(self):
        """Find the ID of the 'Insurance' order type"""
        print('ssssssssssssssssss', self.type_of_order.name, self.session_id, self.fiscal_position_id)
        if not self.session_id:
            self.session_id = self.env['pos.session'].search([('state', '=', 'opened')], limit=1)
        if not self.fiscal_position_id:
            self.fiscal_position_id = self.session_id.config_id.default_fiscal_position_id.id
        self.currency_id = self.env.company.currency_id
        self.company_id = self.env.company

        print('ssssssssssssssssss', self.type_of_order.name, self.session_id, self.fiscal_position_id)
        for rec in self.lines:
            # Ensure that the type of order is mapped to a valid selection value
            print('rec.order_id.type_of_order12222222222222', rec.order_id.type_of_order, self.session_id.config_id)
            if rec.order_id.type_of_order.name == 'Insurance':
                rec.product_type = 'insurance'
            else:
                rec.product_type = 'non_insurance'
            print('rec.product_type33333333333333', rec.product_type)

    # @api.constrains('patient_eid')
    # def _check_patient_eid_format(self):
    #     pattern = r'^\d{3}-\d{4}-\d{5}-\d{2}-\d{1}$'
    #     for record in self:
    #         if record.patient_eid and not re.match(pattern, record.patient_eid):
    #             raise ValidationError("Invalid Patient EID format! Use: 000-0000-00000-00-0")

    @api.onchange('patient_phone_no',)
    def onchange_phone_no(self):
        if self.patient_phone_no:
            patient = self.env['res.partner'].search([
                ('phone', '=', self.patient_phone_no)
            ], limit=1)
            # for rec in self:

            if patient:
                    self.patient_name = patient.name
                    self.patient_email = patient.email
                    self.patient_eid = patient.eid
                    self.patient_eid_expiry = patient.eid_expiry_date
                    self.partner_id = patient
                    self.patient_phone_no = patient.phone
            print('patientpatientpatient', patient, self.partner_id, patient.eid)
            # elif not patient:
            #     print('elifffffffffffffff')
            #     self.env['res.partner'].create({
            #             'name': self.patient_name,
            #             'email': self.patient_email,
            #             'eid': self.patient_eid,
            #             'eid_expiry_date': self.patient_eid_expiry,
            #             'is_patient': True,
            #         })
            # else:
            #     print('elseeeeeeeeeeeeeee')
            #     self.env['res.partner'].write({
            #         'name': self.patient_name,
            #         'email': self.patient_email,
            #         'eid': self.patient_eid,
            #         'eid_expiry_date': self.patient_eid_expiry,
            #         'is_patient': True,
            #     })



    @api.model_create_multi
    def create(self, vals_list):
        print('vals_listvals_listvals_list', vals_list)

        patient = self.env['res.partner'].search([
            ('phone', '=', vals_list[0]['patient_phone_no'])
        ], limit=1)
        print('kkkkkkkkkkkkkkkkkkkkkkk', patient.type, patient.name, patient.phone, patient.name)
        # self.partner_id = patient
        if not patient:
            patient = self.env['res.partner'].create({
                'name': vals_list[0]['patient_name'],
                'email': vals_list[0]['patient_email'],
                'eid': vals_list[0]['patient_eid'],
                'eid_expiry_date': vals_list[0]['patient_eid_expiry'],
                'phone': vals_list[0]['patient_phone_no'],
                'type': 'contact',
                'is_patient': True,
            })

        else:
            patient.write({
                'name': vals_list[0]['patient_name'],
                'email': vals_list[0]['patient_email'],
                'eid': vals_list[0]['patient_eid'],
                'eid_expiry_date': vals_list[0]['patient_eid_expiry'],
                'phone': vals_list[0]['patient_phone_no'],
                'type': 'contact',
                'is_patient': True,
            })
        self.partner_id = patient
        res = super().create(vals_list)
        return res

    def write(self, vals):
        res = super().write(vals)
        patient = self.env['res.partner'].search([
            ('phone', '=', self.patient_phone_no)
        ], limit=1)
        print('patientpatientpatient', patient, vals)
        if patient:
            patient.write({
                'is_patient': True,
            })
            if vals.get('patient_name'):
                patient.name = vals['patient_name']
            if vals.get('patient_email'):
                patient.email = vals['patient_email']
            if vals.get('patient_eid'):
                patient.eid = vals['patient_eid']
            if vals.get('patient_eid_expiry'):
                patient.eid_expiry = vals['patient_eid_expiry']
            if vals.get('patient_phone_no'):
                patient.phone = vals['patient_phone_no']
        else:
            patient = self.env['res.partner'].create({
                'name': vals.get('patient_name'),  # Using .get() here too
                'email': vals.get('patient_email'),
                'eid': vals.get('patient_eid'),
                'eid_expiry_date': vals.get('patient_eid_expiry'),
                'phone': vals.get('patient_phone_no'),
                'type': 'contact',
                'is_patient': True,
            })
            self.partner_id = patient

        return res

    def action_print_receipt(self):
        print('receipt')
        if self.state == 'paid':
            # Replace 'your_module.report_name' with the actual report ID
            return self.env.ref('synergia_pharmacy.synergia_pharmacy_receipt_report').report_action(self)

    def amount_to_text(self, amount, currency):
        lang = currency.position == 'after' and 'en' or 'en'
        amount_in_words = num2words(amount, to='currency', lang=lang)
        return amount_in_words

    def _generate_pos_order_invoice(self):
        # Initialize moves as an empty recordset for storing generated invoices
        res = super()._generate_pos_order_invoice()
        if self.is_insurance_order:
            moves = self.env['account.move']

            for order in self:
                if not order.partner_id:
                    raise UserError(_('Please provide a partner for the sale.'))

                # Generate the first invoice (standard)
                first_invoice_vals = order._prepare_invoice_vals()
                first_invoice_lines = [(0, 0, {
                    'product_id': line.product_id.id,  # Corrected: .id to reference the product ID
                    'quantity': line.qty,
                    'price_unit': line.price_unit,
                    'insurance_discount_percentage': line.ins_disc_percentage,
                    'copay_percentage': line.copay,
                    'subtotal_after_ins_disc_amt': line.subtotal_after_ins_disc_amt,
                    'patient_share_amount': line.patient_share_amount,
                    'price_subtotal': line.price_subtotal - line.patient_share_amount,
                }) for line in order.lines]  # Assuming you want to add insurance lines to the first invoice too

                # Update the first invoice values
                first_invoice_vals.update({
                    'pos_order_id': order.id,
                    'insurance_amount': order.insurance_amount,  # Custom insurance amount for first invoice
                    'invoice_line_ids': first_invoice_lines,  # Updated lines for the first invoice
                })
                first_move = order._create_invoice(first_invoice_vals)
                order.state = 'invoiced'
                first_move.sudo().with_company(order.company_id).with_context(skip_invoice_sync=True)._post()

                # Generate the insurance invoice with custom values (only modified fields)
                insurance_invoice_vals = order._prepare_invoice_vals()  # Copy the original invoice values

                # Modify the invoice values specifically for the insurance invoice (only the updated fields)
                invoice_lines = [(0, 0, {
                    'product_id': line.product_id.id,  # Correctly reference the product ID
                    'quantity': line.qty,
                    'price_unit': line.price_unit,
                    'insurance_discount_percentage': line.ins_disc_percentage,
                    'copay_percentage': line.copay,
                    'subtotal_after_ins_disc_amt': line.subtotal_after_ins_disc_amt,
                    'patient_share_amount': line.patient_share_amount,
                    'price_subtotal': line.price_subtotal-line.patient_share_amount,
                }) for line in order.insurance_lines]

                # Now update insurance_invoice_vals with only the necessary changes
                insurance_invoice_vals.update({
                    'partner_id':order.partner_company_id,
                    'pos_order_id': order.id,
                    'insurance_amount': order.insurance_amount,  # Custom insurance amount
                    'invoice_line_ids': invoice_lines,  # Updated lines for the insurance invoice
                    'copay_amount': order.patient_share_amount,
                    'insurance_discount': order.insurance_disc_amount,
                    'total_payable_amount': order.insurance_amount
                })

                # Create the insurance invoice with custom values (only updated values)
                insurance_invoice_move = order.env['account.move'].create(insurance_invoice_vals)
                insurance_invoice_move.sudo().with_company(order.company_id).with_context(skip_invoice_sync=True)._post()

                # Add both invoices (first and insurance) to the moves collection
                moves |= first_move  # Add the first invoice
                moves |= insurance_invoice_move   # Add the insurance invoice with updated values

                # Apply payments and other actions if necessary
                payment_moves = order._apply_invoice_payments(order.session_id.state == 'closed')

                # Send and Print (generate PDF)
                if self.env.context.get('generate_pdf', True):
                    first_move.with_context(skip_invoice_sync=True)._generate_and_send()
                    insurance_invoice_move.with_context(skip_invoice_sync=True)._generate_and_send()

                # Create a reversal move if session is closed
                if order.session_id.state == 'closed':
                    order._create_misc_reversal_move(payment_moves)
        return res

    def action_view_invoice(self):
        # Call the original method to retain the base functionality
        # res = super().action_view_invoice()
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('synergia_pharmacy.action_account_move_tree_ready')
        action['display_name'] = _('Invoices')
        action['context'] = {}
        action['domain'] = [('id', 'in', self.account_move_ids.ids)]
        return action
        # return res
