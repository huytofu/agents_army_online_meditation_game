### Purpose

This is a feature in stealth-mode
It will soon appear on entourage-ai.life/online-meditation.html

What it is:
a) a multiplayer online game
b) open world format of a forest with variety of sceneries (waterfall, valley, big trees, strange faunna, river, moss plain...). 3D elements of scenery building block preferred
c) forest has thousands of spots throughout
d) player can have simple movement across forest (left,right,front,back). Can alternate between POV and 3rd-person view. 360 rotation camera to view forest elements and other players. Players can also lock on a forest spot to sit on it.
d) players cannot appear within 5 meters of one another. No contact, interaction or communication between players possible
e) each forest spot can be occupied by only 1 player at a time. First come first serve
f) what spot provides: first person POV static scenery, schenery elements can move slightly in predictable patterns + 1 audio player spot that can play any youtube video while sitting 

First phase architecture:
a) Postgres database
b) can access locally at port 8765 to play
c) simple 3D engine
d) No sound tied to scenery elements yet.

Focus:
a) Visuals is king! Arts and variety of scenery is the core offerings. Open-ended nature of the forest. Player customization + art + movement or activities are not as importat. Can be stick men with simple movements

## Run

```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
docker compose up -d
python -m uvicorn forest_server.app:app --host 127.0.0.1 --port 8765
```

On Linux, activate with `source .venv/bin/activate` instead. Open `http://127.0.0.1:8765/`.