from re import compile, escape, I
from pymongo import InsertOne, ReplaceOne, MongoClient, UpdateOne
from os import environ
from uuid import uuid4
from functools import wraps

_sub_regex = compile('(A|(An)|(The)) ')

try:
    _database = MongoClient(
        f'mongodb://{environ["MONGODB_USER"]}:{environ["MONGODB_PASSWORD"]}@{environ.get("MONGODB_HOST", "localhost")}/{environ["MONGODB_DATABASE"]}',
        ssl = 'MONGODB_SSL' in environ
    )[environ['MONGODB_DATABASE']]
except:
    _database = MongoClient()[environ['MONGODB_DATABASE']]
_api_keys = _database.api_keys
_deleted = _database.deleted
_quartermasters = _database.quartermasters
_items = _database.items

def api_key_exists(key):
    return _api_keys.count_documents({'key': key})

def _create_filters(arguments, **kwargs):
    filters = {}
    max_players = arguments.get('max_players')
    if max_players:
        try:
            filters['max_players'] = int(max_players)
        except:
            filters['max_players'] = -1
    min_players = arguments.get('min_players')
    if min_players:
        try:
            filters['min_players'] = int(min_players)
        except:
            filters['min_players'] = -1
    name = arguments.get('name')
    if name:
        try:
            filters['name'] = compile(name, I)
        except:
            filters['name'] = compile(escape(name), I)
    owner = arguments.get('owner')
    if owner:
        filters['owner'] = owner
    players = arguments.get('players')
    if players:
        try:
            players = int(players)
            filters['$and'] = [
                {'min_players': {'$lte': players}},
                {'max_players': {'$gte': players}}
            ]
        except:
            filters['$and'] = [
                {'min_players': {'$lte': -1}},
                {'max_players': {'$gte': -1}}
            ]
    submitter = arguments.get('submitter')
    if submitter:
        filters['submitter'] = submitter
    return dict(filters, **kwargs)

def _create_sort(arguments, **kwargs):
    try:
        return dict(
            {arguments['sort']: -1 if 'descending' in arguments else 1},
            **kwargs
        )
    except:
        return kwargs

def delete_item(name, submitter):
    item = _items.find_one({'name': name})
    if not item or (not is_quartermaster(submitter) and submitter != item['submitter']):
        return False
    _deleted.insert_one(item)
    _items.delete_one({'name': name})
    try:
        id = list(_items.find().sort([('_id', -1)]).limit(10))[-1]['_id']
        _items.update_many({'_id': {'$gte': id}}, {'$set': {'new': True}})
    except:
        pass
    return True

def item_exists(name):
    return _items.count_documents({'name': compile(f'^{escape(name)}$', I)})

def generate_api_key():
    uuid = str(uuid4())
    _api_keys.insert_one({'key': uuid})
    return uuid

def get_api_keys():
    return _api_keys.find()

def get_count(arguments):
    return _items.count_documents(_create_filters(arguments))

def get_item(name):
    return _items.find_one({'name': name})

def get_item_names(expansion = None):
    return (item['name'] for item in _items.find(
        {'expansion': expansion} if expansion else {},
        {'_id': False, 'name': True}
    ).sort([('sort_name', 1)]))

def get_items(arguments):
    return _items.aggregate([
        {'$match': _create_filters(arguments)},
        {'$sort': _create_sort(arguments, sort_name = 1)},
        {'$project': {'_id': False}}
    ])

def get_newest_items(arguments):
    return _items.aggregate([
        {'$match': _create_filters(arguments, new = True)},
        {'$sort': _create_sort(arguments, _id = -1)},
        {'$project': {'_id': False}}
    ])

def get_owners(arguments = None):
    aggregation = [{'$group': {'_id': '$owner'}}, {'$sort': {'_id': 1}}]
    if arguments:
        aggregation = {'$match': _create_filters(arguments)} + aggregation
    return (item['_id'] for item in _items.aggregate(aggregation))

def get_players():
    try:
        return next(_items.aggregate([
            {'$group': {'_id': False, 'max': {'$max': '$max_players'}, 'min': {'$min': '$min_players'}}}
        ]))
    except:
        return None

def get_random_items(arguments, sample_size):
    return _items.aggregate([
        {'$match': _create_filters(arguments)},
        {'$sample': {'size': sample_size}}, {'$project': {'_id': False}}
    ])

def get_submissions(arguments, submitter):
    return _items.aggregate([
        {'$match': _create_filters(arguments, submitter = submitter)},
        {'$sort': _create_sort(arguments, sort_name = 1)},
        {'$project': {'_id': False}}
    ])

def get_submitters(arguments = None):
    aggregation = [{'$group': {'_id': '$submitter'}}, {'$sort': {'_id': 1}}]
    if arguments:
        aggregation = {'$match': _create_filters(arguments)} + aggregation
    return (item['_id'] for item in _items.aggregate(aggregation))

def insert_item(item, submitter, update = False, update_name = None):
    del item['image']
    item['new'] = True
    item['sort_name'] = _sub_regex.sub('', item['name'])
    item['submitter'] = submitter
    if update:
        requests = [ReplaceOne({"name" : update_name},  item)]
    else:
        requests = [InsertOne(item)]
    stuff = list(_items.find().sort([('_id', -1)]).limit(10))
    if len(stuff) == 10:
        requests.append(UpdateOne({'_id': stuff[-1]['_id']}, {
            '$unset': {'new': 1}
        }))
    _items.bulk_write(requests)

def is_quartermaster(username):
    return _quartermasters.count_documents({'username': username})
