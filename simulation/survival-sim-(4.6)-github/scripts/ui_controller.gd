extends Node

@onready var hud = $"../MainHUD"
@onready var graph = $"../EmotionGraph"
@onready var minimap = $"../MiniMap"
@onready var sub_viewport: SubViewport = $"../MiniMap/PanelContainer/SubViewportContainer/SubViewport"
@onready var minimap_camera: Camera2D = $"../MiniMap/PanelContainer/SubViewportContainer/SubViewport/MiniMapCamera2D"

var agent_node: CharacterBody2D = null

const WORLD_LEFT: float = 0.0
const WORLD_TOP: float = 0.0
const WORLD_RIGHT: float = 1152.0   
const WORLD_BOTTOM: float = 648.0  


func fit_camera_to_world(): 
	var viewport_size = sub_viewport.size 
	var world_size = Vector2( WORLD_RIGHT - WORLD_LEFT, WORLD_BOTTOM - WORLD_TOP )
	var zoom_value = viewport_size.x / world_size.x 
	minimap_camera.zoom = Vector2(zoom_value, zoom_value)

func _process(_delta: float) -> void:
	if not is_instance_valid(agent_node):
		agent_node = _find_agent_by_class(get_tree().root)
		if agent_node:
			sub_viewport.world_2d = agent_node.get_world_2d()
			sub_viewport.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
			if is_instance_valid(minimap_camera):
				minimap_camera.zoom = Vector2(0.222222, 0.222222)
		return

	if is_instance_valid(minimap_camera) and is_instance_valid(agent_node):
		# 1. Start with the agent's real-time position
		var target_pos: Vector2 = agent_node.global_position
		var viewport_size = sub_viewport.size
		# 2. Calculate how much of the world the camera lens actually sees based on its 0.2 zoom factor
		# Viewport size (256) divided by zoom (0.2) = 1280 world pixels wide visible. Divide by 2 for the padding radius.
		var half_view_width: float = (viewport_size.x / minimap_camera.zoom.x ) / 2.0
		var half_view_height: float = ( viewport_size.y / minimap_camera.zoom.y ) / 2.0
		
		# 3. Clamp camera positions so the lens stops moving before it peaks past the boundary edges
		target_pos.x = clamp(target_pos.x, WORLD_LEFT + half_view_width, WORLD_RIGHT - half_view_width)
		target_pos.y = clamp(target_pos.y, WORLD_TOP + half_view_height, WORLD_BOTTOM - half_view_height)
		
		# 4. Snap the camera safely to the clamped boundary coordinates
		minimap_camera.global_position = target_pos

# Recursive search utility remains identical
func _find_agent_by_class(root_node: Node) -> CharacterBody2D:
	if root_node is CharacterBody2D:
		return root_node
	for i in range(root_node.get_child_count()):
		var result = _find_agent_by_class(root_node.get_child(i))
		if result:
			return result
	return null
	
func _input(event):
	# TAB = Main HUD
	if event.is_action_pressed("toggle_hud"):
		hud.visible = !hud.visible

	 #G = Graph
	if event.is_action_pressed("toggle_graph"):
		graph.visible = !graph.visible

	# M = Minimap
	if event.is_action_pressed("toggle_minimap"):
		minimap.visible = !minimap.visible

	## E = Episodic Memory
	#if event.is_action_pressed("toggle_memory"):
		#memory.visible = !memory.visible
