import api
from pick import pick
import pandas as pd
from datetime import datetime, UTC
import plotly.express as px
import dash
from dash import html, dcc, Output, Input, State
from dash.exceptions import PreventUpdate
import dateutil.parser as dateparser
from typing import Dict, Any, Optional

realms = api.getRealms()

realmId = '20229023'
if realmId is None:
	# picker reactivating?
	picker = pick([(realm['name'], realm['id']) for realm in realms], 'arrows/enter to select realm:', clear_screen=False)
	realmId = picker[0][1]

activity = api.getActivity(realmId)
print(activity)

gamertags = api.batchGetGamertags(list(activity.keys()))

userTotalHours = pd.DataFrame([
	dict(gamertag=gamertags[xuid], hours=sum([(d['e'] - d['s']) / 3600 for d in activity[xuid]]))
	for xuid in activity
])
print(userTotalHours)

df = pd.DataFrame([
	dict(gamertag=gamertags[xuid], start=datetime.fromtimestamp(d['s'], UTC).astimezone(), end=datetime.fromtimestamp(d['e'], UTC).astimezone(), hours=((d['e'] - d['s']) / 3600))
	for xuid in activity for d in activity[xuid]
])

one_hour = 60 * 60 * 1000
one_day = 24 * one_hour
a_yearish = 365.25 * one_day

time_min: float = min(df['start']).timestamp()
time_max: float = max(df['end']).timestamp()
data_range = (time_max - time_min) * 1000

def get_ticks(time_min: float, time_max: float):
	interval = (time_max - time_min) * 1000
	if interval <= 1.5 * one_day:
		dtick = one_hour
		dtickformat = "%b %e %H:%M" # todo: use 2 x axis, one for day, one for hour
		tick0 = datetime.fromtimestamp(time_min).replace(hour=0, minute=0, second=0, microsecond=0)
	elif one_day < interval:
		dtick = one_day
		dtickformat = "%b %e"
		tick0 = datetime.fromtimestamp(time_min).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
	print('dtick=', dtick, 'dtickformat=', dtickformat)
	return {'dtick': dtick, 'tickformat': dtickformat, 'tick0': tick0.isoformat()}

timeline = px.timeline(df, template='plotly_dark', x_start='start', x_end='end', y='gamertag', hover_name='gamertag', hover_data={
	'gamertag': False,
	'start': '|%Y-%m-%d %H:%M',
	'end': '|%Y-%m-%d %H:%M',
	'hours': ':.1f'
})
timeline.update_yaxes(autorange='reversed')
# minor=dict(ticklen=4, gridcolor='#333333', tick0='2024-01-01', dtick=60*60*1000)
timeline.update_xaxes(type='date', dtick='D1', ticklabelmode='period', rangeslider_visible=True,
	rangeselector=dict(buttons=list([
		dict(count=1, label='1d', step='day', stepmode='backward'),
		dict(count=7, label='1w', step='day', stepmode='backward'),
		dict(count=1, label='1y', step='year', stepmode='backward'),
		dict(step='all')
	])),
	# tickformatstops=[ # doesn't currently work when using specific dtick
	# 	dict(dtickrange=[None, 3600000], value='%H:%M'),
	# 	dict(dtickrange=[3600000, None], value='%b %e')
	# ]
)
timeline.update_xaxes(get_ticks(time_min, time_max))
timeline.update_layout(xaxis_rangeselector_font_color='white', xaxis_rangeselector_activecolor='#333333', xaxis_rangeselector_bgcolor='#222222')

bar = px.bar(userTotalHours, x='gamertag', y='hours', template='plotly_dark')

app = dash.Dash(__name__, external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css'])
app.layout = html.Div([
	dcc.Tabs([
		dcc.Tab(label='timeline', children=[
			dcc.Graph(id='fig', figure=timeline)
		]),
		dcc.Tab(label='totals', children=[
			dcc.Graph(id='total', figure=bar)
		])
	])
], style={'width': '100vw', 'height': '100vh'})

@app.callback(
	Output('fig', 'figure'),
	[Input('fig', 'relayoutData'), State('fig', 'figure')]
)
def scale_xaxes(relayout_data: Optional[Dict[str, Any]], figure):
	print(relayout_data)
	if relayout_data is None: raise PreventUpdate

	if 'xaxis.range' in relayout_data: # normalize rangeslider inputs
		relayout_data['xaxis.range[0]'] = relayout_data['xaxis.range'][0]
		relayout_data['xaxis.range[1]'] = relayout_data['xaxis.range'][1]

	if 'xaxis.range[0]' in relayout_data and 'xaxis.range[1]' in relayout_data:
		print('zooming in: ', datetime.now().isoformat())
		in_time_min = dateparser.parse(relayout_data['xaxis.range[0]']).timestamp()
		in_time_max = dateparser.parse(relayout_data['xaxis.range[1]']).timestamp()
		ticks = get_ticks(in_time_min, in_time_max)
		figure['layout']['xaxis'].update(ticks)
		return figure
	elif 'xaxis.autorange' in relayout_data:
		print('resetting zoom to original: ', datetime.now().isoformat())
		ticks = get_ticks(time_min, time_max)
		figure['layout']['xaxis'].update(ticks)
		return figure
	else:
		raise dash.exceptions.PreventUpdate

if __name__ == '__main__':
	app.run(debug=True)