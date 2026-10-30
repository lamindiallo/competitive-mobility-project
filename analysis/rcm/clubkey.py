import re, unicodedata
DROP={'fc','afc','a','f','c','cf'}
ALIAS={'wolves':'wolverhampton wanderers','qpr':'queens park rangers','mk dons':'milton keynes dons',
 'west brom':'west bromwich albion','brighton':'brighton and hove albion','spurs':'tottenham hotspur',
 'man city':'manchester city','man utd':'manchester united','sheff utd':'sheffield united',
 'sheff wed':'sheffield wednesday','nottm forest':'nottingham forest','bournemouth':'bournemouth',
 'peterborough':'peterborough united','hull':'hull city','cardiff':'cardiff city','swansea':'swansea city',
 'stoke':'stoke city','leicester':'leicester city','norwich':'norwich city','ipswich':'ipswich town',
 'coventry':'coventry city','bristol':'bristol city','luton':'luton town','huddersfield':'huddersfield town',
 'preston':'preston north end','birmingham':'birmingham city','derby':'derby county','blackburn':'blackburn rovers',
 'bolton':'bolton wanderers','wigan':'wigan athletic','charlton':'charlton athletic','oldham':'oldham athletic',
 'yeovil':'yeovil town','doncaster':'doncaster rovers','rotherham':'rotherham united','scunthorpe':'scunthorpe united',
 'barnsley':'barnsley','burton':'burton albion','plymouth':'plymouth argyle','southend':'southend united',
 'crewe':'crewe alexandra','gillingham':'gillingham','brentford':'brentford','millwall':'millwall',
 # D283: the 2022/23 openfootball patch names three clubs differently from engsoccerdata
 'accrington stanley':'accrington','cheltenham town':'cheltenham','stevenage':'stevenage borough'}
def ck(s):
    s=unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode().lower()
    s=s.replace('&',' and ').replace('.',' ')
    s=re.sub(r'[^a-z0-9 ]',' ',s)
    if ' '.join(s.split())=='afc wimbledon': return 'afc wimbledon'   # D283: phoenix club (2002), not Wimbledon FC
    toks=[t for t in s.split() if t not in DROP]
    k=' '.join(toks)
    return ALIAS.get(k,k)
