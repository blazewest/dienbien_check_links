# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ZaloTemplate(models.Model):
    _name = 'field.zalo.api'
    _description = 'field.zalo.api'

    @api.model
    def _compute_root_model_name(self):
        res = self.env['ir.model'].search([('id', '=', self._context.get('root_model_id'))], [])
        if len(res):
            model_name = res.model
            return model_name

    root_model_id = fields.Many2one(string='Report Root Model', related='zalo_template_id.model')
    zalo_template_id = fields.Many2one('zalo.template', string='Section', ondelete='cascade')
    root_model_name = fields.Char(related='root_model_id.model')
    cumulative_model_field = fields.Char(compute='_compute_cumulative_model_field', string='Field ', readonly=True)
    model_field_selector = fields.Char(string='Trường thông tin', default='id')
    field_type = fields.Char(string='Field Type')
    zalo_parameter = fields.Char(string="Tham số zalo")

    @api.depends('model_field_selector')
    def _compute_cumulative_model_field(self):
        for rec in self:
            name = ''
            name = rec.model_field_selector if rec.model_field_selector else ''
            name_split = name.split('.')
            new_name = ''
            model = rec.root_model_name
            field_err = False
            try:
                for i in name_split:
                    field = self.env[model].fields_get([i])
                    display_name = field[i].get('string')
                    field_dict = field[i]
                    if 'relation' in field_dict:
                        rel = field[i].get('relation')
                    else:
                        rel = ''
                    new_name = (new_name + ' --> ' + display_name + '(' + model + ')') if (new_name != '') else (
                            display_name + '(' + model + ')')
                    model = rel
                    field_type = field[i].get('type')
            except KeyError:
                new_name = ' '
                field_err = True
            if not field_err:
                rec.field_type = field_type
            rec.cumulative_model_field = new_name

    @api.model
    def _list_all_models(self):
        self._cr.execute("SELECT model, name FROM ir_model ORDER BY name")
        return self._cr.fetchall()






























