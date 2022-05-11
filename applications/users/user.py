import typing as t

from flask import request, jsonify
from flask.views import MethodView
from flask_login import current_user
from flask_pydantic import validate
from flask_restful import reqparse
from pydantic import BaseModel, Field
from sqlalchemy import desc

from common.utils.http import fail_api, success_api, table_api
from extensions import db
from models import LogModel
from models import UserModel, RoleModel, DepartmentModel


def get_current_user_logs():
    """ 获取当前用户日志 """
    log = LogModel.query.filter_by(url='/passport/login').filter_by(uid=current_user.id).order_by(
        desc(LogModel.create_at)).limit(10)
    return log


def is_user_exists(username):
    """ 判断用户是否存在 """
    res = UserModel.query.filter_by(username=username).count()
    return bool(res)


def delete_by_id(_id):
    """ 删除用户 """
    user = UserModel.query.filter_by(id=_id).first()
    roles_id = []
    for role in user.role:
        roles_id.append(role.id)
    roles = RoleModel.query.filter(RoleModel.id.in_(roles_id)).all()
    for r in roles:
        user.role.remove(r)
    res = UserModel.query.filter_by(id=_id).delete()
    db.session.commit()
    return res


def batch_remove(ids):
    """ 批量删除 """
    for _id in ids:
        delete_by_id(_id)


def update_user_role(_id, roles_list):
    user = UserModel.query.filter_by(id=_id).first()
    roles_id = []
    for role in user.role:
        roles_id.append(role.id)
    roles = RoleModel.query.filter(RoleModel.id.in_(roles_id)).all()
    for r in roles:
        user.role.remove(r)
    roles = RoleModel.query.filter(RoleModel.id.in_(roles_list)).all()
    for r in roles:
        user.role.append(r)
    db.session.commit()


def users_delete():
    """批量删除"""
    ids = request.form.getlist('ids[]')
    batch_remove(ids)
    return success_api(message="批量删除成功")


class QueryModel(BaseModel):
    page: int = 1
    limit: int = 10
    real_name: t.Optional[str] = Field(alias='realName')
    username: t.Optional[str]
    dept_id: t.Optional[str] = Field(alias='deptId', default=0)
    phone: t.Optional[str]
    sort: t.Optional[int]
    status: t.Optional[int]


class PersonModel(BaseModel):
    role_ids: str = Field(alias='roleIds')
    username: str
    real_name: str = Field(alias='realName')
    password: str


class UserApi(MethodView):
    """修改用户数据"""

    @validate()
    def get(self, _id, body: QueryModel):

        filters = []

        if body.real_name:
            filters.append(UserModel.realname.like('%' + body.real_name + '%'))
        if body.username:
            filters.append(UserModel.username.like('%' + body.username + '%'))
        if body.dept_id:
            filters.append(UserModel.dept_id == body.dept_id)

        paginate = UserModel.query.filter(*filters).paginate(page=body.page,
                                                             per_page=body.limit,
                                                             error_out=False)

        dept_name = lambda _id: DepartmentModel.query.filter_by(id=_id).first().dept_name if _id else ""
        user_data = [{
            'id': item.id,
            'username': item.username,
            'realname': item.realname,
            'enable': item.enable,
            'create_at': str(item.create_at),
            'update_at': str(item.update_at),
            'dept': dept_name(item.dept_id),
        } for item in paginate.items]
        return table_api(result={'items': user_data,
                                 'total': paginate.total}
                         , code=0)

    @validate()
    def post(self, body: PersonModel):
        """新建单个用户"""

        role_ids = body.role_ids.split(',')

        if is_user_exists(body.username):
            return fail_api(message="用户已经存在")

        user = UserModel()
        user.username = body.username
        user.realname = body.real_name
        user.set_password(body.password)
        db.session.add(user)
        db.session.commit()

        """ 增加用户角色 """
        user = UserModel.query.filter_by(id=user.id).first()
        roles = RoleModel.query.filter(RoleModel.id.in_(role_ids)).all()
        for r in roles:
            user.role.append(r)
        db.session.commit()

        return success_api(message="增加成功", code=0)

    def delete(self, _id):
        # 删除用户
        res = delete_by_id(_id)
        if not res:
            return fail_api(message="删除失败")
        return success_api(message="删除成功")


class PersonModel2(BaseModel):
    role_ids: str = Field(alias='roleIds')
    user_id: str = Field(alias='userId')
    username: str
    real_name: str = Field(alias='realName')
    dept_id: str = Field(alias='deptId')


@validate()
def user_role_resource(_id, body: PersonModel2):
    role_ids = body.role_ids.split(',')

    # 更新用户数据
    UserModel.query.filter_by(id=_id).update({'username': body.username,
                                              'realname': body.real_name,
                                              'dept_id': body.dept_id})
    db.session.commit()

    update_user_role(_id, role_ids)

    return success_api(message="更新成功")


def user_info(_id, action):
    if action == 'info':
        parser = reqparse.RequestParser()
        parser.add_argument('realName', type=str, dest='real_name')
        parser.add_argument('username', type=str)
        parser.add_argument('remark', type=str)
        parser.add_argument('details', type=str)

        res = parser.parse_args()

        ret = UserModel.query.get(_id)
        ret.username = res.username
        ret.realname = res.real_name
        ret.remark = res.details
        db.session.commit()
        if not ret:
            return fail_api(message="出错啦")
        return success_api(message="更新成功")
    elif action == 'status':
        parser = reqparse.RequestParser()
        parser.add_argument('userId', type=int, required=True, dest='user_id')
        parser.add_argument('operate', type=int, required=True, dest='operate', choices=[0, 1])

        res = parser.parse_args()

        if res.operate == 1:
            user = UserModel.query.get(_id)
            user.enable = res.operate
            message = success_api(message="启动成功")
        else:
            user = UserModel.query.filter_by(id=res.user_id).update({"enable": res.operate})
            message = success_api(message="禁用成功")
        if user:
            db.session.commit()
        else:
            return fail_api(message="出错啦")
        return message
    elif action == 'avatar':
        url = request.json.get("avatar").get("src")
        ret = UserModel.query.get(_id)
        ret.avatar = url
        db.session.commit()
        if not ret:
            return fail_api(message="出错啦")
        return success_api(message="修改成功")
    elif action == 'password':
        parser = reqparse.RequestParser()
        parser.add_argument('oldPassword', type=str, required=True, help='旧密码不得为空')
        parser.add_argument('newPassword', type=str, required=True, help='新密码不得为空')
        parser.add_argument('confirmPassword', type=str, required=True, help='确认密码不能为空')

        res = parser.parse_args()

        if res.newPassword != res.confirmPassword:
            return fail_api(message='确认密码不一致')

        """ 修改当前用户密码 """
        user = UserModel.query.get(_id)
        is_right = user.validate_password(res.oldPassword)
        if not is_right:
            return jsonify(success=False, message="旧密码错误")
        user.set_password(res.newPassword)
        db.session.add(user)
        db.session.commit()

        return jsonify(success=True, message="更改成功")
    else:
        return jsonify(success=False, message="操作有误")
