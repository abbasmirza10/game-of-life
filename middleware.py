from flask import Flask, request, jsonify
import requests
import random
import time
import threading

MY_PORT = 34034 # random.randrange(1<<12, 1<<15)
MY_URL = "http://localhost:"+str(MY_PORT)

app = Flask(__name__)

known_servers = {}
tile_w, tile_h = 0,0
board_w, board_h = 0,0
live_servers = {}
tick_delay = 0
deadline = 0
speed_cv = threading.Condition()
tiles = {}


@app.get('/')
def index():
  return open('middleware_ui.html', 'r').read()

@app.put('/addTS')
def newTS():
  """Endpoint for registering new Tile Servers"""
  try:
    response = requests.get(request.json['url']+'/ping')
    if not response.ok:
      print(response)
      return 'GET '+request.json['url']+'/ping failed', response.status_code
  except BaseException as ex:
    print(ex)
    return 'GET '+request.json['url']+'/ping crashed', 500
  answer = 'OK' if request.json['url'] not in known_servers else 'already added'
  known_servers[request.json['url']] = request.json
  return answer

@app.get('/stop')
def stop_all():
  """Stop all live servers"""
  global tick_delay, live_servers, tile_w, tile_h, board_w, board_h
  if not live_servers: return 'Not running', 409
  if tick_delay > 0:
    with speed_cv:
      tick_delay = 0
      speed_cv.notify_all()
  for s in live_servers.values():
    try: requests.get(s+'/stop')
    except: pass
  tile_w = tile_h = board_w = board_h = 0
  live_servers = {}
  return 'OK'

@app.get('/pause')
def pause():
  """Pause all live servers"""
  global tick_delay
  if tick_delay <= 0: return 'Not simulating', 409
  with speed_cv:
    tick_delay = 0
    speed_cv.notify_all()
  for s in live_servers.values():
    try: requests.get(s+'/pause')
    except: pass
  return 'OK'

@app.post('/config')
def config():
  """assemble connected servers into a board"""
  global tile_w, tile_h, board_w, board_h, tick_delay, tiles
  if live_servers: return 'Already runnning; must /stop first', 409
  
  tile_w = max(request.json['tile_width'],1)
  tile_h = max(request.json['tile_height'],1)
  board_w = max(request.json['board_width'],1)
  board_h = max(request.json['board_height'],1)
  tidxs = [(x,y) for x in range(board_w) for y in range(board_h)]
  random.shuffle(tidxs)
  for s in request.json.get('include',[]) + list(known_servers.keys()):
    if s in live_servers.values(): continue # no repeats
    try:
      response = requests.post(s+'/config', json={'width':tile_w,'height':tile_h})
      assert response.ok
      print(s+'/config OK')
      live_servers[tidxs.pop()] = s
    except BaseException as ex:
      print('skipping',s,ex)
    if not tidxs: break
  
  tiles = {(x,y):('"'*tile_w+'\n')*tile_h for x in range(tile_w) for y in range(tile_h)}
  
  tick_delay = 0
  for tidx, server in live_servers.items():
    th = TileTicker(server, tidx) # make a thread
    th.daemon = True # configure it to run in the background
    th.start() # start it running
  
  print('configured',live_servers)
  if len(tidxs) == 0:
    return 'OK'
  else:
    return f'Tiles with no server: {len(tidxs)}'

@app.post('/speed')
def speed():
  global tick_delay
  new_delay = float(request.data)
  if new_delay <= 0:
    return '/speed is for running the simulation; try /pause to stop it', 409
  if tick_delay <= 0:
    # leaving edit mode; find initial boards
    for key in live_servers:
      try:
        res = requests.get(live_servers[key]+'/ping')
        tiles[key] = res.json()['tile']
      except BaseException as ex:
        tiles[key] = ('"'*tile_w+'\n')*tile_h
        print(key, live_servers[key], ex)
  with speed_cv:
    tick_delay = new_delay
    speed_cv.notify_all()
  return str(new_delay)

