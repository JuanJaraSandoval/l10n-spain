# Copyright 2024 OCA Contributors
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResCity(models.Model):
    _inherit = "res.city"

    ine_code_state = fields.Char(
        string="INE State Code",
        size=2,
        help="Código de Comunidad Autónoma del INE (CODAUTO), 2 dígitos.",
    )
    ine_code_province = fields.Char(
        string="INE Province Code",
        size=2,
        help=(
            "Código de Provincia del INE (CPRO), 2 dígitos. "
            "Coincide con res.country.state.code en España."
        ),
    )
    ine_code_municipality = fields.Char(
        string="INE Municipality Code",
        size=3,
        help="Código de municipio dentro de la provincia (CMUN), 3 dígitos.",
    )
    ine_code_control_digit = fields.Char(
        string="INE Control Digit",
        size=1,
        help="Dígito de control del código INE (DC).",
    )
    ine_code = fields.Char(
        string="INE Full Code",
        compute="_compute_ine_code",
        store=True,
        index=True,
        help="Código INE completo: CPRO (2d) + CMUN (3d) = 5 dígitos. Ej: 28079.",
    )

    ine_code_locked = fields.Boolean(
        string="Lock INE code",
        help="Automatic INE updates will not modify this city.",
    )

    @api.depends("ine_code_province", "ine_code_municipality")
    def _compute_ine_code(self):
        for city in self:
            if city.ine_code_province and city.ine_code_municipality:
                city.ine_code = city.ine_code_province + city.ine_code_municipality
            else:
                city.ine_code = False
