import Pull_data3

import pandas as pd  # pip install pandas openpyxl
import plotly.express as px
from pyparsing import Regex  # pip install plotly-express
import streamlit as st  # pip install streamlit

# emojis: https://www.webfx.com/tools/emoji-cheat-sheet/
st.set_page_config(page_title="NT Dashboard 4 Kim :-)", page_icon=":bar_chart:", layout="wide")

# ---- READ EXCEL ----
@st.cache
def get_data():
    #df = [None]*3
    # df[0] = pd.read_csv("NTD_1.csv")
    # df[1] = pd.read_csv("NTD_2.csv")
    # df[2] = pd.read_csv("NTD_3.csv")
    df = Pull_data3.GetKimData()
    for x in range(3):
        df[x].reset_index(inplace=True)
    return df
placeholder = st.empty()
placeholder.title("Loading data directly from NT database. Please be patient.")
df = get_data()
placeholder.empty()
# ---- SIDEBAR ----
st.sidebar.header("Please Select:")
dataset = st.sidebar.radio(
     "Database:",
     ("Financial performance","Cash flow","Financial position"))
if dataset == "Financial performance":
    this_df = df[0].copy()
elif dataset == "Cash flow":
    this_df = df[1].copy()
else:
    this_df = df[2].copy() 

st.title(":bar_chart: Municipal Total for 2020")
st.markdown("###")

chosen_vars = st.multiselect(
    "Select Variables:",
    options=this_df["item.label.Cap.new"].unique()[::-1],
    default=this_df["item.label.Cap.new"].unique()[::-1]
)
this_df['Variables'] = this_df['item.label.Cap.new']
this_df['Rands(M)'] = this_df[2020]/1e6
df_to_plot = this_df.query(
    "Variables == @chosen_vars"
)
# ---- MAINPAGE ----

fig_projections = px.bar(
    df_to_plot,
    x='Rands(M)',
    y = 'Variables',
    orientation='h',
    text_auto='.2s'
)
fig_projections.update_yaxes(dtick=1,type='category')
fig_projections.update_traces(textposition="outside")
#fig_projections.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightPink')
st.plotly_chart(fig_projections, use_container_width=True)

# ---- HIDE STREAMLIT STYLE ----
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)
