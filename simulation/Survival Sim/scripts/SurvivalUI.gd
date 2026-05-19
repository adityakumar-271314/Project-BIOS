extends CanvasLayer


var memory_renderer = null


func _ready():
	await get_tree().process_frame
	memory_renderer = get_tree().get_first_node_in_group(
		"episodic_renderer"
	)

# =========================
# PROGRESS BARS
# =========================

@onready var thrust_bar = $MainHUD/PanelContainer/VBoxContainer/GridContainer/ThrustBar

@onready var energy_bar = $MainHUD/PanelContainer/VBoxContainer/GridContainer/EnergyBar
@onready var integrity_bar = $MainHUD/PanelContainer/VBoxContainer/GridContainer/IntegrityBar

@onready var stress_bar = $MainHUD/PanelContainer/VBoxContainer/GridContainer/StressBar
@onready var fear_bar = $MainHUD/PanelContainer/VBoxContainer/GridContainer/FearBar
@onready var drive_bar = $MainHUD/PanelContainer/VBoxContainer/GridContainer/DriveBar

# =========================
# TEXT LABELS
# =========================

@onready var alive_value = $MainHUD/PanelContainer/VBoxContainer/AliveContainer/AliveValue
@onready var goal_value = $MainHUD/PanelContainer/VBoxContainer/GoalContainer/GoalValue

# Optional numeric labels
@onready var thrust_number = $MainHUD/PanelContainer/VBoxContainer/GridContainer/ThrustNumber
@onready var steer_number = $MainHUD/PanelContainer/VBoxContainer/GridContainer/SteerNumber

@onready var energy_number = $MainHUD/PanelContainer/VBoxContainer/GridContainer/EnergyNumber
@onready var integrity_number = $MainHUD/PanelContainer/VBoxContainer/GridContainer/IntegrityNumber

@onready var stress_number = $MainHUD/PanelContainer/VBoxContainer/GridContainer/StressNumber
@onready var fear_number = $MainHUD/PanelContainer/VBoxContainer/GridContainer/FearNumber
@onready var drive_number = $MainHUD/PanelContainer/VBoxContainer/GridContainer/DriveNumber

@onready var graph_renderer = $EmotionGraph/VBoxContainer/HBoxContainer/GraphRenderer
# =========================
# SMOOTHING
# =========================

var smooth_speed := 10.0

# Internal targets
var thrust_target := 0.0
var steer_target := 50.0

var energy_target := 0.0
var integrity_target := 0.0

var stress_target := 0.0
var fear_target := 0.0
var drive_target := 0.0


# =========================
# PROCESS
# =========================

func _process(delta):

	thrust_bar.value = lerp(
		thrust_bar.value,
		thrust_target,
		delta * smooth_speed
	)


	energy_bar.value = lerp(
		energy_bar.value,
		energy_target,
		delta * smooth_speed
	)

	integrity_bar.value = lerp(
		integrity_bar.value,
		integrity_target,
		delta * smooth_speed
	)

	stress_bar.value = lerp(
		stress_bar.value,
		stress_target,
		delta * smooth_speed
	)

	fear_bar.value = lerp(
		fear_bar.value,
		fear_target,
		delta * smooth_speed
	)

	drive_bar.value = lerp(
		drive_bar.value,
		drive_target,
		delta * smooth_speed
	)


# =========================
# MAIN UPDATE FUNCTION
# =========================

func update_display(data: Dictionary):

	#
	# THRUST
	# expected range:
	# 0.0 → 1.0
	#

	var thrust = float(data.get("thrust", 0.0))

	thrust_target = thrust * 100.0

	thrust_number.text = "%.2f" % thrust


#
	# STEER
	#

	var steer = float(data.get("steer", 0.0))

	steer_target = ((steer + 1.0) / 2.0) * 100.0

	steer_number.text = "%.2f" % steer


	#
	# ENERGY
	#

	var energy = float(data.get("energy", 0.0))

	energy_target = clamp(energy, 0.0, 100.0)

	energy_number.text = "%.1f" % energy


	#
	# INTEGRITY
	#

	var integrity = float(data.get("integrity", 0.0))

	integrity_target = clamp(integrity, 0.0, 100.0)

	integrity_number.text = "%.1f" % integrity


	#
	# STRESS
	#

	var stress = float(data.get("stress", 0.0))

	stress_target = clamp(stress * 100.0, 0.0, 100.0)

	stress_number.text = "%.2f" % stress


	#
	# FEAR
	#

	var fear = float(data.get("fear", 0.0))

	fear_target = clamp(fear * 100.0, 0.0, 100.0)

	fear_number.text = "%.2f" % fear


	#
	# DRIVE
	# expected:
	# 0 → 1
	#

	var drive = float(data.get("drive", 0.0))

	drive_target = drive * 100.0

	drive_number.text = "%.2f" % drive


	#
	# ALIVE STATE
	#

	var alive = data.get("alive", true)

	if alive:
		alive_value.text = "ACTIVE"
		alive_value.modulate = Color.GREEN
	else:
		alive_value.text = "DECEASED"
		alive_value.modulate = Color.RED


	#
	# GOAL
	#

	goal_value.text = str(
		data.get("current_goal", "Wander")
	)

	graph_renderer.add_values(stress, fear)

	#
	# CRITICAL WARNINGS
	#

	_update_warning_states()


# =========================
# WARNINGS
# =========================

func _update_warning_states():

	#
	# Integrity critical
	#

	if integrity_target < 20:
		integrity_bar.modulate = Color(1.0, 0.4, 0.4)
	else:
		integrity_bar.modulate = Color.WHITE


	#
	# Stress critical
	#

	if stress_target > 70:
		stress_bar.modulate = Color(1.0, 0.5, 0.5)
	else:
		stress_bar.modulate = Color.WHITE


	#
	# Fear critical
	#

	if fear_target > 65:
		fear_bar.modulate = Color(1.0, 0.3, 0.3)
	else:
		fear_bar.modulate = Color.WHITE
		


func _on_toggle_memories_button_pressed() -> void:
	if memory_renderer:
		memory_renderer.toggle_memories()
func _input(event): 
	if event.is_action_pressed( "toggle_memories", false, true ): 
		_on_toggle_memories_button_pressed()
