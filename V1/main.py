# -*- coding: utf-8 -*-
import sys
import os

# 設定 V1 模組路徑 (請依實際狀況修改)
MODULE_PATH = r"D:\\Sky_CAETool\\V1"
if MODULE_PATH not in sys.path:
    sys.path.append(MODULE_PATH)

# 匯入所有 Worker 模組
import ZFaceSelector_V1
# import ContactTool_V1
# import Mesh_V1
# import BC_V1
# import Solver_V1
# import Post_V1

# 開發模式：強制 Reload 避免 Cache
reload(ZFaceSelector_V1)
# reload(ContactTool_V1)
# reload(Mesh_V1)
# reload(BC_V1)
# reload(Solver_V1)
# reload(Post_V1)

# ==========================================
# 使用者參數定義 (User Inputs)
# ==========================================
# 1. 幾何篩選
Z_TOLERANCE = 0.001

# 2. 接觸
# FRICTION = 0.2

# 3. 網格
# MESH_SIZE = 3.0       # mm
# IS_QUAD = True
# REFINE = 0.5

# 4. 邊界條件 (依賴步驟 1 的結果)
# Z_DISP_MAG = 5.0      # mm (絕對值)
# Z_DIR_SIGN = -1.0     # -1 代表向下

# 5. 求解
# CORES = 6
# TIME_STEPS = (0.05, 1e-4, 0.1) # Init, Min, Max

# ==========================================
# 主流程執行 (Sequential Execution)
# ==========================================
def main_workflow():
    print("=== Sky CAE Tool V1 自動化流程啟動 ===")
    
    # STEP 1: Z Face Selector (產出 NS 供 BC 使用)
    print("\n>>> [1/6] 執行 ZFaceSelector...")
    ZFaceSelector_V1.run(
        ExtAPI, Model, Transaction, SelectionTypeEnum, 
        tolerance=Z_TOLERANCE
    )
    
    # STEP 2: Contact Tool (產出 Contact Region 供 Mesh Sizing 使用)
    # print("\n>>> [2/6] 執行 ContactTool...")
    # ContactTool_V1.run(
    #     ExtAPI, Model, Transaction, ExtAPI.SelectionManager, 
    #     friction=FRICTION
    # )
    
    # STEP 3: Mesh (依賴 Geometry 與 Contact)
    # print("\n>>> [3/6] 執行 Mesh...")
    # Mesh_V1.run(
    #     ExtAPI, Model, Transaction, ExtAPI.SelectionManager,
    #     size=MESH_SIZE, is_quad=IS_QUAD, refine_factor=REFINE
    # )
    
    # STEP 4: BC (依賴 ZFaceSelector 的 NS)
    # print("\n>>> [4/6] 執行 BC...")
    # BC_V1.run(
    #     ExtAPI, Model, Transaction, 
    #     z_val=Z_DISP_MAG, direction=Z_DIR_SIGN
    # )
    
    # STEP 5: Solver Setup
    # print("\n>>> [5/6] 執行 Solver 設定...")
    # Solver_V1.run(
    #     ExtAPI, Model, 
    #     init=TIME_STEPS[0], min_t=TIME_STEPS[1], max_t=TIME_STEPS[2], cores=CORES
    # )
    
    # STEP 6: Post Processing Prep
    # print("\n>>> [6/6] 執行 Post 設定...")
    # Post_V1.run(ExtAPI, Model)
    
    print("\n=== 全部設定完成，請手動點擊 Solve 或加入 Solve 指令 ===")

# 執行
try:
    main_workflow()
except Exception as e:
    import traceback
    print("流程發生錯誤:")
    print(traceback.format_exc())