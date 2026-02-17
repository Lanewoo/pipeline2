import customtkinter as ctk
import sqlite3
from tkinter import messagebox

# 设置外观模式
ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue", "green", "dark-blue"

class SalesPipelineApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 窗口设置
        self.title("简易销售管道管理 (Sales Pipeline)")
        self.geometry("900x600")

        # 数据库初始化
        self.init_db()

        # 布局配置
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 左侧侧边栏
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="销售管家", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.add_btn = ctk.CTkButton(self.sidebar_frame, text="+ 新建交易", command=self.open_add_deal_window)
        self.add_btn.grid(row=1, column=0, padx=20, pady=10)

        self.refresh_btn = ctk.CTkButton(self.sidebar_frame, text="刷新数据", fg_color="transparent", border_width=2, text_color=("gray10", "#DCE4EE"), command=self.load_data)
        self.refresh_btn.grid(row=2, column=0, padx=20, pady=10)

        # 主区域 - 管道标签页
        self.tabview = ctk.CTkTabview(self, width=250)
        self.tabview.grid(row=0, column=1, padx=(20, 20), pady=(20, 20), sticky="nsew")
        
        # 定义销售阶段
        self.stages = ["潜在客户 (Prospect)", "提案阶段 (Proposal)", "谈判中 (Negotiation)", "已成交 (Won)", "丢失 (Lost)"]
        for stage in self.stages:
            self.tabview.add(stage)

        # 加载数据
        self.load_data()

    def init_db(self):
        """初始化SQLite数据库"""
        self.conn = sqlite3.connect('sales_data.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS deals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_name TEXT NOT NULL,
                value REAL,
                stage TEXT,
                notes TEXT
            )
        ''')
        self.conn.commit()

    def open_add_deal_window(self):
        """打开添加交易的弹窗"""
        window = ctk.CTkToplevel(self)
        window.title("添加新交易")
        window.geometry("400x400")
        window.attributes("-topmost", True)

        ctk.CTkLabel(window, text="客户名称:").pack(pady=5)
        name_entry = ctk.CTkEntry(window)
        name_entry.pack(pady=5)

        ctk.CTkLabel(window, text="预估金额 (￥):").pack(pady=5)
        value_entry = ctk.CTkEntry(window)
        value_entry.pack(pady=5)

        ctk.CTkLabel(window, text="备注:").pack(pady=5)
        notes_entry = ctk.CTkTextbox(window, height=100)
        notes_entry.pack(pady=5, padx=10)

        def save_deal():
            name = name_entry.get()
            val = value_entry.get()
            notes = notes_entry.get("0.0", "end")
            
            if not name:
                messagebox.showerror("错误", "客户名称不能为空")
                return

            try:
                self.cursor.execute("INSERT INTO deals (client_name, value, stage, notes) VALUES (?, ?, ?, ?)", 
                                    (name, val, self.stages[0], notes)) # 默认进入第一个阶段
                self.conn.commit()
                self.load_data()
                window.destroy()
            except Exception as e:
                messagebox.showerror("错误", str(e))

        ctk.CTkButton(window, text="保存", command=save_deal).pack(pady=20)

    def load_data(self):
        """从数据库读取并渲染界面"""
        # 清空当前显示的内容
        for stage in self.stages:
            for widget in self.tabview.tab(stage).winfo_children():
                widget.destroy()

        self.cursor.execute("SELECT * FROM deals")
        rows = self.cursor.fetchall()

        # 为每个交易创建卡片
        for row in rows:
            deal_id, name, value, stage, notes = row
            
            # 如果数据库里的stage不在我们定义的列表里（比如旧数据），默认放第一个
            if stage not in self.stages:
                stage = self.stages[0]

            parent = self.tabview.tab(stage)
            self.create_deal_card(parent, deal_id, name, value, stage, notes)

    def create_deal_card(self, parent, deal_id, name, value, stage, notes):
        """创建单个交易卡片"""
        card = ctk.CTkFrame(parent)
        card.pack(fill="x", pady=5, padx=5)

        # 信息部分
        info_text = f"客户: {name}\n金额: ￥{value}"
        label = ctk.CTkLabel(card, text=info_text, justify="left", font=ctk.CTkFont(size=14, weight="bold"))
        label.pack(side="left", padx=10, pady=10)

        # 操作按钮部分
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(side="right", padx=10)

        # 下一步按钮
        current_idx = self.stages.index(stage)
        if current_idx < len(self.stages) - 1:
            next_stage = self.stages[current_idx + 1]
            ctk.CTkButton(btn_frame, text="推进 ->", width=60, height=24, 
                          fg_color="#2CC985", hover_color="#229A65",
                          command=lambda: self.move_stage(deal_id, next_stage)).pack(pady=2)

        # 删除按钮
        ctk.CTkButton(btn_frame, text="删除", width=60, height=24, 
                      fg_color="#C92C33", hover_color="#9A2226",
                      command=lambda: self.delete_deal(deal_id)).pack(pady=2)

    def move_stage(self, deal_id, new_stage):
        self.cursor.execute("UPDATE deals SET stage = ? WHERE id = ?", (new_stage, deal_id))
        self.conn.commit()
        self.load_data()

    def delete_deal(self, deal_id):
        if messagebox.askyesno("确认", "确定要删除这条记录吗？"):
            self.cursor.execute("DELETE FROM deals WHERE id = ?", (deal_id,))
            self.conn.commit()
            self.load_data()

if __name__ == "__main__":
    app = SalesPipelineApp()
    app.mainloop()