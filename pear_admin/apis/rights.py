from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from pear_admin.extensions import db
from pear_admin.orms import RightsORM

rights_api = Blueprint("rights", __name__)


@rights_api.get("/rights")
@jwt_required()
def rights_list():
    page = request.args.get("page", type=int, default=1)
    per_page = request.args.get("per_page", type=int, default=10)

    q = db.select(RightsORM).where(RightsORM.type == "menu")
    pages = db.paginate(q, page=page, per_page=per_page, error_out=False)

    ret = []

    for page in pages.items:
        data = page.json()
        data["children"] = []
        for child in page.children:
            child_data = child.json()
            if child.children:
                child_data["children"] = [
                    sub_child.json() for sub_child in child.children
                ]
                child_data["isParent"] = True

            data["children"].append(child_data)
            data["isParent"] = True
        ret.append(data)
    return {"code": 0, "message": "请求权限数据成功", "count": pages.total, "data": ret}


@rights_api.post("/rights")
@jwt_required()
def create_rights():
    data = request.get_json()
    if not data["pid"]:
        data["pid"] = 0
    if not data["sort"]:
        data["sort"] = int(data["sort"])
    rights_obj = RightsORM(**data)
    rights_obj.save()
    return {"code": 0, "message": "新增权限数据成功"}


@rights_api.put("/rights/<int:rid>")
@jwt_required()
def change_rights(rid):
    data = request.get_json()
    del data["id"]

    rights_obj = RightsORM.query.get(rid)
    for key, value in data.items():
        setattr(rights_obj, key, value)
    rights_obj.save()
    return {"code": 0, "message": "修改权限数据成功"}


@rights_api.delete("/rights/<int:rid>")
@jwt_required()
def delete_rights(rid):
    rights_obj = RightsORM.query.get(rid)
    rights_obj.delete()
    return {"code": 0, "message": "删除权限数据成功"}
