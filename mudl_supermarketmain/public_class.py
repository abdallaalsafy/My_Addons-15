class MainClass:
    xsql_goods_in_buys_backs = """ SELECT fld_class_id, fld_goods_id, Sum(fld_goods_num) AS fld_goods_num, fld_customer_id
    FROM(
    SELECT fld_class_id, fld_goods_id, fld_goods_num, fld_customer_id From tbl_buygoods
    Union  All 
    SELECT fld_class_id, fld_goods_id, -fld_goods_num, fld_customer_id From tbl_bbackgoods)
    GROUP BY 
    fld_class_id, fld_goods_id, fld_customer_id
    HAVING Sum(fld_goods_num)>0
    """
    xqry_stores_goods = """ SELECT fld_class_id, fld_goods_id, Sum(fld_goods_num) AS fld_goods_num, fld_store_id
    FROM(
    SELECT fld_class_id, fld_goods_id, fld_goods_num, fld_store_id From tbl_buygoods
    Union  All 
    SELECT fld_class_id, fld_goods_id, -fld_goods_num, fld_store_id From tbl_bbackgoods
    Union  All 
    SELECT fld_class_id, fld_goods_id, -fld_goods_num, fld_store_id From tbl_cashgoods
    Union  All 
    SELECT fld_class_id, fld_goods_id, -fld_goods_num, fld_store_id From tbl_qstgoods)
    GROUP BY 
    fld_class_id, fld_goods_id, fld_store_id
    """
    # xqry_un_move_goods_price = """SELECT GoodsID,TypeClassID,TypeClass,TypeName,Min(BuyDate) As DateF,Max(BuyDate) As DateT,Price As MovePrice,'Buy' As SortMove From
    # (SELECT GoodsID,TypeClassID,TypeClass,TypeName,BuyDate,Price From QryFatoraGoods
    # Union All
    # SELECT GoodsID,TypeClassID,TypeClass,TypeName,BackDate,Price From QryFatoraBackGoods) Group By GoodsID,TypeClassID,TypeClass,TypeName,Price
    # Union All
    # SELECT GoodsID,TypeClassID,TypeClass,TypeName,Min(CshDate) As DateF,Max(CshDate) As DateT,Hafez ,'Hafz' From
    #
    # (SELECT GoodsID,TypeClassID,TypeClass,TypeName,CshDate,Hafez From QryMabeaatCashGoods
    # Union All
    # SELECT GoodsID,TypeClassID,TypeClass,TypeName,QDate,MGHafez From QryMabeaatGoods) Group By GoodsID,TypeClassID,TypeClass,TypeName,Hafez
    # Union All
    # SELECT GoodsID,TypeClassID,TypeClass,TypeName,Min(CshDate),Max(CshDate),Price,'Cash' From QryMabeaatCashGoods Group By GoodsID,TypeClassID,TypeClass,TypeName,Price
    # UNION ALL SELECT GoodsID,TypeClassID,TypeClass,TypeName,Min(QDate),Max(QDate),Price,'Qst' From QryMabeaatGoods Group By GoodsID,TypeClassID,TypeClass,TypeName,Price
    # """

    def fnc_update_goods_price(self, fldprice, newprice, gid):
        if self:  # عملت هذا السطر فقط ليمنع الخطأ وليس منه ضرر
            return """Update tbl_goods set %s=%s Where id=%s
            """ % (fldprice, newprice, gid)

    # def fnc_insert_move_goods_price(self, classid, goodsid, sortmove, moveprice, datestart, dateend):
    #     if self:  # عملت هذا السطر فقط ليمنع الخطأ وليس منه ضرر
    #         return """INSERT INTO tbl_movegoodsprices (fld_class_id,fld_goods_id,fld_sort_move,fld_move_price,fld_first_move_date,fld_end_move_date)
    #         Values (%s,%s,%s,%s,'%s','%s')""" % (classid, goodsid, sortmove, moveprice, datestart, dateend)
# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

    def fnc_renum(self, slf):
        vrb = 0
        for obj in slf:
            vrb = vrb + 1
            obj.fld_sonum = vrb
        return self  # عملت هذا السطر فقط ليمنع الخطأ وليس منه ضرر
# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

    def fnc_maxum(self, slf, fld):
        if self:  # عملت هذا السطر فقط ليمنع الخطأ وليس منه ضرر
            vrb = slf.search([])
            if len(vrb) > 0:
                return max(vrb.mapped(fld)) + 1
            else:
                return 1
# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

    def fnc_editstring(self, slf):
        if slf:
            xdctnry = {"أ": "ا", "إ": "ا", "آ": "ا", "ة": "ه", "ي ": "ى "}
            vrb = str(slf)
            vrb = vrb + " "
            for xx in xdctnry:
                vrb = vrb.replace(xx, xdctnry[xx])
            xlist = vrb.split(" ")
            vrb = ""
            for x in xlist:
                if x == "":
                    continue
                vrb = vrb + x
                if (x != "ابو") and (x != "عبد"):
                    vrb = vrb + " "
            if self:  # عملت هذا السطر فقط ليمنع الخطأ وليس منه ضرر
                return vrb.strip().lower()
