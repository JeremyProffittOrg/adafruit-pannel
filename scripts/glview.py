"""Headless STL renderer (moderngl). Millimetres, orthographic or perspective."""
from __future__ import annotations

import math
from pathlib import Path

import moderngl
import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
STL_DIR = ROOT / "cad" / "stl"

VS = """
#version 330
in vec3 in_vert;
in vec3 in_norm;
uniform mat4 u_mvp;
uniform mat4 u_model;
uniform mat3 u_nmat;
out vec3 v_world;
out vec3 v_norm;
void main() {
    vec4 w = u_model * vec4(in_vert, 1.0);
    v_world = w.xyz;
    v_norm = normalize(u_nmat * in_norm);
    gl_Position = u_mvp * vec4(in_vert, 1.0);
}
"""

FS = """
#version 330
in vec3 v_world;
in vec3 v_norm;
uniform vec3 u_color;
uniform vec3 u_eye;
uniform vec3 u_light;
uniform float u_alpha;
out vec4 f_color;
void main() {
    vec3 n = normalize(v_norm);
    vec3 l = normalize(u_light - v_world);
    vec3 v = normalize(u_eye - v_world);
    vec3 h = normalize(l + v);
    float ndl = max(dot(n, l), 0.0);
    float spec = pow(max(dot(n, h), 0.0), 48.0);
    float rim = pow(1.0 - max(dot(n, v), 0.0), 3.0);
    vec3 ambient = u_color * 0.28;
    vec3 diffuse = u_color * ndl * 0.72;
    vec3 highlight = vec3(1.0) * spec * 0.22;
    vec3 rimc = vec3(0.55, 0.70, 0.90) * rim * 0.18;
    vec3 rgb = ambient + diffuse + highlight + rimc;
    f_color = vec4(rgb, u_alpha);
}
"""

GRID_VS = """
#version 330
in vec3 in_vert;
uniform mat4 u_mvp;
void main() { gl_Position = u_mvp * vec4(in_vert, 1.0); }
"""
GRID_FS = """
#version 330
uniform vec4 u_color;
out vec4 f_color;
void main() { f_color = u_color; }
"""

COLORS = {
    "strip": (0.18, 0.22, 0.28),
    "join": (0.45, 0.48, 0.52),
    "adapter": (0.82, 0.55, 0.16),
    "faceplate": (0.78, 0.82, 0.86),
    "standoff": (0.72, 0.58, 0.22),
    "board": (0.12, 0.45, 0.28),
}


def part_kind(name: str) -> str:
    if name.startswith("strip"):
        return "strip"
    if name.startswith("join"):
        return "join"
    if name.startswith("adapter"):
        return "adapter"
    if name.startswith("faceplate"):
        return "faceplate"
    return "strip"


def mat4_mul(a, b):
    return a @ b


def perspective(fovy_deg, aspect, near, far):
    f = 1.0 / math.tan(math.radians(fovy_deg) / 2.0)
    m = np.zeros((4, 4), np.float32)
    m[0, 0] = f / aspect
    m[1, 1] = f
    m[2, 2] = (far + near) / (near - far)
    m[2, 3] = (2 * far * near) / (near - far)
    m[3, 2] = -1.0
    return m


def ortho(l, r, b, t, n, f):
    m = np.zeros((4, 4), np.float32)
    m[0, 0] = 2 / (r - l)
    m[1, 1] = 2 / (t - b)
    m[2, 2] = -2 / (f - n)
    m[0, 3] = -(r + l) / (r - l)
    m[1, 3] = -(t + b) / (t - b)
    m[2, 3] = -(f + n) / (f - n)
    m[3, 3] = 1
    return m


def look_at(eye, target, up=(0, 0, 1)):
    eye = np.asarray(eye, np.float64)
    target = np.asarray(target, np.float64)
    up = np.asarray(up, np.float64)
    z = eye - target
    z = z / (np.linalg.norm(z) + 1e-12)
    x = np.cross(up, z)
    if np.linalg.norm(x) < 1e-8:
        up = np.array([0.0, 1.0, 0.0])
        x = np.cross(up, z)
        if np.linalg.norm(x) < 1e-8:
            up = np.array([1.0, 0.0, 0.0])
            x = np.cross(up, z)
    x = x / (np.linalg.norm(x) + 1e-12)
    y = np.cross(z, x)
    m = np.eye(4, dtype=np.float32)
    m[0, :3] = x
    m[1, :3] = y
    m[2, :3] = z
    t = np.eye(4, dtype=np.float32)
    t[:3, 3] = -eye
    return m @ t


def iso_eye(center, dist, yaw_deg=45.0, pitch_deg=35.264):
    yaw = math.radians(yaw_deg)
    pitch = math.radians(pitch_deg)
    x = dist * math.cos(pitch) * math.cos(yaw)
    y = dist * math.cos(pitch) * math.sin(yaw)
    z = dist * math.sin(pitch)
    return np.array(center, np.float64) + np.array([x, y, z])


def translate(x, y, z):
    m = np.eye(4, dtype=np.float32)
    m[0, 3] = x
    m[1, 3] = y
    m[2, 3] = z
    return m


