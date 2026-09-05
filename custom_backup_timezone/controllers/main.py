# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
import logging
import pytz

import odoo
from odoo import http
from odoo.http import content_disposition, request
from odoo.addons.web.controllers.main import Database

_logger = logging.getLogger(__name__)


class CustomBackupController(Database):
    
    def backup(self, master_pwd, name, backup_format='zip'):
        """
        Override the backup function to use user's timezone for filename
        instead of UTC time.
        """
        insecure = odoo.tools.config.verify_admin_password('admin')
        if insecure and master_pwd:
            http.dispatch_rpc('db', 'change_admin_password', ["admin", master_pwd])
        try:
            odoo.service.db.check_super(master_pwd)
            
            # Get user timezone or fallback to system timezone
            user_timezone = self._get_user_timezone()
            
            # Generate timestamp in user's timezone
            ts = self._get_localized_timestamp(user_timezone)
            
            # Create filename with localized timestamp
            filename = "%s_%s.%s" % (name, ts, backup_format)
            
            headers = [
                ('Content-Type', 'application/octet-stream; charset=binary'),
                ('Content-Disposition', content_disposition(filename)),
            ]
            dump_stream = odoo.service.db.dump_db(name, None, backup_format)
            
            import werkzeug.wrappers
            response = werkzeug.wrappers.Response(dump_stream, headers=headers, direct_passthrough=True)
            return response
            
        except Exception as e:
            _logger.exception('Database.backup')
            error = "Database backup error: %s" % (str(e) or repr(e))
            return self._render_template(error=error)
    
    def _get_user_timezone(self):
        """
        Get the user's timezone from system configuration or user preferences.
        Falls back to system default timezone if not found.
        """
        try:
            # Try to get timezone from system configuration
            system_timezone = odoo.tools.config.get('timezone')
            if system_timezone:
                return system_timezone
            
            # Try to get timezone from database (if available)
            # This will work for authenticated users
            if request and request.session and hasattr(request, 'env'):
                try:
                    user = request.env['res.users'].browse(request.uid)
                    if user and user.tz:
                        return user.tz
                except:
                    pass
            
            # Fallback to UTC
            return 'UTC'
            
        except Exception:
            return 'UTC'
    
    def _get_localized_timestamp(self, timezone_str='UTC'):
        """
        Generate timestamp in the specified timezone.
        
        Args:
            timezone_str (str): Timezone string (e.g., 'Africa/Cairo', 'Asia/Riyadh')
            
        Returns:
            str: Formatted timestamp string
        """
        try:
            # Get current UTC time
            utc_now = datetime.datetime.utcnow()
            
            # Convert to user timezone
            if timezone_str and timezone_str != 'UTC':
                try:
                    tz = pytz.timezone(timezone_str)
                    utc_time = pytz.utc.localize(utc_now)
                    local_time = utc_time.astimezone(tz)
                    return local_time.strftime("%Y-%m-%d_%H-%M-%S")
                except pytz.exceptions.UnknownTimeZoneError:
                    _logger.warning(f"Unknown timezone: {timezone_str}, falling back to UTC")
            
            # Fallback to UTC
            return utc_now.strftime("%Y-%m-%d_%H-%M-%S")
            
        except Exception as e:
            _logger.error(f"Error generating localized timestamp: {e}")
            # Fallback to UTC timestamp
            return datetime.datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    
    def _render_template(self, error=None):
        """
        Use parent's _render_template method if available
        """
        try:
            # Try to use the parent method
            return super()._render_template(error=error)
        except:
            # Fallback to simple error page
            return f"<html><body><h1>Database Backup Error</h1><p>{error}</p></body></html>"
