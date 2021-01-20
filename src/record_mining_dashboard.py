import numpy as np
import pandas as pd
import argparse
import base64
from collections import OrderedDict
import time, os, fnmatch, shutil, glob

import plotly.graph_objects as go
import plotly.offline as pyo

import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_table as dt
from dash_table.Format import Format, Scheme, Sign, Symbol
from dash.dependencies import State, Input, Output
from dash.exceptions import PreventUpdate
from dash_extensions import Download
from dash_extensions.snippets import send_bytes

## USAGE
'''
python3 src/modules/dashboard/record_mining_dashboard.py
--input_file='input/predictions_train.tsv'
--output_file='output/Output_Aug_20_2020_174852.tsv'
'''

in_file_name = r'input/predictions_train.tsv'

t = time.localtime()
timestamp = time.strftime('%b_%d_%Y_%H%M%S', t)
output_path = r'output/'


parser = argparse.ArgumentParser()

parser.add_argument('--input_file', type=str, default=in_file_name,
                    help='Directory where your validated file is.')

parser.add_argument('--output_file', type=str, default=output_path,
                    help='Directory where your validated file is.')

args = parser.parse_args()


input_dash_file=os.path.join(args.input_file)
data = pd.read_csv(input_dash_file, sep='\t')
data['validated_coordinates']='revise'
data['found_coordinates']='write_the_coordinates'

# GDDID dropdown
gddid_list = list(data['title'].unique())
options_list = []
for i in gddid_list:
    options_list.append({'label':i, 'value':i})

# Sentence ID dropdown
sentid_list = list(data['sentid'].unique())
list.sort(sentid_list)
sent_opt_list = []
for i in sentid_list:
    sent_opt_list.append({'label':i, 'value':i})


# Dataframe 0 or 1

marking_df = pd.DataFrame(OrderedDict([('coords_or_not', ['0', '1', 'revise'])]))
validated_opt_list = [{'label': i, 'value': i} for i in marking_df['coords_or_not'].unique()]

# Validated coords
'''
validated_list = list(data['validated_coordinates'].unique())
validated_opt_list = []
for i in validated_list:
    validated_opt_list.append({'label':i, 'value':i})
'''

# Data Generator
def datagen(data = data):
    data=data[['gddid', 'title', 'sentid', 'sentence', 'prediction_proba', 'true_label', 'predicted_label', 'found_lat', 'found_long', 'Train/Pred', 'validated_coordinates', 'found_coordinates']]
    return(data)

# Figure generator for first graph
def fig_generator(sample_data):
    sample_data.reset_index(drop=True)
    sample_data=sample_data.loc[(sample_data['prediction_proba']>0.15) | (sample_data['true_label']>0.15)]
    sample_data=sample_data.sort_values(by='sentid')
    plot_data=[]

    plot_layout=go.Layout(title="Probability that a sentence has coordinates")
    fig = go.Figure(layout=plot_layout)
    fig.add_trace(go.Scatter(x=sample_data['sentid'], y=sample_data['prediction_proba'], mode='markers', name='proba'))
    fig.add_trace(go.Scatter(x=sample_data['sentid'], y=sample_data['true_label'], mode='markers', name='original label'))
    fig.add_trace(go.Scatter(x=sample_data['sentid'], y=sample_data['validated_coordinates'], mode='markers', name='validated label'))
    fig.update_layout(xaxis=dict(range=[0,1000]))
    fig.update_layout(yaxis=dict(range=[0,1.02]))
    return(fig.data, fig.layout)


def table_generator(data):
    data.reset_index(drop=True)
    data=sample_data.sort_values(by='sentid')
    data=data[['sentence', 'sentid', 'prediction_proba', 'true_label', 'predicted_label', 'found_lat', 'found_long', 'validated_coordinates', 'found_coordinates']]
    return data.to_json()

# Dash application
app = dash.Dash()

app.config['suppress_callback_exceptions'] = True

app.layout = html.Div(children=[html.H1('Record Mining Dashboard'),
                                html.Div(children=[html.P('Choose a paper:'),
                                                   dcc.Dropdown(id="title_dropdown",
                                                                options=options_list)#,
                                                                #value='Paradigms and proboscideans in the southern Great Lakes region, USA'),
                                                    ]),
                                html.Div(id='gddid_output', style={'whiteSpace': 'pre-line'}),

                                dcc.Tabs(id='tabs-example', value='tab-1', children=[
                                                                                     dcc.Tab(label='Data Exploration', value='tab-1'),
                                                                                     dcc.Tab(label='Article', value='tab-2'),
                                                                                     ]),
                                html.Div(id='tabs-example-content')
                                ])


# Graph
@app.callback(Output('proba_graph', 'figure'),
              [Input('title_dropdown', 'value')])

def update_plot(input_title):
    df= datagen()
    sample_data = df[df["title"] == input_title]
    trace,layout = fig_generator(sample_data)
    return {
           'data': trace,
           'layout':layout
           }

# GDD output
@app.callback(Output('gddid_output', 'children'),
              [Input('title_dropdown', 'value')])

def update_output(input_title):
    df= datagen()
    sample_data = df[df["title"] == input_title]
    gdd = sample_data['gddid'].unique()
    return 'The GDDID for that title is: \n{}'.format(gdd)

# Table
@app.callback(Output('json_df_store', 'children'),
              [Input('title_dropdown', 'value'),
               Input('sentid_dropdown', 'value')])

