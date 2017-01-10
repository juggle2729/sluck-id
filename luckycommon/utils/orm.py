# -*- coding: utf-8 -*-
from functools import partial
import threading

import sqlalchemy
from django.utils.encoding import smart_unicode
from datetime import datetime
from dateutil import parser
from sqlalchemy import orm, func
from sqlalchemy import inspect
from sqlalchemy.orm.session import Session as SessionBase
from sqlalchemy.sql import operators, visitors
from sqlalchemy.orm.exc import UnmappedClassError
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta

from luckycommon.utils.tz import local_to_utc


class RouteKeyError(sqlalchemy.exc.SQLAlchemyError):
    pass


class DbConfigError(sqlalchemy.exc.SQLAlchemyError):
    pass


def get_count(q):
    count_q = q.statement.with_only_columns([func.count()]).order_by(None)
    count = q.session.execute(count_q).scalar()
    return count


def convert_type(instance, k, v, convert_timezone=True):
    if v is None:
        return None
    should_type = getattr(
        instance.__table__.columns, k).type.python_type
    if issubclass(should_type, basestring):
        return smart_unicode(v)
    elif should_type is datetime:
        localtime = parser.parse(v)
        if convert_timezone:
            return local_to_utc(localtime).replace(tzinfo=None)
        else:
            return localtime
    else:
        return should_type(v)


def _to_list(x, default=None):
    if x is None:
        return default
    if not isinstance(x, (list, tuple)):
        return [x]
    else:
        return x


def _include_sqlalchemy(obj):
    for module in sqlalchemy, sqlalchemy.orm:
        for key in module.__all__:
            if not hasattr(obj, key):
                setattr(obj, key, getattr(module, key))
    obj.Model
    obj.OrmError = sqlalchemy.exc.SQLAlchemyError


def query_property(db):

    class query(object):

        def __get__(s, instance, owner):
            try:
                mapper = orm.class_mapper(owner)
                if mapper:
                    return db.session.query(mapper)
            except UnmappedClassError:
                return None
    return query()


class _InnerDeclarativeMeta(DeclarativeMeta):

    def __new__(self, name, bases, d):
        def save(instance, auto_commit=True):
            persistent = inspect(instance).persistent
            if not persistent:
                instance.orm.session.add(instance)
            else:
                if hasattr(instance, 'updated_at'):
                    instance.updated_at = datetime.utcnow()
            if auto_commit:
                instance.orm.session.commit()

        def delete(instance, auto_commit=True):
            instance.orm.session.delete(instance)
            if auto_commit:
                instance.orm.session.commit()

        def as_dict(instance):
            return {c.name: getattr(
                instance, c.name) for c in instance.__table__.columns}

        def from_dict(instance, dct, convert=True):
            for k, v in dct.iteritems():
                if hasattr(instance, k) and k != 'extend':
                    value = v if not convert else convert_type(instance, k, v)
                    setattr(instance, k, value)
            return instance

        d['save'] = save
        d['delete'] = delete
        d['as_dict'] = as_dict
        d['from_dict'] = from_dict
        return DeclarativeMeta.__new__(self, name, bases, d)

    def __init__(self, name, bases, d):
        route_key = d.pop('__route_key__', None)
        shard_key = d.pop('__shard_key__', None)
        shard_lookup = d.pop('__shard_lookup__', None)
        DeclarativeMeta.__init__(self, name, bases, d)
        if route_key is not None:
            self.__table__.info['route_key'] = route_key
        if shard_key is not None:
            self.__table__.info['shard_key'] = shard_key
        if shard_lookup is not None:
            self.__table__.info['shard_lookup'] = shard_lookup


class ShardedQuery(orm.Query):

    def __init__(self, *args, **kwargs):
        super(ShardedQuery, self).__init__(*args, **kwargs)
        self.id_chooser = self.session.id_chooser
        self.query_chooser = self.session.query_chooser
        self._shard_id = None

    def set_shard(self, shard_id):
        """return a new query, limited to a single shard ID.

        all subsequent operations with the returned query will
        be against the single shard regardless of other state.
        """

        q = self._clone()
        q._shard_id = shard_id
        return q

    def _execute_and_instances(self, context):
        def iter_for_shard(shard_id):
            context.attributes['shard_id'] = shard_id
            result = self._connection_from_session(
                mapper=self._mapper_zero(),
                shard_id=shard_id).execute(
                context.statement,
                self._params)
            return self.instances(result, context)

        if self._shard_id is not None:
            return iter_for_shard(self._shard_id)
        else:
            partial = []
            for shard_id in self.query_chooser(self):
                partial.extend(iter_for_shard(shard_id))

            # if some kind of in memory 'sorting'
            # were done, this is where it would happen
            return iter(partial)

    def get(self, ident, **kwargs):
        if self._shard_id is not None:
            return super(ShardedQuery, self).get(ident)
        else:
            ident = _to_list(ident)
            for shard_id in self.id_chooser(self, ident):
                o = self.set_shard(shard_id).get(ident, **kwargs)
                if o is not None:
                    return o
            else:
                return None


