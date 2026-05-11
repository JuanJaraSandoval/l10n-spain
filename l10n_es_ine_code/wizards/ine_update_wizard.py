# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

from ..ine_assign import run_ine_assignment


class IneUpdateWizard(models.TransientModel):
    _name = "ine.update.wizard"
    _description = "INE update wizard"

    overwrite = fields.Boolean(
        help="Overwrite existing INE codes except locked cities.",
    )
    dry_run = fields.Boolean(
        default=True,
        help="Simulate changes without writing data.",
    )
    result = fields.Text(readonly=True)

    def _format_result(self, result):
        lines = []
        for key in sorted(result):
            lines.append(f"{key}: {result[key]}")
        return "\n".join(lines)

    def _run(self, dry_run):
        self.ensure_one()
        result = run_ine_assignment(
            self.env,
            overwrite=self.overwrite,
            dry_run=dry_run,
        )
        self.result = self._format_result(result)
        return {
            "type": "ir.actions.act_window",
            "name": self._description,
            "res_model": self._name,
            "view_mode": "form",
            "res_id": self.id,
            "target": "new",
        }

    def action_simulate(self):
        return self._run(dry_run=True)

    def action_apply(self):
        return self._run(dry_run=False)
