# -*- coding: utf-8 -*-
# ==========================================
# Jetsoft 自動接觸生成工具 (自動分群版)
# ==========================================
import clr
import re

# --- 設定參數 ---
FRICTION_COEFF = 0.2

# --- 取得主要物件 ---
connections = Model.Connections
sel_mgr = ExtAPI.SelectionManager
ns_list = Model.NamedSelections.Children

# 1. 取得 Connections 根目錄物件
conn_root = Model.Connections

# 2. 取得 Connections 底下所有的子物件 (通常就是 Connection Group 資料夾)
# 注意：這裡使用 list() 轉換很重要，因為我們要在迴圈中刪除物件，
# 如果直接遍歷動態列表，刪除時會導致索引錯亂而漏刪。
target_groups = list(conn_root.Children)

# 3. 開啟 Transaction 加速並刪除
with Transaction():
    for group in target_groups:
        # 確保我們刪除的是資料夾 (Group)
        # 雖然 conn_root.Children 通常都是 Group，但加個判斷更保險
        # 如果您想暴力全刪，可以直接 group.Delete()
        if group.DataModelObjectCategory == DataModelObjectCategory.ConnectionGroup:
            group.Delete()

print("已刪除 Connections 下的所有接觸群組資料夾。")

# ==========================================
# 1. 自動掃描 ID 邏輯
# ==========================================
def scan_target_ids():
    """掃描 NS，找出所有 [Cont]_[Target]_[ID] 的 ID"""
    found_ids = []
    # 正則表達式：抓取括號內的內容
    pattern = r"^\[Cont\]_\[Target\]_\[(.*?)\]$"
    
    print("正在掃描模型中的 Named Selection...")
    for ns in ns_list:
        match = re.match(pattern, ns.Name)
        if match:
            found_id = match.group(1)
            found_ids.append(found_id)
    
    # 去除重複並排序
    found_ids = list(set(found_ids))
    found_ids.sort()
    return found_ids

# ==========================================
# 2. 輔助函式：取得幾何 ID
# ==========================================
def get_ids_from_ns(ns_name):
    # 搜尋名稱完全符合的 NS
    target_ns = next((x for x in ns_list if x.Name == ns_name), None)
    
    if target_ns and target_ns.Location.Ids.Count > 0:
        return list(target_ns.Location.Ids)
    return []

# ==========================================
# 3. 主程式
# ==========================================
def create_grouped_contacts():
    # 步驟 A: 掃描 ID
    target_group_ids = scan_target_ids()
    
    if not target_group_ids:
        print("錯誤：未發現符合格式的 Named Selection。")
        return

    print("--- 開始執行：將為 {} 個 ID 建立獨立群組 ---".format(len(target_group_ids)))
    
    # 步驟 B: 開啟 Transaction 加速
    with Transaction():
        for grp_id in target_group_ids:
            
            # --- 核心修改 1: 在迴圈內建立專屬 Group ---
            # 每一組 ID 都產生一個新的 Connection Group
            new_group = connections.AddConnectionGroup()
            
            # --- 核心修改 2: 重新命名 Group ---
            new_group.Name = "[ContGroup]_[{}]".format(grp_id)
            
            # 準備 NS 名稱 (請確保拼字正確)
            t_name = "[Cont]_[Target]_[{}]".format(grp_id)
            c_name = "[Cont]_[Contact]_[{}]".format(grp_id) 
            # 註：若您的 NS 真的是 Conatct，請自行修改上面那行
            
            # 獲取 Face IDs
            t_ids = get_ids_from_ns(t_name)
            c_ids = get_ids_from_ns(c_name)
            
            if not t_ids or not c_ids:
                print("群組 [{}] 資料不全 (可能是 Contact 端名稱不符)，跳過。".format(grp_id))
                # 如果群組是空的，可以選擇刪除它，這裡保留空群組以便除錯
                continue
            
            # --- 核心修改 3: 將接觸對加入到 "new_group" 而非根目錄 ---
            count = 1
            for t_id in t_ids:
                for c_id in c_ids:
                    # 注意：這裡是 new_group.AddContactRegion()
                    cr = new_group.AddContactRegion()
                    
                    cr.Name = "Pair_{}_Run_{}".format(grp_id, count)
                    
                    # 設定 Contact Side
                    sel_c = sel_mgr.CreateSelectionInfo(SelectionTypeEnum.GeometryEntities)
                    sel_c.Ids = [c_id]
                    cr.SourceLocation = sel_c
                    
                    # 設定 Target Side
                    sel_t = sel_mgr.CreateSelectionInfo(SelectionTypeEnum.GeometryEntities)
                    sel_t.Ids = [t_id]
                    cr.TargetLocation = sel_t
                    
                    # 設定物理屬性
                    cr.ContactType = ContactType.Frictional
                    cr.FrictionCoefficient = FRICTION_COEFF
                    
                    count += 1
            
            print("已建立群組: [ContGroup]_[{}]，包含 {} 個接觸對。".format(grp_id, count-1))

# 執行
create_grouped_contacts()
