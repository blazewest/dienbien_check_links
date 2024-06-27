# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ZaloTemplate(models.Model):
    _name = 'zalo.template'
    _description = 'zalo.template'

    name = fields.Char('Tên Mẫu')
    id_template = fields.Char('Template ID', required=True)
    active = fields.Boolean(string='Kích hoạt', store=True, readonly=True, default=False)
    template_name = fields.Char(related="model.model")
    model = fields.Many2one('ir.model')
    zalo_fields_ids = fields.One2many('field.zalo.api', 'zalo_template_id',
                                              string='List fields zalo', copy=True)
    # contact = fields.Char('Trường liên hệ', required=True)

    _sql_constraints = [('code_id_template_uniq', 'unique (id_template)', 'ID mẫu đã tồn tại!')]

    def active_template(self):
        type_template = self.model.model
        tamplate_active = self.env['zalo.template'].search(
            [('template_name', '=', type_template), ('active', '=', True)])
        tamplate_active.write({'active': False})
        self.active = True
        # Tạo hành động trong ir.actions.server
        if self.model:
            action_vals = {
                'name': f"Action for {self.name}",
                'model_id': self.model.id,
                'state': 'code',
                'code': "model.send_mess_zalo()",
            }
            action_server = self.env['ir.actions.server'].create(action_vals)
            action_server.create_action()


