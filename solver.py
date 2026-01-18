import pandas as pd
from ortools.sat.python import cp_model

class SchoolScheduler:
    def __init__(self, courses_data, days=5, periods=7):
        """
        初始化排課器
        :param courses_data: list of dict, 包含開課資訊 [{'class': '101', 'teacher': '王老師', 'subject': '國文', 'hours': 4}, ...]
        :param days: 每週天數 (預設5天)
        :param periods: 每天節數 (預設7節)
        """
        self.courses = courses_data
        self.days = days
        self.periods = periods
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        
        # 建立索引映射 (為了處理字串名稱)
        self.all_teachers = sorted(list(set(c['teacher'] for c in self.courses)))
        self.all_classes = sorted(list(set(c['class'] for c in self.courses)))
        
        # 決策變數儲存容器
        # 結構: self.vars[(course_index, day, period)] = BoolVar
        self.vars = {} 
        
        self._create_variables()
        self._add_hard_constraints()

    def _create_variables(self):
        """
        步驟 1: 建立決策變數
        我們為每一個 '課程' 在每一個 '時間格' 建立一個布林變數 (0 或 1)
        如果是 1，代表這門課排在這個時間。
        """
        print(f"正在建立變數... (課程數: {len(self.courses)}, 時間格: {self.days * self.periods})")
        
        for c_idx, course in enumerate(self.courses):
            for d in range(self.days):
                for p in range(self.periods):
                    # 變數名稱範例: c0_d1_p3 (第0號課程, 第1天, 第3節)
                    self.vars[(c_idx, d, p)] = self.model.NewBoolVar(f'c{c_idx}_d{d}_p{p}')

    def _add_hard_constraints(self):
        """
        步驟 2: 加入硬限制
        """
        print("正在加入限制條件...")

        # --- 限制 A: 課時滿足 ---
        # 每門課必須剛好排滿指定的節數 (hours)
        for c_idx, course in enumerate(self.courses):
            required_hours = course['hours']
            # 取出這門課在所有時間格的變數，加總必須等於 required_hours
            self.model.Add(
                sum(self.vars[(c_idx, d, p)] for d in range(self.days) for p in range(self.periods)) 
                == required_hours
            )

        # --- 限制 B: 班級不衝堂 ---
        # 同一個班級，在同一個時間 (d, p)，所有的課程變數加總 <= 1
        for cls in self.all_classes:
            # 找出屬於這個班級的所有課程 index
            class_course_indices = [i for i, c in enumerate(self.courses) if c['class'] == cls]
            
            for d in range(self.days):
                for p in range(self.periods):
                    self.model.Add(
                        sum(self.vars[(idx, d, p)] for idx in class_course_indices) <= 1
                    )

        # --- 限制 C: 老師不衝堂 ---
        # 同一位老師，在同一個時間 (d, p)，所有的課程變數加總 <= 1
        for teacher in self.all_teachers:
            # 找出這位老師教的所有課程 index
            teacher_course_indices = [i for i, c in enumerate(self.courses) if c['teacher'] == teacher]
            
            for d in range(self.days):
                for p in range(self.periods):
                    self.model.Add(
                        sum(self.vars[(idx, d, p)] for idx in teacher_course_indices) <= 1
                    )

    def solve(self):
        """
        步驟 3: 開始求解
        """
        print("開始運算最佳解 (Solver Running)...")
        status = self.solver.Solve(self.model)

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            print("找到可行解！")
            return self._format_solution()
        else:
            print("無解 (Infeasible)！可能是課程太多或限制太嚴格。")
            return None

    def _format_solution(self):
        """
        將結果轉換為 Pandas DataFrame 方便檢視
        """
        schedule_data = []
        days_map = {0: '週一', 1: '週二', 2: '週三', 3: '週四', 4: '週五'}
        
        for c_idx, course in enumerate(self.courses):
            for d in range(self.days):
                for p in range(self.periods):
                    if self.solver.Value(self.vars[(c_idx, d, p)]) == 1:
                        schedule_data.append({
                            '班級': course['class'],
                            '節次': f'第 {p+1} 節',
                            '星期': days_map[d],
                            '科目': course['subject'],
                            '老師': course['teacher'],
                            'Day_Index': d, # 為了排序用
                            'Period_Index': p
                        })
        
        df = pd.DataFrame(schedule_data)
        # 排序讓表格好看一點
        df = df.sort_values(by=['班級', 'Day_Index', 'Period_Index'])
        return df[['班級', '星期', '節次', '科目', '老師']]

# --- 測試區 (Main Block) ---
if __name__ == "__main__":
    # 模擬資料：兩個班級，幾位老師
    mock_data = [
        # 101班的課表
        {'class': '101', 'teacher': '王大明', 'subject': '國文', 'hours': 4},
        {'class': '101', 'teacher': '李英文', 'subject': '英文', 'hours': 4},
        {'class': '101', 'teacher': '陳數學', 'subject': '數學', 'hours': 4},
        
        # 102班的課表 (注意：王大明老師也有教 102，這是衝突測試點)
        {'class': '102', 'teacher': '王大明', 'subject': '國文', 'hours': 4},
        {'class': '102', 'teacher': '李英文', 'subject': '英文', 'hours': 4},
        {'class': '102', 'teacher': '林物理', 'subject': '物理', 'hours': 3},
    ]

    # 設定每週 5 天，每天 4 節課 (為了測試方便縮小範圍)
    scheduler = SchoolScheduler(mock_data, days=5, periods=4)
    result_df = scheduler.solve()

    if result_df is not None:
        print("\n=== 排課結果 ===")
        print(result_df.to_string(index=False))
        
        # 如果您想測試存成 CSV
        # result_df.to_csv("schedule_result.csv", index=False, encoding='utf-8-sig')