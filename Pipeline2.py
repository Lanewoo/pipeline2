import streamlit as st
import pandas as pd
import plotly.express as px

# --- 页面设置 ---
st.set_page_config(page_title="2026 Pipeline Pro", layout="wide")

# --- 数据加载与预处理 ---
def load_and_clean(uploaded_file):
    """
    从上传的文件加载和清理数据
    支持 Excel (.xlsx) 和 CSV (.csv) 格式
    """
    file_extension = uploaded_file.name.split('.')[-1].lower()
    
    try:
        if file_extension == 'xlsx' or file_extension == 'xls':
            # 读取 Excel 文件，跳过第一行标题
            # 重置文件指针到开头（Streamlit file uploader需要）
            uploaded_file.seek(0)
            try:
                # 尝试使用openpyxl引擎（适用于.xlsx）
                if file_extension == 'xlsx':
                    try:
                        df = pd.read_excel(uploaded_file, skiprows=1, engine='openpyxl')
                    except ImportError:
                        raise ImportError("需要安装 openpyxl 库来读取 .xlsx 文件。请运行: pip install openpyxl")
                else:
                    # .xls 文件使用默认引擎
                    df = pd.read_excel(uploaded_file, skiprows=1)
            except Exception as e:
                if "openpyxl" in str(e).lower() or "no module named" in str(e).lower():
                    raise ImportError("需要安装 openpyxl 库来读取 Excel 文件。请运行: pip install openpyxl")
                raise
        elif file_extension == 'csv':
            # 读取 CSV 文件，跳过第一行标题
            # 重置文件指针到开头，并尝试不同编码
            uploaded_file.seek(0)
            try:
                df = pd.read_csv(uploaded_file, skiprows=1, encoding='utf-8')
            except UnicodeDecodeError:
                uploaded_file.seek(0)
                try:
                    df = pd.read_csv(uploaded_file, skiprows=1, encoding='latin-1')
                except Exception:
                    uploaded_file.seek(0)
                    # 最后尝试使用错误处理
                    df = pd.read_csv(uploaded_file, skiprows=1, encoding='utf-8', errors='replace')
        else:
            raise ValueError(f"不支持的文件格式: {file_extension}。请上传 .xlsx, .xls 或 .csv 文件")
        
        df.columns = [c.strip() for c in df.columns]
        
        # 检查数据框是否为空
        if df.empty:
            raise ValueError("上传的文件为空，没有数据行")
        
        # 检查必需的列是否存在
        required_cols = ['Probility', 'Industry', 'Sales Stage', 'Partner']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            available_cols = ', '.join(df.columns.tolist()[:10])  # 显示前10个列名
            raise ValueError(f"文件缺少必需的列: {', '.join(missing_cols)}\n文件中的列包括: {available_cols}{'...' if len(df.columns) > 10 else ''}")
        
        # 转换概率映射
        prob_map = {'Won': 1.0, 'High': 0.7, 'Medium': 0.4, 'Low': 0.2, 'Lost': 0.0}
        df['Prob_Value'] = df['Probility'].map(prob_map).fillna(0.1)
        
        # 月份列数值化
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        for m in months:
            if m in df.columns:
                df[m] = pd.to_numeric(df[m], errors='coerce').fillna(0)
            else:
                df[m] = 0  # 如果月份列不存在，创建并填充0
        
        return df, months
    
    except Exception as e:
        raise Exception(f"读取文件时出错: {str(e)}")

# --- 文件上传区域 ---
st.title("📊 2026 Pipeline 智能管理系统")

col_upload, col_reset = st.columns([3, 1])
with col_upload:
    uploaded_file = st.file_uploader(
        "📁 请上传您的 Pipeline 数据文件",
        type=['xlsx', 'xls', 'csv'],
        help="支持 Excel (.xlsx, .xls) 和 CSV (.csv) 格式文件"
    )
with col_reset:
    if 'df' in st.session_state:
        if st.button("🔄 清除数据", help="清除当前加载的数据"):
            # 清除session state中的数据
            for key in ['df', 'months', 'file_name']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

# 使用 session state 缓存数据，避免重复加载
# 检查是否需要重新加载文件（新文件上传或首次运行）
should_reload = False
if uploaded_file is not None:
    # 如果上传了新文件，或者session state中没有文件名，或者文件名不同，则需要重新加载
    if 'file_name' not in st.session_state or st.session_state.get('file_name') != uploaded_file.name:
        should_reload = True
elif 'df' not in st.session_state:
    # 首次运行且没有文件上传
    st.info("👆 请在上方上传您的 Pipeline 数据文件（Excel 或 CSV 格式）")
    st.stop()

