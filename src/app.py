import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Patch, clientside_callback, callback, dash_table
from dash.dependencies import Input, Output, State
from functions import extract_sunburst_data, get_content, llm1claude, get_all_candidats, scraper_resume, llm, llm3v2, get_html_content, extract_links, get_dataframe
import plotly.graph_objects as go
import json
from dash_bootstrap_templates import load_figure_template
import plotly.io as pio
import html as ht
import os
import pandas as pd
import os
hierarchy_path = os.path.join("hierarchy", "Hierarchy2.json")
logo_path=os.path.join("assets","logo.png")
load_figure_template(["minty", "minty_dark"])
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.MINTY, dbc.icons.BOOTSTRAP], suppress_callback_exceptions=True)
server = app.server
color_mode_switch = html.Span(
    [
        dbc.Label(className="fa fa-moon", html_for="color-mode-switch"),
        dbc.Switch(id="color-mode-switch", value=False, className="d-inline-block ms-1", persistence=True),
        dbc.Label(className="fa fa-sun", html_for="color-mode-switch"),
    ]
)

liens_existants = []
result = ""



navbar = dbc.Navbar(
            dbc.Container(
                [
                    dbc.Row([
                        dbc.Col([
                              dbc.NavbarBrand("Resoneo AI App", className="ms-2" ,style={"color": "black"})
                        ],
                        width={"size":"auto"})
                    ],
                    align="center",
                    className="g-0"),

                    dbc.Row([
                        dbc.Col([
                            dbc.Nav([
                                dbc.NavItem(dbc.NavLink("Dashboard", href="/" ,style={ "color": "black"})),

                                dbc.NavItem(dbc.NavLink("Netlinking", href="/analyzer", style={ "color": "black"})),
                        
                            ],
                            navbar=True
                            )
                        ],
                        width={"size":"auto"})
                    ],
                    align="center"),
                    dbc.Col(dbc.NavbarToggler(id="navbar-toggler", n_clicks=0)),
                    
                    dbc.Row([
                        dbc.Col(
                             dbc.Collapse(
                                dbc.Nav([
                                    
                                    color_mode_switch
                                ]
                                ),
                                id="navbar-collapse",
                                is_open=False,
                                navbar=True
                             )
                        )
                    ],
                    align="center")
                ],
            fluid=True
            ),
    dark=True,
   
)


# Load the sunburst data
labels, parents, ids, values = [], [], [], []
with open(hierarchy_path, "r", encoding='utf-8') as f:
    data = json.load(f)
for item in data:
    labels, parents, ids, values = extract_sunburst_data(item)
fig1 = go.Figure(go.Sunburst(
    labels=labels,
    parents=parents,
    ids=ids,
    values=values,
    hoverinfo='label',
    hovertemplate='<span style="font-size: 20px;">%{label}</span><extra></extra>',
))

fig1.update_layout(
    margin=dict(t=0, l=0, r=0, b=0),
    uniformtext=dict(minsize=10)
)

fig1.update_traces(textinfo="label+percent parent")
fig1.update_traces(textfont=dict(size=16))


