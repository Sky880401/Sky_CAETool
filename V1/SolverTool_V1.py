# -*- coding: utf-8 -*-

class SolverTool(object):
    """
    求解器自動化工具 (Time-Based + Large Deflection + Cores)
    負責：設定分析步數、幾何非線性、核心數、觸發求解
    """
    def __init__(self, ext_api, model=None, transaction_cls=None, quantity_cls=None,
                 auto_time_stepping_enum=None, time_step_define_by_type_enum=None):
        
        self.api = ext_api
        self.model = model if model is not None else ext_api.DataModel.Project.Model
        self.transaction_cls = transaction_cls
        self.Quantity = quantity_cls
        self.AutoTimeStepping = auto_time_stepping_enum
        self.TimeStepDefineByType = time_step_define_by_type_enum
        
        if self.model.Analyses.Count > 0:
            self.analysis = self.model.Analyses[0]
            self.settings = self.analysis.AnalysisSettings
        else:
            raise Exception("錯誤：專案中沒有任何分析系統！")

    # ==========================================================
    # [新增] 設定核心數的方法 (移植自 Solver.py)
    # ==========================================================
    def set_solver_cores(self, num_cores):
        """設定求解使用的 CPU 核心數"""
        print("-> 設定求解核心數 (Cores): {}".format(num_cores))
        try:
            # 存取 Application 層級的求解設定
            solve_settings = self.api.Application.SolveConfigurations["My Computer"]
            solve_settings.SolveProcessSettings.MaxNumberOfCores = int(num_cores)
            
            # 若您原本的腳本有開啟 Distributed Parallel，可在此加入：
            # solve_settings.DistributeSolution = True
            
        except Exception as e:
            print("   警告：無法設定核心數 (可能是版本差異或權限不足): " + str(e))

    def configure_time_settings(self, num_steps=1, end_time_list=None, 
                                auto_time_stepping=True, 
                                initial_time_step=0.1, min_time_step=0.01, max_time_step=0.5,
                                large_deflection=True):
        
        print("-> 正在設定分析控制...")
        
        # 1. 設定大變形
        self.settings.LargeDeflection = large_deflection

        # 2. 設定總步數
        self.settings.NumberOfSteps = num_steps
        
        if not self.Quantity:
            print("錯誤：未傳入 Quantity 類別！")
            return

        # 3. 逐一設定每一步
        for i in range(num_steps):
            step_id = i + 1
            self.settings.CurrentStepNumber = step_id
            
            if end_time_list and len(end_time_list) >= step_id:
                val = end_time_list[i]
                self.settings.StepEndTime = self.Quantity(str(val) + " [s]")
            
            if auto_time_stepping:
                if self.AutoTimeStepping:
                    self.settings.AutomaticTimeStepping = self.AutoTimeStepping.On
                
                if self.TimeStepDefineByType:
                    self.settings.DefineBy = self.TimeStepDefineByType.Time
                
                self.settings.InitialTimeStep = self.Quantity(str(initial_time_step) + " [s]")
                self.settings.MinimumTimeStep = self.Quantity(str(min_time_step) + " [s]")
                self.settings.MaximumTimeStep = self.Quantity(str(max_time_step) + " [s]")
            else:
                if self.AutoTimeStepping:
                    self.settings.AutomaticTimeStepping = self.AutoTimeStepping.Off

    def solve_analysis(self):
        print("-> 開始求解 (Solving)...")
        self.analysis.Solution.Solve(True)
        print("   求解完成！")


# ==========================================================
# 更新 runSolver 介面，加入 cores 參數
# ==========================================================
def runSolver(ext_api, num_steps=1, end_time_list=None,
              auto_time_stepping=True,
              initial_time_step=0.1, min_time_step=0.001, max_time_step=1.0,
              large_deflection=True,
              cores=4,  # [新增] 預設 4 核心
              model=None, transaction_cls=None, quantity_cls=None,
              auto_time_stepping_enum=None,
              time_step_define_by_type_enum=None):
    
    if end_time_list is None: end_time_list = [1.0]

    tool = SolverTool(ext_api, model=model, transaction_cls=transaction_cls,
                      quantity_cls=quantity_cls,
                      auto_time_stepping_enum=auto_time_stepping_enum,
                      time_step_define_by_type_enum=time_step_define_by_type_enum)

    # 1. 設定核心數 (不需要 Transaction，這是 Application 層級設定)
    tool.set_solver_cores(cores)

    # 2. 設定分析參數 (使用 Transaction 加速)
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

    # 3. 執行求解
    # tool.solve_analysis()