extends Node2D
## Aphelios in Godot: una mesh sola (il disegno approvato) mossa da uno scheletro 2D con pesi fusi.
## Gli occhi sono i buchi veri del disegno: seguono l'osso della testa con la prospettiva a sfera
## approvata (l'occhio vicino cresce, quello lontano si abbassa) e crescono come espressione.
## Stati: idle, petting, look, wow, angry, sleep, hi. API: set_state(nome), S (parametri).

@onready var skel: Skeleton2D = $Skeleton2D
@onready var corpo: Polygon2D = $Corpo
@onready var eye_l: Sprite2D = $Corpo/OcchioSx
@onready var eye_r: Sprite2D = $Corpo/OcchioDx
var B := {}                       # ossa per nome
var REST := {}                    # trasformazione di riposo di ogni osso (locale)
var META := {}
var EYES := {}                    # texture degli occhi per espressione: nome -> [sx, dx]
var eye_base_scale := [Vector2.ONE, Vector2.ONE]

# parametri del rig (come nel rig 2D in pagina): il cervello e gli stati muovono questi
var S := {
	"look_x": 0.0, "look_y": 0.0, "eye": 1.0, "near": 0.0, "body": 0.0, "head_rot": 0.0, "head_y": 0.0,
	"blink": 1.0, "ears": 0.0, "ear_l": 0.0, "ear_r": 0.0, "eye_l": 1.0, "eye_r": 1.0, "pop": 1.0,
	"arm_l": 0.0, "arm_r": 0.0, "elb_l": 0.0, "elb_r": 0.0, "lean": 0.0, "squash": 0.0, "jump": 0.0,
}
var state := ""
var tw: Tween
var loop_tw: Tween
var t_idle := 0.0
var blink_t := 2.0
var glance_t := 6.0
var ear_t := 4.0
var hover := false
# molla delle orecchie: seguono la testa con un po' di ritardo (movimento secondario)
var ear_ang := [0.0, 0.0]
var ear_vel := [0.0, 0.0]
var last_head_rot := 0.0
# cattura fotogrammi per la verifica: --shots=cartella --state=nome
var shots_dir := ""
var shots_at := [0.4, 1.0, 1.6, 2.4, 3.2]
var shots_i := 0
var t_run := 0.0
var R := 272.0
var PHI := 0.5
var EYE_DY := 0.0
var EYE_W := 172.0

func _ready() -> void:
	META = JSON.parse_string(FileAccess.get_file_as_string("res://meta.json"))
	for b in skel.get_children():
		_collect(b)
	R = float(META["headW"]) / 2.0
	var e0 = META["eyes"][0]; var e1 = META["eyes"][1]
	var eye_dx: float = (float(e1["cx"]) - float(e0["cx"])) / 2.0
	PHI = asin(eye_dx / R)
	EYE_DY = float(e0["cy"]) - float(META["chin"])
	eye_base_scale = [eye_l.scale, eye_r.scale]
	EYE_W = eye_l.texture.get_width() * eye_l.scale.x
	_load_eyes()
	set_eyes("neutro")
	var args := OS.get_cmdline_user_args()
	var st := "idle"
	for a in args:
		if a.begins_with("--shots="): shots_dir = a.substr(8)
		if a.begins_with("--state="): st = a.substr(8)
	set_state(st)

func _collect(b: Node) -> void:
	if b is Bone2D:
		B[b.name] = b
		REST[b.name] = b.transform
	for c in b.get_children():
		_collect(c)

func _load_eyes() -> void:
	# occhio neutro = i buchi del disegno; le espressioni dal set approvato (bianche su trasparente)
	EYES["neutro"] = [eye_l.texture, eye_r.texture]
	for n in ["cuori", "tondi", "arrabbiato", "dorme", "spirali", "triste", "contento", "diffidente"]:
		var l := "res://tex/occhio-%s-sx.png" % n
		var r := "res://tex/occhio-%s-dx.png" % n
		if ResourceLoader.exists(l) and ResourceLoader.exists(r):
			EYES[n] = [load(l), load(r)]

var eye_name := ""
func set_eyes(n: String) -> void:
	if not EYES.has(n) or eye_name == n: return
	eye_name = n
	var w0: float = EYE_W   # larghezza dell'occhio base nella scena
	for i in 2:
		var spr: Sprite2D = [eye_l, eye_r][i]
		var t: Texture2D = EYES[n][i]
		spr.texture = t
		if n == "neutro":
			spr.scale = eye_base_scale[i]
		else:
			var k := (w0 * 1.05) / t.get_width()
			spr.scale = Vector2(k, k)
	eye_base_scale_cur = [eye_l.scale, eye_r.scale]
