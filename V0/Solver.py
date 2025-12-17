# -*- coding: utf-8 -*-
# ==========================================
# Jetsoft 自動求解設定工具 (Solver Controls)
# ==========================================
import clr

# 引入 Ansys Mechanical 相關 Enum (確保 API 辨識設定值)
# 若是較舊版本，可能需要 import Ansys.ACT.Interfaces 等
# 但通常在 Scripting 環境中這些是預載的

class SolverSetup:
    def __init__(self, api):
        self.api = api
        self.model = api.DataModel.Project.Model
        self.config = api.Application
        
        # 取得當前分析系統 (預設抓第一個)
        if self.model.Analyses.Count > 0:
            self.analysis = self.model.Analyses[0]
            self.settings = self.analysis.AnalysisSettings
        else:
            raise Exception("錯誤：專案中沒有任何分析系統！")

    def configure_step_controls(self, init_time, min_time, max_time):
        """
        設定時間步長與非線性選項
        """
        print("-> 正在設定分析步長控制 (Analysis Settings)...")
        
        # 1. 開啟大變形 (Large Deflection)
        # 插拔分析必開，否則接觸滑移量大時會失真或不收斂
        self.settings.LargeDeflection = True
        print("   大變形 (Large Deflection): On")

        # 2. 開啟自動時間步長 (Auto Time Stepping)
        # 使用 Enum: AutomaticTimeStepping.On
        self.settings.SetAutomaticTimeStepping(1, AutomaticTimeStepping.On)
        print("   自動時間步長 (Auto Time Stepping): On")

        # 3. 定義方式改為 Time (預設可能是 Substeps)
        # 使用 Enum: TimeStepDefineBy.Time
        self.settings.DefineBy = TimeStepDefineByType.Time
        print("   定義方式 (Define By): Time")

        # 4. 設定具體時間數值
        # 注意：必須使用 Quantity 物件，並帶上單位 (預設秒 [s])
        self.settings.InitialTimeStep = Quantity(str(init_time) + " [s]")
        self.settings.MinimumTimeStep = Quantity(str(min_time) + " [s]")
        self.settings.MaximumTimeStep = Quantity(str(max_time) + " [s]")
        
        print("   時間設定: Init={}, Min={}, Max={}".format(init_time, min_time, max_time))

    def set_solver_cores(self, core_count):
        """
        設定求解核心數量 (Solve Process Settings)
        """
        print("-> 正在設定求解核心數量...")
        
        # 核心數量的設定位於 Model 層級的 SolveProcessSettings
        # 這對應於介面上的 "Tools > Solve Process Settings"
        solve_config = self.config.SolveConfigurations["My Computer"]
        
        # 設定核心數
        solve_config.SolveProcessSettings.MaxNumberOfCores = int(core_count)
        
        # 建議同時開啟 "Distributed" (分散式平行運算)，效能較好
        # 如果是 4 核心，通常建議開啟 DMP
        #solve_config.DistributeSolution = True
        
        print("   核心數 (Cores): {}".format(core_count))
        #print("   分散式運算 (Distributed): On")

# ==========================================
# 主執行區 (Main Execution)
# ==========================================
def main():
    print("--- 開始執行求解設定 ---")
    
    try:
        # 1. 初始化工具
        setup_tool = SolverSetup(ExtAPI)
        
        # 2. 執行分析設定 (Analysis Settings)
        # 參數: Initial, Min, Max
        setup_tool.configure_step_controls(
            init_time=0.01, 
            min_time=0.0001, 
            max_time=0.1
        )
        
        # 3. 執行核心設定 (Solve Process Settings)
        # 參數: 核心數量
        setup_tool.set_solver_cores(16)
        
        print("--- 設定完成 ---")
        
    except Exception as e:
        print("發生錯誤: " + str(e))

# 執行
main()
