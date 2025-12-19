import sys

# 依你的環境放工具庫位置（保持原本的 D:\Sky_CAETool）
sys.path.append(r"C:\Users\Jetsoft_Sky\Downloads")

from ZFaceSelector_fixed import run

# 由 Mechanical 主環境傳入 ExtAPI / Model / Transaction / SelectionTypeEnum
# 這樣 worker 模組就不會再遇到：ExtAPI / Model / Transaction / SelectionTypeEnum 找不到
run(
    ExtAPI,
    tolerance=0.001,
    model=Model,
    transaction_cls=Transaction,
    selection_type_enum=SelectionTypeEnum
)
