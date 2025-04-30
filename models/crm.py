from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta
import base64
import csv
from io import StringIO

class CrmLeadImportWizard(models.TransientModel):
    _name = 'crm.lead.import.wizard'
    _description = 'Import Leads Wizard'

    csv_file = fields.Binary(string="CSV File", required=True)
    csv_filename = fields.Char(string="CSV Filename")

    def action_import(self):
        if not self.csv_file:
            raise ValidationError(_("Please upload a CSV file."))

        csv_data = base64.b64decode(self.csv_file).decode('utf-8')
        csv_reader = csv.DictReader(StringIO(csv_data))

        required_columns = ["City/Town", "Customer", "Email", "Opportunity", "Phone", "Referred By", "Sales Team", "Source"]
        for column in required_columns:
            if column not in csv_reader.fieldnames:
                raise ValidationError(_("The CSV file is missing the required column: %s") % column)

        # Use importing_leads context
        ctx = {'importing_leads': True}
        for row in csv_reader:
            partner = self.env['res.partner'].search([('name', '=', row['Customer'])], limit=1)
            if not partner:
                partner = self.env['res.partner'].create({'name': row['Customer']})

            team = self.env['crm.team'].search([('name', '=', row['Sales Team'])], limit=1)
            source = self.env['utm.source'].search([('name', '=', row['Source'])], limit=1)
            referred_by = self.env['hr.employee'].search([('name', '=', row['Referred By'])], limit=1)

            self.env['crm.lead'].with_context(ctx).sudo().create({
                'name': row['Opportunity'],
                'partner_id': partner.id,
                'email_from': row['Email'],
                'phone': row['Phone'],
                'city': row['City/Town'],
                'source_id': source.id if source else False,
                'team_id': team.id if team else False,
                'referred_by': referred_by.id if referred_by else False,
                'type': 'lead',
            })

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

class CrmStage(models.Model):
    _inherit = "crm.stage"
    probability = fields.Float(string="Probability")