def rotate_x(deg):
    a = math.radians(float(deg))
    c, s = math.cos(a), math.sin(a)
    m = np.eye(4, dtype=np.float32)
    m[1, 1] = c
    m[1, 2] = -s
    m[2, 1] = s
    m[2, 2] = c
    return m


def rotate_about(origin, rot):
    o = np.asarray(origin, np.float64)
    return translate(o[0], o[1], o[2]) @ rot @ translate(-o[0], -o[1], -o[2])


# Matches cad/case.scad: top_lid_print is rotate([180,0,0]) then
# translate([0, -case_d, -(BOTTOM_T+INNER_H+TOP_T)]) of the use pose.
PRINT_PITCH = 25.4
PRINT_WALL = 8.0
PRINT_ZOFF = 3.0 + 25.0 + 3.2  # BOTTOM_T + INNER_H + TOP_T


def lid_print_to_use(rows, lift=0.0):
    """Map the print-oriented lid STL onto the tray. lift>0 holds it above."""
    case_d = rows * PRINT_PITCH + 2 * PRINT_WALL
    return translate(0.0, 0.0, lift) @ translate(0.0, case_d, PRINT_ZOFF) @ rotate_x(180)


def lid_flip_animate(tb, bb, rows, angle, drop):
    """angle 0 = as printed (bosses up). 180 = posts down. drop 0..1 seats it."""
    hover = 52.0
    pc = (tb[0] + tb[1]) * 0.5
    bc = (bb[0] + bb[1]) * 0.5
    start = translate(bc[0] - pc[0], bc[1] - pc[1], bb[1][2] + hover - tb[0][2])
    start_c = np.array(
        [bc[0], bc[1], pc[2] + (bb[1][2] + hover - tb[0][2])],
        np.float64,
    )
    flipping = rotate_about(start_c, rotate_x(angle)) @ start
    seated = lid_print_to_use(rows, lift=0.0)
    t = 0.0 if drop < 0 else 1.0 if drop > 1 else drop
    return _lerp_mat(flipping, seated, t)


def _lerp_mat(a, b, t):
    t = 0.0 if t < 0 else 1.0 if t > 1 else t
    t = t * t * (3 - 2 * t)
    return (a * (1.0 - t) + b * t).astype(np.float32)


def scale(sx, sy, sz):
    m = np.eye(4, dtype=np.float32)
    m[0, 0] = sx
    m[1, 1] = sy
    m[2, 2] = sz
    return m


def load_mesh(path: Path):
    mesh = trimesh.load(path, force="mesh")
    if not isinstance(mesh, trimesh.Trimesh):
        mesh = trimesh.util.concatenate(tuple(mesh.geometry.values()))
    v = np.asarray(mesh.vertices, np.float32)
    f = np.asarray(mesh.faces, np.int32)
    tri = v[f]
    e1 = tri[:, 1] - tri[:, 0]
    e2 = tri[:, 2] - tri[:, 0]
    n = np.cross(e1, e2)
    ln = np.linalg.norm(n, axis=1, keepdims=True) + 1e-8
    n = n / ln
    verts = tri.reshape(-1, 3)
    norms = np.repeat(n, 3, axis=0).astype(np.float32)
    return verts, norms, mesh.bounds.copy()


def cylinder(radius, height, segments=20):
    th = np.linspace(0, 2 * math.pi, segments, endpoint=False)
    cx = radius * np.cos(th)
    cy = radius * np.sin(th)
    z0, z1 = 0.0, height
    verts = []
    norms = []
    # sides
    for i in range(segments):
        j = (i + 1) % segments
        p00 = [cx[i], cy[i], z0]
        p10 = [cx[j], cy[j], z0]
        p01 = [cx[i], cy[i], z1]
        p11 = [cx[j], cy[j], z1]
        n = [(cx[i] + cx[j]) * 0.5, (cy[i] + cy[j]) * 0.5, 0]
        n = np.array(n, np.float32)
        n = n / (np.linalg.norm(n) + 1e-8)
        for a, b, c in ((p00, p10, p11), (p00, p11, p01)):
            verts.extend([a, b, c])
            norms.extend([n, n, n])
    # caps
    for z, sign in ((z0, -1.0), (z1, 1.0)):
        n = np.array([0, 0, sign], np.float32)
        c = [0, 0, z]
        for i in range(segments):
            j = (i + 1) % segments
            a = [cx[i], cy[i], z]
            b = [cx[j], cy[j], z]
            if sign > 0:
                verts.extend([c, a, b])
            else:
                verts.extend([c, b, a])
            norms.extend([n, n, n])
    return np.asarray(verts, np.float32), np.asarray(norms, np.float32)


