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



# 1. UI Node References
@onready var energy_bar = $CanvasLayer/VBoxContainer/EnergyBar
@onready var integrity_bar = $CanvasLayer/VBoxContainer/IntegrityBar
@onready var action_label = $CanvasLayer/VBoxContainer/Action
@onready var stress_label = $CanvasLayer/VBoxContainer/Stress
@onready var energy_label = $CanvasLayer/VBoxContainer/EnergyBar/Energy
@onready var integrity_label = $CanvasLayer/VBoxContainer/IntegrityBar/Integrity

# 2. Connection Variables
var socket = StreamPeerTCP.new()
var server_address = "127.0.0.1"
var server_port = 9999

# 3. Local State
var stats = {"energy": 100, "integrity": 100, "action": "WAITING", "stress": 0.0}
var tick_rate = 0.1 
var tick_timer = 0.0

func _ready():
	socket.connect_to_host(server_address, server_port)

func _process(delta):
	socket.poll()
	var state = socket.get_status()
	
	if state == StreamPeerTCP.STATUS_CONNECTED:
		tick_timer += delta
		if tick_timer >= tick_rate:
			tick_timer = 0.0
			send_world_state()
		receive_brain_decisions()
	elif state != StreamPeerTCP.STATUS_CONNECTING:
		socket.connect_to_host(server_address, server_port)

func send_world_state():
	var sensory_input = {"hazard": 0.0, "food": 0.0}
	var packet = JSON.stringify(sensory_input) + "\n"
	socket.put_data(packet.to_utf8_buffer())

func receive_brain_decisions():
	# Use a while loop to ensure we clear the buffer if multiple packets arrived
	while socket.get_available_bytes() > 0:
		var raw_data = socket.get_utf8_string(socket.get_available_bytes())
		var messages = raw_data.split("\n", false)
		for msg in messages:
			var json = JSON.new()
			if json.parse(msg) == OK:
				stats = json.get_data()
				update_ui(stats) # Update visual bars/text
				execute_decision(stats["action"]) # Move the box

func update_ui(data):
	# Using 'data.get()' is safer—it won't crash if a key is missing
	energy_label.text = "Energy"
	integrity_label.text = "Integrity"
	energy_bar.value = data.get("energy", 0)
	integrity_bar.value = data.get("integrity", 0)
	
	action_label.text = "ACTION: " + str(data.get("action", "IDLE"))
	# snapped() rounds the float for readability
	stress_label.text = "STRESS: " + str(snapped(data.get("stress", 0), 0.01))
	
	# Visual Feedback
	if energy_bar.value < 30:
		energy_bar.modulate = Color(1, 0, 0) # Red
	else:
		energy_bar.modulate = Color(1, 1, 1) # White

func execute_decision(action):
	var speed = 150
	velocity = Vector2.ZERO
	
	match action:
		"FORAGE": velocity = Vector2(speed, 0) 
		"HIDE": velocity = Vector2(-speed, 0)
		"REST": velocity = Vector2.ZERO
		"WANDER": velocity = Vector2(0, speed)
		
	move_and_slide()