def json_safe(dict_with_tuple_keys):
  return {','.join(str(_) for _ in k):v for k,v in dict_with_tuple_keys.items()}

@app.get('/ping')
def ping():
  return jsonify({
    'servers':list(known_servers),
    'config':json_safe(live_servers),
    'delay':tick_delay,
    'tiles':json_safe(tiles),
    'dimensions':[tile_w,tile_h,board_w,board_h],
  })

@app.get('/get_known_servers')
def get_known_servers():
  return jsonify(known_servers)



def borderOf(x,y):
  """Use Python's strided slice to create the border of a tile
  [nw][n from w to e][ne][e from n to s][se][s from e to w][sw][w from s to n]
  """
  xp = (x+1)%board_w
  xm = (x+board_w-1)%board_w
  yp = (y+1)%board_h
  ym = (y+board_h-1)%board_h
  W,H = tile_w, tile_h
  bits = [
    tiles[(xm,ym)][-2:-1], # bottom-right
    tiles[(x ,ym)][(W+1)*(H-1):-1], # bottom
    tiles[(xp,ym)][(W+1)*(H-1):(W+1)*(H-1)+1], # bottom-left
    tiles[(xp,y )][::W+1], # left
    tiles[(xp,yp)][0:1], # top-left
    tiles[(x ,yp)][W-1::-1], # top backwards -- [:W] is top
    tiles[(xm,yp)][W-1:W], # top-right
    tiles[(xm,y )][-2::-W-1], # right backwards -- [W-1::W+1] is right
  ]
  return ''.join(bits)

class TileTicker(threading.Thread):
  """Because we have multiple tile servers, each of which will take some time to process each /tick,
  we want to be able to run all the POST /tick requests in parrallel."""
  def __init__(self, target, tileid):
    super().__init__()
    self.target = target
    self.tileid = tileid
    # A session allows us to use the same TCP connection for multiple requests,
    # resulting in a noticeable speedup for repeated requests like this thread makes
    self.session = requests.Session()
  def run(self):
    """Depends on a global "deadline" variable to time requests
    and a condition variable to not run when tick_delay=0"""
    while live_servers.get(self.tileid) == self.target:
      with speed_cv:
        while tick_delay <= 0 or deadline <= time.time():
          if live_servers[self.tileid] != self.target: return
          speed_cv.wait()
      try:
        r = self.session.post(
          self.target + '/tick', 
          data=borderOf(*self.tileid), 
          timeout=(deadline - time.time())
        )
        tiles[self.tileid] = r.text
      except requests.Timeout as ex:
        tiles[self.tileid] = ('"'*tile_w+'\n')*tile_h
      except BaseException as ex:
        print(self.target,'died',ex)
        tiles[self.tileid] = ('"'*tile_w+'\n')*tile_h
        return
      if time.time() < deadline:
        time.sleep(deadline-time.time())


class TickController(threading.Thread):
  def __init__(self):
    super().__init__()
  def run(self):
    global deadline
    while True:
      with speed_cv:
        while tick_delay <= 0:
          speed_cv.wait()
        deadline = time.time() + tick_delay
        speed_cv.notify_all()
      time.sleep(tick_delay)

controller = TickController() # make a controlling thread
controller.daemon = True # set it to run in the background
controller.start() # start it running




def disconnect_if_killed():
  """A special atexit callback to ensure servers are stopped if middleware exists"""
  if live_servers:
    print('shutting down gracefully by sending /stop to',len(live_servers),'servers')
  for tidx in tuple(live_servers):
    try: requests.get(live_servers[tidx]+'/stop')
    except: pass
    del live_servers[tidx]
import atexit
atexit.register(disconnect_if_killed)






if __name__ == '__main__':
  app.run(host="0.0.0.0", port=MY_PORT)