class Renderer:
    def __init__(self, width=1280, height=960, bg=(0.94, 0.95, 0.97)):
        self.w = width
        self.h = height
        self.bg = bg
        self.ctx = moderngl.create_standalone_context()
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.CULL_FACE)
        self.prog = self.ctx.program(vertex_shader=VS, fragment_shader=FS)
        self.gprog = self.ctx.program(vertex_shader=GRID_VS, fragment_shader=GRID_FS)
        color = self.ctx.texture((width, height), 4)
        depth = self.ctx.depth_texture((width, height))
        self.fbo = self.ctx.framebuffer(color_attachments=[color], depth_attachment=depth)
        self._vaos = {}
        self._bounds = {}

    def upload(self, name, verts, norms):
        buf = np.hstack([verts, norms]).astype(np.float32).tobytes()
        vbo = self.ctx.buffer(buf)
        vao = self.ctx.vertex_array(self.prog, [(vbo, "3f 3f", "in_vert", "in_norm")])
        self._vaos[name] = (vao, len(verts))

    def load_stl(self, name: str, path: Path):
        verts, norms, bounds = load_mesh(path)
        self.upload(name, verts, norms)
        self._bounds[name] = bounds
        return bounds

    def load_all_stls(self):
        for p in sorted(STL_DIR.glob("*.stl")):
            self.load_stl(p.stem, p)

    def _draw_item(self, name, model, color, eye, light, alpha=1.0):
        vao, nvert = self._vaos[name]
        nmat = np.linalg.inv(model[:3, :3]).T.astype(np.float32)
        self.prog["u_model"].write(model.T.tobytes())
        self.prog["u_nmat"].write(nmat.T.tobytes())
        mvp = self._proj @ self._view @ model
        self.prog["u_mvp"].write(mvp.T.tobytes())
        self.prog["u_color"].value = tuple(float(c) for c in color)
        self.prog["u_eye"].value = tuple(float(x) for x in eye)
        self.prog["u_light"].value = tuple(float(x) for x in light)
        self.prog["u_alpha"].value = float(alpha)
        if alpha < 0.999:
            self.ctx.enable(moderngl.BLEND)
            self.ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)
        vao.render(moderngl.TRIANGLES, vertices=nvert)
        if alpha < 0.999:
            self.ctx.disable(moderngl.BLEND)

    def begin(self, eye, target, ortho_span=None, fovy=28.0, near=1.0, far=800.0):
        self.fbo.use()
        self.ctx.viewport = (0, 0, self.w, self.h)
        self.ctx.clear(*self.bg, 1.0)
        aspect = self.w / self.h
        if ortho_span is not None:
            hspan = ortho_span
            wspan = hspan * aspect
            self._proj = ortho(-wspan, wspan, -hspan, hspan, near, far)
        else:
            self._proj = perspective(fovy, aspect, near, far)
        self._view = look_at(eye, target)
        self._eye = np.asarray(eye, np.float64)
        self._light = self._eye + np.array([40.0, -30.0, 80.0])

    def draw(self, name, model=None, color=None, alpha=1.0):
        if model is None:
            model = np.eye(4, dtype=np.float32)
        if color is None:
            color = COLORS[part_kind(name)]
        self._draw_item(name, model.astype(np.float32), color, self._eye, self._light, alpha)

    def draw_grid(self, nx=8, ny=8, pitch=25.4, z=-0.2):
        lines = []
        x0, y0 = -nx * pitch / 2, -ny * pitch / 2
        for i in range(nx + 1):
            x = x0 + i * pitch
            lines += [[x, y0, z], [x, y0 + ny * pitch, z]]
        for j in range(ny + 1):
            y = y0 + j * pitch
            lines += [[x0, y, z], [x0 + nx * pitch, y, z]]
        arr = np.asarray(lines, np.float32)
        vbo = self.ctx.buffer(arr.tobytes())
        vao = self.ctx.vertex_array(self.gprog, [(vbo, "3f", "in_vert")])
        mvp = self._proj @ self._view
        self.gprog["u_mvp"].write(mvp.T.tobytes())
        self.gprog["u_color"].value = (0.70, 0.74, 0.78, 1.0)
        self.ctx.line_width = 1.0
        vao.render(moderngl.LINES)

    def image(self) -> Image.Image:
        data = self.fbo.read(components=3)
        img = Image.frombytes("RGB", (self.w, self.h), data)
        return img.transpose(Image.FLIP_TOP_BOTTOM)


def caption(img: Image.Image, lines: list[str], footer: str = "") -> Image.Image:
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 22)
        small = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 16)
    except OSError:
        font = ImageFont.load_default()
        small = font
    y = 16
    for line in lines:
        draw.rectangle([12, y - 4, 12 + 8 + int(draw.textlength(line, font=font)), y + 26], fill=(255, 255, 255))
        draw.text((16, y), line, fill=(11, 15, 25), font=font)
        y += 28
    if footer:
        draw.rectangle([12, img.height - 36, img.width - 12, img.height - 10], fill=(15, 23, 42))
        draw.text((18, img.height - 32), footer, fill=(226, 232, 240), font=small)
    return img


def ensure_standoff(rnd: Renderer):
    if "standoff" in rnd._vaos:
        return
    v, n = cylinder(2.5, 12.0, 18)
    rnd.upload("standoff", v, n)
    rnd._bounds["standoff"] = np.array([[-2.5, -2.5, 0], [2.5, 2.5, 12]])
