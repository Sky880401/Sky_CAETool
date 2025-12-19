# -*- coding: utf-8 -*-
import re

class MeshTool(object):
    """
    網格劃分自動化工具 (Logic Only)
    負責：全域設定、Body Method 套用、接觸區域加密、生成網格
    """
    def __init__(self, ext_api, model=None, transaction_cls=None,
                 selection_type_enum=None,
                 data_model_object_category_enum=None,
                 quantity_cls=None,
                 element_order_enum=None,
                 method_type_enum=None):
        
        self.api = ext_api
        self.model = model if model is not None else ext_api.DataModel.Project.Model
        self.mesh = self.model.Mesh
        self.transaction_cls = transaction_cls
        self.sel_mgr = self.api.SelectionManager
        
        # 注入的 Enum 與 Class
        self.SelectionTypeEnum = selection_type_enum
        self.DataModelObjectCategory = data_model_object_category_enum
        self.Quantity = quantity_cls
        self.ElementOrder = element_order_enum
        self.MethodType = method_type_enum

    def set_global_mesh(self, element_size, is_quadratic=True):
        """設定全域尺寸與階數"""
        print("-> 設定全域尺寸: {} mm".format(element_size))
        
        # 使用注入的 Quantity 類別來建立單位物件
        if self.Quantity:
            self.mesh.ElementSize = self.Quantity(str(element_size) + " [mm]")
        else:
            print("警告：未傳入 Quantity 類別，無法設定尺寸！")

        if self.ElementOrder:
            if is_quadratic:
                self.mesh.ElementOrder = self.ElementOrder.Quadratic
            else:
                self.mesh.ElementOrder = self.ElementOrder.Linear

    def apply_body_method(self):
        """套用 Tetrahedrons Method 到所有 Body"""
        print("-> 正在套用 Tetrahedrons Method...")
        
        # 使用注入的 DataModelObjectCategory
        if not self.DataModelObjectCategory:
            print("錯誤：未傳入 DataModelObjectCategory，無法搜尋 Body。")
            return

        all_mech_bodies = self.api.DataModel.GetObjectsByType(self.DataModelObjectCategory.Body)
        all_bodies_ids = []

        for body in all_mech_bodies:
            if body.Suppressed:
                continue
            geo_body = body.GetGeoBody()
            if geo_body:
                all_bodies_ids.append(geo_body.Id)
        
        if not all_bodies_ids:
            print("警告：找不到任何有效的實體 (Body)。")
            return

        # 刪除舊的 Method
        for child in self.mesh.Children:
            if child.Name == "Global_Tetrahedrons":
                child.Delete()

        method = self.mesh.AddAutomaticMethod()
        method.Name = "Global_Tetrahedrons"
        
        if self.SelectionTypeEnum:
            sel = self.sel_mgr.CreateSelectionInfo(self.SelectionTypeEnum.GeometryEntities)
            sel.Ids = all_bodies_ids
            method.Location = sel
        
        if self.MethodType:
            method.Method = self.MethodType.AllTriAllTet
        
        print("   已成功套用至 {} 個 Body。".format(len(all_bodies_ids)))

    def apply_contact_sizing(self, global_size, refinement_factor=0.5):
        """針對接觸區域進行加密"""
        target_size = global_size * refinement_factor
        print("-> 正在搜尋接觸區域進行加密 (尺寸: {} mm)...".format(target_size))
        
        target_ids = []
        ns_list = self.model.NamedSelections.Children
        # 保留您原本的 Regex 邏輯
        pattern = r"^\[Cont\]_\[(Target|Contact|Conyacy|Conatct)\]_\[(.*?)\]$"
        
        for ns in ns_list:
            if re.match(pattern, ns.Name):
                if ns.Location.Ids.Count > 0:
                    target_ids.extend(list(ns.Location.Ids))
        
        if not target_ids:
            print("   警告：未發現任何符合規則的 Named Selection。")
            return

        target_ids = list(set(target_ids))
        
        sizing_name = "Contact_Refinement_x{}".format(refinement_factor)
        for child in self.mesh.Children:
            if child.Name == sizing_name:
                child.Delete()

        sizing = self.mesh.AddSizing()
        sizing.Name = sizing_name
        
        if self.SelectionTypeEnum:
            sel = self.sel_mgr.CreateSelectionInfo(self.SelectionTypeEnum.GeometryEntities)
            sel.Ids = target_ids
            sizing.Location = sel
            
        if self.Quantity:
            sizing.ElementSize = self.Quantity(str(target_size) + " [mm]")

    def generate_mesh(self):
        """觸發網格生成"""
        print("-> 正在生成網格 (Generate Mesh)...")
        self.mesh.GenerateMesh()
        print("   網格生成完畢！")


def runMesh(ext_api, element_size=5.0, is_quadratic=True, do_contact_refine=True,
            model=None, transaction_cls=None,
            selection_type_enum=None,
            data_model_object_category_enum=None,
            quantity_cls=None,
            element_order_enum=None,
            method_type_enum=None):
    """
    Caller 呼叫用的便利函式
    """
    tool = MeshTool(ext_api, model=model, transaction_cls=transaction_cls,
                    selection_type_enum=selection_type_enum,
                    data_model_object_category_enum=data_model_object_category_enum,
                    quantity_cls=quantity_cls,
                    element_order_enum=element_order_enum,
                    method_type_enum=method_type_enum)

    # 設定參數 (包在 Transaction 中以提升效能)
    if transaction_cls:
        with transaction_cls():
            tool.set_global_mesh(element_size, is_quadratic)
            tool.apply_body_method()
            if do_contact_refine:
                tool.apply_contact_sizing(element_size, 0.5)
    else:
        tool.set_global_mesh(element_size, is_quadratic)
        tool.apply_body_method()
        if do_contact_refine:
            tool.apply_contact_sizing(element_size, 0.5)

    # 生成網格通常比較耗時，且需要即時更新進度，建議放在 Transaction 之外
    tool.generate_mesh()