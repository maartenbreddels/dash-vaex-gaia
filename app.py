import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

import vaex
import numpy as np

with open('token.txt') as f:  # if you want to try out, ask us for the token
    token = f.read().strip()
df = vaex.open(f'ws://ec2-18-222-183-211.us-east-2.compute.amazonaws.com:9000/gaia_ps1_nochunk?token={token}')

# df = df[:1_000_000]  # comment out for full dataset


x = 'l'
y = 'b'
z = 'phot_g_mean_mag'
limits_z = [5, 24]
shape_z = 32
limits = df.limits([x, y])

app.layout = html.Div(
    children=[
        html.H1(children='Hello Dash & Vaex with Gaia'),
        # dcc.Dropdown(id='month',
        #     options=[{'label': k, 'value': i} for i, k in enumerate(labels['month'])],
        #     value=0
        # ),
        html.Div([dcc.Graph(id='my-graph')], style={'width': '49%', 'display': 'inline-block', 'padding': '0 20'}),
        html.Div(
            [
                dcc.RadioItems(
                    id='yaxis-type',
                    options=[{'label': i, 'value': i} for i in ['Linear', 'Log']],
                    value='Linear',
                    labelStyle={'display': 'inline-block'},
                ),
                dcc.Graph(id='my-bar'),
            ],
            style={'width': '49%', 'display': 'inline-block', 'float': 'right', 'padding': '0 20'},
        ),
    ]
)


@app.callback(
    [
        Output(component_id='my-graph', component_property='figure'),
        Output(component_id='my-bar', component_property='figure'),
    ],
    [Input(component_id='my-graph', component_property='relayoutData'), Input('yaxis-type', 'value')],
)
def update_output_div(relayoutData, yaxis_type):
    print(relayoutData)
    if relayoutData is not None and 'xaxis.range[0]' in relayoutData:
        d = relayoutData
        user_limits = [[d['xaxis.range[0]'], d['xaxis.range[1]']], [d['yaxis.range[0]'], d['yaxis.range[1]']]]
    else:
        user_limits = limits
    limits_x, limits_y = user_limits
    shape = 128
    dff = df  # optionally do some filtering
    count_all = dff.count(
        binby=[x, y, z], limits=[user_limits[0], user_limits[1], limits_z], shape=[shape, shape, shape_z], edges=True
    )
    count = count_all.sum(axis=2)[2:-1, 2:-1]
    count_z_zoom = count_all[2:-1, 2:-1].sum(axis=(0, 1))[2:-1]
    count_z_all = count_all.sum(axis=(0, 1))[2:-1]

    total_count = count.sum()
    zgrid = np.log1p(count).T.tolist()
    data = {
        'z': zgrid,
        'x': dff.bin_centers(x, limits_x, shape=shape),
        'y': dff.bin_centers(y, limits_y, shape=shape),
        'type': 'heatmap',
    }
    figure_heat = {
        'data': [data],
        'layout': {
            'title': f'Gaia DR2 - {x} vs {y} (total {total_count:,})',
            'xaxis': {'label': x},
            'yaxis': {'label': y},
        },
    }

    z_centers = dff.bin_centers(z, limits_z, shape=shape_z)
    figure_bar = {
        'data': [
            {'x': z_centers, 'y': count_z_zoom.tolist(), 'type': 'bar', 'name': 'Zoomed region'},
            {'x': z_centers, 'y': count_z_all.tolist(), 'type': 'bar', 'name': 'Full region'},
        ],
        'layout': {
            'title': f'{z} histogram',
            'xaxis': {'label': '{z}'},
            'yaxis': {'label': 'counts', 'type': 'linear' if yaxis_type == 'Linear' else 'log'},
        },
    }
    return figure_heat, figure_bar


if __name__ == '__main__':
    app.run_server(debug=True)
