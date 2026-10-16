extends Node3D
## Procedural prototype scene. Every interactive mesh carries a model port or device ID.
## Backend is authoritative; scene visuals refresh ONLY from returned backend state.

var api_url := "http://127.0.0.1:8765"
var state: Dictionary = {}
var token := ""
var http: HTTPRequest
var player: CharacterBody3D
var camera: Camera3D
var ui: Control
var notice: Label
var details: RichTextLabel
var prompt: Label
var terminal: LineEdit
var token_input: LineEdit
var ip_input: LineEdit
var pc_select: OptionButton
var checkpoint_select: OptionButton
var delete_dialog: ConfirmationDialog
var pending_delete_id := 0
var hud_scroll: ScrollContainer
var inspected_id := ""
var cable_mesh: MeshInstance3D
var repair_visual: MeshInstance3D
var port_visual: MeshInstance3D
var cli_output: RichTextLabel
var pending_cli := ""
var cli_lines: Array[String] = []
var ray_targets: Dictionary = {}
var cable_selected := false
var cable_port := ""
var busy := false
var cursor_locked := false
var vertical_speed := 0.0

func _ready() -> void:
	# Override is permitted only for local ephemeral-port integration tests; no remote token transport.
	var override := OS.get_environment("NETFORGE_API_URL")
	if override.begins_with("http://127.0.0.1:"):
		var port_text := override.trim_prefix("http://127.0.0.1:")
		if port_text.is_valid_int() and int(port_text) >= 1 and int(port_text) <= 65535 and str(int(port_text)) == port_text:
			api_url = override
	_build_world()
	_build_ui()
	http = HTTPRequest.new()
	add_child(http)
	http.request_completed.connect(_on_response)
	_set_notice("Start the Python bridge, paste its session token, then click Connect. Simulation only.")

func _box(name: String, pos: Vector3, size: Vector3, color: Color, interactive_id: String = "") -> MeshInstance3D:
	var mesh := MeshInstance3D.new()
	mesh.name = name
	# The headless display driver has only a dummy renderer: it cannot allocate a BoxMesh RID.
	# Keep real colliders and state/visible flags for integration tests; GUI builds create the geometry.
	if DisplayServer.get_name() != "headless":
		var shape := BoxMesh.new()
		shape.size = size
		mesh.mesh = shape
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	mesh.material_override = material
	mesh.position = pos
	add_child(mesh)
	if interactive_id != "":
		var body := StaticBody3D.new()
		body.position = pos
		var collider := CollisionShape3D.new()
		var box := BoxShape3D.new()
		box.size = size
		collider.shape = box
		body.add_child(collider)
		add_child(body)
		ray_targets[body.get_instance_id()] = interactive_id
	return mesh

func _build_world() -> void:
	_box("Floor", Vector3(0, -0.15, 0), Vector3(15, 0.3, 12), Color(0.16, 0.20, 0.24))
	var floor_body := StaticBody3D.new()
	floor_body.position.y = -0.15
	var floor_shape := CollisionShape3D.new()
	var floor_box := BoxShape3D.new()
	floor_box.size = Vector3(15, 0.3, 12)
	floor_shape.shape = floor_box
	floor_body.add_child(floor_shape)
	add_child(floor_body)
	_box("Rear wall", Vector3(0, 2, -6), Vector3(15, 4, 0.2), Color(0.18, 0.24, 0.29))
	_box("Desk", Vector3(0, 0.75, -3), Vector3(9, 0.15, 1.8), Color(0.29, 0.35, 0.39))
	_box("PC A monitor • 192.168.10.10", Vector3(-3.3, 1.45, -3.25), Vector3(1.4, 0.9, 0.25), Color(0.08, 0.53, 0.64), "pc-a")
	_box("PC B monitor • 192.168.10.11", Vector3(3.3, 1.45, -3.25), Vector3(1.4, 0.9, 0.25), Color(0.08, 0.53, 0.64), "pc-b")
	_box("Managed switch SW1", Vector3(0, 1.15, -3.4), Vector3(2.2, 0.36, 0.6), Color(0.14, 0.19, 0.22), "sw1")
	_box("Fa0/1", Vector3(-0.6, 1.19, -3.04), Vector3(0.22, 0.13, 0.09), Color(0.09, 0.72, 0.40), "sw1:fa0/1")
	port_visual = _box("Fa0/3 • repair target", Vector3(0.55, 1.19, -3.04), Vector3(0.28, 0.13, 0.09), Color(0.98, 0.48, 0.16), "sw1:fa0/3")
	cable_mesh = _box("Loose copper cable • pick up", Vector3(2.0, 0.88, -2.5), Vector3(0.9, 0.08, 0.15), Color(1.0, 0.55, 0.11), "cable")
	repair_visual = _box("PC B repair link", Vector3(1.8, 0.9, -3.0), Vector3(2.2, 0.035, 0.035), Color(0.2, 0.9, 0.3))
	repair_visual.visible = false
	_box("Router R1 • visual only", Vector3(-5.2, 1.1, -3.5), Vector3(0.9, 0.5, 0.55), Color(0.46, 0.40, 0.61), "router")
	var light := DirectionalLight3D.new()
	light.rotation_degrees = Vector3(-55, -35, 0)
	light.light_energy = 0.85
	add_child(light)
	var ambient := WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.08, 0.13, 0.18)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.8, 0.85, 1.0)
	ambient.environment = env
	add_child(ambient)
	player = CharacterBody3D.new()
	player.position = Vector3(0, 0.05, 3.2)
	var collider := CollisionShape3D.new()
	var capsule := CapsuleShape3D.new()
	capsule.radius = 0.32
	capsule.height = 1.7
	collider.position.y = 0.95
	collider.shape = capsule
	player.add_child(collider)
	add_child(player)
	camera = Camera3D.new()
	camera.position.y = 1.65
	camera.current = true
	player.add_child(camera)