dashboard_layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Sunburst Plot", className="text-center"),
                dbc.CardBody([
                    dcc.Graph(id="sunburst-plot", figure=fig1, style={"height": "600px", "width": "100%"}),
                ]),
            ], className="mb-4 shadow", style={"cursor": "pointer"}),
        ], width=6),
        dbc.Col([
            dbc.Card([

                dbc.CardHeader([
                    "Cluster Documents",
                    html.I(className="bi bi-fullscreen float-end", id="open-modal", style={"cursor": "pointer"})
                ], className="text-center"),
                dbc.CardBody([
                    dash_table.DataTable(
                        id="cluster-documents",
                        columns=[],
                        data=[],
                        page_size=10,
                        style_cell={'textAlign': 'left'},
                        style_table={'overflowX': 'auto', 'maxHeight': '300px'},
                    ),
                ]),
            ], className="mb-4 shadow"),
            dbc.Card([
                dbc.CardHeader("Cluster Information", className="text-center"),
                dbc.CardBody([
                    html.Div([
                        html.Div(id="breadcrumb", style={"marginBottom": "10px"}),
                    ]),
                  
                ]),
            ], className="mb-4 shadow"),
        ], width=6),
    ]),
    dbc.Modal([
        dbc.ModalHeader(id="modal-header"),
        dbc.ModalBody([
            dash_table.DataTable(
                id="modal-table",
                columns=[],
                data=[],
                page_size=60,
                style_cell={'textAlign': 'left'},
                style_table={'overflowX': 'auto', 'maxHeight': '400px'},
            ),
            html.Div(id="download-notification")
        ]),
        dbc.ModalFooter([
           
            html.I(className="bi bi-cloud-download", id="export-table", style={"fontSize": "2rem", "cursor": "pointer"}),
            dbc.Button("Download Table", id="btn-download-table"),
            dcc.Download(id="download-table"),


            dbc.Button("Close", id="close-modal", className="ms-auto", n_clicks=0),
        ]),
    ], id="modal", size="xl", is_open=False),
], fluid=True)
analyzer_layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Options"),
                dbc.CardBody([
                    dcc.Dropdown(
                        id="option-dropdown",
                        options=[
                            {"label": "From a link", "value": "url"},
                            {"label": "From content", "value": "contenu"}
                        ],
                        value="url",
                        className="mb-3"
                    ),
                    html.Div(id="option-content")
                ])
            ], className="mt-4 shadow")
        ], width=4),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Result"),
                dbc.CardBody([
                    html.Div(id="content-output", style={'color': 'black'}),
                    html.Div(id="url-output", style={'color': 'black', 'font-family': 'Arial, sans-serif', 'font-size': '14px'})
                ])
            ], className="mt-4 shadow")
        ], width=8),
    ]),
], fluid=True)

# Define the main layout
app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    navbar,
    html.Div(id="page-content"),
])

# Callback to update page content based on URL
@app.callback(Output("page-content", "children"),
              [Input("url", "pathname")])
def display_page(pathname):
    if pathname == "/":
        return dashboard_layout
    elif pathname == "/analyzer":
        return analyzer_layout
    else:
        return "404 Page Not Found"

@app.callback(
    Output("url-output", "children"),
    Input("analyze-url-button", "n_clicks"),
    State("url-input", "value")
)
def analyze_url(n_clicks, url):
    if n_clicks is not None and n_clicks > 0 and url:
        htmlcontent = get_html_content(url)
        htmlfinal = htmlcontent.values[0]
        decoded_html = ht.unescape(htmlfinal)
        
        content = get_content(url)
        themes = llm1claude(content)
        split = themes.split("\n")
        theme = [elem for elem in split[1:] if elem != ""]
        sujets = []
        for the in theme:
            sujet,="helo"
            sujets.append(sujet)
        all = []
        for element in sujets:
            if element not in all:
                all.append(element)

        all_candidats = get_all_candidats(all)
        liens_existants = extract_links(decoded_html)
        liens_existants.append(url)
        liens_a_ajouter = [element for element in all_candidats if element not in liens_existants]
        to_send = {}
        for i in liens_a_ajouter:
            resume = scraper_resume(i)
            to_send[i] = resume
        texte = llm(content.values[0], to_send)
        global result
        result = llm3v2(decoded_html, texte)
        return [
            dbc.CardBody([
                dbc.Card([
                    dbc.CardHeader("Existing Links"),
                    dbc.CardBody([
                        html.Ul([
                            html.Li([
                                html.I(className="bi bi-link-45deg"),
                                html.A(url, href=url, target="_blank", style={'font-size': '18px'})
                            ]) for url in liens_existants
                        ], className="list-unstyled"),
                    ], className="bg-light")
                ], className="mb-4 shadow"),
                dbc.Card([
                    dbc.CardHeader("Links to Add"),
                    dbc.CardBody([
                        dcc.Markdown(texte, dangerously_allow_html=True, style={'font-size': '18px'})
                    ], className="bg-light")
                ], className="mb-4 shadow"),
                dbc.Card([
                    dbc.CardHeader("Recreated Text"),
                    dbc.CardBody([

                        dcc.Markdown(result, dangerously_allow_html=True, style={'font-size': '18px'}),
                               dbc.Row([
            dbc.Col([
                dbc.Button("Download HTML",id="btn-download-txt"),
                dcc.Download(id="download-text")
              
            ], className="mb-3"),
        ]),
                    ], className="bg-light")
                ], className="mb-4 shadow")
            ])]

