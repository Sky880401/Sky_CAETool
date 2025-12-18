# -*- coding: utf-8 -*-
import sys

# ==========================================
# 1. 設定模組路徑
# ==========================================
# 請修改為您實際存放 .py 檔案的路徑
MODULE_PATH = r"D:\Sky_CAETool\V1"
if MODULE_PATH not in sys.path:
    sys.path.append(MODULE_PATH)

# ==========================================
# 2. 匯入模組 (使用 from ... import ...)
# ==========================================
# 注意：若您在開發階段修改了 .py 檔，這種 import 方式不會自動 reload。
# 若需 reload，建議重啟 Console 或使用 importlib。

from ZFaceSelector_V1 import runZFaceSelector
from ContactTool_V1   import runContact
# from Mesh_V1          import run as runMesh
# from BC_V1            import run as runBC
# from Solver_V1        import run as runSolver
# from Post_V1          import run as runPost

# ==========================================
# 3. 參數定義 (User Inputs)
# ==========================================
# 幾何篩選
Z_TOLERANCE = 0.001

# 接觸
Friction_coeff = 0.2

# # 網格
# MESH_SIZE = 3.0       # mm
# IS_QUAD = True
# REFINE = 0.5

# # 邊界條件
# Z_DISP_MAG = 5.0      # mm
# Z_DIR_SIGN = -1.0     # 向下

# # 求解
# CORES = 6
# TIME_STEPS = (0.05, 1e-4, 0.1)

# ==========================================
# 4. 執行流程 (依賴注入)
# ==========================================
print("=== Sky CAE Tool V1 自動化流程啟動 ===")

try:
    # --- STEP 1: Z Face Selector ---
    print("\n>>> [1/6] 執行 ZFaceSelector...")
    # 傳入：ExtAPI, Model, Transaction, SelectionTypeEnum
    runZFaceSelector(
        ExtAPI,
        tolerance=Z_TOLERANCE,
        model=Model,
        transaction_cls=Transaction,
        selection_type_enum=SelectionTypeEnum
    )

    # # --- STEP 2: Contact Tool ---
    # print("\n>>> [2/6] 執行 ContactTool...")
    runContact(
    ExtAPI,
    model=Model,
    transaction_cls=Transaction,
    selection_type_enum=SelectionTypeEnum,
    
    # [關鍵修改] 傳入必要的列舉 (Enum)，讓模組能識別資料夾與接觸類型
    data_model_object_category=DataModelObjectCategory,
    contact_type=ContactType,
    
    # 設定參數
    friction_coeff=Friction_coeff,            # 摩擦係數
    delete_existing_groups=True,   # 是否先刪除舊的接觸群組
    contact_name_typo_is_conatct=False # 是否處理 "Conatct" 拼字問題
    )

    # # --- STEP 3: Mesh Tool ---
    # print("\n>>> [3/6] 執行 Mesh...")
    # # 傳入：ExtAPI, Model, Transaction, SelectionManager
    # runMesh(
    #     ExtAPI,
    #     model=Model,
    #     transaction_cls=Transaction,
    #     selection_mgr=ExtAPI.SelectionManager,
    #     size=MESH_SIZE,
    #     is_quad=IS_QUAD,
    #     refine_factor=REFINE
    # )

    # # --- STEP 4: Boundary Conditions ---
    # print("\n>>> [4/6] 執行 BC...")
    # # 傳入：ExtAPI, Model, Transaction
    # runBC(
    #     ExtAPI,
    #     model=Model,
    #     transaction_cls=Transaction,
    #     z_val=Z_DISP_MAG,
    #     direction=Z_DIR_SIGN
    # )

    # # --- STEP 5: Solver Setup ---
    # print("\n>>> [5/6] 執行 Solver 設定...")
    # # 傳入：ExtAPI, Model
    # runSolver(
    #     ExtAPI,
    #     model=Model,
    #     init=TIME_STEPS[0],
    #     min_t=TIME_STEPS[1],
    #     max_t=TIME_STEPS[2],
    #     cores=CORES
    # )

    # # --- STEP 6: Post Processing ---
    # print("\n>>> [6/6] 執行 Post 設定...")
    # # 傳入：ExtAPI, Model
    # runPost(
    #     ExtAPI, 
    #     model=Model
    # )

    # print("\n=== 全部設定完成 ===")

except Exception as e:
    import traceback
    print("流程發生錯誤:")
    print(traceback.format_exc())