func _button(parent: Node, text: String, callback: Callable) -> void:
	var button := Button.new()
	button.text = text
	button.pressed.connect(callback)
	parent.add_child(button)

func _build_ui() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)
	ui = Control.new()
	ui.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	ui.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layer.add_child(ui)
	var crosshair := Label.new()
	crosshair.text = "+"
	crosshair.add_theme_font_size_override("font_size", 24)
	crosshair.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	crosshair.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ui.add_child(crosshair)
	var scroll := ScrollContainer.new()
	scroll.position = Vector2(12, 12)
	scroll.size = Vector2(450, min(720, get_viewport().get_visible_rect().size.y - 24))
	hud_scroll = scroll
	get_viewport().size_changed.connect(_resize_hud)
	ui.add_child(scroll)
	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(425, 0)
	scroll.add_child(panel)
	var layout := VBoxContainer.new()
	panel.add_child(layout)
	var title := Label.new()
	title.text = "NETFORGE 3D  •  SIMULATED school lab"
	layout.add_child(title)
	token_input = LineEdit.new()
	token_input.placeholder_text = "Paste local bridge session token"
	token_input.secret = true
	layout.add_child(token_input)
	_button(layout, "Connect to local simulator", func(): token = token_input.text.strip_edges(); _request("GET", "/state"))
	prompt = Label.new()
	prompt.text = "WASD move  |  Mouse look  |  Click inspect  |  Esc release cursor"
	layout.add_child(prompt)
	_button(layout, "Capture mouse / resume exploration", func(): _capture(true))
	_button(layout, "Pick up / place cable: click orange cable, PC B, SW1 Fa0/3", func(): _set_notice("Click orange cable, then PC B, then switch Fa0/3."))
	_button(layout, "Disconnect PC B repair cable", func(): _action({"action":"disconnect", "port":"pc-b:eth0"}))
	_button(layout, "Simulated ping: PC B → PC A", func(): _action({"action":"ping", "source":"pc-b:eth0", "target":"pc-a:eth0"}))
	_button(layout, "Assess missions A + B", func(): _action({"action":"assess"}))
	_button(layout, "Save simulated lab checkpoint (SQLite required)", func(): _action({"action":"checkpoint"}))
	checkpoint_select = OptionButton.new()
	checkpoint_select.tooltip_text = "Select a saved simulated lab checkpoint (newest first)."
	layout.add_child(checkpoint_select)
	_button(layout, "Restore selected checkpoint (SQLite required)", _restore_latest)
	_button(layout, "Delete selected checkpoint (requires confirmation)", _ask_delete_checkpoint)
	delete_dialog = ConfirmationDialog.new()
	delete_dialog.title = "Delete simulated checkpoint?"
	delete_dialog.confirmed.connect(_delete_checkpoint)
	ui.add_child(delete_dialog)
	_button(layout, "Reset active lab (saved checkpoints remain)", func(): cable_selected = false; cable_port = ""; _action({"action":"reset"}))
	var ip_label := Label.new()
	ip_label.text = "Endpoint IPv4/CIDR (simulated, e.g. 192.168.10.11/24)"
	layout.add_child(ip_label)
	pc_select = OptionButton.new()
	pc_select.add_item("PC A · eth0")
	pc_select.add_item("PC B · eth0")
	pc_select.select(1)
	layout.add_child(pc_select)
	ip_input = LineEdit.new()
	ip_input.placeholder_text = "192.168.10.11/24"
	ip_input.max_length = 32
	layout.add_child(ip_input)
	_button(layout, "Apply modeled IPv4 address", _configure_ip)
	notice = Label.new()
	notice.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	notice.custom_minimum_size = Vector2(400, 45)
	layout.add_child(notice)
	details = RichTextLabel.new()
	details.custom_minimum_size = Vector2(400, 230)
	details.scroll_following = true
	layout.add_child(details)
	var cli_label := Label.new()
	cli_label.text = "SIMULATED switch CLI (not Cisco IOS) — enter command:"
	layout.add_child(cli_label)
	terminal = LineEdit.new()
	terminal.placeholder_text = "enable"
	terminal.text_submitted.connect(_submit_cli)
	layout.add_child(terminal)
	_button(layout, "Send switch command", func(): _submit_cli(terminal.text))
	cli_output = RichTextLabel.new()
	cli_output.custom_minimum_size = Vector2(400, 100)
	cli_output.scroll_following = true
	cli_output.text = "Simulated switch CLI output appears here."
	layout.add_child(cli_output)
	_resize_hud()

