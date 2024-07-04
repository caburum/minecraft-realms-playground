import api
from pick import pick
from datetime import datetime
import os
import json

realms = api.getRealms()

realm, _ = pick([(realm['name'], realm['id']) for realm in realms], 'arrows/enter to select realm:', clear_screen=False)

if realm is None:
	print('no realm selected')
	exit()

activity = api.getActivity(realm[1])

filename = f'data/activity_{realm[0]}_{realm[1]}_{datetime.now().strftime('%Y-%m-%d %H%M%S')}.json'

os.makedirs(os.path.dirname(filename), exist_ok=True)
with open(filename, 'w') as f:
	f.write(json.dumps(activity, indent='\t'))
	f.close()