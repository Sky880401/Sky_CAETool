# -*- coding: utf-8 -*-
# ==========================================
# Jetsoft 自動網格劃分工具 (修正 Body 抓取版)
# ==========================================
import clr
import sys
import re

# 引入必要的 .NET 函式庫
try:
    clr.AddReference("System.Windows.Forms")
    clr.AddReference("System.Drawing")
    from System.Windows.Forms import (Application, Form, Label, TextBox, Button, 
                                      CheckBox, RadioButton, GroupBox, DialogResult, FormStartPosition, MessageBox)
    from System.Drawing import Point, Size
except Exception as e:
    print("錯誤：無法載入 Windows Forms 函式庫。" + str(e))

# ==========================================
# 1. 後端邏輯類別
# ==========================================
class AutoMesher:
    def __init__(self, api):
        self.api = api
        self.model = api.DataModel.Project.Model
        self.mesh = self.model.Mesh
        self.sel_mgr = api.SelectionManager

    def set_global_mesh(self, element_size, is_quadratic=True):
        print("-> 設定全域尺寸: {} mm".format(element_size))
        self.mesh.ElementSize = Quantity(str(element_size) + " [mm]")
        if is_quadratic:
            self.mesh.ElementOrder = ElementOrder.Quadratic
        else:
            self.mesh.ElementOrder = ElementOrder.Linear

    def apply_body_method(self):
        print("-> 正在套用 Tetrahedrons Method...")
        all_bodies_ids = []
        
        # ★★★ 修正點：使用全域搜尋抓取 Body ★★★
        all_mech_bodies = self.api.DataModel.GetObjectsByType(DataModelObjectCategory.Body)
        print("   (系統偵測到 {} 個 Body 物件)".format(len(all_mech_bodies)))

        for body in all_mech_bodies:
            # 排除被抑制的 Body
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
        
        sel = self.sel_mgr.CreateSelectionInfo(SelectionTypeEnum.GeometryEntities)
        sel.Ids = all_bodies_ids
        method.Location = sel
        method.Method = MethodType.AllTriAllTet
        print("   已成功套用至 {} 個 Body。".format(len(all_bodies_ids)))

    def apply_contact_sizing(self, global_size, refinement_factor=0.5):
        target_size = global_size * refinement_factor
        print("-> 正在搜尋接觸區域進行加密 (尺寸: {} mm)...".format(target_size))
        
        target_ids = []
        ns_list = self.model.NamedSelections.Children
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
        sel = self.sel_mgr.CreateSelectionInfo(SelectionTypeEnum.GeometryEntities)
        sel.Ids = target_ids
        sizing.Location = sel
        sizing.ElementSize = Quantity(str(target_size) + " [mm]")

    def run_mesh_generation(self):
        print("-> 正在生成網格 (Generate Mesh)，請稍候...")
        self.mesh.GenerateMesh()
        print("   網格生成完畢！")

# ==========================================
# 2. 前端 GUI 類別
# ==========================================
class MeshInputForm(Form):
    def __init__(self):
        self.Text = "Jetsoft 網格設定與生成"
        self.Size = Size(350, 320)
        self.StartPosition = FormStartPosition.CenterScreen
        self.TopMost = True
        
        # 全域尺寸
        self.lbl_size = Label()
        self.lbl_size.Text = "全域尺寸 (mm):"
        self.lbl_size.Location = Point(20, 20)
        self.Controls.Add(self.lbl_size)
        
        self.txt_size = TextBox()
        self.txt_size.Text = "5.0"
        self.txt_size.Location = Point(20, 45)
        self.Controls.Add(self.txt_size)
        
        # 元素階數
        self.grp_order = GroupBox()
        self.grp_order.Text = "元素階數"
        self.grp_order.Location = Point(20, 80)
        self.grp_order.Size = Size(280, 80)
        self.Controls.Add(self.grp_order)
        
        self.rb_quad = RadioButton()
        self.rb_quad.Text = "二階 (Quadratic)"
        self.rb_quad.Location = Point(15, 25)
        self.rb_quad.Checked = True
        self.rb_quad.Size = Size(200, 20)
        self.grp_order.Controls.Add(self.rb_quad)
        
        self.rb_linear = RadioButton()
        self.rb_linear.Text = "一階 (Linear)"
        self.rb_linear.Location = Point(15, 50)
        self.rb_linear.Size = Size(200, 20)
        self.grp_order.Controls.Add(self.rb_linear)
        
        # 加密選項
        self.chk_refine = CheckBox()
        self.chk_refine.Text = "加密接觸區域 (0.5x)"
        self.chk_refine.Location = Point(20, 180)
        self.chk_refine.Size = Size(250, 20)
        self.chk_refine.Checked = True
        self.Controls.Add(self.chk_refine)
        
        # 按鈕
        self.btn_run = Button()
        self.btn_run.Text = "執行設定並生成"
        self.btn_run.Location = Point(100, 220)
        self.btn_run.Size = Size(120, 40)
        self.btn_run.DialogResult = DialogResult.OK
        self.Controls.Add(self.btn_run)

# ==========================================
# 3. 主執行區
# ==========================================
def main():
    print("--- Mesh 腳本開始執行 ---")
    try:
        form = MeshInputForm()
        result = form.ShowDialog()
        
        if result != DialogResult.OK:
            print("使用者取消。")
            return

        try:
            global_size = float(form.txt_size.Text)
        except ValueError:
            MessageBox.Show("請輸入有效的數字！")
            return
            
        is_quadratic = form.rb_quad.Checked
        do_refine = form.chk_refine.Checked
        
        mesher = AutoMesher(ExtAPI)
        
        with Transaction():
            mesher.set_global_mesh(global_size, is_quadratic)
            mesher.apply_body_method()
            if do_refine:
                mesher.apply_contact_sizing(global_size, 0.5)
        
        # 移出 Transaction 以確保網格生成介面會刷新
        mesher.run_mesh_generation()
        
        print("--- 全部完成 ---")
        MessageBox.Show("完成！")
        
    except Exception as e:
        import traceback
        print("錯誤:\n" + traceback.format_exc())
        MessageBox.Show("錯誤：" + str(e))

main()