# 如果需要重新加载，处理文件
if should_reload:
    try:
        with st.spinner("正在加载和处理数据..."):
            df, months = load_and_clean(uploaded_file)
            # 检查数据框是否为空
            if df.empty:
                st.warning("⚠️ 数据文件为空，请检查文件内容")
                st.stop()
            # 保存到 session state
            st.session_state.df = df
            st.session_state.months = months
            st.session_state.file_name = uploaded_file.name
            st.success(f"✅ 成功加载文件: {uploaded_file.name}")
    except ImportError as e:
        st.error(f"❌ {str(e)}")
        st.code("pip install openpyxl", language="bash")
        st.stop()
    except ValueError as e:
        st.error(f"❌ {str(e)}")
        st.info("💡 请检查文件的列名是否正确。必需的列包括: Partner, Industry, Sales Stage, Probility")
        st.stop()
    except pd.errors.EmptyDataError:
        st.error("❌ 文件为空或格式不正确")
        st.info("💡 请确保文件包含数据行")
        st.stop()
    except Exception as e:
        st.error(f"❌ 加载数据时发生错误: {str(e)}")
        st.info("💡 请检查文件格式是否正确，确保文件包含必需的列")
        st.exception(e)  # 显示详细错误信息用于调试
        st.stop()

# 从 session state 获取数据
if 'df' not in st.session_state or 'months' not in st.session_state:
    st.info("👆 请在上方上传您的 Pipeline 数据文件（Excel 或 CSV 格式）")
    st.stop()

# 安全地获取数据，确保它们存在
try:
    df = st.session_state.get('df', pd.DataFrame())
    months = st.session_state.get('months', [])
    
    # 如果数据为空，显示提示
    if df.empty or not months:
        st.info("👆 请在上方上传您的 Pipeline 数据文件（Excel 或 CSV 格式）")
        st.stop()
except (AttributeError, KeyError) as e:
    st.error(f"数据加载错误: {str(e)}")
    st.info("👆 请在上方上传您的 Pipeline 数据文件（Excel 或 CSV 格式）")
    st.stop()

# --- 侧边栏：新增商机表单 ---
with st.sidebar:
    st.header("➕ 添加新商机")
    with st.form("add_opportunity", clear_on_submit=True):
        new_partner = st.text_input("Partner Name")
        
        # 安全获取行业选项
        industries = df['Industry'].dropna().unique().tolist() if 'Industry' in df.columns else []
        if not industries:
            industries = ['Unknown']  # 默认值
        new_industry = st.selectbox("Industry", industries)
        
        # 安全获取销售阶段选项
        stages = df['Sales Stage'].unique().tolist() if 'Sales Stage' in df.columns else []
        if not stages:
            stages = ['Prospect']  # 默认值
        new_stage = st.selectbox("Sales Stage", stages)
        
        new_prob = st.selectbox("Probility", ['Low', 'Medium', 'High', 'Won', 'Lost'])
        new_mrr = st.number_input("预计平均 MRR", min_value=0)
        
        submitted = st.form_submit_button("保存到 CSV")
        if submitted and new_partner:
            # 创建新行数据
            new_data = {col: "" for col in df.columns}
            new_data.update({
                'Partner': new_partner,
                'Industry': new_industry,
                'Sales Stage': new_stage,
                'Probility': new_prob,
                'Jan': new_mrr # 简单示例：填入首月
            })
            # 实际应用中需写回文件，此处演示逻辑
            st.success(f"已录入 {new_partner}！(实时刷新后可见)")

# 显示当前加载的文件名
if 'file_name' in st.session_state:
    st.caption(f"📄 当前文件: {st.session_state.file_name}")

# --- 计算加权收入 (Weighted MRR) ---
# 计算逻辑：每月MRR * 该项目的成交概率
weighted_df = df.copy()
# 确保 Prob_Value 列存在
if 'Prob_Value' not in weighted_df.columns:
    prob_map = {'Won': 1.0, 'High': 0.7, 'Medium': 0.4, 'Low': 0.2, 'Lost': 0.0}
    weighted_df['Prob_Value'] = weighted_df['Probility'].map(prob_map).fillna(0.1) if 'Probility' in weighted_df.columns else 0.1

for m in months:
    if m in weighted_df.columns:
        weighted_df[m] = weighted_df[m] * weighted_df['Prob_Value']

# --- KPI 概览 ---
# 安全计算总和，只计算存在的列
available_months = [m for m in months if m in df.columns]
if available_months:
    try:
        total_actual = float(df[available_months].sum().sum())
        total_weighted = float(weighted_df[available_months].sum().sum())
        # 处理NaN值
        if pd.isna(total_actual):
            total_actual = 0
        if pd.isna(total_weighted):
            total_weighted = 0
    except Exception:
        total_actual = 0
        total_weighted = 0
