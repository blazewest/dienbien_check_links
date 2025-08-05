from odoo import models, fields

class ResUsers(models.Model):
    _inherit = 'res.partner'

    id_zalo = fields.Char(string='Zalo ID')
