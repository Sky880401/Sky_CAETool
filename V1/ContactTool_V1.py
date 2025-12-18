# -*- coding: utf-8 -*-
import re

class ContactTool(object):
    """
    專門用來管理與生成接觸 (Contact) 的工具。
    負責：清除舊群組、掃描 Named Selection、自動配對並建立 Contact Region。
    """

    def __init__(self, ext_api, model=None, transaction_cls=None,
                 selection_type_enum=None,
                 data_model_object_category=None,
                 contact_type_enum=None):
        """
        初始化 Worker，接收所有需要的「工具」與「權限」。
        
        Parameters
        ----------
        ext_api : ExtAPI
        model : Model (DataModel.Project.Model)
        transaction_cls : Transaction (用於 Undo/Redo 群組化)
        selection_type_enum : SelectionTypeEnum (用於指定選擇類型)
        data_model_object_category : DataModelObjectCategory (用於辨識資料夾類型)
        contact_type_enum : ContactType (用於設定接觸類型，如 Frictional, Bonded)
        """
        self.api = ext_api
        self.model = model if model is not None else ext_api.DataModel.Project.Model
        self.transaction_cls = transaction_cls
        self.selection_type_enum = selection_type_enum
        self.data_model_object_category = data_model_object_category
        self.contact_type_enum = contact_type_enum
        
        # 快捷存取 SelectionManager
        self.sel_mgr = self.api.SelectionManager

    def clear_existing_groups(self):
        """[功能] 刪除 Connections 下所有的 Connection Group"""
        connections = self.model.Connections
        # 取得所有子物件轉為 list，避免刪除時索引錯亂
        target_groups = list(connections.Children)
        
        count = 0
        
        # 定義刪除邏輯
        def _do_delete():
            nonlocal count
            for group in target_groups:
                # 判斷是否為 Connection Group (依賴注入的 Enum)
                if self.data_model_object_category and \
                   group.DataModelObjectCategory == self.data_model_object_category.ConnectionGroup:
                    group.Delete()
                    count += 1
                elif self.data_model_object_category is None:
                    # 如果沒傳入 Enum，就比較寬鬆地刪除 (或透過名稱判斷)
                    # 這裡示範簡單的全刪保護
                    group.Delete()
                    count += 1

        # 執行刪除 (包在 Transaction 中)
        if self.transaction_cls:
            with self.transaction_cls():
                _do_delete()
        else:
            _do_delete()
            
        print("已清理 {} 個舊的接觸群組。".format(count))

    def _scan_target_ids(self, ns_list):
        """[內部] 掃描 NS，找出所有 [Cont]_[Target]_[ID] 的 ID"""
        found_ids = []
        pattern = r"^\[Cont\]_\[Target\]_\[(.*?)\]$"
        
        for ns in ns_list:
            match = re.match(pattern, ns.Name)
            if match:
                found_ids.append(match.group(1))
        
        # 去除重複並排序
        return sorted(list(set(found_ids)))

    def _get_ids_from_ns(self, ns_list, ns_name):
        """[內部] 輔助函式：取得特定 NS 名稱內的幾何 ID"""
        target_ns = next((x for x in ns_list if x.Name == ns_name), None)
        if target_ns and target_ns.Location.Ids.Count > 0:
            return list(target_ns.Location.Ids)
        return []

    def create_grouped_contacts(self, friction_coeff=0.2, contact_name_typo_is_conatct=False):
        """
        [主要功能] 執行自動接觸生成
        
        Parameters
        ----------
        friction_coeff : float
            摩擦係數
        contact_name_typo_is_conatct : bool
            是否要處理使用者拼錯字的情況 (Contact vs Conatct)
        """
        # 取得 Named Selections 列表
        ns_list = self.model.NamedSelections.Children
        
        # 1. 掃描 ID
        target_ids = self._scan_target_ids(ns_list)
        if not target_ids:
            print("警告：未掃描到符合 [Cont]_[Target]_[ID] 格式的 Named Selection。")
            return

        print("--- 開始執行：將為 {} 個 ID 建立獨立群組 ---".format(len(target_ids)))

        connections = self.model.Connections

        # 2. 建立接觸 (包在 Transaction 中)
        def _do_create():
            for grp_id in target_ids:
                # A. 建立新群組
                new_group = connections.AddConnectionGroup()
                new_group.Name = "[ContGroup]_[{}]".format(grp_id)
                
                # B. 決定 NS 名稱 (處理拼字)
                tag = "Conatct" if contact_name_typo_is_conatct else "Contact"
                t_name = "[Cont]_[Target]_[{}]".format(grp_id)
                c_name = "[Cont]_[{}]_[{}]".format(tag, grp_id)

                # C. 獲取幾何 ID
                t_ids = self._get_ids_from_ns(ns_list, t_name)
                c_ids = self._get_ids_from_ns(ns_list, c_name)
                
                if not t_ids or not c_ids:
                    print("群組 [{}] 資料不全 (尋找 {} 失敗)，跳過。".format(grp_id, c_name))
                    continue

                # D. 迴圈生成接觸對 (Pair)
                count = 1
                for t_id in t_ids:
                    for c_id in c_ids:
                        cr = new_group.AddContactRegion()
                        cr.Name = "Pair_{}_Run_{}".format(grp_id, count)
                        
                        # 設定 Target Side (SelectionInfo 需要 SelectionTypeEnum)
                        if self.selection_type_enum:
                            sel_t = self.sel_mgr.CreateSelectionInfo(self.selection_type_enum.GeometryEntities)
                            sel_t.Ids = [t_id]
                            cr.TargetLocation = sel_t
                            
                            # 設定 Source (Contact) Side
                            sel_c = self.sel_mgr.CreateSelectionInfo(self.selection_type_enum.GeometryEntities)
                            sel_c.Ids = [c_id]
                            cr.SourceLocation = sel_c
                        else:
                             print("錯誤：未提供 SelectionTypeEnum，無法設定幾何位置。")

                        # 設定物理屬性 (需要 ContactType Enum)
                        if self.contact_type_enum:
                            cr.ContactType = self.contact_type_enum.Frictional
                            cr.FrictionCoefficient = friction_coeff
                        
                        count += 1
                
                print("建立群組: {} ({} 對)".format(new_group.Name, count-1))

        if self.transaction_cls:
            with self.transaction_cls():
                _do_create()
        else:
            _do_create()


def runContact(ext_api, model=None, transaction_cls=None,
                   selection_type_enum=None,
                   data_model_object_category=None,
                   contact_type=None,
                   friction_coeff=0.2,
                   delete_existing_groups=True,
                   contact_name_typo_is_conatct=False):
    """
    Caller 呼叫用的便利函式
    """
    tool = ContactTool(ext_api, model, transaction_cls,
                       selection_type_enum, data_model_object_category, contact_type)
    
    if delete_existing_groups:
        tool.clear_existing_groups()
        
    tool.create_grouped_contacts(friction_coeff, contact_name_typo_is_conatct)