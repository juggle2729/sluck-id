import sys
import MySQLdb

db = MySQLdb.connect(user='lucky', passwd='P@55word',
                     host='10.168.144.78',
                     db='lucky')
# db = MySQLdb.connect(user='root', passwd='123456',
#                      host='127.0.0.1',
#                      db='lucky')
cursor = db.cursor()


def get_unique_user_list():
    cursor.execute('SELECT DISTINCT `user_id` FROM `transaction`;')
    result = cursor.fetchall()
    user_id_list = [x[0] for x in result]
    return user_id_list


def get_consume(user_id):
    cursor.execute('SELECT SUM(`price`) FROM `transaction` WHERE `user_id`=%s AND `status`=1 AND `type`=4;',
                   (user_id,))
    consume = cursor.fetchone()[0]
    if consume:
        return abs(consume)
    return 0


def get_award(user_id):
    cursor.execute('SELECT SUM(`price`) FROM `transaction` WHERE `user_id`=%s AND `status`=1 AND `type`=2;',
                   (user_id,))
    award = cursor.fetchone()[0]
    if is_virtual(user_id):
        return 0
    if award:
        return abs(award)
    return 0


def get_exp(user_id):
    consume = get_consume(user_id)
    award = get_award(user_id)
    e = consume - award
    return e if e > 0 else 0


def is_virtual(user_id):
    cursor.execute('SELECT `is_virtual` FROM `account` WHERE `id`=%s;',
                   (user_id,))
    result = cursor.fetchone()
    if result:
        return result[0]
    return 1


def get_exp_list(type='all'):
    uid_list = get_unique_user_list()
    exp_list = []
    for uid in uid_list:
        if type == 'real':
            if not is_virtual(uid):
                exp_list.append((int(uid), float(get_exp(uid)), is_virtual(uid)))
        elif type == 'virtual':
            if is_virtual(uid):
                exp_list.append((int(uid), float(get_exp(uid)), is_virtual(uid)))
        else:
            exp_list.append((int(uid), float(get_exp(uid)), is_virtual(uid)))
    return exp_list


def virtual_ratio(l):
    real = [x for x in l if not x[2]]
    virtual = [x for x in l if x[2]]
    return 'real/virtual/all : %s/%s/%s' % (len(real), len(virtual), len(l))


def get_all_top():
    exp_tuple_list = get_exp_list()
    exp_rank = sorted(exp_tuple_list, key=lambda item: item[1], reverse=True)
    top_10 = exp_rank[0:10]
    top_20 = exp_rank[0:20]
    top_50 = exp_rank[0:50]
    top_100 = exp_rank[0:100]
    print 'total: %s\n' % virtual_ratio(exp_rank)
    print 'top 10: %s, %s\n' % (virtual_ratio(top_10), top_10)
    print 'top 20: %s, %s\n' % (virtual_ratio(top_20), top_20)
    print 'top 50: %s, %s\n' % (virtual_ratio(top_50), top_50)
    print 'top 100: %s, %s\n' % (virtual_ratio(top_100), top_100)


def get_real_top():
    exp_tuple_list = get_exp_list(type='real')
    exp_rank = sorted(exp_tuple_list, key=lambda item: item[1], reverse=True)
    top_10 = exp_rank[0:10]
    top_20 = exp_rank[0:20]
    top_50 = exp_rank[0:50]
    top_100 = exp_rank[0:100]
    print 'top 10: %s\n' % top_10
    print 'top 20: %s\n' % top_20
    print 'top 50: %s\n' % top_50
    print 'top 100: %s\n' % top_100


def get_virtual_top():
    exp_tuple_list = get_exp_list(type='virtual')
    exp_rank = sorted(exp_tuple_list, key=lambda item: item[1], reverse=True)
    top_10 = exp_rank[0:10]
    top_20 = exp_rank[0:20]
    top_50 = exp_rank[0:50]
    top_100 = exp_rank[0:100]
    print 'top 10: %s\n' % top_10
    print 'top 20: %s\n' % top_20
    print 'top 50: %s\n' % top_50
    print 'top 100: %s\n' % top_100


if __name__ == '__main__':
    if sys.argv[1] == 'all':
        print 'getting all top ...'
        get_all_top()
    elif sys.argv[1] == 'real':
        print 'getting real top ...'
        get_real_top()
    elif sys.argv[1] == 'virtual':
        print 'getting virtual top ...'
        get_virtual_top()
