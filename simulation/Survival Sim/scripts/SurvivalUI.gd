extends CanvasLayer


@onready var energy_bar = $VBoxContainer/EnergyBar
@onready var integrity_bar = $VBoxContainer/IntegrityBar
@onready var motor_label = $VBoxContainer/MotorStatus
@onready var stress_label = $VBoxContainer/Stress

var memory_renderer = null


func _ready():
	await get_tree().process_frame
	memory_renderer = get_tree().get_first_node_in_group(
		"episodic_renderer"
	)
	
func update_display(data: Dictionary):
	energy_bar.value = data.get("energy", 0)
	integrity_bar.value = data.get("integrity", 0)
	
	# Display the raw motor vectors
	var t = snapped(data.get("thrust", 0.0), 0.01)
	var s = snapped(data.get("steer", 0.0), 0.01)
	motor_label.text = "THRUST: %s | STEER: %s" % [str(t), str(s)]
	
	stress_label.text = "STRESS: " + str(snapped(data.get("stress", 0), 0.01))
	
	# Visual feedback for critical states
	if data.get("alive") == false:
		motor_label.text = "STATUS: DECEASED"
		motor_label.add_theme_color_override("font_color", Color.RED)
		


func _on_toggle_memories_button_pressed() -> void:
	if memory_renderer:
		memory_renderer.toggle_memories()
