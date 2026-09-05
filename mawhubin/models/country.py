# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class country(models.Model):
    _name = 'mdl_country'
    _description = 'country'

    @api.model
    def name_search(self, name, args=None, operator="ilike", limit=100):
        rtn = super().name_search(name=name, args=args, operator=operator, limit=limit)

        xnamids = xtbl.search([('country_id', '!=', False)])
        xcuntrylst=[]
        for xname in xnamids:
            if xname.country_id:xcuntrylst.append(xname.country_id.id)
        if xcuntrylst:
            xnewcountrylst = []
            for xcountry in rtn:
                if xcountry[0] not in xcuntrylst: xnewcountrylst.append(xcountry)
            return xnewcountrylst

        return rtn

    # @api.model
    # def name_search(self, name, args=None, operator="ilike", limit=100):
    #     rtn = super().name_search(name=name, args=args, operator=operator, limit=limit)
    #     xcontxt = self.env.context
    #     xmykey = xcontxt.get('AnyKey', [])
    #     # print(xcontxt, '\n', xmykey)
    #     #--------------------
    #     xcuntrylst=[]
    #     xtbl=self.env['mawhubin2']
    #     for xname in xmykey:
    #         if xname[0]==4:
    #             xnamid=xtbl.search([('id','=',xname[0]),('country_id','!=',False)])
    #             if xnamid:xcuntrylst.append(xnamid.country_id.id)
    #         if xname[0] == 0 or xname[0] == 1:
    #             xcuntryid=xname[2].get('country_id')
    #             if xcuntryid: xcuntrylst.append(xcuntryid)
    #     if xcuntrylst:
    #         xnewcountrylst=[]
    #         for xcountry in rtn:
    #             if xcountry[0] not in xcuntrylst:xnewcountrylst.append(xcountry)
    #         return xnewcountrylst
    #
    #     return rtn

    name = fields.Char()