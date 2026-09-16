extends Node2D

var brain_link = null
var memories = []
var memories_visible = true

var simulation_origin = Vector2(
	576,
	324
)


func _ready():

	brain_link = get_tree().get_first_node_in_group(
        "brain_link"
	)
	add_to_group("episodic_renderer")

func toggle_memories():
	memories_visible = !memories_visible
	queue_redraw()
	
func _process(_delta):

	if brain_link == null:
		return

	var new_memories = brain_link.episodic_memories
	
	if new_memories.size() != memories.size():
		memories = new_memories.duplicate(true)
		queue_redraw()


func _draw():
	if not memories_visible:
		return

	for memory in memories:

		if not ("peak_x" and "peak_y" in memory):
			continue

		#var pos_data = memory["peak_position"]

		var pos = simulation_origin + Vector2(
			memory.get("peak_x", 0.0),
			-memory.get("peak_y", 0.0)
		)

		var event_type = memory.get(
			"event_type",
            "unknown"
		)

		var significance = float(memory.get("peak_significance", 1.0))

		var color = _get_memory_color(
			event_type
		)

		# Opaque
		color.a = clamp(
			significance / 10.0,
			0.25,
			0.9
		)

		var radius = clamp(
			significance * 1.5,
			6.0,
			30.0
		)

		draw_circle(
			pos,
			radius,
			color
		)


func _get_memory_color(event_type: String) -> Color:

	match event_type:

		"food_recovery":
			return Color.GREEN

		"damage_spike":
			return Color.RED

		"near_death":
			return Color(0.5, 0.0, 0.0)

		"critical_starvation":
			return Color.YELLOW

		"danger_state":
			return Color.ORANGE

		_:
			return Color.WHITE
