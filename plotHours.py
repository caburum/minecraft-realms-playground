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
fig = px.timeline(df, x_start='start', x_end='end', y='gamertag', hover_data="hours", template='plotly_dark')
fig.update_yaxes(autorange='reversed')
fig.show()