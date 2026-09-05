# -*- coding: utf-8 -*-
from odoo import http


class Mawhubin(http.Controller):
    @http.route('/mawhubin/mawhubin/', auth='public')
    def index(self, **kw):
        return "Hello, world"

    @http.route('/mawhubin/mawhubin/objects/', auth='public')
    def list(self, **kw):
        return http.request.render('mawhubin.listing', {
            'root': '/mawhubin/mawhubin',
            'objects': http.request.env['mawhubin.mawhubin'].search([]),
        })

    @http.route('/mawhubin/mawhubin/objects/<model("mawhubin.mawhubin"):obj>/', auth='public')
    def object(self, obj, **kw):
        return http.request.render('mawhubin.object', {
            'object': obj
        })
