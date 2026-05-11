# Copyright 2024 OCA Contributors
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    ine_code = fields.Char(
        string="INE Code",
        related="city_id.ine_code",
        store=True,
        readonly=True,
        help="Código INE completo (5 dígitos). Auto-rellenado desde la ciudad.",
    )
    ine_code_province = fields.Char(
        string="INE Province Code",
        related="city_id.ine_code_province",
        store=True,
        readonly=True,
        help="Código de provincia INE (2 dígitos). Auto-rellenado desde la ciudad.",
    )
