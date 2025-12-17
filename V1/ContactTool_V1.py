# -*- coding: utf-8 -*-
import re

class ContactTool(object):
    def __init__(self, api, model, transaction_cls, selection_mgr):
        self.api = api
        self.model = model
        self.connections = model.Connections
        self.transaction_cls = transaction_cls
        self.sel_mgr = selection_mgr

    def run_contact(self, friction_coeff=0.2):
        # 1. 清除舊群組
        groups = [c for c in self.connections.Children if "ConnectionGroup" in str(c.GetType())]
        if groups:
            with self.transaction_cls():
                for g in groups: g.Delete()
            print("[Contact] 已清除舊接觸群組")

        # 2. 掃描 ID
        ids = []
        pattern = r"^\[Cont\]_\[Target\]_\[(.*?)\]$"
        for ns in self.model.NamedSelections.Children:
            match = re.match(pattern, ns.Name)
            if match:
                ids.append(match.group(1))
        ids = sorted(list(set(ids)))

        # 3. 建立新接觸
        if ids:
            with self.transaction_cls():
                for i in ids:
                    self._create_group(i, friction_coeff)
        else:
            print("[Contact] 警告：未發現符合格式的 Named Selection")

    def _create_group(self, cid, friction):
        t_name = "[Cont]_[Target]_[{}]".format(cid)
        c_name = "[Cont]_[Contact]_[{}]".format(cid) # V0原始碼為 Contact
        
        t_ns = self._get_ns(t_name)
        c_ns = self._get_ns(c_name)
        
        if not t_ns or not c_ns:
            return

        grp = self.connections.AddConnectionGroup()
        grp.Name = "[ContGroup]_[{}]".format(cid)
        
        # 建立配對 (簡化版：假設 NS 內是一對一或多對多)
        cr = grp.AddContactRegion()
        cr.Name = "Pair_{}".format(cid)
        cr.TargetLocation = t_ns.Location
        cr.SourceLocation = c_ns.Location
        
        # 設定物理性質 (需確保 ContactType Enum 存在於環境中，或傳入 int)
        # Frictional = 2
        try:
            cr.ContactType = ContactType.Frictional
        except:
            pass # 如果環境中沒有 Enum 定義，可能需要手動指定
            
        cr.FrictionCoefficient = friction
        print("[Contact] 建立群組 ID: {}".format(cid))

    def _get_ns(self, name):
        for ns in self.model.NamedSelections.Children:
            if ns.Name == name: return ns
        return None

def run(api, model, transaction_cls, selection_mgr, friction=0.2):
    tool = ContactTool(api, model, transaction_cls, selection_mgr)
    tool.run_contact(friction)