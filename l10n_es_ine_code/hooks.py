# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from .ine_assign import run_ine_assignment

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Initial INE assignment on module installation."""
    _logger.info("l10n_es_ine_location: running post-init INE assignment")
    run_ine_assignment(env, overwrite=False, dry_run=False)
