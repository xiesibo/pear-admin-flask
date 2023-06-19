from flask import jsonify


def success_api(msg: str = "成功",info=None):
    """ 成功响应 默认值“成功” """
    if info:
        return jsonify(success=True, msg=msg,info=info)
    else:
        return jsonify(success=True, msg=msg)

def fail_api(msg: str = "失败",code:int = 200):
    """ 失败响应 默认值“失败” """
    return jsonify(success=False, msg=msg),code


def table_api(msg: str = "", count=0, data=None, limit=10):
    """ 动态表格渲染响应 """
    res = {
        'msg': msg,
        'code': 0,
        'data': data,
        'count': count,
        'limit': limit

    }
    return jsonify(res)
