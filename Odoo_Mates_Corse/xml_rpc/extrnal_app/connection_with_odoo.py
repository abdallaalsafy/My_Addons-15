##########################################################################
# url = "https://demo.odoo.com/start"                                    #
#     info = xml_rpc.ServerProxy(url).start()                            #
#                                                                        #
#     host = info['host']                                                #
#     user = info['user']                                                #
#     password = info['password']                                        #
#     database = info['database']                                        #
#                                                                        #
#     print('host: ',host)# https://demo2.odoo.com                       #
#     print('user: ',user)# admin                                        #
#     print('password: ',password)# admin                                #
#     print('database: ',database)# demo_saas-192_6ef58c0b08e9_1776527161#
##########################################################################

from xmlrpc import client as xml_rpc


def get_main_conn_data():
    url = "http://localhost:8015"
    user = "Alsafy"
    password = "D9kaky"# OR api-key
    db = "xml_rpc-15"

    # /xmlrpc/common -->> old way
    # /xmlrpc/2/common -->> new way

    common = xml_rpc.ServerProxy(url + "/xmlrpc/2/common")
    print('version info: ',common.version())# version info:  {'server_version': '15.0-20240131', 'server_version_info': [15, 0, 0, 'final', 0, ''], 'server_serie': '15.0', 'protocol_version': 1}

    #  common.login -->> Old OR common.authenticate -->> New
    # the old way
    user_id = common.login(db, user, password)
    print('user_id login: ',user_id)

    #OR -->> the new way

    user_id = common.authenticate(db, user, password,{})
    print('user_id authenticate: ', user_id)

    return url, user, password, db, user_id