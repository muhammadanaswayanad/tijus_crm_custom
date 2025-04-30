from odoo import models, fields, api
from datetime import datetime

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    date_closed_editable = fields.Boolean('Allow Editing Date Closed', default=False)
    date_closed = fields.Datetime('Closed Date', readonly=True, copy=False, tracking=True)

    possible_country = fields.Char(
        string='Possible Country',
        compute='_compute_possible_country',
        store=True,
        help='Country detected based on the phone number'
    )

    def set_date_closed_editable(self):
        """Method to toggle date_closed editability"""
        for record in self:
            record.date_closed_editable = not record.date_closed_editable
        return True

    def write(self, vals):
        # Override write to handle date_closed field editability
        if 'date_closed' in vals and not self.date_closed_editable:
            vals.pop('date_closed')
        return super(CrmLead, self).write(vals)

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        # Override to dynamically set readonly status
        res = super(CrmLead, self).fields_get(allfields, attributes)
        if 'date_closed' in res:
            res['date_closed']['readonly'] = False
        return res

    @api.depends('phone')
    def _compute_possible_country(self):
        for lead in self:
            country = "Unknown"
            flag = ""

            if lead.phone:
                phone = lead.phone.strip()

                # Check for common country codes
                if phone.startswith('+91'):
                    country = "India 🇮🇳"
                    flag = "🇮🇳"
                elif phone.startswith('+1'):
                    country = "USA/Canada 🇺🇸"
                    flag = "🇺🇸"
                elif phone.startswith('+44'):
                    country = "UK 🇬🇧"
                    flag = "🇬🇧"
                elif phone.startswith('+971'):
                    country = "UAE 🇦🇪"
                    flag = "🇦🇪"
                elif phone.startswith('+61'):
                    country = "Australia 🇦🇺"
                    flag = "🇦🇺"

            lead.possible_country = country
