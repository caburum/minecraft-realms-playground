from enum import Enum
import dotenv
import json
import re
from datetime import datetime
from dotenv import set_key
from pathlib import Path
from os import environ
import requests

dotenv.load_dotenv()

class RelyingParty(Enum):
	XBOX_LIVE = ('xbox', 'http://xboxlive.com')
	BEDROCK_REALMS = ('realms', 'https://pocket.realms.minecraft.net/')

# uses https://x-bot.live/ to generate tokens
class API():
	def __init__(self, relyingParty: RelyingParty):
		self.relyingParty = relyingParty
		self.tokens = None
		self.session = requests.Session()

		if relyingParty == RelyingParty.BEDROCK_REALMS:
			self.session.headers.update({
				'Client-Version': '1.21.0',
				'User-Agent': 'MCPE/UWP',
			})

		key = 'XSTSToken_' + relyingParty.value[0]
		cachedTokensString = environ.get(key)
		if cachedTokensString:
			try:
				cachedTokensStringJson = json.loads(cachedTokensString)
				# https://github.com/SAML-Toolkits/python3-saml/issues/163
				TIME_FORMAT_WITH_FRAGMENT = re.compile(r'^(\d{4,4}-\d{2,2}-\d{2,2}T\d{2,2}:\d{2,2}:\d{2,2})(\.\d*)?Z?$')
				expiresOn = datetime.strptime(TIME_FORMAT_WITH_FRAGMENT.match(cachedTokensStringJson['expiresOn']).groups()[0] + 'Z', '%Y-%m-%dT%H:%M:%SZ')
				if (expiresOn - datetime.now()).total_seconds() > 1: return self._setTokens(cachedTokensStringJson)
			except:
				pass

		res = requests.get(f'https://x-bot.live/api/postman/auth?relyingParty={relyingParty.value[1]}', headers={
			'authorization': environ['X_BOT_API_KEY'],
		}).json()
		if 'XSTSToken' not in res:
			raise Exception('invalid tokens', res)

		env_file_path = Path('./.env')
		env_file_path.touch(mode=0o600, exist_ok=True)
		set_key(dotenv_path=env_file_path, key_to_set=key, value_to_set=json.dumps(res))
		self._setTokens(res)

	def _setTokens(self, tokens):
		self.tokens = tokens
		self.session.headers.update({
			'authorization': f'XBL3.0 x={self.tokens["userHash"]};{self.tokens["XSTSToken"]}'
		})

realmsAPI = API(RelyingParty.BEDROCK_REALMS)

def getRealms():
	res = realmsAPI.session.get('https://pocket.realms.minecraft.net/worlds').json()
	return res['servers']

def getActivity(realmId) -> dict[str, list[dict[str, int]]]:
	res = realmsAPI.session.get(f'https://frontend.realms.minecraft-services.net/api/v1.0/worlds/{realmId}/stories/playeractivity').json()
	return res['result']['activity']

xboxAPI = API(RelyingParty.XBOX_LIVE)

# def getGamertag(xuid: str) -> str:
# 	res = xboxAPI.session.get(f'https://profile.xboxlive.com/users/xuid({xuid})/profile/settings?settings=Gamertag', headers={
# 		'x-xbl-contract-version': '3'
# 	})

def batchGetGamertags(xuids: list[str]) -> dict[str, str]:
	res = xboxAPI.session.post(f'https://profile.xboxlive.com/users/batch/profile/settings', headers={
		'x-xbl-contract-version': '3'
	}, json={
		'settings': ['Gamertag'],
		'userIds': xuids
	}).json()['profileUsers']
	return {x['id']: x['settings'][0]['value'] for x in res}