class CRMLead(models.Model):
    _inherit = 'crm.lead'

    date_closed = fields.Datetime(
        string='Closed Date',
        tracking=True,
        readonly=False,
        copy=False,
        help="Date this lead/opportunity was closed."
    )

    # Selection field for Mode of Study
    mode_of_study = fields.Selection([
        ('offline', 'Offline'),
        ('online', 'Online')
    ], string="Mode of Study", default='offline')

    avatar_128 = fields.Binary(string="Avatar 128", related='partner_id.avatar_128', store=True, readonly=False)
    image_1920 = fields.Binary(string="Image", related="partner_id.image_1920", store=True, readonly=False)

    whatsapp_number = fields.Char(string="WhatsApp Number", related="partner_id.whatsapp_number", store=True, readonly=False)
    date_of_birth = fields.Date(string="Date of Birth", related="partner_id.date_of_birth", store=True, readonly=False)
    age = fields.Integer(string="Age", related="partner_id.age", store=True, readonly=False)
    father_guardian = fields.Char(string="Father/Guardian", related="partner_id.father_guardian", store=True, readonly=False)
    qualification = fields.Char(string="Qualification", related="partner_id.qualification", store=True, readonly=False)
    street = fields.Char(string="Address 1", related='partner_id.street', store=True, readonly=False)
    street2 = fields.Char(string="Address 2", related='partner_id.street2', store=True, readonly=False)
    city = fields.Char(string="City/Town", related='partner_id.city', store=True, readonly=False)
    district = fields.Char(string="District", store=True, readonly=False)
    country_id = fields.Many2one('res.country',string="Country", related='partner_id.country_id', store=True, readonly=False, default=lambda self: self.env.company.country_id.id)
    state_id = fields.Many2one('res.country.state',string="State", related='partner_id.state_id', store=True, readonly=False, default=lambda self: self.env.company.state_id.id)
    mobile_alt = fields.Char(string="Mobile (Alt)", related='partner_id.mobile_alt', store=True, readonly=False)

    aadhaar_no = fields.Char(string="Student Aadhaar No", related='partner_id.aadhaar_no', store=True, readonly=False)
    # Bank Details
    bank_account_name = fields.Char(string="Account Holder Name", related='partner_id.bank_account_name', store=True, readonly=False)
    bank_account_no = fields.Char(string="Account No", related='partner_id.bank_account_no', store=True, readonly=False)
    bank_ifsc_code = fields.Char(string="IFSC Code", related='partner_id.bank_ifsc_code', store=True, readonly=False)
    bank_name = fields.Char(string="Bank Name", related='partner_id.bank_name', store=True, readonly=False)
    relation_with_bank_acc_holder = fields.Selection(
        selection=[('self', 'Self/Own'),('spouse', 'Spouse'),
            ('mother', 'Mother'),('father', 'Father'),('grand_father', 'Grand Father'),
            ('grand_mother', 'Grand Mother'),('uncle', 'Uncle'),
            ('aunt', 'Aunt'),('brother', 'Brother'),
            ('sister', 'Sister'),('son', 'Son'),
            ('daughter', 'Daughter'),('other', 'Other (Specify)')
        ],
        string="Relationship with Account Holder", default="self", related='partner_id.relation_with_bank_acc_holder', store=True, readonly=False
    )

    categ_id = fields.Many2one('product.category',string='Product Category',compute='_compute_category', store=True)
    @api.depends('course_id')
    def _compute_category(self):
        for rec in self:
            rec.categ_id = rec.course_id.categ_id.id if rec.course_id else False
    relation_with_bank_acc_holder_manual = fields.Char(string="Specify Relation", related='partner_id.relation_with_bank_acc_holder_manual', store=True, readonly=False)

    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id.id)
    course_id = fields.Many2one('product.product', string="Course", required=False)
    enrollment_number = fields.Char(string="Enrollment No", )

    expected_revenue = fields.Monetary(compute="_compute_expected_revenue", store=True, readonly=False, required=True)
    
    referred_by = fields.Many2one('hr.employee', string="Referred By")
    @api.depends('course_id')
    def _compute_expected_revenue(self):
        for record in self:
            if record.course_id:
                record.expected_revenue = record.course_id.list_price

    # Override the built-in probability compute method
    probability = fields.Float(compute="_compute_probability")

    @api.depends('stage_id')
    def _compute_probabilities(self):
        for lead in self:
            if lead.stage_id:
                lead.probability = lead.stage_id.probability

    invoice_status = fields.Selection(
        selection=lambda self: self.env["sale.order"]._fields["invoice_status"].selection,
        related="sale_order_id.invoice_status",
        string="Invoice Status",
        readonly=True, copy=False,
        )
    
    is_won = fields.Boolean(related='stage_id.is_won')
    sale_order_id = fields.Many2one('sale.order', string="Sale Order")

    def action_create_sale_order(self):
        if not self.partner_id:
            raise ValidationError(f'You need to set a Customer before confirming the Sale!')
        if not self.course_id:
            raise ValidationError(f'You need to selecte a Course before confirming the Sale!')

        if not self.aadhaar_no or not self.bank_account_name or not self.bank_account_no or not self.bank_ifsc_code or not self.bank_name or not self.relation_with_bank_acc_holder:
            raise ValidationError(f'You have to fill the following fields before confirming Sale:\n Aadhaar No, Account Holder Name, Account No, IFSC Code, Bank Name, Relationship with Account Holder')
        sale_order_data = {
            'opportunity_id': self.id,
            'partner_id': self.partner_id.id,
            'campaign_id': self.campaign_id.id,
            'medium_id': self.medium_id.id,
            'origin': self.name,
            'source_id': self.source_id.id,
            'company_id': self.company_id.id or self.env.company.id,
            'tag_ids': [(6, 0, self.tag_ids.ids)],
            'order_line': [
                (0,0, {
                    'product_id': self.course_id.id,
                })
                ]
        }
        if self.team_id:
            sale_order_data['team_id'] = self.team_id.id
        if self.user_id:
            sale_order_data['user_id'] = self.user_id.id

        sale_order = self.env['sale.order'].create(sale_order_data)
        sale_order.action_confirm()
        self.sale_order_id = sale_order.id

    def action_create_invoice(self):
        if self.sale_order_id:
            return {
                'name': _('Create Invoice'),
                'res_model': 'sale.advance.payment.inv',
                'view_mode': 'form',
                'context': {
                    'active_model': 'sale.order',
                    'active_ids': [self.sale_order_id.id],
                },
                'target': 'new',
                'type': 'ir.actions.act_window',
            }
    invoice_count = fields.Integer(related="sale_order_id.invoice_count")
        
    def action_view_invoice(self):
        if self.sale_order_id:
            if self.invoice_count > 0:
                return self.sale_order_id.action_view_invoice()

    @api.model_create_multi
    def create(self, vals):
        res = super(CRMLead, self).create(vals)
        if not self.env.context.get('importing_leads'):
            for record in res:
                record.set_lead_queue()
                if record.type == 'opportunity':
                    record._check_course_id_required()
                    record._check_source_id_required()
        return res
    
    def write(self, vals):
        # Store old user_id before write
        old_user_ids = {record.id: record.user_id.id for record in self}
        
        res = super(CRMLead, self).write(vals)
        
        # If user_id (salesperson) changed, reassign pending activities
        if 'user_id' in vals:
            for record in self:
                old_user_id = old_user_ids[record.id]
                new_user_id = vals['user_id']
                if old_user_id != new_user_id:
                    # Get all pending activities for this lead
                    activities = self.env['mail.activity'].search([
                        ('res_id', '=', record.id),
                        ('res_model', '=', 'crm.lead'),
                        ('user_id', '=', old_user_id),
                        ('state', '!=', 'done')
                    ])
                    # Reassign activities to new user
                    if activities:
                        activities.write({'user_id': new_user_id})
        
        # Add check for type change (lead to opportunity conversion)
        converting_to_opportunity = vals.get('type') == 'opportunity'
        res = super(CRMLead, self).write(vals)
        if not self.env.context.get('importing_leads'):
            for record in self:
                record.set_lead_queue()
                # Only check source and course if converting to opportunity or updating specific fields
                if converting_to_opportunity or any(f in vals for f in ['stage_id', 'source_id', 'course_id']):
                    if record.type == 'opportunity':
                        record._check_course_id_required()
                        record._check_source_id_required()
        return res

    def set_lead_queue(self):
        for record in self:
            if record.team_id and record.type=='lead' and not record.user_id:
                if record.team_id.queue_line_ids:
                    all_users_assigned_lead = len(record.team_id.queue_line_ids.mapped('current_lead')) == len(record.team_id.queue_line_ids)
                    # Reset current lead of all salespersons to False, to allow allocating new leads to them in next round
                    if all_users_assigned_lead:
                        record.team_id.queue_line_ids[0].write({'current_lead': record.id})
                        record.write({'user_id': record.team_id.queue_line_ids[0].salesperson_id.id})
                        for queue_line in record.team_id.queue_line_ids[1:]:
                            queue_line.write({'current_lead': False})
                    else:
                        for queue_line in record.team_id.queue_line_ids:
                            # If no lead is assigned to this salesperson in current round
                            if not queue_line.current_lead:
                                queue_line.write({'current_lead': record.id})
                                record.write({'user_id': queue_line.salesperson_id.id})
                                break

    date_deadline = fields.Date(string="Deadline", required=False)

    def _check_course_id_required(self):
        # Skip all validations if importing leads
        if self.env.context.get('importing_leads'):
            return
        required_stages = ['Prospect (P)', 'Hot Prospect (HP)']
        malayalee_required_stages = ['Neutral Prospect (NP)', 'Prospect (P)', 'Hot Prospect (HP)', 'Admission (A)']
        
        for record in self:
            if record.type == 'opportunity':
                # Validate malayalee status for specific stages
                if record.stage_id.name in malayalee_required_stages and not record.malayalee_status:
                    raise ValidationError(_('You need to select Malayalee Status when the lead is in stage: %s') % record.stage_id.name)
                
                # Existing validations
                if record.stage_id.name in required_stages:
                    if not record.course_id:
                        raise ValidationError(_('You need to select a Course when the lead is in stage: %s') % record.stage_id.name)
                    if not record.date_deadline:
                        raise ValidationError(_('You need to set a Deadline when the lead is in stage: %s') % record.stage_id.name)

    def _check_source_id_required(self):
        # Skip validation if importing leads
        if self.env.context.get('importing_leads'):
            return
        for record in self:
            # Only validate if it's an opportunity and in a relevant stage
            if record.type == 'opportunity' and record.stage_id.name not in ['Lost', 'Won']:
                if not record.source_id:
                    # Set a default source if missing
                    default_source = self.env['utm.source'].search([('name', '=', 'Unknown')], limit=1)
                    if not default_source:
                        default_source = self.env['utm.source'].create({'name': 'Unknown'})
                    record.source_id = default_source

    def action_import_lead(self):
        # Logic to handle lead import
        self.ensure_one()
        if not self.source_id:
            raise ValidationError(_('You need to select a Source for the lead.'))
        if not self.date_deadline:
            raise ValidationError(_('You need to set a Deadline for the lead.'))
        # Additional import logic here
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def action_change_expected_revenue(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Change Expected Revenue',
            'res_model': 'crm.lead.change.revenue.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_currency_id': self.currency_id.id},
        }

    def action_open_collection_form(self):
        collection = self.env['crm.lead.collection'].search([('lead_id', '=', self.id), ('state', '=', 'pending')], limit=1)
        if collection:
            view_id = self.env.ref('tijus_crm_custom.view_crm_lead_collection_form').id
            return {
                'type': 'ir.actions.act_window',
                'name': 'Collect Payment',
                'res_model': 'crm.lead.collection',
                'view_mode': 'form',
                'view_id': view_id,
                'res_id': collection.id,
                'target': 'new',
            }
        else:
            raise ValidationError(_('No pending collections found for this lead.'))

    sales_objection = fields.Selection([
        ('trust', 'Trust'),
        ('fees', 'Fees'),
        ('need', 'Need'),
        ('stall', 'Stall')
    ], string="Sales Objection", tracking=True)

    malayalee_status = fields.Selection([
        ('malayalee', 'Malayalee'),
        ('non_malayalee', 'Non-Malayalee')
    ], string="Malayalee Status", tracking=True)

    date_closed_editable = fields.Boolean('Allow Editing Date Closed', default=False)

    def edit_date_closed(self):
        """Toggle editability of date_closed field"""
        self.ensure_one()
        self.date_closed_editable = not self.date_closed_editable
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        if custom_values is None:
            custom_values = {}
        
        # Extract information from the message body
        if msg_dict.get('body'):
            body = msg_dict['body']
            
            # Clean HTML tags and convert <br> to newlines
            import re
            from html import unescape
            
            # Remove HTML tags but keep the content
            body = re.sub(r'<[^>]+>', '\n', body)
            body = unescape(body)  # Convert HTML entities
            body = re.sub(r'\n+', '\n', body)  # Remove multiple newlines
            
            # Split the body into lines for processing
            lines = body.strip().split('\n')
            
            # Initialize variables
            name = None
            phone = None
            email = None
            whatsapp = None
            course_mode = None

            # Try to detect the format (detailed form vs simple form)
            if 'First Name:' in body:
                # Detailed form format
                first_name = re.search(r'First Name:\s*([^\n]+)', body)
                last_name = re.search(r'Last Name:\s*([^\n]+)', body)
                name = ''
                if first_name:
                    name += first_name.group(1).strip()
                if last_name:
                    name += ' ' + last_name.group(1).strip()
                
                email = re.search(r'Email:\s*([^\n]+)', body)
                phone = re.search(r'Phone Number\s*:\s*([^\n]+)', body)
                whatsapp = re.search(r'Whatsapp Number\s*:\s*([^\n]+)', body)
                course_mode = re.search(r'Course Mode\s*:\s*([^\n]+)', body)
            else:
                # Simple form format - first line is name, second line might be phone
                if len(lines) >= 1:
                    name = lines[0].strip()
                    # Look for phone number in first few lines
                    for line in lines[1:4]:  # Check first few lines
                        # Match phone number (with or without +91)
                        clean_line = line.strip()
                        if re.match(r'^\+?(?:91)?[6-9]\d{9}$', clean_line.replace(' ', '')):
                            phone = clean_line
                            break
            
            # Check for duplicates if email or phone exists
            if email or phone:
                domain = []
                if email:
                    email_value = email.group(1).strip() if hasattr(email, 'group') else email
                    if email_value:
                        domain.append(('email_from', '=', email_value))
                if phone:
                    phone_value = phone.group(1).strip() if hasattr(phone, 'group') else phone
                    if phone_value:
                        domain.append(('phone', '=', phone_value))
                
                if domain:
                    existing_lead = self.env['crm.lead'].search(['|'] + domain, limit=1)
                    if existing_lead:
                        return existing_lead
            
            # Update custom values with extracted information
            if name:
                custom_values['name'] = name.strip()
                # Create or update partner
                partner_vals = {
                    'name': name.strip(),
                    'email': email.group(1).strip() if email and hasattr(email, 'group') else False,
                    'phone': phone.group(1).strip() if phone and hasattr(phone, 'group') else (phone if phone else False),
                    'whatsapp_number': whatsapp.group(1).strip() if whatsapp else False,
                }
                partner = self.env['res.partner'].create(partner_vals)
                custom_values['partner_id'] = partner.id
            
            if email and hasattr(email, 'group'):
                custom_values['email_from'] = email.group(1).strip()
            if phone:
                custom_values['phone'] = phone.group(1).strip() if hasattr(phone, 'group') else phone
            if course_mode and hasattr(course_mode, 'group'):
                mode = course_mode.group(1).strip().lower()
                custom_values['mode_of_study'] = 'online' if 'online' in mode else 'offline'
            
            # Set source as Google Ads
            google_ads_source = self.env['utm.source'].search([('name', '=', 'Google Ads')], limit=1)
            if not google_ads_source:
                google_ads_source = self.env['utm.source'].create({'name': 'Google Ads'})
            custom_values['source_id'] = google_ads_source.id
            
            # Set type as lead
            custom_values['type'] = 'lead'
        
        return super(CRMLead, self).message_new(msg_dict, custom_values)

