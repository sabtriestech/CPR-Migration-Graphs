import pandas as pd
import altair as alt
import geopandas as gpd
import os
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import numpy as np
import plotly.express as px
import matplotlib.colors as mcolors
from matplotlib import font_manager


shape = gpd.read_file("C:/Users/s_bea/Downloads/cb_2018_us_state_500k/cb_2018_us_state_500k.shp", encoding='latin-1') 
state_inflows = pd.read_excel("C:/Users/s_bea/Downloads/State_to_State_Migration_Table_2024_T13.xlsx", 
                             sheet_name="Supplemental - Current Res",
                             skiprows=7,
                             skipfooter=7)
state_outflows = pd.read_excel("C:/Users/s_bea/Downloads/State_to_State_Migration_Table_2024_T13.xlsx", 
                             sheet_name="Supplemental - Res 1 Year Ago",
                             skiprows=7,
                             skipfooter=5)
state_flows = pd.read_excel("C:/Users/s_bea/Downloads/State_to_State_Migration_Table_2024_T13.xlsx", 
                             sheet_name="Table",
                             skiprows=7,
                             skipfooter=7)
state_flows = state_flows.rename(columns={'Unnamed: 0': 'Arrival', 'Unnamed: 1': 'Departure'})
state_flows_new = state_flows[
    ~state_flows['Estimate'].isin(["X", "N"])]
state_flows_new['Estimate'] = pd.to_numeric(state_flows_new['Estimate'])

state_inflows['percent inflow'] = (state_inflows['Estimate.3'] / state_inflows['Estimate']) * 100
state_inperc = state_inflows[['Unnamed: 0', 'percent inflow']]
state_outflows['percent outflow'] = (state_outflows['Estimate.3'] / state_outflows['Estimate']) * 100
state_outperc = state_outflows[['Unnamed: 0', 'percent outflow']]
state_net = state_inperc.merge(state_outperc, how='inner', on='Unnamed: 0')
state_net['net'] = state_net['percent inflow'] - state_net['percent outflow']

net_w_shape = shape.merge(state_net, how='left', left_on='NAME', right_on='Unnamed: 0')

to_drop = ['Commonwealth of the Northern Mariana Islands', 
           'American Samoa', 'Alaska', 'Hawaii', 'Guam',
           'Puerto Rico']

net_w_shape = net_w_shape[
    ~net_w_shape['NAME'].isin(to_drop)]

net_w_shape.to_csv('net_w_shape.csv', index=False)

# will need to download font from google: https://fonts.google.com/selection?preview.script=Latn
font_path = "C:/Users/s_bea/Downloads/Slabo_13px,Slabo_27px/Slabo_27px/Slabo27px-Regular.ttf"
custom_font = font_manager.FontProperties(fname=font_path, size=24)

colors = ["#092F33", "#84c2d1", "#E4CBA9", "#AF5031"] 
my_cmap = mcolors.LinearSegmentedColormap.from_list("my_theme", colors)

fig, ax = plt.subplots(1, 1, figsize=(12, 8))

net_w_shape.plot(
    column='net',              
    linewidth=0.2,           
    edgecolor='0.5',          
    legend=True,              
    ax=ax,
    cmap=my_cmap
    )

cbar_ax = fig.axes[-1]

for label in cbar_ax.get_yticklabels():
    label.set_fontproperties(custom_font)

cbar_ax.tick_params(labelsize=12)

ax.set_title('Domestic Migration Flows 2024-2025 \n(% population)', 
             fontproperties=custom_font, y=1.12)
ax.axis('off')  

ax.set_axis_off()
#save_path = os.path.join(SAVE_DIR, 'net_migration.png')
#plt.savefig(save_path, dpi=300, bbox_inches='tight')
plt.show()

net_sorted = net_w_shape.sort_values(by='net')
# The 5 states with the biggest net losses are South Dakota, New Jersey, New York, Illinois, and California

outflow_states = ['New Jersey', "New York", 'Illinois', 'California']
sample_states = state_flows_new[state_flows_new['Departure'].isin(outflow_states)]
states_top5 = sample_states.loc[
    sample_states.groupby("Departure")["Estimate"]
      .rank(method="first", ascending=False) <= 5
]

dep_nodes = (
    states_top5.groupby("Departure")["Estimate"]
    .sum()
    .sort_values(ascending=False)
    .index
)

arr_nodes = (
    states_top5.groupby("Arrival")["Estimate"]
    .sum()
    .sort_values(ascending=False)
    .index
)

dep_labels = [f"{s} (out)" for s in dep_nodes]
arr_labels = [f"{s} (in)" for s in arr_nodes]
all_nodes = dep_labels + arr_labels

node_dict = {name: i for i, name in enumerate(all_nodes)}

states_top5["source"] = states_top5["Departure"].map(
    lambda x: node_dict[f"{x} (out)"]
)
states_top5["target"] = states_top5["Arrival"].map(
    lambda x: node_dict[f"{x} (in)"]
)

def spaced_positions(n, pad=0.06):
    return np.linspace(pad, 1 - pad, n)

node_x = [0]*len(dep_nodes) + [1]*len(arr_nodes)
node_y = list(spaced_positions(len(dep_nodes))) + list(spaced_positions(len(arr_nodes)))

display_labels = list(dep_nodes) + list(arr_nodes)

brand_colors = ["#FDABA5", "#AF5031", "#4B5B34", "#84C2D1"]
color_map = {
    dep: brand_colors[i % len(brand_colors)]
    for i, dep in enumerate(dep_nodes)
}

link_colors = states_top5["Departure"].map(
    lambda d: color_map[d].replace("rgb", "rgba").replace(")", ",0.45)")
)

fig = go.Figure(go.Sankey(
    arrangement="fixed",
    node=dict(
        label=display_labels,
        x=node_x,
        y=node_y,
        pad=18,
        thickness=18,
        color=["#092F33"]*len(dep_nodes) + ["#E4CBA9"]*len(arr_nodes),
        line=dict(color="rgba(0,0,0,0.2)", width=0.5),
    ),
    link=dict(
        source=states_top5["source"],
        target=states_top5["target"],
        value=states_top5["Estimate"],
        color=link_colors
    )
))

fig.update_layout(
    title="State-to-State Migration 2024-2025",
    font=dict(
        family="Slabo 27px",
        size=14,
        color="#092F33"
    ),
    width=900,
    height=600,
    margin=dict(l=40, r=40, t=60, b=40)
)

fig.update_traces(
    textfont=dict(
        family="Slabo 27px",
        size=9,
        color="#092F33"
    )
)

fig.show()
fig.write_image("migration_sankey.png", scale=2)