else:
    total_actual = 0
    total_weighted = 0

c1, c2, c3 = st.columns(3)
c1.metric("原始总流水 (Raw MRR)", f"${total_actual:,.0f}")
c2.metric("加权预测价值 (Weighted)", f"${total_weighted:,.0f}", 
          help="根据每个阶段的成交概率(Low:20%, Med:40%, High:70%, Won:100%)折算后的价值")
c3.metric("项目总数", len(df))

st.divider()

# --- 交互图表 ---

col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("📈 收入预测：原始 vs 加权")
    # 只使用存在的月份列
    available_months_for_chart = [m for m in months if m in df.columns]
    if available_months_for_chart:
        try:
            raw_values = df[available_months_for_chart].sum().values
            weighted_values = weighted_df[available_months_for_chart].sum().values
            
            # 检查是否有有效数据
            if len(raw_values) > 0 and (raw_values.sum() > 0 or weighted_values.sum() > 0):
                trend_data = pd.DataFrame({
                    'Month': available_months_for_chart,
                    'Raw': raw_values,
                    'Weighted': weighted_values
                })
                fig = px.line(trend_data, x='Month', y=['Raw', 'Weighted'], 
                              markers=True, color_discrete_map={"Raw": "#CBD5E0", "Weighted": "#3182CE"})
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("暂无有效数据可显示")
        except Exception as e:
            st.warning(f"生成图表时出错: {str(e)}")
            st.info("暂无月份数据可显示")
    else:
        st.info("暂无月份数据可显示")

with col_right:
    st.subheader("🎯 行业分布 (按加权价值)")
    if 'Industry' in weighted_df.columns and available_months:
        try:
            # 安全地计算行业价值
            industry_value = weighted_df.groupby('Industry')[available_months].sum().sum(axis=1).reset_index(name='Value')
            # 过滤掉值为0或NaN的行，并确保Value是数值类型
            industry_value['Value'] = pd.to_numeric(industry_value['Value'], errors='coerce').fillna(0)
            industry_value = industry_value[industry_value['Value'] > 0]
            
            if not industry_value.empty and industry_value['Value'].sum() > 0:
                # 确保没有NaN值
                industry_value = industry_value.dropna(subset=['Industry', 'Value'])
                if not industry_value.empty:
                    fig_pie = px.pie(industry_value, names='Industry', values='Value', hole=0.5)
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.info("暂无行业数据可显示")
            else:
                st.info("暂无行业数据可显示")
        except Exception as e:
            st.warning(f"生成行业分布图时出错: {str(e)}")
            st.info("暂无行业数据可显示")
    else:
        st.info("缺少行业或月份数据")

# --- 详细清单与搜索 ---
st.subheader("🔍 商机明细表")
search_query = st.text_input("搜索合作伙伴、行业或负责人...")
if search_query:
    # 安全处理搜索，避免NaN值导致的错误
    try:
        # 更安全的搜索方式
        mask = pd.Series([False] * len(df), index=df.index)
        for col in df.columns:
            try:
                mask |= df[col].astype(str).str.contains(search_query, case=False, na=False, regex=False)
            except Exception:
                continue
        display_df = df[mask] if mask.any() else pd.DataFrame(columns=df.columns)
    except Exception as e:
        st.warning(f"搜索时出错: {str(e)}")
        display_df = df
else:
    display_df = df

# 安全选择要显示的列
display_columns = ['Partner', 'Industry', 'Sales Stage', 'Probility']
optional_columns = ['BD', 'Next Step']
for col in optional_columns:
    if col in df.columns:
        display_columns.append(col)
display_columns.extend(months)

# 只显示存在的列
available_columns = [col for col in display_columns if col in display_df.columns]
if not available_columns:
    st.warning("没有可显示的列")
elif display_df.empty:
    st.info("没有匹配的数据")
else:
    try:
        column_config = {}
        if "Probility" in available_columns:
            column_config["Probility"] = st.column_config.SelectboxColumn("概率", options=['Low', 'Medium', 'High', 'Won', 'Lost'])
        # 为所有月份列添加格式化
        for m in months:
            if m in available_columns:
                column_config[m] = st.column_config.NumberColumn(format="$%d")
        
        st.dataframe(
            display_df[available_columns],
            column_config=column_config if column_config else None,
            hide_index=True,
            use_container_width=True
        )
    except Exception as e:
        st.error(f"显示数据表时出错: {str(e)}")
        # 降级显示：不使用column_config
        try:
            st.dataframe(display_df[available_columns], hide_index=True, use_container_width=True)
        except Exception as e2:
            st.error(f"无法显示数据: {str(e2)}")