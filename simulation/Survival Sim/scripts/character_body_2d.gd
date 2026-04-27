extends CharacterBody2D

#@export var speed = 400.0
#
#func _physics_process(delta):
	## This captures 8-way movement (WASD/Arrows) and normalizes it
	## so diagonal movement isn't faster than straight movement.
	#var direction = Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
	#
	#if direction:
		#velocity = direction * speed
	#else:
		## Stop smoothly when no input is detected
		#velocity = velocity.move_toward(Vector2.ZERO, speed)
#
	## move_and_slide() uses the 'velocity' property to handle collisions automatically
	#move_and_slide()
	#print("Velocity: ", velocity, " | Position: ", global_position)
	
#
var socket = StreamPeerTCP.new()
var server_address = "127.0.0.1"
var server_port = 9999

var stats = {"energy": 100, "integrity": 100, "action": "WAITING"}

# Timer logic to avoid spamming the Python server
var tick_rate = 0.1 # 10 times per second
var tick_timer = 0.0

func _ready():
	var err = socket.connect_to_host(server_address, server_port)
	if err != OK:
		print("Attempting to connect to Brain Server...")

func _process(delta):
	socket.poll()
	var state = socket.get_status()
	
	if state == StreamPeerTCP.STATUS_CONNECTED:
		# --- PHASE 1: SEND DATA (Timed) ---
		tick_timer += delta
		if tick_timer >= tick_rate:
			tick_timer = 0.0
			send_world_state()
		
		# --- PHASE 2: RECEIVE DATA ---
		receive_brain_decisions()
	
	elif state == StreamPeerTCP.STATUS_ERROR or state == StreamPeerTCP.STATUS_NONE:
		# Basic auto-reconnect logic
		socket.connect_to_host(server_address, server_port)

func send_world_state():
	# Gather current data (Update these variables as you add Area2Ds)
	var sensory_input = {
		"hazard": 0.0, 
		"food": 0.0
	}
	
	# Pack and send with newline delimiter
	var packet = JSON.stringify(sensory_input) + "\n"
	socket.put_data(packet.to_utf8_buffer())

func receive_brain_decisions():
	var available_bytes = socket.get_available_bytes()
	if available_bytes > 0:
		var raw_data = socket.get_utf8_string(available_bytes)
		var messages = raw_data.split("\n", false)
		
		for msg in messages:
			var json = JSON.new()
			var error = json.parse(msg)
			if error == OK:
				stats = json.get_data()
				execute_decision(stats["action"])
			else:
				print("JSON Parse Error: ", json.get_error_message(), " in: ", msg)

func execute_decision(action):
	var speed = 150
	velocity = Vector2.ZERO
	
	match action:
		"FORAGE":
			velocity = Vector2(speed, 0) 
		"HIDE":
			velocity = Vector2(-speed, 0)
		"REST":
			velocity = Vector2.ZERO
		"WANDER":
			velocity = Vector2(0, speed)
	move_and_slide()
	if velocity != Vector2.ZERO:
		print("Action: ", action, " | Pos: ", global_position)
