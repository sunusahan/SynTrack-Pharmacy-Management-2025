from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_insurance_company = fields.Boolean(string="Is Insurance Company")
    is_patient = fields.Boolean(string="Is Patient")
    is_clinic = fields.Boolean(string="Is Clinic")
    is_doctor = fields.Boolean(string="Is Doctor")
    eid = fields.Char(string='EID', unique=True)
    eid_expiry_date = fields.Date(string='EID Expiry Date')
    insurance_plan_ids = fields.One2many('synergia.partner.insurance.plan', 'partner_id', string='Insurance Plans')



    @api.onchange('is_insurance_company','is_patient', 'is_clinic', 'is_doctor')
    def onchange_individual_company(self):
        if self.is_insurance_company or self.is_clinic:
            self.is_company = True
            self.company_type = 'company'
        elif self.is_patient or self.is_doctor:
            self.is_company = False
            self.company_type = 'person'
        else:
            self.is_company = True
            self.company_type = 'company'

    @api.onchange('is_insurance_company')
    def _onchange_insurance_company(self):
        if not self.is_insurance_company:
            # Check if the partner has insurance plans
            if self.insurance_plan_ids:
                # Raise a warning to the user
                raise UserError(_(
                    'Delete insurance plans first, then you can uncheck "Is Insurance Company".')
                )
                # Automatically delete all related insurance plans after the warning
                # self.insurance_plan_ids.unlink()
        # for rec in self:
        if self.is_insurance_company:
            self.is_patient = False
            self.is_doctor = False
            self.is_clinic = False

    @api.onchange('is_clinic')
    def _onchange_clinic(self):
        # for rec in self:
        if self.is_clinic:
            self.is_patient = False
            self.is_doctor = False
            self.is_insurance_company = False

    @api.onchange('is_patient')
    def _onchange_patient(self):
        # for rec in self:
        if self.is_patient:
            self.is_insurance_company = False
            self.is_clinic = False
            self.is_doctor = False

    @api.onchange('is_doctor')
    def _onchange_patient(self):
        # for rec in self:
        if self.is_doctor:
            self.is_insurance_company = False
            self.is_clinic = False
            self.is_patient = False


class CustomerType(models.Model):
    _name = 'synergia.customer.type'
    _description = 'Customer Type'

    name = fields.Char('Name', required=True)
    code = fields.Char('Code', required=True)