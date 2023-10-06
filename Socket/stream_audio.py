import pyshine as ps
from websocket import create_connection
import json

audio,context = ps.audioCapture(mode='send')
ps.showPlot(context,name='pyshine.com')
ws = create_connection("ws://localhost:3000/websocket/stream")
while True:
  frame = audio.get()
  ws.send(json.dumps({"event": "stream", "data": frame}))