func _resize_hud() -> void:
	if hud_scroll == null:
		return
	var view := get_viewport().get_visible_rect().size
	hud_scroll.size = Vector2(min(450.0, max(280.0, view.x - 24.0)), max(180.0, view.y - 24.0))

func _configure_ip() -> void:
	var cidr := ip_input.text.strip_edges()
	if cidr == "":
		_set_notice("Enter an IPv4 address with prefix, for example 192.168.10.11/24.")
		return
	var port := "pc-a:eth0" if pc_select.selected == 0 else "pc-b:eth0"
	_action({"action":"ip", "port":port, "cidr":cidr})

func _set_notice(text: String) -> void:
	if notice != null:
		notice.text = text

func _capture(enabled: bool) -> void:
	cursor_locked = enabled
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED if enabled else Input.MOUSE_MODE_VISIBLE

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and event.keycode == KEY_ESCAPE:
		_capture(false)
	if not cursor_locked:
		return
	if event is InputEventMouseMotion:
		player.rotate_y(-event.relative.x * 0.002)
		camera.rotation.x = clamp(camera.rotation.x - event.relative.y * 0.002, -1.4, 1.4)
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and event.pressed:
		var from := camera.global_position
		var to := from - camera.global_transform.basis.z * 5.5
		var query := PhysicsRayQueryParameters3D.create(from, to)
		query.exclude = [player.get_rid()]
		var hit := get_world_3d().direct_space_state.intersect_ray(query)
		if not hit.is_empty():
			var id: String = ray_targets.get(hit.collider.get_instance_id(), "")
			_interact(id)

func _physics_process(delta: float) -> void:
	if player == null:
		return
	var input := Vector2.ZERO
	if cursor_locked:
		input = Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
		if Input.is_key_pressed(KEY_A): input.x -= 1
		if Input.is_key_pressed(KEY_D): input.x += 1
		if Input.is_key_pressed(KEY_W): input.y -= 1
		if Input.is_key_pressed(KEY_S): input.y += 1
	input = input.limit_length()
	var heading := player.global_transform.basis * Vector3(input.x, 0, input.y)
	player.velocity.x = heading.x * 3.5
	player.velocity.z = heading.z * 3.5
	player.velocity.y -= 16.0 * delta
	player.move_and_slide()

