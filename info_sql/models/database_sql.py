from odoo import models, fields


class DatabaseSQL(models.Model):
    _name = 'database.sql'
    _description = 'Database SQL'

    name_database = fields.Char("Tên Database")
    sql_seversql = fields.Char("Phiên bản SQL Server")
    telegraf_data_id = fields.Many2one('telegraf.data', string="Telegraf Data")
    name = fields.Char("Database", required=True)
    table_ids = fields.One2many('table.sql', 'database_id', string="Tables" )
    column_ids = fields.One2many( 'table.column.sql', 'database_id', string="Columns")
    partner_ids = fields.Many2many(comodel_name='res.partner', string='Người phụ trách', required=False)


class TableSQL(models.Model):
    _name = 'table.sql'
    _description = 'Table Info'

    name_table = fields.Char("Tên bảng", required=True)
    record_date = fields.Date("Ngày ghi nhận", default=fields.Date.context_today)
    sum_record = fields.Integer("Tổng số dữ liệu")
    database_id = fields.Many2one('database.sql', string="Database")


class TableColumnSQL(models.Model):
    _name = 'table.column.sql'
    _description = 'Table Column Info'

    column_name = fields.Char("Tên cột", required=True)
    data_type = fields.Char("Kiểu dữ liệu")
    database_id = fields.Many2one('database.sql', string="Database")
