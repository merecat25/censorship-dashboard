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

MONITORED_COUNTRIES = [
    "RU", "CN", "IR", "IQ", "BY", "ET", "IN",
    "EG", "TR", "SA", "CU", "VE", "NG", "SD"
]

DISCLAIMER = "⚠️ OONI data may contain false positives. Some measurements from unlikely regions may appear due to test anomalies."

# ----------------------------------------
# Function: Fetch OONI measurement results
# ----------------------------------------
def fetch_ooni_measurements(domain="telegram.org", limit=100):
    try:
        url = f"https://api.ooni.io/api/v1/measurements?domain={domain}&limit={limit}"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json().get("results", [])

        rows = []
        for entry in data:
            cc = entry.get("probe_cc")
            if cc in MONITORED_COUNTRIES:
                rows.append({
                    "source": "OONI",
                    "domain": domain,
                    "country": cc,
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
# Create Dash app
# ----------------------------------------
app = dash.Dash(__name__)

app.layout = html.Div(children=[
    html.H1("Censorship Dashboard", style={'textAlign': 'center'}),
    html.P("Live monitoring of network interference, probe data, and global outages."),

    # ---------- First Static Chart ----------
    html.Div([
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
        html.P("Ping latency to Iran. Updated manually from RIPE Atlas.", style={'textAlign': 'center', 'fontSize': '14px'})
    ], style={'marginBottom': '40px'}),

    # ---------- Cloudflare Outage Chart ----------
    html.Div([
        html.Img(
            src='/assets/cloudflare_outage_chart.png',
            style={
                'width': '100%',
                'maxWidth': '1000px',
                'margin': '0 auto',
                'display': 'block',
                'boxShadow': '0 4px 10px rgba(0,0,0,0.1)',
                'borderRadius': '6px'
            }
        ),
        html.P("Cloudflare Outage Map – Source: Cloudflare Radar", style={'textAlign': 'center', 'fontSize': '14px'})
    ], style={'marginBottom': '40px'}),

    # ---------- OONI Section ----------
    html.H2("OONI Measurement Data"),
    html.P(DISCLAIMER, style={'color': 'red', 'fontStyle': 'italic'}),

    html.Label("Select a Domain:"),
    dcc.Dropdown(
        id='domain-dropdown',
        options=[
            {'label': 'Telegram', 'value': 'telegram.org'},
            {'label': 'BBC', 'value': 'bbc.com'},
            {'label': 'Wikipedia', 'value': 'wikipedia.org'},
            {'label': 'YouTube', 'value': 'youtube.com'},
            {'label': 'NYTimes', 'value': 'nytimes.com'},
            {'label': 'Signal', 'value': 'signal.org'}
        ],
        value='telegram.org',
        style={'width': '50%'}
    ),

    html.Div(id='ooni-table-container', style={'marginTop': '20px'}),
    html.Div(id='ooni-graph-container', style={'marginTop': '40px'}),

    # ---------- News Section ----------
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
    df = fetch_ooni_measurements(domain=domain, limit=100)
    df["time"] = pd.to_datetime(df["time"])
    df["blocked"] = df["blocked"].astype(str)

    # Ensure all monitored countries are represented
    all_countries = pd.DataFrame({"country": MONITORED_COUNTRIES})
    df = pd.merge(all_countries, df, on="country", how="left")

    table = dash_table.DataTable(
        data=df.fillna("N/A").to_dict("records"),
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
        df.dropna(subset=["blocked"]), x="country", color="blocked",
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

