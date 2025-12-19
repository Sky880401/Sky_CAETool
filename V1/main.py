import sys

# 依你的環境放工具庫位置（保持原本的 D:\Sky_CAETool）
sys.path.append(r"D:\Sky_CAETool\V1")

import ZFaceSelector_V1
reload(ZFaceSelector_V1)
from ZFaceSelector_V1 import runZFaceSelector

import ContactTool_V1
reload(ContactTool_V1)
from ContactTool_V1 import runContact

import MeshTool_V1
reload(MeshTool_V1)
from MeshTool_V1 import runMesh

import BCTool_V1
reload(BCTool_V1)
from BCTool_V1 import runBC

# 由 Mechanical 主環境傳入 ExtAPI / Model / Transaction / SelectionTypeEnum
# 這樣 worker 模組就不會再遇到：ExtAPI / Model / Transaction / SelectionTypeEnum 找不到
runZFaceSelector(
    ExtAPI,
    tolerance=0.001,
    model=Model,
    transaction_cls=Transaction,
    selection_type_enum=SelectionTypeEnum
)

runContact(
    ExtAPI,
    model=Model,
    transaction_cls=Transaction,
    selection_type_enum=SelectionTypeEnum,
    contact_type=ContactType,
    friction_coeff=0.2,
    delete_existing_groups=True,
    contact_name_typo_is_conatct=False
)

runMesh(
    ExtAPI,
    element_size=1.0,
    is_quadratic=True,
    do_contact_refine=True,
    model=Model,
    transaction_cls=Transaction,
    selection_type_enum=SelectionTypeEnum,
    data_model_object_category_enum=DataModelObjectCategory,
    quantity_cls=Quantity,
    element_order_enum=ElementOrder,
    method_type_enum=MethodType
)

runBC(
    ExtAPI,
    z_magnitude=5.0,        # 位移量 5mm
    direction_sign=-1.0,    # -1 代表向下/插入 (-Z)
    model=Model,
    transaction_cls=Transaction,
    # --- 關鍵依賴注入 ---
    quantity_cls=Quantity,          # [重要] 傳入單位類別
    load_define_by_enum=LoadDefineBy # [重要] 傳入 LoadDefineBy Enum
)