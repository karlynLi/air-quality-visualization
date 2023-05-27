# reference : https://docs.streamlit.io/library/api-reference/charts/st.plotly_chart

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# -------------------------------------------------------- Load Data ------------------------------------------------------#

air_data = pd.read_csv('./rawData/空氣品質監測月值.csv')
site_data = pd.read_csv('./rawData/監測站基本資料.csv')

# ----------------------------------------------------- Data Processing ---------------------------------------------------#

def tidydata(air_df, site_df):

    new_col_names = {'"siteid"':'siteid', '"sitename"':'sitename', '"itemid"':'itemid', '"itemname"':'itemname', 
                    '"itemengname"':'itemengname', '"itemunit"':'itemunit', '"monitormonth"':'monitormonth', '"concentration"':'concentration'}
    air_df = air_df.rename(columns=new_col_names)

    # 只保留需要的測量指標
    air_df = air_df[air_df['itemengname'].isin(['NOx', 'SO2', 'AMB_TEMP'])]
    df = air_df.merge(site_df[['sitename', 'areaname', 'county']], on='sitename')

    # concentration 型態設定，以利後續視覺化呈現
    df['concentration'] = pd.to_numeric(df['concentration'], errors='coerce')
    print(df.dtypes['concentration'])

    # 日期格式設定
    df['monitormonth'] = df['monitormonth'].astype(str)
    df[['year', 'month']] = df['monitormonth'].str.extract(r'(.{4})(.*)')
    df['monitormonth'] = pd.to_datetime(df['year'].astype(str) + '-' + df['month'].astype(str), format='%Y-%m')
    df['monitormonth'] = df['monitormonth'].dt.strftime('%Y/%m')

    return df


def transform(df) :

    temp = df[df['itemengname'] == 'AMB_TEMP']
    temp['temperature'] = temp['concentration']
    temp = temp[['monitormonth', 'sitename', 'county', 'areaname', 'temperature']]

    df = df[df['itemengname'].isin(['NOx', 'SO2'])]
    mergeKey = ['monitormonth', 'sitename', 'county', 'areaname']
    merge = pd.merge(df, temp, on=mergeKey)

    # 空值處理
    merge.dropna(subset=['temperature', 'concentration'], inplace=True) 
    merge['temperature'].fillna(0, inplace=True) 
    merge['concentration'].fillna(0, inplace=True)

    return merge

tidyData = transform(tidydata(air_data, site_data))
columns_to_keep = ['monitormonth', 'sitename', 'county', 'areaname', 'temperature', 'itemengname', 'concentration']
tidyData = tidyData.reindex(columns=columns_to_keep)

# print('\nTidy Data :\n', tidyData)

# ---------------------------------------------------------- Plotly ----------------------------------------------------------#

def plot(df, area) :
    df = df[df['areaname'].isin([area])]

    _min = df['concentration'].min()
    _max = df['concentration'].max()

    fig = px.scatter(df, x='concentration', y="temperature", size='concentration',
                color="itemengname", hover_name="sitename", log_x=True, size_max=60, 
                animation_frame='monitormonth', animation_group='sitename', range_x=[_min, _max], range_y=[0, 40],
                labels=dict(itemengname='Measurement Item', concentration='Concentration (ppb)', temperature='Temperature (℃)'))
    
    fig.update_layout(
        # width = 800,
        sliders=[
            dict(
                active=0,
                currentvalue={"prefix": "MonitorTime: "},
            )
        ]
    )
    
    for trace in fig.data:
        trace.marker.line.width = 1
        trace.marker.line.color = 'white'
    
    return fig

# --------------------------------------------------------- Streamlit -----------------------------------------------------------#
st.set_page_config(layout='wide')

st.header('Do different regions and temperature conditions contribute to an increase in the concentrations of acid rain precursors (NOx, SO2)?')

list_area = ['北部空品區', '竹苗空品區', '中部空品區', '雲嘉南空品區', '高屏空品區', '宜蘭空品區', '花東空品區', '其他']
option = st.sidebar.selectbox(
    'Please Select an Air Quality Area',
    list_area)

st.markdown("""
<style>
    .plot-container {
        width: 800px;
    }
</style>
""", unsafe_allow_html=True)

st.plotly_chart(plot(tidyData, option), theme=None, use_container_width=True)