class CrmLeadChangeRevenueWizard(models.TransientModel):
    _name = 'crm.lead.change.revenue.wizard'
    _description = 'Change Expected Revenue Wizard'

    new_expected_revenue = fields.Monetary(string="New Expected Revenue", required=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.company.currency_id.id)
    next_collection_date = fields.Date(string="Next Collection Date", required=True)

    def action_change_revenue(self):
        lead = self.env['crm.lead'].browse(self.env.context.get('active_id'))
        lead.expected_revenue = self.new_expected_revenue
        lead.activity_schedule(
            'mail.mail_activity_data_todo',
            date_deadline=self.next_collection_date,
            summary=_('Collect Pending Fee'),
            note=_('Please collect the pending fee from the customer.')
        )
        self.env['crm.lead.collection'].create({
            'lead_id': lead.id,
            'collection_date': self.next_collection_date,
            'amount': self.new_expected_revenue,
        })

class CrmLeadCollection(models.Model):
    _name = 'crm.lead.collection'
    _description = 'CRM Lead Collection'

    lead_id = fields.Many2one('crm.lead', string="Lead", required=True)
    collection_date = fields.Date(string="Collection Date", required=True)
    amount = fields.Monetary(string="Amount", required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.company.currency_id.id)
    collected_amount = fields.Monetary(string="Collected Amount", default=0.0)
    balance = fields.Monetary(string="Balance", compute="_compute_balance", store=True)
    state = fields.Selection([('pending', 'Pending'), ('collected', 'Collected')], string="State", default='pending')

    @api.depends('amount', 'collected_amount')
    def _compute_balance(self):
        for record in self:
            record.balance = record.amount - record.collected_amount
            if record.balance <= 0:
                record.state = 'collected'
            else:
                record.state = 'pending'

    def action_enter_collected_amount(self):
        view_id = self.env.ref('tijus_crm_custom.view_enter_collected_amount_form').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Enter Collected Amount',
            'res_model': 'crm.lead.collection.enter.amount',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'new',
            'context': {'default_collection_id': self.id},
        }