var eye_base_scale_cur := [Vector2.ONE, Vector2.ONE]

func _bone(n: String, rot_deg: float, sc: Vector2 = Vector2.ONE, off: Vector2 = Vector2.ZERO) -> void:
	var b: Bone2D = B[n]
	var r: Transform2D = REST[n]
	b.position = r.origin + off
	b.rotation = deg_to_rad(rot_deg)
	b.scale = sc

func _process(dt: float) -> void:
	t_run += dt
	_secondary(dt)
	_apply()
	_auto(dt)
	_shots()

func _secondary(dt: float) -> void:
	# le orecchie seguono la rotazione della testa con una molla (ritardo e rimbalzo)
	var dv: float = (float(S["head_rot"]) - last_head_rot) / max(dt, 0.001)
	last_head_rot = float(S["head_rot"])
	for i in 2:
		var target: float = (float(S["ears"]) * 14.0 + float(S["ear_l"] if i == 0 else S["ear_r"])) * (1.0 if i == 0 else -1.0)
		var acc: float = (target - ear_ang[i]) * 140.0 - ear_vel[i] * 14.0 - dv * 0.12 * (1.0 if i == 0 else -1.0)
		ear_vel[i] += acc * dt
		ear_ang[i] += ear_vel[i] * dt

func _apply() -> void:
	var th: float = float(S["look_x"]) * 0.62
	var ps: float = float(S["look_y"]) * 0.35
	var sin_t := sin(th)
	var bob: float = float(S["body"]) * -10.0
	var zoom: float = 1.0 + float(S["near"]) * 0.14
	var hx: float = R * sin_t * 0.28
	var hy: float = float(S["look_y"]) * 10.0 + float(S["head_y"]) + float(S["near"]) * 26.0
	var rot: float = float(S["head_rot"]) + float(S["ears"]) * 2.0 + float(S["look_x"]) * 3.0
	var sq: float = float(S["squash"])
	# radice: respiro e squash & stretch di tutto il corpo (i piedi restano a terra: la radice sta alle anche)
	_bone("root", 0.0, Vector2(1.0 + sq * 0.5, 1.0 - sq), Vector2(0, bob * 0.6 - float(S["jump"])))
	_bone("spine", float(S["lean"]), Vector2(1.0 + float(S["body"]) * 0.02, 1.0 - float(S["body"]) * 0.04), Vector2(hx * 0.25, bob * 0.4))
	_bone("neck", rot * 0.35, Vector2.ONE, Vector2(hx * 0.3, 0))
	_bone("head", rot * 0.65, Vector2((1.0 - 0.09 * abs(sin_t)) * zoom, (1.0 - float(S["body"]) * 0.03) * zoom), Vector2(hx * 0.45, hy))
	_bone("earL", ear_ang[0]); _bone("earR", ear_ang[1])
	_bone("upperL", float(S["arm_l"])); _bone("foreL", float(S["elb_l"]))
	_bone("upperR", -float(S["arm_r"])); _bone("foreR", -float(S["elb_r"]))
	_bone("legL", 0.0, Vector2(1.0, 1.0 - float(S["body"]) * 0.06)); _bone("legR", 0.0, Vector2(1.0, 1.0 - float(S["body"]) * 0.06))
	# occhi: sulla sfera della testa, nello spazio dell'osso della testa
	var head: Bone2D = B["head"]
	var xf: Transform2D = corpo.global_transform.affine_inverse() * head.global_transform
	for i in 2:
		var sg := -1.0 if i == 0 else 1.0
		var spr: Sprite2D = [eye_l, eye_r][i]
		var phi := sg * PHI
		var near := -sg * sin_t
		var depth := 1.0 + 0.28 * near
		var ex: float = R * sin(phi + th) + sg * max(0.0, float(S["eye"]) * depth - 1.0) * 90.0
		var wsc: float = clamp(cos(phi + th) / cos(phi), 0.3, 1.0)
		var ey: float = EYE_DY + R * 0.5 * sin(ps) + (-near * 44.0 if near < 0.0 else 0.0)
		var sc: float = float(S["eye"]) * depth * float(S["eye_l"] if i == 0 else S["eye_r"]) * float(S["pop"])
		# posizione nello spazio dell'osso testa (origine = mento), poi nello spazio del corpo
		var local := Vector2(ex, ey)
		spr.position = xf * local
		spr.rotation = xf.get_rotation()
		var bs: Vector2 = eye_base_scale_cur[i]
		spr.scale = Vector2(bs.x * sc * wsc * xf.get_scale().x, bs.y * sc * float(S["blink"]) * xf.get_scale().y)

# ---------------- stati ----------------
func _kill() -> void:
	if tw: tw.kill()
	if loop_tw: loop_tw.kill()

