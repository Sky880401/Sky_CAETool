# -*- coding: utf-8 -*-
# ==========================================
# Jetsoft 自動邊界條件生成工具 (修正版 - 解決 SystemError)
# ==========================================
import clr
import sys
import re

# 引入 .NET GUI 庫
try:
    clr.AddReference("System.Windows.Forms")
    clr.AddReference("System.Drawing")
    from System.Windows.Forms import (Application, Form, Label, TextBox, Button, 
                                      RadioButton, GroupBox, DialogResult, FormStartPosition, MessageBox)
    from System.Drawing import Point, Size
except Exception as e:
    print("無法載入 GUI 庫: " + str(e))

# ==========================================
# 1. 後端邏輯類別
# ==========================================
class AutoBCGenerator:
    def __init__(self, api):
        self.api = api
        self.model = api.DataModel.Project.Model
        # 取得當前分析環境
        if self.model.Analyses.Count > 0:
            self.analysis = self.model.Analyses[0]
        else:
            raise Exception("專案中沒有任何分析系統！")

        self.ns_list = self.model.NamedSelections.Children

    def clear_existing_bcs(self):
        """清除舊的自動化邊界條件"""
        objects_to_delete = []
        for child in self.analysis.Children:
            if child.Name.startswith("Auto_Fixed") or child.Name.startswith("Auto_Disp"):
                objects_to_delete.append(child)
        
        if objects_to_delete:
            for obj in objects_to_delete:
                obj.Delete()
            print("已清除 {} 個舊的自動化邊界條件。".format(len(objects_to_delete)))

    def apply_boundary_conditions(self, z_magnitude, direction_sign):
        """
        z_magnitude: 位移大小 (絕對值)
        direction_sign: 方向 (+1 或 -1)
        """
        final_z_value = z_magnitude * direction_sign
        print("-> 目標 Z 軸位移值: {} mm".format(final_z_value))

        count_fixed = 0
        count_disp = 0

        # Regex 規則
        p_fixed = re.compile(r"Fixed", re.IGNORECASE)
        p_disp = re.compile(r"Disp", re.IGNORECASE)

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
                    disp.DefineBy = LoadDefineBy.Components
                    
                    # ★★★ 修正點：使用 Inputs 強制賦值，避免 Output 為 Null 的錯誤 ★★★
                    # 設定 X 為 0
                    disp.XComponent.Output.DiscreteValues = [Quantity("0[mm]")]
                    
                    # 設定 Y 為 0
                    disp.YComponent.Output.DiscreteValues = [Quantity("0[mm]")]
                    
                    # 設定 Z 軸位移
                    disp.ZComponent.Output.DiscreteValues = [Quantity(str(final_z_value) + " [mm]")]
                    
                    count_disp += 1
                    print("   已建立位移: " + disp.Name)

        print("總計建立: Fixed x {}, Disp x {}".format(count_fixed, count_disp))
        return count_fixed, count_disp

# ==========================================
# 2. 前端 GUI 類別
# ==========================================
class BCInputForm(Form):
    def __init__(self):
        self.Text = "Jetsoft 邊界條件設定"
        self.Size = Size(350, 280)
        self.StartPosition = FormStartPosition.CenterScreen
        self.TopMost = True

        # 輸入標籤
        self.lbl_val = Label()
        self.lbl_val.Text = "Z 軸位移量 (Magnitude, mm):"
        self.lbl_val.Location = Point(20, 20)
        self.lbl_val.Size = Size(250, 20)
        self.Controls.Add(self.lbl_val)

        # 輸入框
        self.txt_val = TextBox()
        self.txt_val.Text = "5.0"
        self.txt_val.Location = Point(20, 45)
        self.Controls.Add(self.txt_val)

        # 方向選擇
        self.grp_dir = GroupBox()
        self.grp_dir.Text = "移動方向 (Direction)"
        self.grp_dir.Location = Point(20, 80)
        self.grp_dir.Size = Size(280, 80)
        self.Controls.Add(self.grp_dir)

        self.rb_neg = RadioButton()
        self.rb_neg.Text = "-Z 方向 (向下/插入)"
        self.rb_neg.Location = Point(15, 25)
        self.rb_neg.Size = Size(200, 20)
        self.rb_neg.Checked = True
        self.grp_dir.Controls.Add(self.rb_neg)

        self.rb_pos = RadioButton()
        self.rb_pos.Text = "+Z 方向 (向上/拉伸)"
        self.rb_pos.Location = Point(15, 50)
        self.rb_pos.Size = Size(200, 20)
        self.grp_dir.Controls.Add(self.rb_pos)

        # 按鈕
        self.btn_ok = Button()
        self.btn_ok.Text = "套用邊界條件"
        self.btn_ok.Location = Point(100, 180)
        self.btn_ok.Size = Size(120, 40)
        self.btn_ok.DialogResult = DialogResult.OK
        self.Controls.Add(self.btn_ok)

# ==========================================
# 3. 主執行區
# ==========================================
def main():
    print("--- 啟動邊界條件設定工具 ---")
    try:
        # 1. 顯示 GUI
        form = BCInputForm()
        result = form.ShowDialog()

        if result != DialogResult.OK:
            print("使用者取消。")
            return

        # 2. 取得數據
        try:
            mag = float(form.txt_val.Text)
        except ValueError:
            MessageBox.Show("請輸入有效的數字！")
            return

        sign = -1.0 if form.rb_neg.Checked else 1.0
        
        # 3. 執行後端邏輯
        bc_gen = AutoBCGenerator(ExtAPI)
        
        # ★★★ 修正點：移除 Transaction ★★★
        # 讓物件建立後立即初始化，避免 Null Reference
        bc_gen.clear_existing_bcs()
        c_fix, c_disp = bc_gen.apply_boundary_conditions(mag, sign)

        # 4. 完成提示
        if c_fix == 0 and c_disp == 0:
            MessageBox.Show("警告：未建立任何邊界條件！\n請檢查 Named Selection 是否包含 'Fixed' 或 'Disp'。")
        else:
            final_val = mag * sign
            MessageBox.Show("設定完成！\nFixed: {}\nDisp: {}\nZ軸位移: {} mm".format(c_fix, c_disp, final_val))

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        MessageBox.Show("發生錯誤: " + str(e))

main()
