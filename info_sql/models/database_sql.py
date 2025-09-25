from odoo import models, fields


class DatabaseSQL(models.Model):
    _name = 'database.sql'
    _description = 'Database SQL'

    name = fields.Char("Database Name", required=True)
    table_ids = fields.Many2many('table.sql', 'rel_database_table', 'database_id', 'table_id', string="Tables")
    sum_record_ids = fields.Many2many('sum.record.sql', 'rel_database_sumrecord', 'database_id', 'sum_id', string="Row Counts")


class TableSQL(models.Model):
    _name = 'table.sql'
    _description = 'Table Schema Info'

    name_table = fields.Char("Table Name", required=True)
    column_name = fields.Char("Column Name")
    data_type = fields.Char("Data Type")


class SumRecordSQL(models.Model):
    _name = 'sum.record.sql'
    _description = 'Table Row Counts'

    name_table = fields.Char("Table Name", required=True)
    sum_record = fields.Integer("Total Rows")
