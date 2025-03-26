from odoo import models, fields, api


class InsurancePlan(models.Model):
    _name = 'synergia.insurance.plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Insurance Plan'

    name = fields.Char('Name', required=True, tracking=True)
    code = fields.Char('Code', tracking=True)
    ins_disc = fields.Float('Ins. Disco', required=True, tracking=True)
    copay = fields.Float('Copay(%)', tracking=True)
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm')], string="Status", tracking=True, default='draft')

    def confirm(self):
        self.state = 'confirm'

    def reset_to_draft(self):
        self.state = 'draft'



class PartnerInsurancePlan(models.Model):
    _name = 'synergia.partner.insurance.plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    insurance_plan = fields.Many2one('synergia.insurance.plan',  tracking=True)
    ins_disc = fields.Float('Ins. Disco',  tracking=True)
    copay = fields.Float('Copay(%)', readonly=1,  tracking=True)
    partner_id = fields.Many2one('res.partner', string='Insurance Company',  tracking=True)
    # pos_id = fields.Many2one('pos.order', string='Insurance Details')
    insurance_company_type = fields.Many2one(
        'synergia.insurance.company.type',
        string='Insurance Company Type',  tracking=True

    )

    @api.onchange('insurance_plan')
    def onchange_insurance_plan(self):
        insurance_plan = self.env['synergia.insurance.plan'].search([('id', '=', self.insurance_plan.id)])
        if insurance_plan:
            self.ins_disc = insurance_plan.ins_disc
            self.copay = insurance_plan.copay



class CustomerType(models.Model):
    _name = 'synergia.insurance.company.type'
    _description = 'Insurance Company Type'

    name = fields.Char('Name', required=True)
    code = fields.Char('Code', required=True)