func _interact(id: String) -> void:
	if id == "cable":
		cable_selected = true
		cable_port = ""
		_set_notice("Copper cable picked up. Click PC B, then the orange SW1 Fa0/3 port.")
	elif id == "pc-b" and cable_selected:
		cable_port = "pc-b:eth0"
		_set_notice("PC B eth0 selected. Click SW1 Fa0/3 port to connect.")
	elif id == "sw1:fa0/3" and cable_port == "pc-b:eth0":
		cable_selected = false
		cable_port = ""
		_action({"action":"connect", "a":"pc-b:eth0", "b":"sw1:fa0/3", "media":"copper"})
	elif id == "sw1:fa0/3":
		_set_notice("SW1 Fa0/3: click cable then PC B then this port; CLI controls its security.")
	elif id == "router":
		_set_notice("Router R1 is VISUAL ONLY. No routing behavior is available yet.")
	elif id == "pc-a" or id == "pc-b":
		inspected_id = id
		_refresh()
		_set_notice(id + ": live interface status appears in the lab panel. Use Ping to test modeled connectivity.")
	elif id == "sw1" or id == "sw1:fa0/1":
		_set_notice("SW1 simulated switch. Release mouse (Esc) to type CLI commands.")
	else:
		_set_notice("No equipment selected. Aim at a device or cable within reach.")

func _submit_cli(line: String) -> void:
	if line.strip_edges() == "" or busy or token == "":
		_set_notice("Enter a command after connecting; wait for the previous action to finish.")
		return
	pending_cli = line
	_action({"action":"command", "device":"sw1", "line":line})
	terminal.clear()

func _selected_checkpoint_id() -> int:
	if checkpoint_select.selected < 0:
		return 0
	return int(checkpoint_select.get_item_metadata(checkpoint_select.selected))

func _restore_latest() -> void:
	var checkpoint_id := _selected_checkpoint_id()
	if checkpoint_id == 0:
		_set_notice("No saved checkpoint. Start the SQLite bridge and save one first.")
		return
	cable_selected = false
	cable_port = ""
	_action({"action":"restore", "checkpoint_id":checkpoint_id})

func _ask_delete_checkpoint() -> void:
	pending_delete_id = _selected_checkpoint_id()
	if pending_delete_id == 0:
		_set_notice("Select a saved checkpoint before deleting it.")
		return
	_capture(false)
	delete_dialog.dialog_text = "Permanently delete simulated checkpoint #" + str(pending_delete_id) + "? Active lab progress is unchanged."
	delete_dialog.popup_centered()

func _delete_checkpoint() -> void:
	if pending_delete_id > 0:
		_action({"action":"delete_checkpoint", "checkpoint_id":pending_delete_id})
	pending_delete_id = 0

func _action(payload: Dictionary) -> void:
	_request("POST", "/action", payload)

func _request(method: String, path: String, payload: Dictionary = {}) -> void:
	if token == "":
		_set_notice("Paste the local session token from the bridge terminal first.")
		return
	if busy:
		_set_notice("Waiting for simulator response. Try again in a moment.")
		return
	busy = true
	var body := JSON.stringify(payload) if method == "POST" else ""
	var headers := PackedStringArray(["X-NetForge-Token: " + token, "Content-Type: application/json"])
	var err := http.request(api_url + path, headers, HTTPClient.METHOD_POST if method == "POST" else HTTPClient.METHOD_GET, body)
	if err != OK:
		busy = false
		pending_cli = ""
		_set_notice("Could not reach local bridge. Start python -m backend.server: " + str(err))

