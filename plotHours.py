import api
from datetime import datetime, UTC
import plotly.express as px
import pandas as pd

realms = api.getRealms()
realmId = realms[0]['id'] # todo: allow multiple

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
fig = px.timeline(df, x_start='start', x_end='end', y='gamertag', hover_data='hours', template='plotly_dark')
fig.update_yaxes(autorange='reversed')
# minor=dict(ticklen=4, gridcolor='#333333', tick0='2024-01-01', dtick=60*60*1000)
fig.update_xaxes(type='date', dtick='D1', ticklabelmode='period', rangeslider_visible=True, rangeselector=dict(buttons=list([
	dict(count=1, label='1d', step='day', stepmode='backward'),
	dict(count=7, label='1w', step='day', stepmode='backward'),
	dict(count=1, label='1y', step='year', stepmode='backward'),
	dict(step='all')
])), tickformatstops=[ # doesn't currently work when using specific dtick
	dict(dtickrange=[None, 3600000], value='%H:%M'),
	dict(dtickrange=[3600000, None], value='%b %e')
])
fig.update_layout(template='plotly_dark', xaxis_rangeselector_font_color='white', xaxis_rangeselector_activecolor='#333333', xaxis_rangeselector_bgcolor='#222222')
fig.show()