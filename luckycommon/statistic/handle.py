#! coding=utf-8

import types
import csv
import os
import tablib

from luckycommon.utils.mail import MailSender


# declear calculat value fuction
# inject fuction to instance
# use instance that injected mehtod calculat all column

class Methodproxy(object):
    def __init__(self, column_name):
        self.column_name = column_name
        self.result_value = []
        self.NEED_ITER = True

    def close_iter(self):
        self.NEED_ITER = False

    def inject_calc_value(self, func):
        self.calc_value = types.MethodType(func, self)

    def start_job(self, id_list):
        if not callable(self.calc_value):
            return []
        if not self.NEED_ITER:
            return self.calc_value(id_list)
        self.result_value = map(lambda x: self.calc_value(x), id_list)


class Merge(object):
    def __init__(self):
        self.column_method_pool = []
        self.id_list = []
        self.table_value = []

    #add column value method
    def add_column_method_pool(self, object):
        if isinstance(object, Methodproxy) and callable(object.calc_value):
            self.column_method_pool.append(object)

    def inject_id_list(self, id_list):
        self.id_list = id_list

    #calculate column value
    def calculate_value(self):
        for method_obj in self.column_method_pool:
            method_obj.start_job(self.id_list)

    #merge all the column value list
    def merge_info(self, *args, **kwargs):
        ## TODO run the method automaticlly without parameter pass
        self.table_value = zip(*args)
        if not kwargs.get("file_name", None):
            return
        file_save_name = kwargs.get("file_name", "result_file")
        with open("%s" % file_save_name, 'wb') as result_file:
            wr = csv.writer(result_file, dialect="excel")
            title_list = ["id_list"]+[x.column_name for x in self.column_method_pool]
            wr.writerow(title_list)
            for i in self.table_value:
                wr.writerow(i)


EXPORT_PATH = "/home/ubuntu/af-env/data/"

def redirect_to_file(items, header, filename):
    file_path = os.path.join(EXPORT_PATH, filename)
    data = tablib.Dataset(*items, headers=header)
    with open(file_path, 'wb') as f:
        f.write(data.xlsx)
    return file_path

class MailProxy(object):
    def __init__(self):
        self.TOOL_MAIL_SENDER = MailSender.getInstance()
        self.TOOL_MAIL_SENDER.init_conf({
            'server': 'smtp.mxhichina.com:25',
            'user': 'ops@zhuohan-tech.com',
            'passwd': 'madP@ssw0rd',
            'from': 'Adsquare Service Statistics<ops@zhuohan-tech.com>',
            'to': [
                'yzhen@zhuohan-tech.com',
            ]
        })

    def add_mail_to_list(self, mail_list):
        for mail_address in mail_list:
            self.TOOL_MAIL_SENDER.mail_to.append(mail_address)

    def send_format_value_file(self, table_info=[], value=[], file_name="", mail_info=""):
        file_path = redirect_to_file(table_info, value, u'%s.xlsx' % file_name)
        self.TOOL_MAIL_SENDER.send(u"%s"%mail_info, "see the attachment", attachments=[file_path])