class _EngineRouter(object):

    def __init__(self, db):
        self._lock = threading.Lock()
        self._bind_maps = {}
        db_config = db.config['db']
        debug_config = db.config['DEBUG']
        recycle = db.config.get('pool_recycle', 3600)
        create_partial = partial(sqlalchemy.create_engine, encoding='utf-8',
                                 echo=debug_config, pool_recycle=recycle)

        if isinstance(db_config, dict):
            for route_key in db_config:
                self._bind_maps[route_key] = []
                route_value = db_config[route_key]
                conn_list = []
                if isinstance(route_value, str):
                    conn_list = [{'master': route_value, 'slave': route_value}]
                elif isinstance(route_value, dict):
                    conn_list = [{'master': route_value['master'],
                                  'slave': route_value['slave']}]
                elif isinstance(route_value, list):
                    for config_dict in route_value:
                        conn_list.append({'master': config_dict['master'],
                                          'slave': config_dict['slave']})
                for conn_dct in conn_list:
                    try:
                        engine_dict = {
                            'master': create_partial(conn_dct['master']),
                            'slave': create_partial(conn_dct['slave'])
                        }
                        self._bind_maps[route_key].append(engine_dict)
                    except TypeError as e:
                        raise DbConfigError(e)
        else:
            self._bind_maps['default'] = create_partial(db_config)

    def get_engine(self, route_key, shard_key, is_master):
        with self._lock:
            if self._bind_maps.get(route_key, None):
                try:
                    engine = self._bind_maps[route_key][shard_key]['master'] \
                        if is_master else \
                        self._bind_maps[route_key][shard_key]['slave']
                    return engine
                except TypeError as e:
                    raise RouteKeyError(e)
            else:
                return self._bind_maps['default']

    def get_engine_counts_by_route(self, route_key):
        engine_list = self._bind_maps.get(route_key, None)
        if isinstance(engine_list, list):
            return len(self._bind_maps[route_key])
        else:
            raise RouteKeyError


class ShardedSession(SessionBase):

    def __init__(self, db, autocommit=False, autoflush=True,
                 query_cls=ShardedQuery, **options):
        self.db = db
        super(ShardedSession, self).__init__(
            autocommit=False, autoflush=autoflush, bind=None,
            binds={}, query_cls=query_cls, **options)

        def shard_lookup(shard_id, engine_counts):
            return shard_id % engine_counts

        def id_chooser(query, ident):
            return [0]

        def _get_query_comparisons(query):
            binds = {}
            clauses = set()
            comparisons = []

            def visit_bindparam(bind):
                # visit a bind parameter.

                # check in _params for it first
                if bind.key in query._params:
                    value = query._params[bind.key]
                elif bind.callable:
                    # some ORM functions (lazy loading)
                    # place the bind's value as a
                    # callable for deferred evaulation.
                    value = bind.callable()
                else:
                    # just use .value
                    value = bind.value

                binds[bind] = value

            def visit_column(column):
                clauses.add(column)

            def visit_binary(binary):
                # special handling for "col IN (params)"
                if (binary.left in clauses and
                    binary.operator == operators.in_op and
                        hasattr(binary.right, 'clauses')):
                    comparisons.append(
                        (binary.left, binary.operator,
                         tuple(binds[bind] for bind in binary.right.clauses))
                    )
                elif binary.left in clauses and binary.right in binds:
                    comparisons.append(
                        (binary.left, binary.operator, binds[binary.right])
                    )

                elif binary.left in binds and binary.right in clauses:
                    comparisons.append(
                        (binary.right, binary.operator, binds[binary.left])
                    )

            # here we will traverse through the query's criterion, searching
            # for SQL constructs.  We will place simple column comparisons
            # into a list.
            if query._criterion is not None:
                visitors.traverse_depthfirst(query._criterion, {},
                                             {'bindparam': visit_bindparam,
                                              'binary': visit_binary,
                                              'column': visit_column
                                              }
                                             )
            return comparisons

        def query_chooser(query):
            ids = []
            try:
                shard_key = query._mapper_zero().mapped_table.info.get(
                    'shard_key', None)
                route_key = query._mapper_zero().mapped_table.info.get(
                    'route_key', None)
            except Exception as e:
                print e
                shard_key = None

            if shard_key is None:
                return [0]
            engine_counts = query.session.db.get_engine_counts_by_route(
                route_key)
            shard_lookup_func = query._mapper_zero().mapped_table.info.get(
                'shard_lookup', None)
            if not shard_lookup_func:
                shard_lookup_func = shard_lookup

            for column, operator, value in _get_query_comparisons(query):
                if column.key == shard_key:
                    if operator == operators.eq:
                        ids.append(shard_lookup_func(value, engine_counts))
                    elif operator == operators.in_op:
                        ids.extend(shard_lookup_func(v, engine_counts)
                                   for v in value)

            if len(ids) == 0:
                return [engine_counts]
            else:
                return ids
        self.id_chooser = id_chooser
        self.query_chooser = query_chooser

    def get_bind(self, mapper, shard_id=None, clause=None):
        # if mapper is not None:
        #     route_key = mapper.mapped_table.info.get('route_key')
        #     return self.db.get_engine(route_key, shard_id, self._flushing)

        return self.db.get_engine(None, None, self._flushing)


