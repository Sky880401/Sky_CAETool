# -*- coding: utf-8 -*-

class SolverTool(object):
    def __init__(self, ext_api, model=None, transaction_cls=None, quantity_cls=None,
                 # 新增兩個 Enum 參數
                 auto_time_stepping_enum=None,
                 time_step_define_by_type_enum=None):
        
        self.api = ext_api
        self.model = model if model is not None else ext_api.DataModel.Project.Model
        self.transaction_cls = transaction_cls
        self.Quantity = quantity_cls
        
        # 儲存注入的 Enums
        self.AutoTimeStepping = auto_time_stepping_enum
        self.TimeStepDefineByType = time_step_define_by_type_enum
        
        if self.model.Analyses.Count > 0:
            self.analysis = self.model.Analyses[0]
            self.settings = self.analysis.AnalysisSettings
        else:
            raise Exception("錯誤：專案中沒有任何分析系統！")

    def configure_time_settings(self, num_steps=1, end_time_list=None, 
                                auto_time_stepping=True, 
                                initial_time_step=0.1, min_time_step=0.01, max_time_step=0.5,
                                large_deflection=True):
        
        print("-> 正在設定分析控制...")
        
        # 1. 設定大變形
        if large_deflection:
            self.settings.LargeDeflection = True
        else:
            self.settings.LargeDeflection = False

        self.settings.NumberOfSteps = num_steps
        
        if not self.Quantity:
            print("錯誤：未傳入 Quantity 類別！")
            return

        for i in range(num_steps):
            step_id = i + 1
            self.settings.CurrentStepNumber = step_id
            
            if end_time_list and len(end_time_list) >= step_id:
                val = end_time_list[i]
                self.settings.StepEndTime = self.Quantity(str(val) + " [s]")
            
            if auto_time_stepping:
                # 使用注入的 Enum
                if self.AutoTimeStepping:
                    self.settings.AutomaticTimeStepping = self.AutoTimeStepping.On
                
                # 使用注入的 Enum
                if self.TimeStepDefineByType:
                    self.settings.DefineBy = self.TimeStepDefineByType.Time
                
                self.settings.InitialTimeStep = self.Quantity(str(initial_time_step) + " [s]")
                self.settings.MinimumTimeStep = self.Quantity(str(min_time_step) + " [s]")
                self.settings.MaximumTimeStep = self.Quantity(str(max_time_step) + " [s]")
            else:
                if self.AutoTimeStepping:
                    self.settings.AutomaticTimeStepping = self.AutoTimeStepping.Off

    def solve_analysis(self):
        print("-> 開始求解...")
        self.analysis.Solution.Solve(True)
        print("   求解完成！")

# 更新函式介面
def runSolver(ext_api, num_steps=1, end_time_list=None,
              auto_time_stepping=True,
              initial_time_step=0.1, min_time_step=0.001, max_time_step=1.0,
              large_deflection=True,
              model=None, transaction_cls=None, quantity_cls=None,
              # 新增參數
              auto_time_stepping_enum=None,
              time_step_define_by_type_enum=None):
    
    if end_time_list is None: end_time_list = [1.0]

    tool = SolverTool(ext_api, model=model, transaction_cls=transaction_cls,
                      quantity_cls=quantity_cls,
                      # 傳遞參數
                      auto_time_stepping_enum=auto_time_stepping_enum,
                      time_step_define_by_type_enum=time_step_define_by_type_enum)

    if transaction_cls:
        with transaction_cls():
            tool.configure_time_settings(num_steps, end_time_list, 
                                         auto_time_stepping, 
                                         initial_time_step, min_time_step, max_time_step,
                                         large_deflection)
    else:
        tool.configure_time_settings(num_steps, end_time_list, 
                                     auto_time_stepping, 
                                     initial_time_step, min_time_step, max_time_step,
                                     large_deflection)

    #　預設先不要自動求解，有一個設計斷點讓USER確認
    # tool.solve_analysis()