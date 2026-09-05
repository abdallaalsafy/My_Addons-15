# -*- coding: utf-8 -*-
# from odoo import http


# class MudlSupermarketmain(http.Controller):
#     @http.route('/mudl_supermarketmain/mudl_supermarketmain/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mudl_supermarketmain/mudl_supermarketmain/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('mudl_supermarketmain.listing', {
#             'root': '/mudl_supermarketmain/mudl_supermarketmain',
#             'objects': http.request.env['mudl_supermarketmain.mudl_supermarketmain'].search([]),
#         })

#     @http.route('/mudl_supermarketmain/mudl_supermarketmain/objects/<model("mudl_supermarketmain.mudl_supermarketmain"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mudl_supermarketmain.object', {
#             'object': obj
#         })
