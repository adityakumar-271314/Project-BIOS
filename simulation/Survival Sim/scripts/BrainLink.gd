extends Node

var socket = StreamPeerTCP.new()
var tick_rate = 0.016
var tick_timer = 0.0

@onready var body = $"../BodySurround"
@onready var agent = get_parent()
@onready var ui = get_node("../CanvasLayer")

func _process(delta):
	socket.poll()
	var state = socket.get_status()
	
	if state == StreamPeerTCP.STATUS_CONNECTED:
		tick_timer += delta
		if tick_timer >= tick_rate:
			tick_timer = 0.0
			_send_to_python()
		_receive_from_python()
	elif state != StreamPeerTCP.STATUS_CONNECTING:
		socket.connect_to_host("127.0.0.1", 9999)

func _send_to_python():
	var packet = agent.get_sensory_data()
	
	var hazard_stim = 0.0
	var food_stim = 0.0
	
	# Detect EVERYTHING touching the agent's physical body
	var touch_zones = body.get_overlapping_areas()
	touch_zones.append_array(body.get_overlapping_bodies())
	
	for thing in touch_zones:
		# 1. HAZARD LOGIC
		if thing.is_in_group("hazard") or thing.get_parent().is_in_group("hazard"):
			if thing.has_method("get_intensity"):
				hazard_stim = thing.get_intensity(agent.global_position)
			elif thing.get_parent().has_method("get_intensity"):
				hazard_stim = thing.get_parent().get_intensity(agent.global_position)
			else:
				hazard_stim = 0.8 # Fallback damage
	
		# 2. FOOD LOGIC (Checks parent and self for properties)
		if thing.is_in_group("food") or thing.get_parent().is_in_group("food"):
			# Check for energy_value on the object or its parent
			if "energy_value" in thing:
				food_stim = thing.energy_value
			elif "energy_value" in thing.get_parent():
				food_stim = thing.get_parent().energy_value
			else:
				food_stim = 20.0
			
			# Delete the food (and its parent if it's a sub-area)
			if thing.get_parent().is_in_group("food") and thing.get_parent() != get_tree().root:
				thing.get_parent().queue_free()
			else:
				thing.queue_free()
	
	packet["hazard_stim"] = hazard_stim
	packet["food_stim"] = food_stim
	
	socket.put_data((JSON.stringify(packet) + "\n").to_utf8_buffer())
	
func _receive_from_python():
	while socket.get_available_bytes() > 0:
		var raw = socket.get_utf8_string(socket.get_available_bytes())
		var messages = raw.split("\n", false)
		for msg in messages:
			var json = JSON.new()
			if json.parse(msg) == OK:
				var data = json.get_data()
				ui.update_display(data)
				
				# Check if agent is deceased first
				if data.get("action") == "DECEASED" or data.get("alive") == false:
					set_process(false) # Stop the brain link
				else:
					agent.execute_move(data)
