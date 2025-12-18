import sys

# 依你的環境放工具庫位置（保持原本的 D:\Sky_CAETool）
sys.path.append(r"D:\Sky_CAETool\V1")

import ZFaceSelector_V1
reload(ZFaceSelector_V1)
from ZFaceSelector_V1 import runZFaceSelector

import ContactTool_V1
reload(ContactTool_V1)
from ContactTool_V1 import runContact

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
