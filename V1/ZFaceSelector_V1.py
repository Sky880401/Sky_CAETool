# -*- coding: utf-8 -*-
class ZFaceSelectorTool(object):
    def __init__(self, ext_api, model=None, transaction_cls=None, selection_type_enum=None):
        self.api = ext_api
        self.model = model if model is not None else ext_api.DataModel.Project.Model
        self.transaction_cls = transaction_cls
        self.st_enum = selection_type_enum
        self.geo_data = ext_api.DataModel.GeoData

    def run_selection(self, tolerance=0.001):
        # 1. 取得 Z 軸極值
        max_z = -1e20
        min_z = 1e20
        
        # 遍歷所有面找出極值
        for assembly in self.geo_data.Assemblies:
            for part in assembly.Parts:
                for body in part.Bodies:
                    for face in body.Faces:
                        z = face.Centroid[2]
                        if z > max_z: max_z = z
                        if z < min_z: min_z = z
        
        print("[ZFace] Max Z: {:.4f}, Min Z: {:.4f}".format(max_z, min_z))

        # 2. 篩選面 ID
        top_ids = []
        bot_ids = []
        
        for assembly in self.geo_data.Assemblies:
            for part in assembly.Parts:
                for body in part.Bodies:
                    for face in body.Faces:
                        z = face.Centroid[2]
                        if abs(z - max_z) < tolerance:
                            top_ids.append(face.Id)
                        if abs(z - min_z) < tolerance:
                            bot_ids.append(face.Id)

        # 3. 建立 Named Selection (名稱必須與 BC 模組的搜尋邏輯對應)
        self._create_ns("[BC]_[Disp]_Top Face", top_ids)
        self._create_ns("[BC]_[Fixed]_Bottom Face", bot_ids)

    def _create_ns(self, name, ids):
        if not ids:
            print("[ZFace] 警告：找不到符合 {} 的面".format(name))
            return

        with self.transaction_cls():
            # 刪除舊的同名 NS (避免重複)
            for ns in self.model.NamedSelections.Children:
                if ns.Name == name:
                    ns.Delete()
            
            new_ns = self.model.AddNamedSelection()
            new_ns.Name = name
            sel = self.api.SelectionManager.CreateSelectionInfo(self.st_enum.GeometryEntities)
            sel.Ids = ids
            new_ns.Location = sel
            print("[ZFace] 已建立: {} ({} Faces)".format(name, len(ids)))

# ContactTool_V1.py 範例結構
def runZFaceSelector(ext_api, model=None, transaction_cls=None, selection_mgr=None, friction=0.2):
    # 如果 caller 沒傳進來，再嘗試用全域變數 (Backward Compatibility)
    # 但在這個新架構下，caller (main.py) 一定會傳
    model = model if model else ext_api.DataModel.Project.Model
    
    # 初始化工具類別
    tool = ContactTool(ext_api, model, transaction_cls, selection_mgr)
    tool.run_contact(friction)