func _to(props: Dictionary, dur: float, ease := Tween.EASE_IN_OUT, trans := Tween.TRANS_SINE) -> Tween:
	var t := create_tween().set_parallel(true).set_ease(ease).set_trans(trans)
	for k in props:
		t.tween_property(self, "S:%s" % k, props[k], dur)
	return t

func _reset(dur := 0.25) -> void:
	_to({"look_x": 0.0, "look_y": 0.0, "near": 0.0, "eye": 1.0, "eye_l": 1.0, "eye_r": 1.0, "body": 0.0, "head_rot": 0.0,
		"head_y": 0.0, "ears": 0.0, "ear_l": 0.0, "ear_r": 0.0, "arm_l": 0.0, "arm_r": 0.0, "elb_l": 0.0, "elb_r": 0.0,
		"lean": 0.0, "squash": 0.0, "jump": 0.0, "blink": 1.0}, dur)

func set_state(n: String) -> void:
	_kill()
	state = n
	t_idle = 0.0
	match n:
		"idle":
			set_eyes("neutro"); _reset(0.4)
			loop_tw = create_tween().set_loops()
			loop_tw.tween_property(self, "S:body", 0.5, 1.4).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
			loop_tw.tween_property(self, "S:body", 0.0, 1.4).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
		"petting":
			set_eyes("cuori"); _reset(0.3)
			_to({"eye": 1.03, "ears": -0.35}, 0.3)
			loop_tw = create_tween().set_loops().set_parallel(true)
			loop_tw.tween_property(self, "S:head_rot", 5.0, 0.7).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
			loop_tw.tween_property(self, "S:body", 0.3, 0.7).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
			loop_tw.chain().tween_property(self, "S:head_rot", -5.0, 0.7).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
			loop_tw.tween_property(self, "S:body", 0.0, 0.7).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
		"look":
			set_eyes("neutro"); _reset(0.3)
			_to({"look_x": 0.85, "look_y": -0.2, "near": 0.4, "eye": 1.05, "ear_r": 14.0, "ear_l": -4.0, "head_rot": 6.0}, 0.6, Tween.EASE_OUT, Tween.TRANS_QUAD)
		"wow":
			set_eyes("tondi"); _reset(0.2)
			tw = create_tween()
			tw.tween_callback(func(): _to({"eye": 1.14, "near": 0.35, "body": -0.6, "ears": 1.0, "squash": -0.06}, 0.15, Tween.EASE_OUT, Tween.TRANS_BACK))
			tw.tween_interval(0.9)
			tw.tween_callback(func(): _to({"eye": 1.0, "near": 0.0, "body": 0.0, "ears": 0.0, "squash": 0.0}, 0.6, Tween.EASE_OUT, Tween.TRANS_ELASTIC))
			tw.tween_interval(0.7)
			tw.tween_callback(func(): set_state("idle"))
		"angry":
			set_eyes("arrabbiato"); _reset(0.2)
			tw = create_tween()
			tw.tween_callback(func(): _to({"eye": 0.92, "body": -0.3, "ears": -0.9, "squash": 0.05}, 0.2))
			tw.tween_interval(0.25)
			for i in 10:
				tw.tween_property(self, "S:head_rot", -3.0 if i % 2 == 0 else 3.0, 0.06)
			tw.tween_callback(func(): _to({"head_rot": 0.0, "body": 0.0, "eye": 1.0, "ears": 0.0, "squash": 0.0}, 0.3))
			tw.tween_interval(0.5)
			tw.tween_callback(func(): set_state("idle"))
		"sleep":
			set_eyes("dorme"); _reset(0.5)
			_to({"ears": -0.8, "head_rot": 4.0, "head_y": 10.0, "lean": 2.0}, 1.2)
			loop_tw = create_tween().set_loops()
			loop_tw.tween_property(self, "S:body", 0.8, 2.2).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
			loop_tw.tween_property(self, "S:body", 0.2, 2.2).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
		"hi":
			# saluto senza alzare il braccio (il braccio ruotato sulla mesh non e' il disegno): un salto felice
			# con squash & stretch, orecchie che scattano e occhi contenti
			set_eyes("contento" if EYES.has("contento") else "neutro"); _reset(0.2)
			tw = create_tween()
			tw.tween_callback(func(): _to({"squash": 0.10, "eye": 1.08}, 0.12, Tween.EASE_OUT, Tween.TRANS_QUAD))
			tw.tween_interval(0.12)
			tw.tween_callback(func(): _to({"squash": -0.08, "jump": 90.0, "head_y": -10.0, "body": -0.6, "ears": 1.0, "head_rot": -6.0}, 0.22, Tween.EASE_OUT, Tween.TRANS_QUAD))
			tw.tween_interval(0.22)
			tw.tween_callback(func(): _to({"squash": 0.08, "jump": 0.0, "head_y": 0.0, "body": 0.0, "head_rot": 4.0}, 0.2, Tween.EASE_IN, Tween.TRANS_QUAD))
			tw.tween_interval(0.2)
			tw.tween_callback(func(): _to({"squash": 0.0, "ears": 0.0, "head_rot": 0.0, "eye": 1.0}, 0.5, Tween.EASE_OUT, Tween.TRANS_ELASTIC))
			tw.tween_interval(1.0)
			tw.tween_callback(func(): set_state("idle"))
		_:
			set_state("idle")

