import dash
from dash import html, dcc, dash_table
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
import requests
import feedparser

# ----------------------------------------
# Constants
# ----------------------------------------
NEWS_FEEDS = {
    "EFF (Digital Rights)": "https://www.eff.org/rss/updates.xml",
    "Access Now (Censorship News)": "https://www.accessnow.org/feed/"
}

# ----------------------------------------
# Function: Fetch IODA outage reports
# ----------------------------------------
def fetch_ioda_outages(limit=10):
    try:
        url = "https://ioda.inetintel.cc.gatech.edu/api/v1/signals"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()

        if not isinstance(data, list) or len(data) == 0:
            raise ValueError("IODA returned empty or invalid data")

        rows = []
        for item in data[:limit]:
            rows.append({
                "source": "IODA",
                "region": item.get("location"),
                "event_time": item.get("start_time"),
                "type": item.get("signal_type")
            })
        return pd.DataFrame(rows)

    except Exception as e:
        print(f"[⚠️] IODA fetch failed, using sample data: {e}")
        return pd.DataFrame([
            {"source": "IODA", "region": "Iran", "event_time": "2025-06-28T14:12", "type": "Internet blackout"},
            {"source": "IODA", "region": "Russia", "event_time": "2025-06-27T22:10", "type": "BGP drop"},
            {"source": "IODA", "region": "India", "event_time": "2025-06-27T18:00", "type": "Darknet loss"},
        ])

# ----------------------------------------
# Function: Fetch OONI measurement results
# ----------------------------------------
def fetch_ooni_measurements(domain="telegram.org", limit=20):
    try:
        url = f"https://api.ooni.io/api/v1/measurements?domain={domain}&limit={limit}"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json().get("results", [])

        rows = []
        for entry in data:
            rows.append({
                "source": "OONI",
                "domain": domain,
                "country": entry.get("probe_cc"),
                "time": entry.get("measurement_start_time"),
                "blocked": entry.get("blocking", "unknown")
            })
        return pd.DataFrame(rows)
    except Exception as e:
        print(f"[⚠️] OONI fetch failed, using sample data: {e}")
        return pd.DataFrame([
            {"source": "OONI", "domain": domain, "country": "IR", "time": "2025-06-27T12:00", "blocked": "true"},
            {"source": "OONI", "domain": domain, "country": "RU", "time": "2025-06-27T11:00", "blocked": "false"},
        ])

# ----------------------------------------
# Function: Fetch news feed
# ----------------------------------------
def fetch_news(feed_url):
    try:
        feed = feedparser.parse(feed_url)
        items = feed.entries[:5]
        return [{"title": item.title, "link": item.link} for item in items]
    except Exception as e:
        print(f"[⚠️] News fetch failed: {e}")
        return [{"title": "News feed unavailable", "link": "#"}]

# ----------------------------------------
# Load IODA data
# ----------------------------------------
ioda_data = fetch_ioda_outages(limit=10)

# ----------------------------------------
# Create Dash app
# ----------------------------------------
app = dash.Dash(__name__)

app.layout = html.Div(children=[
    html.H1("Censorship Dashboard", style={'textAlign': 'center'}),
    html.P("Live monitoring of network interference, probe data, and global outages."),

    # Static ping latency chart from Iran
   html.Img(
    src='/assets/iran_ping_rtt.png',
    style={
        'width': '100%',
        'maxWidth': '1000px',
        'margin': '0 auto',
        'display': 'block',
        'boxShadow': '0 4px 10px rgba(0,0,0,0.1)',
        'borderRadius': '6px'
    }
),

    html.H2("Recent IODA Outage Reports", style={'marginTop': '40px'}),
    dash_table.DataTable(
        data=ioda_data.to_dict("records"),
        columns=[{"name": col, "id": col} for col in ioda_data.columns],
        style_table={'overflowX': 'auto'},
        style_cell={'padding': '8px', 'textAlign': 'left'},
        style_header={'fontWeight': 'bold', 'backgroundColor': '#f0f0f0'}
    ),

    html.H2("Recent OONI Measurements", style={'marginTop': '40px'}),
    html.Label("Select a Domain:"),
    dcc.Dropdown(
        id='domain-dropdown',
        options=[
            {'label': 'Telegram', 'value': 'telegram.org'},
            {'label': 'BBC', 'value': 'bbc.com'},
            {'label': 'Wikipedia', 'value': 'wikipedia.org'},
            {'label': 'YouTube', 'value': 'youtube.com'},
            {'label': 'NYTimes', 'value': 'nytimes.com'}
        ],
        value='telegram.org',
        style={'width': '50%'}
    ),
    html.Div(id='ooni-table-container', style={'marginTop': '20px'}),
    html.Div(id='ooni-graph-container', style={'marginTop': '40px'}),

    html.H2("News Section", style={'marginTop': '40px'}),
    html.Label("Select News Source:"),
    dcc.Dropdown(
        id='news-source-dropdown',
        options=[{"label": name, "value": url} for name, url in NEWS_FEEDS.items()],
        value=list(NEWS_FEEDS.values())[0],
        style={'width': '70%'}
    ),
    html.Div(id='news-feed', style={'marginTop': '20px'})
])

# ----------------------------------------
# Callback: Update OONI table and graph
# ----------------------------------------
@app.callback(
    Output('ooni-table-container', 'children'),
    Output('ooni-graph-container', 'children'),
    Input('domain-dropdown', 'value')
)
def update_ooni_components(domain):
    df = fetch_ooni_measurements(domain=domain, limit=20)
    df["time"] = pd.to_datetime(df["time"])
    df["blocked"] = df["blocked"].astype(str)

    table = dash_table.DataTable(
        data=df.to_dict("records"),
        columns=[{"name": col, "id": col} for col in df.columns],
        style_data_conditional=[
            {"if": {"column_id": "blocked", "filter_query": "{blocked} = 'true'"},
             "backgroundColor": "#ffcccc", "color": "red"},
            {"if": {"column_id": "blocked", "filter_query": "{blocked} = 'false'"},
             "backgroundColor": "#ccffcc", "color": "green"}
        ],
        style_table={'overflowX': 'auto'},
        style_cell={'padding': '8px', 'textAlign': 'left'},
        style_header={'fontWeight': 'bold', 'backgroundColor': '#f0f0f0'}
    )

    graph = px.histogram(
        df, x="country", color="blocked",
        title=f"Blocking Status by Country for {domain}",
        labels={"blocked": "Blocked"},
        barmode="group"
    )

    return table, dcc.Graph(figure=graph)

# ----------------------------------------
# Callback: Update news section
# ----------------------------------------
@app.callback(
    Output('news-feed', 'children'),
    Input('news-source-dropdown', 'value')
)
def update_news_feed(feed_url):
    articles = fetch_news(feed_url)
    return html.Ul([
        html.Li(html.A(article["title"], href=article["link"], target="_blank"))
        for article in articles
    ])

# ----------------------------------------
# Run app
# ----------------------------------------
if __name__ == '__main__':
    app.run(debug=True)



