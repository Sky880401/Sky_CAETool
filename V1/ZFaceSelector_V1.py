# -*- coding: utf-8 -*-
import math

class ZFaceSelector(object):
    """
    專門用來篩選 Z 軸向面並建立 Named Selection 的工具。
    注意：此檔案設計為「被 import 的 worker」，不要在 import 時就直接執行。
    """

    def __init__(self, ext_api, model=None, transaction_cls=None, selection_type_enum=None):
        """
        Parameters
        ----------
        ext_api : ExtAPI
            Mechanical 注入的 ExtAPI 物件（由 caller 傳入）
        model : Model, optional
            Mechanical 的全域 Model（建議由 caller 傳入；若未傳入會嘗試從 ExtAPI 取得）
        transaction_cls : Transaction, optional
            Mechanical 的 Transaction 類別（由 caller 傳入可避免 import scope 找不到）
        selection_type_enum : SelectionTypeEnum, optional
            Mechanical 的 SelectionTypeEnum（由 caller 傳入可避免 import scope 找不到）
        """
        self.api = ext_api
        self.model = model if model is not None else ext_api.DataModel.Project.Model
        self.transaction_cls = transaction_cls
        self.selection_type_enum = selection_type_enum
        self.geo_data = ext_api.DataModel.GeoData

    def _get_z_limits(self):
        """[內部] 掃描所有面，找出 Z 的最大值與最小值（以面重心 Centroid 判斷）"""
        max_z = -1e20
        min_z =  1e20

        for assembly in self.geo_data.Assemblies:
            for part in assembly.Parts:
                for body in part.Bodies:
                    for face in body.Faces:
                        z_coord = face.Centroid[2]
                        if z_coord > max_z:
                            max_z = z_coord
                        if z_coord < min_z:
                            min_z = z_coord

        return max_z, min_z

    def create_selection(self, tolerance=1e-4,
                         top_name="[BC]_[Disp]_Top Face",
                         bottom_name="[BC]_[Fixed]_Bottom Face"):
        """
        [主要功能] 建立最大與最小 Z 的 Named Selection

        Parameters
        ----------
        tolerance : float
            容許誤差（同單位於幾何座標）。用 abs(z - z_extreme) < tolerance 判定。
        top_name, bottom_name : str
            Named Selection 的名稱
        """
        global_max, global_min = self._get_z_limits()
        print("偵測到 Max Z: {:.6g}, Min Z: {:.6g}".format(global_max, global_min))

        top_face_ids = []
        bottom_face_ids = []

        for assembly in self.geo_data.Assemblies:
            for part in assembly.Parts:
                for body in part.Bodies:
                    for face in body.Faces:
                        z_coord = face.Centroid[2]
                        if abs(z_coord - global_max) < tolerance:
                            top_face_ids.append(face.Id)
                        if abs(z_coord - global_min) < tolerance:
                            bottom_face_ids.append(face.Id)

        self._create_ns(top_name, top_face_ids)
        self._create_ns(bottom_name, bottom_face_ids)

        return top_face_ids, bottom_face_ids

    def _create_ns(self, name, ids):
        """[內部] 在 Mechanical 建立 Named Selection"""
        if not ids:
            print("警告：找不到符合 '{}' 的面。".format(name))
            return None

        def _do_create():
            ns = self.model.AddNamedSelection()
            ns.Name = name

            # SelectionTypeEnum 通常在 Mechanical 的 global scope；建議由 caller 傳入
            if self.selection_type_enum is None:
                raise NameError("SelectionTypeEnum 未提供：請由 caller 傳入 selection_type_enum=SelectionTypeEnum")

            sel_info = self.api.SelectionManager.CreateSelectionInfo(self.selection_type_enum.GeometryEntities)
            sel_info.Ids = ids
            ns.Location = sel_info
            return ns

        # Transaction 通常也在 Mechanical 的 global scope；建議由 caller 傳入
        if self.transaction_cls is not None:
            with self.transaction_cls():
                ns = _do_create()
        else:
            ns = _do_create()

        print("成功建立: {} (包含 {} 個面)".format(name, len(ids)))
        return ns


def runZFaceSelector(ext_api, tolerance=0.001,
        top_name="[BC]_[Disp]_Top Face",
        bottom_name="[BC]_[Fixed]_Bottom Face",
        model=None, transaction_cls=None, selection_type_enum=None):
    """
    便利函式：給 caller 一行呼叫用
    """
    tool = ZFaceSelector(ext_api, model=model,
                         transaction_cls=transaction_cls,
                         selection_type_enum=selection_type_enum)
    return tool.create_selection(tolerance=tolerance, top_name=top_name, bottom_name=bottom_name)
