# coding=utf8
import os
import imp
import json
import datetime

from ops_sia import log as logging


def load_url_map(path, package, log=None):
    log = log or logging.getLogger(__name__)
    url_map = []
    our_dir = path[0]
    for dirpath, dirnames, filenames in os.walk(our_dir):
        for fname in filenames:
            root, ext = os.path.splitext(fname)
            if ext != '.py' or root == '__init__':
                continue
            class_path = os.path.join(dirpath, fname)
            handle_class = imp.load_source(fname, class_path)
            _url_map = getattr(handle_class, 'url_map', {})
            if _url_map:
                for _url, _handler in _url_map.items():
                    url_map.append((_url, getattr(handle_class, _handler)))
    log.info('url map:\n' + '\n'.join(['%20s\t%s' % (_url_map[0], _url_map[1]) \
                                       for _url_map in url_map]))
    return url_map


def pageNation(request, page_list, page_name='result', count=None):
    print page_name
    if not isinstance(page_list, list):
        return "page_list must be a list"
    start = int(request.get_argument('start', 0))
    length = int(request.get_argument('length', 10))
    if start > len(page_list) or start < 0: start = 0
    _page_list = page_list[start:(start + length)]
    if _page_list and (not isinstance(_page_list[0], str)):
        try:
            _page_list = [dict(q) for q in _page_list]
        except:
            return 'object of list must be dictable'
    if count:
        return {page_name: _page_list, "count": count}
    else:
        return {page_name: _page_list, "count": len(page_list)}



class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, datetime.date):
            return obj.strftime('%Y-%m-%d')
        else:
            return json.JSONEncoder.default(self, obj)


def query_result_json(context, query_result, field={}, name='', ext_dict={}):
    count = 0
    is_list = False
    if not query_result:
        result = []
        count = 0
    elif isinstance(query_result, list):
        count = len(query_result)
        result = [dict(q) for q in query_result[context['start']:(context['length'] + context['start'])] if q]
        is_list = True
    elif getattr(query_result, '__dict__', ''):
        result = [dict(query_result)]
    elif isinstance(query_result, dict) and ('count' not in query_result.keys()):
        result = [query_result]
    else:
        result = query_result
    if field:
        i = 0
        _result = []
        for query in result:
            tmp_query = {}
            for k, v in field.items():
                dict_str = ''
                for _k in k.split('.'):
                    if k:
                        dict_str += "['%s']" % k
                for _v in set(v):
                    if dict_str:
                        if not isinstance(tmp_query.get(dict_str[2:-2], ''), dict):
                            tmp_query[dict_str[2:-2]] = {}
                        tmp_query[dict_str[2:-2]][_v] = eval('result[%d]%s' % (i, dict_str)).get(_v, '')
                    else:
                        tmp_query[_v] = eval('result[%d]%s' % (i, dict_str)).get(_v, '')
            _result.append(tmp_query)
            i += 1
        result = _result
    if (not is_list) and len(result) == 1:
        result = result[0]
    if not (isinstance(result, dict) and 'count' in result.keys()):
        result = {'count': count, name or 'result': result}
    result.update(ext_dict)
    return json.dumps(result, cls=ComplexEncoder)