class ArmoryOrm(object):

    def __init__(self, session_options=None):
        self.Model = self.make_declarative_base()
        self.Model.orm = self
        _include_sqlalchemy(self)
        self.session = self.create_scoped_session(session_options)

    def init_app(self, app):
        self.from_flask = True
        self.config = app.config
        self._engine_router = _EngineRouter(self)
        teardown = app.teardown_appcontext

        @teardown
        def close_session(response):
            if response is None:
                self.session.flush()
            self.session.remove()
            return response

    def init_conf(self, conf):
        '''
        conf should be like:
        {"test":[{"master":"mysql://vpn:123456@10.164.18.108:3306/access",
        "slave":"mysql://vpn:123456@10.164.130.41:3306/access"}]}
        '''
        self.from_flask = False
        self.config = conf
        self._engine_router = _EngineRouter(self)

    def __del__(self):
        if not self.from_flask:
            self.session.flush()
            self.session.remove()

    def make_declarative_base(self):
        base = declarative_base(metaclass=_InnerDeclarativeMeta)
        base.query = query_property(self)
        return base

    def create_scoped_session(self, options=None):
        if options is None:
            options = {}
        options["expire_on_commit"] = False
        options["autoflush"] = False
        scopefunc = options.pop('scopefunc', None)
        return orm.scoped_session(partial(self.create_session, options),
                                  scopefunc=scopefunc)

    def create_session(self, options):
        return ShardedSession(self, **options)

    def get_engine(self, route_key, shard_key, is_master):
        return self._engine_router.get_engine(route_key, shard_key, is_master)

    def get_engine_counts_by_route(self, route_key):
        return self._engine_router.get_engine_counts_by_route(route_key)

'''
example
'''
if __name__ == '__main__':
    conf = {
        "db": "mysql://root:123456@127.0.0.1:3306/lucky?charset=utf8", 'DEBUG': False}
    orm = ArmoryOrm()
    orm.init_conf(conf)

    class Goods(orm.Model):
        __tablename__ = "goods"
        id = orm.Column(orm.Integer, primary_key=True)
        name = orm.Column(orm.VARCHAR)
        price = orm.Column(orm.FLOAT)     # 商品单价
        unit = orm.Column(orm.Integer)    # 价格单位
        sold = orm.Column(orm.Integer)    # 已售出数量
        total = orm.Column(orm.Integer)   # 总库存数量
        extend = orm.Column(orm.TEXT)
        created_at = orm.Column(orm.DATETIME)
        updated_at = orm.Column(orm.DATETIME)

    goods = Goods.query.filter(Goods.name == 'phone6s').first()
    print 'ready...'
    if not goods:
        goods = Goods()
        goods.from_dict({
            'name': 'xxx',
            'price': '16088',
            'unit': 0,
            'sold': 1,
            'total': 1000
        })
        goods.save(auto_commit=False)
        goods.name = 'xshu'
        orm.session.commit()
        print goods.as_dict()
    else:
        if goods.sold + 1 > 1:
            print 'reached sold limit'
        goods.sold += 1
        Goods.query.filter(Goods.id == 1000).update({'id': 101})
        goods.save()
