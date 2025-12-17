# -*- coding: utf-8 -*-
# ==========================================
# Jetsoft 自動後處理工具 (Connector Post-Processing)
# ==========================================
import clr
import re

# 引入 .NET GUI 庫
try:
    clr.AddReference("System.Windows.Forms")
    clr.AddReference("System.Drawing")
    from System.Windows.Forms import (Application, Form, Label, Button, CheckBox, 
                                      GroupBox, DialogResult, FormStartPosition, MessageBox)
    from System.Drawing import Point, Size
except Exception as e:
    print("無法載入 GUI 庫: " + str(e))

# ==========================================
# 1. 後端邏輯類別
# ==========================================
class AutoPostProcessor:
    def __init__(self, api):
        self.api = api
        self.model = api.DataModel.Project.Model
        
        if self.model.Analyses.Count > 0:
            self.analysis = self.model.Analyses[0]
            self.solution = self.analysis.Solution
        else:
            raise Exception("錯誤：專案中沒有任何分析系統！")

    def _find_bc_by_name_pattern(self, pattern):
        """
        搜尋邊界條件 (用來設定反力探針)
        """
        # 搜尋分析環境下的所有子物件
        for child in self.analysis.Children:
            # 判斷是否為邊界條件且名稱符合規則
            if re.search(pattern, child.Name, re.IGNORECASE):
                return child
        return None

    def add_basic_results(self):
        """加入基本結果: 總變形、等效應力"""
        print("-> 加入基本結果 (Deformation & Stress)...")
        
        # 總變形
        deform = self.solution.AddTotalDeformation()
        deform.Name = "Total Deformation"
        
        # Z 軸方向變形 (觀察插入深度)
        dir_deform = self.solution.AddDirectionalDeformation()
        dir_deform.Name = "Directional Deformation (Z)"
        dir_deform.NormalOrientation = NormalOrientationType.ZAxis
        
        # 等效應力 (Von-Mises)
        stress = self.solution.AddEquivalentStress()
        stress.Name = "Equivalent Stress (Von-Mises)"

    def add_contact_tool(self):
        """加入接觸工具 (Contact Tool) 以檢視接觸壓力與狀態"""
        print("-> 加入接觸工具 (Contact Tool)...")
        
        # 建立 Contact Tool
        c_tool = self.solution.AddContactTool()
        c_tool.Name = "Connector Contact Status"
        
        # 加入子結果：接觸壓力 (Pressure)
        c_tool.AddPressure()
        # 加入子結果：滑移距離 (Sliding Distance)
        c_tool.AddSlidingDistance()

    def add_insertion_force_probe(self):
        """加入反力探針 (Force Reaction) 來測量插拔力"""
        print("-> 正在設定插拔力探針 (Force Reaction)...")
        
        # 策略：優先尋找名為 'Auto_Fixed...' 的固定端，找不到則找 'Auto_Disp...'
        # 這是連接上一支 Script 的關鍵
        target_bc = self._find_bc_by_name_pattern(r"AutoFixed")
        if not target_bc:
            target_bc = self._find_bc_by_name_pattern(r"AutoDisp")
        
        if target_bc:
            probe = self.solution.AddForceReaction()
            probe.Name = "Insertion Force Probe"
            
            # 設定探針位置為 "邊界條件"
            probe.LocationMethod = LocationDefinitionMethod.BoundaryCondition
            probe.BoundaryConditionSelection = target_bc
            
            # 設定顯示 Z 軸分量 (插拔方向)
            probe.ResultSelection = ProbeDisplayFilter.ZAxis
            print("   已將探針綁定至: " + target_bc.Name)
        else:
            print("   警告：找不到 'Auto_Fixed' 或 'Auto_Disp'，無法自動建立反力探針。")

    def evaluate_results(self):
        """計算所有結果 (讓黃色閃電變成綠色打勾)"""
        print("-> 正在提取結果數值 (Evaluate All Results)...")
        self.solution.EvaluateAllResults()

# ==========================================
# 2. 前端 GUI 類別
# ==========================================
class PostInputForm(Form):
    def __init__(self):
        self.Text = "Jetsoft 後處理設定"
        self.Size = Size(300, 300)
        self.StartPosition = FormStartPosition.CenterScreen
        self.TopMost = True

        # GroupBox
        self.grp = GroupBox()
        self.grp.Text = "選擇要輸出的結果"
        self.grp.Location = Point(20, 20)
        self.grp.Size = Size(240, 160)
        self.Controls.Add(self.grp)

        # CheckBoxes
        self.chk_basic = CheckBox()
        self.chk_basic.Text = "基本結果 (變形 + 應力)"
        self.chk_basic.Location = Point(15, 30)
        self.chk_basic.Size = Size(200, 20)
        self.chk_basic.Checked = True
        self.grp.Controls.Add(self.chk_basic)

        self.chk_contact = CheckBox()
        self.chk_contact.Text = "接觸工具 (壓力/狀態)"
        self.chk_contact.Location = Point(15, 60)
        self.chk_contact.Size = Size(200, 20)
        self.chk_contact.Checked = True
        self.grp.Controls.Add(self.chk_contact)

        self.chk_force = CheckBox()
        self.chk_force.Text = "插拔力探針 (Reaction Probe)"
        self.chk_force.Location = Point(15, 90)
        self.chk_force.Size = Size(200, 20)
        self.chk_force.Checked = True
        self.grp.Controls.Add(self.chk_force)
        
        self.chk_eval = CheckBox()
        self.chk_eval.Text = "立即計算結果 (Evaluate)"
        self.chk_eval.Location = Point(15, 120)
        self.chk_eval.Size = Size(200, 20)
        self.chk_eval.Checked = True # 預設直接算出結果
        self.grp.Controls.Add(self.chk_eval)

        # Button
        self.btn_run = Button()
        self.btn_run.Text = "生成結果物件"
        self.btn_run.Location = Point(80, 200)
        self.btn_run.Size = Size(120, 40)
        self.btn_run.DialogResult = DialogResult.OK
        self.Controls.Add(self.btn_run)

# ==========================================
# 3. 主執行區
# ==========================================
def main():
    print("--- 啟動後處理工具 ---")
    try:
        form = PostInputForm()
        result = form.ShowDialog()

        if result != DialogResult.OK:
            return

        post = AutoPostProcessor(ExtAPI)

        # 這裡不需要 Transaction，因為建立結果物件很快，且 Evaluate 需要即時更新
        if form.chk_basic.Checked:
            post.add_basic_results()
            
        if form.chk_contact.Checked:
            post.add_contact_tool()
            
        if form.chk_force.Checked:
            post.add_insertion_force_probe()

        if form.chk_eval.Checked:
            post.evaluate_results()
            
        MessageBox.Show("後處理物件建立完成！")

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        MessageBox.Show("發生錯誤: " + str(e))

main()
