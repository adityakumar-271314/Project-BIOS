extends Node

var socket = StreamPeerTCP.new()

@onready var body = $"../BodySurround"
@onready var agent = get_parent()
@onready var ui = get_node("../CanvasLayer")

var waiting_for_brain = false
var episodic_memories = []

func _ready():
	add_to_group("brain_link")
	
func _physics_process(delta: float) -> void:
	socket.poll()
	var state = socket.get_status()
	
	if state == StreamPeerTCP.STATUS_CONNECTED:
		if not waiting_for_brain:
			_send_to_python()
			waiting_for_brain = true 
		
		_receive_from_python()
	elif state != StreamPeerTCP.STATUS_CONNECTING:
		socket.connect_to_host("127.0.0.1", 9999)

func _send_to_python():
	var packet = agent.get_sensory_data()

	# MUST reset every tick
	var hazard_stim := 0.0
	var food_stim := 0.0

	var touch_zones: Array = []
	touch_zones.assign(body.get_overlapping_areas())
	touch_zones.append_array(body.get_overlapping_bodies())

	for thing in touch_zones:
		if not is_instance_valid(thing):
			continue

		var parent = thing.get_parent()
		var parent_is_valid := is_instance_valid(parent)

		var is_food: bool = thing.is_in_group("food")
		var is_hazard: bool = thing.is_in_group("hazard")

		if parent_is_valid:
			is_food = is_food or parent.is_in_group("food")
			is_hazard = is_hazard or parent.is_in_group("hazard")

		var detected_type := "unknown"

		if is_hazard:
			detected_type = "hazard"
		elif is_food:
			detected_type = "food"

		print(
			"[TOUCH] object=",
			thing.name,
			" groups=",
			thing.get_groups(),
			" parent=",
			parent.name if parent_is_valid else "NULL",
			" parent_groups=",
			parent.get_groups() if parent_is_valid else [],
			" => type=",
			detected_type
		)

		# HAZARD
		if is_hazard:
			if thing.has_method("get_intensity"):
				hazard_stim = thing.get_intensity(agent.global_position)
			elif parent_is_valid and parent.has_method("get_intensity"):
				hazard_stim = parent.get_intensity(agent.global_position)
			else:
				hazard_stim = 0.8

		# FOOD
		elif is_food:
			if "energy_value" in thing:
				food_stim = thing.energy_value
			elif parent_is_valid and "energy_value" in parent:
				food_stim = parent.energy_value
			else:
				food_stim = 20.0

			var food_object: Node = thing

			if parent_is_valid and parent.is_in_group("food"):
				food_object = parent

			_consume_food(food_object)

	packet["hazard_stim"] = hazard_stim
	packet["food_stim"] = food_stim

	print(
		"[STIM] hazard=",
		hazard_stim,
		" food=",
		food_stim,
		" touch_count=",
		touch_zones.size()
	)

	socket.put_data((JSON.stringify(packet) + "\n").to_utf8_buffer())
	
func _receive_from_python():
	while socket.get_available_bytes() > 0:
		var raw = socket.get_utf8_string(socket.get_available_bytes())
		var messages = raw.split("\n", false)
		for msg in messages:
			var json = JSON.new()
			if json.parse(msg) == OK:
				var data = json.get_data()
				if data.has("new_memories") and data["new_memories"] is Array:
					for short_mem in data["new_memories"]:
						episodic_memories.append(short_mem)
				if data.get("type") == "INIT":
					#var world = get_node("../../WorldGenerator")
					#var seed_val = data.get("world_seed", 42) 
					#world.initialize_world(seed_val)
					_handle_init(data)
					continue
				waiting_for_brain = false # We got our answer, allowed to send again
				ui.update_display(data)
				
				# Check if agent is deceased first
				if data.get("action") == "DECEASED" or data.get("alive") == false:
					set_process(false) # Stop the brain link
				else:
					agent.execute_move(data)

func _consume_food(food_object: Node) -> void:
	if not is_instance_valid(food_object):
		print("[FOOD] Already invalid / already consumed")
		return

	var food_id = food_object.get_meta("unique_id", -1)

	print(
		"[FOOD] CONSUMING name=",
		food_object.name,
		" id=",
		food_id,
		" groups=",
		food_object.get_groups()
	)

	if food_id != -1:
		if not agent.consumed_food_ids.has(food_id):
			agent.consumed_food_ids.append(food_id)

	food_object.queue_free()

	print(
		"[FOOD] queue_free called. id=",
		food_id,
		" valid_before_free=",
		is_instance_valid(food_object)
	)
	
func _handle_init(data: Dictionary) -> void:
	var world = get_node("../../WorldGenerator")

	var world_seed: int = data.get("world_seed", 42)
	var continuation: bool = data.get("continuation", false)
	var consumed_food_ids: Array = data.get("consumed_food_ids", [])

	world.initialize_world(
		world_seed,
		continuation,
		consumed_food_ids
	)

	if continuation:
		_restore_agent_state(data.get("agent_state", {}))
		
func _restore_agent_state(state: Dictionary) -> void:
	if state.is_empty():
		return

	# Directly assign exact physical attributes saved from the last live sensors tick
	agent.global_position = Vector2(
		state.get("internal_pos_x", agent.global_position.x),
		state.get("internal_pos_y", agent.global_position.y)
	)

	agent.velocity = Vector2(
		state.get("internal_vel_x", 0.0),
		state.get("internal_vel_y", 0.0)
	)
	
	if state.has("rotation"):
		# Set direct match polarity as we are using the raw sensor value saved at shutdown
		agent.rotation = state.get("rotation", 0.0)
		
	# Pass tick reference downstream to UI layer rather than setting it on the agent body
	if state.has("tick_count") and ui.has_method("set_tick_display"):
		ui.set_tick_display(int(state["tick_count"]))