@app.callback(
    Output("option-content", "children"),
    Input("option-dropdown", "value")
)
def update_option_content(option):
    if option == "contenu":
        return [
            dbc.Textarea(id="content-input", placeholder="Paste your new content", className="mb-2 form-control"),
            dbc.Button("Analyze", id="analyze-content-button", color="primary", className="mt-2")
        ]
    elif option == "url":
        return [
            dbc.Input(id="url-input", placeholder="Enter the link here", className="mb-2 form-control"),
            dbc.Button("Analyze", id="analyze-url-button", color="primary", className="mt-2")
        ]
    else:
        return 0

@callback(
    Output("graph", "figure"),
    Input("color-mode-switch", "value"),
)
def update_figure_template(switch_on):
    template = pio.templates["minty"] if switch_on else pio.templates["minty_dark"]
    patched_figure = Patch()
    patched_figure["layout"]["template"] = template
    return patched_figure

clientside_callback(
    """
    (switchOn) => {
       document.documentElement.setAttribute('data-bs-theme', switchOn ? 'light' : 'dark');  
       return window.dash_clientside.no_update
    }
    """,
    Output("color-mode-switch", "id"),
    Input("color-mode-switch", "value"),
)

@app.callback(
    Output("cluster-documents", "columns"),
    Output("cluster-documents", "data"),
    Output("breadcrumb", "children"),
    Input("sunburst-plot", "clickData"),
)
def update_cluster_documents(click_data):
    global data
    
    if click_data:
        clicked_id = click_data["points"][0]["id"]
        clicked_label = click_data["points"][0]["label"]
        
        def find_node(node, target_id):
            if node["id"] == target_id:
                return node
            for child in node.get("children", []):
                found_node = find_node(child, target_id)
                if found_node:
                    return found_node
            return None
        
        clicked_node = find_node(data[0], clicked_id)
        cluster_value = ""
        if clicked_node and "value" in clicked_node:
            cluster_value = clicked_node["value"]
            cluster_value = cluster_value.replace("000", "")
            df = get_dataframe(int(cluster_value))
            
            columns = [
                {"name": "Link", "id": "url", "presentation": "markdown"},
                {"name": "Description", "id": "resume"},
            ]

            dayta = df.to_dict("records")
 
 
            breadcrumb = html.Span(" > ".join(clicked_id.split("/")), className="breadcrumb-style")
            
            return columns, dayta, breadcrumb
    
    return [], [], ""
# Callback for opening the modal
@app.callback(
    Output("modal", "is_open"),
    [Input("open-modal", "n_clicks"), Input("close-modal", "n_clicks")],
    [State("modal", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

# Callback for updating the modal content
@app.callback(
    Output("modal-header", "children"),
    Output("modal-table", "columns"),
    Output("modal-table", "data"),
    Input("cluster-documents", "data"),
)

def update_modal_content(data):
    if data:
        columns = [
            {"name": "Title", "id": "url", "presentation": "markdown"},
            {"name": "Description", "id": "resume"},
        ]
        return "Cluster Documents (Full Table)", columns, data
    return "", [], []

@app.callback(
    Output("download-table", "data"),
    [Input("btn-download-table", "n_clicks")],
    [State("modal-table", "data")],
    prevent_initial_call=True
)
def download_file(n_clicks, data):
    if n_clicks is not None and n_clicks > 0:
        if data:
            df = pd.DataFrame(data)
            csv_string = df.to_csv(index=False, sep=';')
            return dict(content=csv_string, filename="cluster.csv")

    return None
@app.callback(
    Output("download-text", "data"),
    [Input("btn-download-txt", "n_clicks")],
    [State("url-output", "children")],
    prevent_initial_call=True
)
def download_html_file(n_clicks, html_content):
    if n_clicks is not None and n_clicks > 0:
        if result:
            return dict(content=result, filename="result.txt")



    return None
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run_server(debug=True, port=port)
    
