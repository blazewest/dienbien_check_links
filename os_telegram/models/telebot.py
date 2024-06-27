from odoo import models, fields, api
from odoo.exceptions import UserError
import telegram
import requests

class TelegramBot(models.Model):
    _name = 'telegram.bot'
    _description = 'Telegram Bot'

    name = fields.Char('Name bot', required=True)
    # manager_id = fields.Many2one('hr.employee', string='Manager')
    token = fields.Char('Bot Token', required=True)
    chat_id = fields.Char('Chat ID')
    info = fields.Char('Chat ID',compute='_compute_code', store=True, readonly=True)
    @api.depends('token')
    def _compute_code(self):
        for record in self:
            url = f"https://api.telegram.org/bot{record.token}/getUpdates"
            try:
                response = requests.get(url)
                record.info = response.json()
            except Exception as e:
                record.info = ""
                raise UserError(f"Failed to get updates from Telegram: {str(e)}")


    def send_message(self, message):
        for record in self:
            if not record.token or not record.chat_id:
                raise UserError('Please configure the bot token and chat ID for each bot.')

            try:
                url = f"https://api.telegram.org/bot{record.token}/sendMessage?chat_id={record.chat_id}&text={message}"
                requests.get(url)
            except Exception as e:
                raise UserError(f"Failed to send message: {str(e)}")
