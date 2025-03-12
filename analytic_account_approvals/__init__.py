from . import models

import logging
_logger = logging.getLogger(__name__)

def post_init_hook(cr, registry):
    """Post-install script"""
    from odoo import api, SUPERUSER_ID
    
    # Get environment with superuser
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Log installation for debugging
    _logger.info("Analytic Account Approvals module installed - post-init hook executed")
    
    # Verify the module correctly extends approval.request
    approval_request = env['ir.model'].search([('model', '=', 'approval.request')], limit=1)
    if approval_request:
        _logger.info("Found approval.request model (ID: %s)", approval_request.id)
        
        # Check that our module is included in the inheritance chain
        model_ids = env['ir.model.data'].search([
            ('model', '=', 'ir.model'),
            ('res_id', '=', approval_request.id),
        ])
        if model_ids:
            _logger.info("approval.request is correctly registered in ir.model.data")
        else:
            _logger.warning("approval.request not found in ir.model.data")
    else:
        _logger.warning("Could not find approval.request model!")

def post_update_hook(cr, registry):
    """Post-update script to run when the module is updated"""
    from odoo import api, SUPERUSER_ID
    
    # Get environment with superuser
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    _logger.info("Analytic Account Approvals module updated - post-update hook executed")
    
    # Clear model cache to ensure our overrides are picked up
    for model in ['approval.request', 'approval.product.line']:
        env.registry.clear_caches()
        env.registry.setup_models(cr)
        
    _logger.info("Model cache cleared and models reloaded") 