import importlib.metadata as md 
print('httpx', md.version('httpx')) 
print('httpx requires', md.metadata('httpx').get_all('Requires-Dist')) 
print('httpcore', md.version('httpcore')) 
print('httpcore requires', md.metadata('httpcore').get_all('Requires-Dist')) 
