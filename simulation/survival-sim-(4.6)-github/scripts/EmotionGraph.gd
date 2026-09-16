extends Control

var stress_history = []
var fear_history = []

const MAX_POINTS = 200

const GRAPH_PADDING_LEFT = 30
const GRAPH_PADDING_BOTTOM = 20
const GRAPH_PADDING_TOP = 10
const GRAPH_PADDING_RIGHT = 10


func add_values(stress, fear):
	stress_history.append(stress)
	fear_history.append(fear)

	if stress_history.size() > MAX_POINTS:
		stress_history.pop_front()

	if fear_history.size() > MAX_POINTS:
		fear_history.pop_front()

	queue_redraw()


func _draw():
	var graph_width = size.x - GRAPH_PADDING_LEFT - GRAPH_PADDING_RIGHT
	var graph_height = size.y - GRAPH_PADDING_TOP - GRAPH_PADDING_BOTTOM

	# GRID LINES
	for i in range(5):
		var y = GRAPH_PADDING_TOP + (graph_height / 4.0) * i
		draw_line(
			Vector2(GRAPH_PADDING_LEFT, y),
			Vector2(size.x - GRAPH_PADDING_RIGHT, y),
			Color(0.3, 0.3, 0.35, 0.5),
			1.0
		)

	# AXES
	draw_line(
		Vector2(GRAPH_PADDING_LEFT, GRAPH_PADDING_TOP),
		Vector2(GRAPH_PADDING_LEFT, size.y - GRAPH_PADDING_BOTTOM),
		Color.WHITE,
		2.0
	)

	draw_line(
		Vector2(GRAPH_PADDING_LEFT, size.y - GRAPH_PADDING_BOTTOM),
		Vector2(size.x - GRAPH_PADDING_RIGHT, size.y - GRAPH_PADDING_BOTTOM),
		Color.WHITE,
		2.0
	)

	# STRESS GRAPH (ORANGE)
	_draw_history(stress_history, Color.ORANGE, graph_width, graph_height)

	# FEAR GRAPH (RED)
	_draw_history(fear_history, Color.RED, graph_width, graph_height)


func _draw_history(history, color, graph_width, graph_height):
	if history.size() < 2:
		return

	var x_step = graph_width / float(MAX_POINTS - 1)
	
	# Shift drawing to the right side of the graph when array is not full
	var start_x_offset = GRAPH_PADDING_LEFT + (MAX_POINTS - history.size()) * x_step

	for i in range(history.size() - 1):
		var x1 = start_x_offset + i * x_step
		var y1 = GRAPH_PADDING_TOP + graph_height - (history[i] * graph_height)

		var x2 = start_x_offset + (i + 1) * x_step
		var y2 = GRAPH_PADDING_TOP + graph_height - (history[i + 1] * graph_height)

		draw_line(
			Vector2(x1, y1),
			Vector2(x2, y2),
			color,
			2.5,
			true # Anti-aliasing enabled for smoother lines
		)
