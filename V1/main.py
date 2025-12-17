# -*- coding: utf-8 -*-
import sys

# 工具包位置
sys.path.append(r"D:\Sky_CAETool")

from ZFaceSelector_V1 import runZFaceSelector
from ContactTool_V1 import runContactTool

runZFaceSelector(
    ExtAPI,
    tolerance=0.001,
    model=Model,
    transaction_cls=Transaction,
    selection_type_enum=SelectionTypeEnum
)

runContactTool(
    ExtAPI,
    model=Model,
    transaction_cls=Transaction,
    selection_type_enum=SelectionTypeEnum,
    data_model_object_category=DataModelObjectCategory,
    contact_type=ContactType,
    friction_coeff=0.2,
    delete_existing_groups=True,
    contact_name_typo_is_conatct=False
)
