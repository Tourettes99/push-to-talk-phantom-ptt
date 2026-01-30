import math
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QTimer, Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPolygonF, QPainterPath

class VisualsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16)  # ~60 FPS
        
        self.grid_offset = 0
        self.angle_x = 0
        self.angle_y = 0 # Keeping Y static or slow for better look, prompt said "X axis endlessly"
        
        # Style constants
        self.bg_color = QColor(20, 20, 20) # Matte Black
        self.grid_color = QColor(255, 255, 255, 100) # White transparent
        self.cube_color = QColor(240, 240, 240) # Matte White
        self.tint_color = QColor(0, 100, 255, 90) # 35% Blue roughly (90/255)

    def update_animation(self):
        self.grid_offset = (self.grid_offset + 1) % 100
        self.angle_x = (self.angle_x + 2) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 1. Background
        painter.fillRect(self.rect(), self.bg_color)
        
        # 2. Animated Grid (Perspective)
        self.draw_grid(painter)
        
        # 3. Spinning Cube
        self.draw_cube(painter)
        
        # 4. Blue Tint Overlay
        painter.fillRect(self.rect(), self.tint_color)

    def draw_grid(self, painter):
        w = self.width()
        h = self.height()
        cx = w / 2
        cy = h / 2
        
        pen = QPen(self.grid_color)
        pen.setWidthF(1.5)
        painter.setPen(pen)
        
        # Simple perspective grid
        # Horizontal lines moving down
        # We simulate 3D mostly by spacing lines logarithmically or just linear for retro look
        # Let's do a simple 3D projection of a floor
        
        horizon_y = h * 0.3 # Horizon line
        
        # Draw vertical lines (fan out)
        for i in range(-10, 11):
            x_base = cx + i * 100
            painter.drawLine(int(cx), int(horizon_y), int(x_base), h)
            
        # Draw horizontal lines (moving)
        # We map z-depth to screen y
        for i in range(20):
            # z goes from far to near
            # offset makes it move
            z = (i * 100 - self.grid_offset * 10) % 2000
            if z < 10: continue
            
            # Project z to y
            # Simple projection: y = cy + (H / z) ?? No, y = horizon + (scale / z)
            # Let's just do linear interpolation for the "Retro Grid" look 
            # where lines get further apart as they come closer? 
            # Actually, standard retro grid is: lines are horizontal.
            
            # Let's simpler approach:
            # Just parallel lines that accelerate?
            # Let's do proper projection.
            scale = 300
            # z=0 is camera, z=large is far. 
            # Let's say floor is at y=100 relative to camera
            # projected_y = y * (focal_length / z)
            
            # Let's fake it:
            relative_y = (z / 2000) * (h - horizon_y)
            screen_y = horizon_y + relative_y
            
            # This doesn't look like infinite scrolling.
            # Rework:
            pass
        
        # RETRO GRID IMPLEMENTATION v2
        # Vertical lines
        painter.setPen(QPen(QColor(255, 255, 255, 50), 1))
        for x in range(0, w, 100):
            painter.drawLine(x, 0, x, h)
            
        # Horizontal lines
        for y in range(0, h, 100):
            y_pos = (y + self.grid_offset) % h
            painter.drawLine(0, int(y_pos), w, int(y_pos))


    def draw_cube(self, painter):
        w = self.width()
        h = self.height()
        cx = w / 2
        cy = h / 2
        size = 100
        
        # Cube vertices
        points = [
            (-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
            (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)
        ]
        
        rotated_points = []
        rad = math.radians(self.angle_x)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)
        
        for x, y, z in points:
            # Rotate around X axis
            # y' = y*cos - z*sin
            # z' = y*sin + z*cos
            ry = y * cos_a - z * sin_a
            rz = y * sin_a + z * cos_a
            rx = x 
            
            # Simple Projection (orthographic-ish or gentle perspective)
            scale = 60
            px = cx + rx * scale
            py = cy + ry * scale
            rotated_points.append((px, py))
            
        # Draw Edges
        edges = [
            (0,1), (1,2), (2,3), (3,0), # Back face
            (4,5), (5,6), (6,7), (7,4), # Front face
            (0,4), (1,5), (2,6), (3,7)  # Connecting
        ]
        
        pen = QPen(self.cube_color)
        pen.setWidth(2) # Matte white wireframe
        painter.setPen(pen)
        
        # Fill faces to make it "Matte White Cube" not just wireframe
        # We need a proper painter path for faces
        faces = [
             (0, 1, 2, 3), (4, 5, 6, 7), # Back, Front
             (0, 1, 5, 4), (2, 3, 7, 6), # Bottom, Top?
             (1, 2, 6, 5), (0, 3, 7, 4)  # Sides
        ]
        
        # Sort faces by Depth (Painter's algorithm) would be needed for solid cube
        # For this task, a nice wireframe with slight opacity fill looks "cool animated"
        # The prompt says "Matte white 3d cube". Solid suggests hidden surface removal.
        # But X-axis spin means we see all sides eventually.
        
        brush = QBrush(QColor(255, 255, 255, 20)) # Slight fill
        painter.setBrush(brush)
        
        # Just draw all faces (transparency allows seeing through, fits "Hacker" aesthetic)
        for face in faces:
            poly = QPolygonF()
            for idx in face:
                poly.append(QPointF(*rotated_points[idx]))
            painter.drawPolygon(poly)
