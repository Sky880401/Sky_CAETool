# -*- coding: utf-8 -*-
import math

class ZFaceSelector:
    """
    這是一個專門用來篩選 Z 軸向面的工具箱 (Class)
    """
    def __init__(self, api):
        # 1. 初始化：拿到 Mechanical 的操作權限
        self.api = api
        self.geo_data = api.DataModel.GeoData # 取得幾何資料的入口

    def _get_z_limits(self):
        """
        [內部工具] 掃描所有面，找出 Z 的最大值與最小值
        """
        max_z = -1e20 # 先設定一個極小值
        min_z = 1e20  # 先設定一個極大值
        
        # 遍歷所有的組件 -> 零件 -> 本體 -> 面
        for assembly in self.geo_data.Assemblies:
            for part in assembly.Parts:
                for body in part.Bodies:
                    for face in body.Faces:
                        # 取得面的重心 Z 座標
                        z_coord = face.Centroid[2]
                        
                        # 比大小，更新紀錄
                        if z_coord > max_z: max_z = z_coord
                        if z_coord < min_z: min_z = z_coord
        
        return max_z, min_z

    def create_selection(self, tolerance=1e-4):
        """
        [主要功能] 建立最大與最小 Z 的 Named Selection
        """
        # 1. 先執行第一階段：取得極值
        global_max, global_min = self._get_z_limits()
        
        print("偵測到 Max Z: {:.4f}, Min Z: {:.4f}".format(global_max, global_min))

        top_face_ids = []
        bottom_face_ids = []

        # 2. 執行第二階段：抓取符合條件的面 ID
        for assembly in self.geo_data.Assemblies:
            for part in assembly.Parts:
                for body in part.Bodies:
                    for face in body.Faces:
                        z_coord = face.Centroid[2]
                        
                        # 判斷是否接近最大值 (使用容許誤差 tolerance)
                        if abs(z_coord - global_max) < tolerance:
                            top_face_ids.append(face.Id)
                        
                        # 判斷是否接近最小值
                        if abs(z_coord - global_min) < tolerance:
                            bottom_face_ids.append(face.Id)

        # 3. 建立 Named Selection (呼叫內部函式)
        self._create_ns("[BC]_[Disp]_Top Face", top_face_ids)
        self._create_ns("[BC]_[Fixed]_Bottom Face", bottom_face_ids)

    def _create_ns(self, name, ids):
        """
        [內部工具] 負責在 Mechanical 介面上建立 Named Selection
        """
        if not ids:
            print("警告：找不到符合 " + name + " 的面。")
            return

        # 使用 Transaction 加速介面處理
        with Transaction():
            # 建立 Named Selection 物件
            # 參考來源: Scripting Guide 
            ns = Model.AddNamedSelection()
            ns.Name = name
            
            # 設定選擇資訊
            # 參考來源: Scripting Guide 
            sel_info = self.api.SelectionManager.CreateSelectionInfo(SelectionTypeEnum.GeometryEntities)
            sel_info.Ids = ids
            ns.Location = sel_info
            
        print("成功建立: " + name + " (包含 " + str(len(ids)) + " 個面)")

# --- 執行區 ---
# 這裡就是您在 "主程式" 實際要寫的內容，非常簡潔

# 1. 實例化工具箱
my_tool = ZFaceSelector(ExtAPI)

# 2. 執行功能
my_tool.create_selection(tolerance=0.001)