class CrmLeadCollectionEnterAmount(models.TransientModel):
    _name = 'crm.lead.collection.enter.amount'
    _description = 'Enter Collected Amount'

    collection_id = fields.Many2one('crm.lead.collection', string="Collection", required=True)
    collected_amount = fields.Monetary(string="Collected Amount", required=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency', related='collection_id.currency_id', readonly=True)

    def action_confirm(self):
        self.collection_id.collected_amount += self.collected_amount
        self.collection_id._compute_balance()
        return {'type': 'ir.actions.act_window_close'}

class CrmTeam(models.Model):
    _inherit = "crm.team"
    queue_line_ids = fields.One2many('crm.lead.queueing.line', 'team_id', store=True)

    def create(self, vals):
        res = super().create(vals)
        self.set_queue_line_ids(res)
        return res
    
    def write(self, vals):
        res = super().write(vals)
        self.set_queue_line_ids(self)
        return res
    
    def set_queue_line_ids(self, recs):
        for record in recs:
            queue_line_users = record.queue_line_ids.mapped('salesperson_id.id')
            for member in record.member_ids:
                # Create queue line for the new member
                if member.id not in queue_line_users:
                    self.env['crm.lead.queueing.line'].create({
                        'salesperson_id': member.id,
                        'current_lead': False,
                        'team_id': record.id
                    })
            # Remove queue lines for non existing members
            record.queue_line_ids.filtered(lambda line: line.salesperson_id.id not in record.member_ids.ids).unlink()

    @api.model
    def action_set_queue_line_ids_for_all_teams(self):
        recs = self.env['crm.team'].search([])
        self.set_queue_line_ids(recs)

class CrmLeadQueueingLine(models.Model):
    _name = "crm.lead.queueing.line"
    salesperson_id = fields.Many2one('res.users', string="Salesperson")
    current_lead = fields.Many2one('crm.lead', domain=[('type','=','lead')])
    team_id = fields.Many2one('crm.team', check_company=True)