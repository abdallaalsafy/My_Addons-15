class cls_sqls:
    sql_stores_goods = """ SELECT fld_goods_id,fld_store_id,SUM(fld_count_ref_unit) AS fld_count FROM
    (Select fld_goods_id,fld_count_ref_unit,fld_store_id From mdl_buys_goods
    Union All
    Select fld_goods_id,-fld_count_ref_unit,fld_store_id From mdl_buys_r_goods
    Union All
    Select fld_goods_id,-fld_count_ref_unit,fld_store_id From mdl_sells_goods
    Union All
    Select fld_goods_id,fld_count_ref_unit,fld_store_id From mdl_sells_r_goods
    Union All
    Select fld_goods_id,-fld_count_ref_unit,fld_store_f_id From mdl_charges_goods
    Union All
    Select fld_goods_id,fld_count_ref_unit,fld_store_t_id From mdl_charges_goods) AS tbl
    
    GROUP BY fld_goods_id,fld_store_id
    """
    def fnc_get_count_one_goods_in_one_store(self,slf,goods_id,store_id):
        goods_id=goods_id if goods_id else 0
        store_id=store_id if store_id else 0
        sql= "Select fld_count From (%s) AS tbl2 Where fld_goods_id=%s And fld_store_id=%s"% (self.sql_stores_goods,goods_id,store_id)
        slf._cr.execute(sql)
        rcrds=slf._cr.dictfetchall()
        if rcrds:
            return rcrds[0]['fld_count']
        else:
            return 0
    def fnc_get_count_goods_in_one_store(self,slf,store_id):
        store_id=store_id if store_id else 0
        sql= "Select fld_goods_id,fld_count From (%s) AS tbl2 Where fld_count<>0 And fld_store_id=%s"% (self.sql_stores_goods,store_id)
        slf._cr.execute(sql)
        return slf._cr.dictfetchall()

    def fnc_is_goods_used(self,slf,goods_id):
        goods_id=goods_id if goods_id else 0
        sql= "Select * From (%s) AS tbl2 Where fld_goods_id=%s"% (self.sql_stores_goods,goods_id)
        slf._cr.execute(sql)
        rcrds=slf._cr.dictfetchall()
        if rcrds:
            return True
        else:
            return False


