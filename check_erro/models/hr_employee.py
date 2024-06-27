
from odoo import api, fields, models

class HrEmployee(models.Model):
    _inherit = "hr.employee"


    check_web_id = fields.Many2one('website.status')


