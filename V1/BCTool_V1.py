# -*- coding: utf-8 -*-
import re

class BCTool(object):
    """
    邊界條件自動生成工具 (Logic Only)
    負責：清除舊 BC、掃描 Named Selection、自動建立 Fixed 與 Displacement
    """
    def __init__(self, ext_api, model=None, transaction_cls=None,
                 quantity_cls=None, load_define_by_enum=None):
        
        self.api = ext_api
        self.model = model if model is not None else ext_api.DataModel.Project.Model
        self.transaction_cls = transaction_cls
        
        # 注入的 Enum 與 Class
        self.Quantity = quantity_cls
        self.LoadDefineBy = load_define_by_enum
        
        # 取得當前分析環境 (通常是第一個分析系統)
        if self.model.Analyses.Count > 0:
            self.analysis = self.model.Analyses[0]
        else:
            raise Exception("錯誤：專案中沒有任何分析系統！")

        self.ns_list = self.model.NamedSelections.Children

    def clear_existing_bcs(self):
        """清除舊的自動化邊界條件"""
        objects_to_delete = []
        for child in self.analysis.Children:
            if child.Name.startswith("AutoFixed_") or child.Name.startswith("AutoDisp_"):
                objects_to_delete.append(child)
        
        if objects_to_delete:
            for obj in objects_to_delete:
                obj.Delete()
            print("已清除 {} 個舊的自動化邊界條件。".format(len(objects_to_delete)))

    def apply_boundary_conditions(self, z_magnitude, direction_sign):
        """
        掃描 Named Selection 並套用邊界條件
        注意：此函式建議在 Transaction 之外執行
        """
        final_z_value = z_magnitude * direction_sign
        print("-> 目標 Z 軸位移值: {} mm".format(final_z_value))

        count_fixed = 0
        count_disp = 0

        # Regex 規則 (忽略大小寫)
        p_fixed = re.compile(r"Fixed", re.IGNORECASE)
        p_disp = re.compile(r"Disp", re.IGNORECASE)

        # 檢查依賴是否注入成功
        if not self.Quantity or not self.LoadDefineBy:
            print("錯誤：未傳入 Quantity 或 LoadDefineBy，無法設定位移值。")
            return 0, 0

        for ns in self.ns_list:
            # 1. 處理 Fixed Support
            if p_fixed.search(ns.Name):
                if ns.Location.Ids.Count > 0:
                    fix = self.analysis.AddFixedSupport()
                    fix.Name = "AutoFixed_" + ns.Name
                    fix.Location = ns.Location
                    count_fixed += 1
                    print("   已建立固定支撐: " + fix.Name)

            # 2. 處理 Displacement
            elif p_disp.search(ns.Name):
                if ns.Location.Ids.Count > 0:
                    disp = self.analysis.AddDisplacement()
                    disp.Name = "AutoDisp_" + ns.Name
                    disp.Location = ns.Location
                    
                    # 設定定義方式為 Components
                    disp.DefineBy = self.LoadDefineBy.Components
                    
                    # 設定 X, Y 為 0
                    disp.XComponent.Output.DiscreteValues = [self.Quantity("0[mm]")]
                    disp.YComponent.Output.DiscreteValues = [self.Quantity("0[mm]")]
                    
                    # 設定 Z 軸位移
                    z_qty = self.Quantity(str(final_z_value) + " [mm]")
                    disp.ZComponent.Output.DiscreteValues = [z_qty]
                    
                    count_disp += 1
                    print("   已建立位移: " + disp.Name)

        print("總計建立: Fixed x {}, Disp x {}".format(count_fixed, count_disp))
        return count_fixed, count_disp


def runBC(ext_api, z_magnitude=5.0, direction_sign=-1.0,
          model=None, transaction_cls=None,
          quantity_cls=None, load_define_by_enum=None):
    """
    Caller 呼叫用的便利函式
    """
    tool = BCTool(ext_api, model=model, transaction_cls=transaction_cls,
                  quantity_cls=quantity_cls,
                  load_define_by_enum=load_define_by_enum)

    # 1. 清除舊資料 (可以用 Transaction 加速)
    if transaction_cls:
        with transaction_cls():
            tool.clear_existing_bcs()
    else:
        tool.clear_existing_bcs()

    # 2. 建立新資料
    # 【重要】這裡故意不使用 Transaction
    # 因為 Displacement.Output.DiscreteValues 在 Transaction 內賦值常會報錯 (Null Reference)
    tool.apply_boundary_conditions(z_magnitude, direction_sign)