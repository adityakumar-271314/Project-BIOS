extends Node

var socket = StreamPeerTCP.new()
var tick_rate = 0.016
var tick_timer = 0.0

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
	var packet = agent.get_ray_data()
	# Add any extra world info here
	packet["food_nearby"] = 0 
	
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