func _on_response(result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	busy = false
	if result != HTTPRequest.RESULT_SUCCESS:
		pending_cli = ""
		_set_notice("Bridge unavailable. Is python -m backend.server running? Error " + str(result))
		return
	var parsed = JSON.parse_string(body.get_string_from_utf8())
	if not (parsed is Dictionary):
		pending_cli = ""
		_set_notice("Bridge returned invalid JSON")
		return
	if parsed.has("state"):
		state = parsed["state"]
		_refresh()
	if pending_cli != "":
		cli_lines.append("> " + pending_cli + "\n" + str(parsed.get("result", parsed.get("error", "No output"))))
		if cli_lines.size() > 20:
			cli_lines.pop_front()
		cli_output.text = "\n".join(cli_lines)
		pending_cli = ""
	if response_code != 200:
		_set_notice("Bridge error " + str(response_code) + ": " + str(parsed.get("error", "Unknown error")))
	else:
		_set_notice("SIMULATED: " + str(parsed.get("result", "Connected to local simulator")))

func _mission_lines(title: String, report: Dictionary) -> Array[String]:
	var lines: Array[String] = [title + ": " + ("COMPLETE" if report.get("complete", false) else "in progress") +
		" · " + str(report.get("score", 0)) + "/" + str(report.get("max_score", 0)) + " points"]
	var labels := {"cable_present":"Repair cable connected", "successful_ping_evidence":"Successful ping with valid path",
		"security_and_sticky_mac_learned":"Port security + sticky PC B MAC learned", "saved_configuration":"Current switch configuration saved"}
	var criteria: Dictionary = report.get("criteria", {})
	for key in criteria:
		lines.append(("  ✓ " if criteria[key] else "  ○ ") + str(labels.get(key, str(key).replace("_", " "))))
	if not report.get("prerequisites_met", true):
		lines.append("  Next: complete Mission A to unlock this mission.")
	elif not report.get("complete", false):
		if not report.get("cable", false):
			lines.append("  Next: click the loose cable → PC B → SW1 Fa0/3.")
		elif not report.get("ping_evidence", false):
			lines.append("  Next: ping PC A from PC B; inspect the modeled packet journal.")
		elif title == "MISSION B" and not report.get("sticky_mac_learned", false):
			lines.append("  Next: enable → configure terminal → interface fastethernet 0/3")
			lines.append("  Then: switchport port-security → switchport port-security mac-address sticky → end → ping.")
		elif title == "MISSION B" and not report.get("saved", false):
			lines.append("  Next: in privileged mode, enter write memory (saved in this simulated session).")
	return lines

func _refresh_checkpoints() -> void:
	if checkpoint_select == null:
		return
	var previous := _selected_checkpoint_id()
	checkpoint_select.clear()
	var checkpoints: Array = state.get("checkpoints", [])
	for checkpoint in checkpoints:
		var index := checkpoint_select.item_count
		checkpoint_select.add_item("#" + str(checkpoint["id"]) + " · " + str(checkpoint["created_at"]).substr(0, 19))
		checkpoint_select.set_item_metadata(index, checkpoint["id"])
		if previous == int(checkpoint["id"]):
			checkpoint_select.select(index)
	if checkpoint_select.item_count > 0 and checkpoint_select.selected < 0:
		checkpoint_select.select(0)

func _refresh() -> void:
	var ports: Dictionary = state.get("ports", {})
	var b: Dictionary = ports.get("pc-b:eth0", {})
	var sw: Dictionary = ports.get("sw1:fa0/3", {})
	var assessment: Dictionary = state.get("assessment", {})
	var a: Dictionary = assessment.get("mission_a", {})
	var mission_b: Dictionary = assessment.get("mission_b", {})
	var repaired: bool = b.get("linked", false)
	cable_mesh.visible = not repaired
	repair_visual.visible = repaired
	var port_material := port_visual.material_override as StandardMaterial3D
	port_material.albedo_color = Color(0.2, 0.9, 0.3) if repaired and sw.get("up", false) else Color(0.98, 0.48, 0.16)
	_refresh_checkpoints()
	var lines := _mission_lines("MISSION A", a)
	lines.append_array(_mission_lines("MISSION B", mission_b))
	lines.append("--- Live equipment / topology (SIMULATED) ---")
	for link in state.get("links", []):
		lines.append(str(link["a"]) + " ←copper→ " + str(link["b"]))
	lines.append("PC B eth0 linked: " + str(repaired) + " | SW1 Fa0/3 up: " + str(sw.get("up", false)))
	lines.append("Security: " + str(sw.get("security", false)) + " | Sticky: " + str(sw.get("sticky", false)))
	lines.append("Learned: " + str(sw.get("learned", [])) + " | Saved: " + str(state.get("saved", false)))
	lines.append("CLI mode: " + str(state.get("cli_mode", "user")) + " | Storage: " + str(state.get("storage", "memory")))
	lines.append("Checkpoints: " + str(state.get("checkpoints", []).size()))
	if inspected_id == "pc-a" or inspected_id == "pc-b":
		var endpoint: Dictionary = ports.get(inspected_id + ":eth0", {})
		lines.append("INSPECT " + inspected_id + ": " + str(endpoint.get("address", "unknown")) +
			" | MAC " + str(endpoint.get("mac", "unknown")) + " | link " + str(endpoint.get("linked", false)))
	lines.append("--- Modeled packet decisions (not a PCAP) ---")
	for entry in state.get("trace", []): lines.append(str(entry))
	lines.append("--- Latest audit events ---")
	var events: Array = state.get("events", [])
	for index in range(max(0, events.size() - 5), events.size()): lines.append(str(events[index]))
	details.text = "\n".join(lines)