def load_table(input_title, input_sentid):
    try:
        data=''
        data= datagen()
        data.reset_index(inplace=True)
        data=data[data['title'] == input_title]
        data=data[['sentence', 'sentid', 'prediction_proba', 'true_label', 'predicted_label', 'found_lat', 'found_long', 'Train/Pred']]
        a=data[data['sentid'] == int(input_sentid)-1]
        b=data[data['sentid'] == int(input_sentid)]
        c=data[data['sentid'] == int(input_sentid)+1]
        data = pd.concat([a,b,c])
        data=data.to_json()
        return data

    except:
        print('Can\'t find that index')



@app.callback(Output('table_output', 'children'),
              [Input('json_df_store', 'children')])

def update_output(json_df):
    info_dataframe = pd.read_json(json_df)
    data = info_dataframe.to_dict("rows")
    cols = [{"name": i, "id": i} for i in info_dataframe.columns]

    child = html.Div([
            dt.DataTable(style_data={
                                     'whiteSpace': 'normal',
                                     'height': 'auto',
                                     'lineHeight': '15px'
                                     },
                          id='table',
                          data=data,
                          columns=cols,
                          style_cell={'width': '50px',
                                      'height': '30px',
                                      'textAlign': 'left'}
                          )])
    return child

# Table2
@app.callback(Output('json_df_store_t2', 'children'),
              [Input('title_dropdown', 'value')])
def load_table_t2(input_title):
    pd.options.display.float_format = '${:.6f}'.format
    data =''
    data= datagen()
    data.reset_index(inplace=True)
    pd.set_option("display.precision", 8)
    data=data[data['title'] == input_title]
    data=data[['gddid','sentid','sentence', 'prediction_proba', 'predicted_label', 'validated_coordinates', 'found_coordinates']]

    data1 = data[(data['prediction_proba'] > 0.000) & (data['prediction_proba'] < 0.05)]
    data1 = data.sample(frac = 0.15)
    data2 = data[data['prediction_proba'] > 0.05]
    data = pd.concat([data1, data2])
    data=data.sort_values(by='sentid')
    data.reset_index(inplace=True)

    data=data.to_json()
    return data

@app.callback(Output('table_output_t2', 'children'),
              [Input('json_df_store_t2', 'children')])

def update_output_t2(json_df_t2):
    pd.options.display.float_format = '${:.6f}'.format
    info_dataframe_t2 = pd.read_json(json_df_t2)
    info_dataframe_t2.reset_index(drop=True, inplace=True)
    data = info_dataframe_t2.to_dict("rows")
    cols = [{"name": i, "id": i} for i in info_dataframe_t2.columns]

    child2 = html.Div([
            html.Button(id="save-button",n_clicks=0,children="Save"),
            html.Div(id="output-1",children="Mark the last column if the sentence has a coordinate. Press button to save changes"),
            dt.DataTable(style_data={
                                     'whiteSpace': 'normal',
                                     'height': 'auto',
                                     'lineHeight': '15px'
                                     },
                          id='table',
                          data=data,
                          columns=[{'name': 'sentid', 'id': 'sentid', 'editable':False},
                                   {'name': 'sentence', 'id': 'sentence', 'editable':False},
                                   {'name': 'prediction_proba', 'id': 'prediction_proba',
                                                    'editable':False, 'type': 'numeric',
                                                    'format': Format(precision=7, scheme=Scheme.fixed)},
                                   {'name': 'predicted_label', 'id': 'predicted_label','type': 'numeric', 'editable':False},
                                   {'name': 'validated_coordinates','id': 'validated_coordinates',
                                                    'presentation':'dropdown', 'editable':True},
                                   {'name': 'found_coordinates', 'id': 'found_coordinates', 'editable':True}],

                          dropdown={'validated_coordinates':{
                                                   'options': validated_opt_list
                                                   }},
                          sort_action='native',
                          filter_action='native',
                          style_cell={'width': '50px',
                                      'height': '30px',
                                      'textAlign': 'left'},


                          merge_duplicate_headers=True
                          )
            ])
    return child2

# Save Button
@app.callback(
        Output("output-1","children"),
        [Input("save-button","n_clicks")],
        [State("table","data")]
        )


def selected_data_to_csv(nclicks,table1, path = args.output_file):
    t = time.localtime()
    timestamp = time.strftime('%b_%d_%Y_%H%M%S', t)
    file_name = ('db_val_'+timestamp+'.tsv')
    path = path

    output_file = os.path.join(path,file_name)

    if nclicks == 0:
        raise PreventUpdate
    else:
        table1=pd.DataFrame(table1)
        table1['timestamp']=timestamp
        table1=table1[['gddid','sentid', 'prediction_proba', 'predicted_label', 'validated_coordinates', 'found_coordinates', 'timestamp']]
        table1['timestamp']=timestamp

        table2=table1.loc[table1['validated_coordinates'] != 'revise']

        table2.to_csv(output_file, sep='\t', mode='a+',header=True, index=False)

        return "Data Submitted"


# Tabs
@app.callback(Output('tabs-example-content', 'children'),
              [Input('tabs-example', 'value')])

def render_content(tab):
    if tab == 'tab-1':
        return html.Div(children=[dcc.Graph(id='proba_graph'),

                                  #Table
                                  html.Div(children=[html.P('Choose a sentence number:'),
                                                     dcc.Dropdown(id="sentid_dropdown",
                                                                  options=sent_opt_list,
                                                                  value='5')]),

                                  #Div to store json serialized dataframe
                                  html.Div(id='json_df_store', style={'display':'none'}),
                                  html.Div(id='table_output')

                                  ])

    elif tab == 'tab-2':
        return html.Div(children=[html.Div(id='json_df_store_t2', style={'display':'none'}),
                                  html.Div(id='table_output_t2')
                                  ])


if __name__ == '__main__':
    app.run_server(
        port=8050,
        host='0.0.0.0')
    #app.run_server(debug=True)
    #app.run_server(debug=True)