func _auto(dt: float) -> void:
	# a riposo: sbatte le palpebre e ogni tanto guarda altrove
	if state in ["idle", "petting", "look"]:
		blink_t -= dt
		if blink_t <= 0.0:
			blink_t = 2.5 + randf() * 4.0
			var b := create_tween()
			b.tween_property(self, "S:blink", 0.08, 0.07)
			b.tween_property(self, "S:blink", 1.0, 0.09)
	if state == "idle" or state == "petting":
		ear_t -= dt
		if ear_t <= 0.0:
			ear_t = 5.0 + randf() * 9.0
			var k := "ear_l" if randf() < 0.5 else "ear_r"
			var a := (8.0 + randf() * 10.0) * (1.0 if randf() < 0.7 else -1.0)
			var e := create_tween()
			e.tween_property(self, "S:%s" % k, a, 0.12).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
			e.tween_property(self, "S:%s" % k, a * 0.4, 0.16)
			e.tween_interval(0.3)
			e.tween_property(self, "S:%s" % k, 0.0, 0.45).set_trans(Tween.TRANS_ELASTIC).set_ease(Tween.EASE_OUT)
	if state == "idle":
		t_idle += dt
		if t_idle > 45.0:
			set_state("sleep"); return
		glance_t -= dt
		if glance_t <= 0.0:
			glance_t = 6.0 + randf() * 8.0
			var x := (randf() * 2.0 - 1.0) * 0.9
			var y := (randf() * 2.0 - 1.0) * 0.5
			var g := create_tween()
			g.tween_callback(func(): _to({"look_x": x, "look_y": y}, 0.35, Tween.EASE_OUT, Tween.TRANS_QUAD))
			g.tween_interval(1.2 + randf())
			g.tween_callback(func(): _to({"look_x": 0.0, "look_y": 0.0}, 0.5))

func _shots() -> void:
	if shots_dir == "" or shots_i >= shots_at.size(): return
	if t_run >= float(shots_at[shots_i]):
		var img := get_viewport().get_texture().get_image()
		DirAccess.make_dir_recursive_absolute(shots_dir)
		img.save_png("%s/%s-%02d.png" % [shots_dir, state, shots_i])
		shots_i += 1
		if shots_i >= shots_at.size():
			get_tree().quit()

func _on_body(p: Vector2) -> bool:
	# il punto e' sul personaggio? (contorno della mesh, primi vertici del poligono)
	var n := corpo.polygon.size() - corpo.internal_vertex_count
	var outline := PackedVector2Array()
	for i in n: outline.append(corpo.polygon[i])
	return Geometry2D.is_point_in_polygon(corpo.to_local(p), outline)

func _unhandled_input(ev: InputEvent) -> void:
	if ev is InputEventKey and ev.pressed:
		var names := {KEY_1: "idle", KEY_2: "petting", KEY_3: "look", KEY_4: "wow", KEY_5: "angry", KEY_6: "sleep", KEY_7: "hi"}
		if names.has(ev.keycode): set_state(names[ev.keycode])
	if ev is InputEventMouseButton and ev.pressed:
		var on := _on_body(get_global_mouse_position())
		if ev.button_index == MOUSE_BUTTON_LEFT and on: set_state("wow")
		if ev.button_index == MOUSE_BUTTON_RIGHT and on: set_state("angry")
	if ev is InputEventMouseMotion and shots_dir == "":
		var on := _on_body(get_global_mouse_position())
		if on and state == "idle": set_state("petting")
		if not on and state == "petting": set_state("idle")
		if state == "sleep": set_state("idle")
		if state == "idle":
			var p := get_viewport().get_mouse_position()
			var vs := get_viewport().get_visible_rect().size
			var lx: float = clamp((p.x / vs.x - 0.5) * 2.0, -1.0, 1.0)
			var ly: float = clamp((p.y / vs.y - 0.5) * 2.0, -1.0, 1.0)
			S["look_x"] = lerp(float(S["look_x"]), lx, 0.2)
			S["look_y"] = lerp(float(S["look_y"]), ly, 0.2)
