"""
pandastim/textures.py
Texture classes defined for display in ShowBase stimulus classes.

Part of pandastim package: https://github.com/mattdloring/pandastim

First defines the abstract base class, TextureBase. This defines the attributes
of the textures, but leaves `create_texture` undefined, to be implemented
in each subclass as a numpy array that looks how you want.

Component types (texture data types in panda3d):
https://www.panda3d.org/reference/python/classpanda3d_1_1core_1_1Texture.html#a81f78fc173dedefe5a049c0aa3eed2c0
"""

# TODO: need to create a flashing spots and looming texture - can probably just use the gray circle tex 
# TODO: add length/width parameters to the gratings texture 
# TODO: add ellipses texture (will probably be similar to gray circle tex, with adjustments for major/minor axes?)

try:
    import cv2
except Exception as e:
    # shortcut for making circles on some textures
    print("error importing cv2", e)
try:
    import matplotlib.pyplot as plt
except Exception as e:
    # need this to view the textures
    print("error import matplotlib", e)

import math
from abc import ABC, abstractmethod

import numpy as np
from panda3d.core import Texture

from pandastim import utils


class TextureBase(ABC):
    """
    Base texture class: subclass this for specific textures
    Requires implementation of create_texture and __str__
    """

    def __init__(self, texture_size=512, texture_name="texture"):
        """
        :param texture_size: tuple size for texture
        :param texture_name: name of given texture
        """

        if not hasattr(texture_size, "__iter__"):
            texture_size = texture_size, texture_size

        self.texture_size = texture_size
        self.texture_name = texture_name
        self.texture_array = self.create_texture()

        self.texture = Texture(self.texture_name)

        # Set texture formatting (greyscale or rgb have different settings)
        if self.texture_array.ndim == 2:
            self.texture.setup2dTexture(
                self.texture_size[0],
                self.texture_size[1],
                Texture.T_unsigned_byte,
                Texture.F_luminance,
            )
            self.texture.setRamImageAs(self.texture_array, "L")
        elif self.texture_array.ndim == 3:
            self.texture.setup2dTexture(
                self.texture_size[0],
                self.texture_size[1],
                Texture.T_unsigned_byte,
                Texture.F_rgb8,
            )
            self.texture.setRamImageAs(self.texture_array, "RGB")

    @abstractmethod
    def create_texture(self) -> None:
        """
        :return: returns a numpy array of given size
        """
        return None

    @abstractmethod
    def __str__(self):
        """
        Return the string you want print(Tex) to show, and to save to file
        when saving catalog of stimuli.
        """
        pass

    def view(self):
        """
        Plot the texture using matplotlib. Useful for debugging.
        """
        plt.imshow(self.texture_array, vmin=0, vmax=255)
        if self.texture_array.ndim == 2:
            plt.set_cmap("gray")
        plt.title(self.texture_name)
        plt.show()


class BlankTex(TextureBase):
    """
    Empty Texture
    """

    def __init__(self, texture_name="blank_tex", value=0, *args, **kwargs):
        self.value = value  # 0 : black textures, 255: white textures
        super().__init__(texture_name=texture_name, *args, **kwargs)

    def create_texture(self) -> np.array:
        tex = np.ones((self.texture_size[1], self.texture_size[0])) * self.value
        return np.uint8(tex)

    def __str__(self) -> str:
        return f"{type(self).__name__} size:{self.texture_size}"


class RgbTex(TextureBase):
    """
    full-field color
    """

    def __init__(self, color=(0, 255, 0), texture_name="rgb_field", *args, **kwargs):
        self.color = color
        super().__init__(texture_name=texture_name, *args, **kwargs)

    def create_texture(self) -> np.array:
        if not (
            all([x >= 0 for x in self.color]) and all([x <= 255 for x in self.color])
        ):
            raise ValueError("rgb values must lie in [0,255]")

        rgb_texture = np.zeros(
            (self.texture_size[0], self.texture_size[1], 3), dtype=np.uint8
        )

        for n, i in enumerate(self.color):
            rgb_texture[..., n] = i

        return rgb_texture

    def __str__(self) -> str:
        return f"{type(self).__name__} size:{self.texture_size} rgb:{self.color}"


class CircleGrayTex(TextureBase):
    """
    Filled circle: grayscale on grayscale with circle_radius, centered at circle_center
    with face color fg_intensity on background bg_intensity. Center position is in pixels
    from center of image.

    If frequency (number of circles) > 1, it will set up a grid and sample from a Gaussian distribution, 
    and evenly space out the points based on a self.spacing parameter. 
    """

    def __init__(
        self,
        frequency = 1,
        circle_center=(0, 0),
        circle_radius=100,
        spacing = 20,
        bg_intensity=0,
        fg_intensity=255,
        texture_name="gray_circle",
        *args,
        **kwargs,
    ):
        self.frequency = frequency
        self.circle_center = circle_center
        self.circle_radius = circle_radius
        self.spacing = spacing
        self.bg_intensity = bg_intensity
        self.fg_intensity = fg_intensity
        super().__init__(texture_name=texture_name, *args, **kwargs)

    def create_texture(self) -> np.array:
        if self.fg_intensity > 255 or self.bg_intensity < 0:
            raise ValueError("Circle intensity must lie in [0, 255]")
        
        x = np.linspace(
            0, self.texture_size[0], self.texture_size[0]
        )
        y = np.linspace(
            0, self.texture_size[1], self.texture_size[1]
        )
        X, Y = np.meshgrid(x, y)

        circle_texture = self.bg_intensity * np.ones(
            (self.texture_size[0], self.texture_size[1]), dtype=np.uint8
        )

        # setting up grid for extra dots
        grid_spacing = self.spacing  
        grid_x = np.arange(0, self.texture_size[0], grid_spacing)
        grid_y = np.arange(0, self.texture_size[1], grid_spacing)
        grid_X, grid_Y = np.meshgrid(grid_x, grid_y)
        grid_points = np.column_stack((grid_X.ravel(), grid_Y.ravel()))

        # generating probabilities based on a Gaussian distribution centered at the original circle center
        distance_from_center = np.sqrt(
            (grid_points[:, 0] - self.circle_center[0])**2 +
            (grid_points[:, 1] - self.circle_center[1])**2
        )
        probabilities = np.exp(-distance_from_center**2 / (2 * 50**2))
        probabilities /= probabilities.sum()

        # sample points from grid space
        num_samples = min(self.frequency, len(grid_points))
        selected_indices = np.random.choice(len(grid_points), size=num_samples, p=probabilities, replace=False)
        selected_centers = grid_points[selected_indices]

        for center_x, center_y in selected_centers:
            circle_mask = (X - center_x)**2 + (Y - center_y)**2 <= self.circle_radius**2
            circle_texture[circle_mask] = self.fg_intensity

        return np.uint8(circle_texture)

    def __str__(self) -> str:
        return (
            f"{type(self).__name__} size:{self.texture_size} center:{self.circle_center} radius:{self.circle_radius} num of circles:{self.num_circles}"
            f"bg:{self.bg_intensity} fg:{self.fg_intensity}"
        )
    
class EllipseGrayTex(TextureBase):
    def __init__(
        self,
        frequency = 1,
        center=(0, 0),
        width=50, #semi major axis
        length=100,#semi minor axis
        bg_intensity=0,
        fg_intensity=255,
        texture_name="gray_circle",
        *args,
        **kwargs,
    ):
        self.frequency = frequency
        self.center = center
        self.h_radius = width / 2
        self.v_radius = length / 2
        self.bg_intensity = bg_intensity
        self.fg_intensity = fg_intensity
        super().__init__(texture_name=texture_name, *args, **kwargs)

    def create_texture(self) -> np.array:
        if self.fg_intensity > 255 or self.bg_intensity < 0:
            raise ValueError("Ellipse intensity must lie in [0, 255]")
        
        x = np.linspace(0, self.texture_size[0], self.texture_size[0])
        y = np.linspace(0, self.texture_size[1], self.texture_size[1])
        X, Y = np.meshgrid(x, y)

        ellipse_texture = self.bg_intensity * np.ones(
            (self.texture_size[0], self.texture_size[1]), dtype=np.uint8)
        
        if self.frequency > 1:
        # setting up grid for extra dots
            if self.h_radius > self.v_radius:
                grid_spacing = self.v_radius * 2 + 100 
            else: 
                grid_spacing = self.h_radius * 2 + 100

            grid_x = np.arange(0, self.texture_size[0], grid_spacing)
            grid_y = np.arange(0, self.texture_size[1], grid_spacing)
            grid_X, grid_Y = np.meshgrid(grid_x, grid_y)
            grid_points = np.column_stack((grid_X.ravel(), grid_Y.ravel()))

            # generating probabilities based on a Gaussian distribution centered at the original circle center
            distance_from_center = np.sqrt(
                (grid_points[:, 0] - self.center[0])**2 +
                (grid_points[:, 1] - self.center[1])**2
            )
            probabilities = np.exp(-distance_from_center**2 / (2 * 60**2))
            probabilities /= probabilities.sum()

            # sample points from grid space
            num_samples = min(self.frequency, len(grid_points))
            selected_indices = np.random.choice(len(grid_points), size=num_samples, p=probabilities, replace=False)
            selected_centers = grid_points[selected_indices]

            for center_x, center_y in selected_centers:
                if (
                    self.h_radius <= center_x < self.texture_size[0] - self.h_radius
                    and self.v_radius <= center_y < self.texture_size[1] - self.v_radius
                ):
                    ellipse_mask = ((X - center_x) ** 2 / self.h_radius ** 2 + 
                                    (Y - center_y) ** 2 / self.v_radius ** 2) <=1
                    
                    ellipse_texture[ellipse_mask] = self.fg_intensity
        else:
            ellipse_mask = ((X - self.center[0]) ** 2 / self.h_radius ** 2 + 
                            (Y - self.center[1]) ** 2 / self.v_radius ** 2) <=1
                    
            ellipse_texture[ellipse_mask] = self.fg_intensity

        return np.uint8(ellipse_texture)

    def __str__(self) -> str:
        return (
            f"{type(self).__name__} size:{self.texture_size} center:{self.circle_center} radius:{self.circle_radius} num of circles:{self.num_circles}"
            f"bg:{self.bg_intensity} fg:{self.fg_intensity}")

class RectGrayTex(TextureBase):
    '''
    Rectangle texture with changeable length x width, frequency, and spacing between rectangles (default is None)
    '''
    def __init__(
        self,
        frequency = 1,
        center=(0, 0),
        length=50, 
        width=100, 
        bg_intensity=0,
        fg_intensity=255,
        texture_name="gray_rect",
        *args,
        **kwargs,
    ):
        self.frequency = frequency
        self.center = center
        self.length = length
        self.width = width
        self.bg_intensity = bg_intensity
        self.fg_intensity = fg_intensity
        super().__init__(texture_name=texture_name, *args, **kwargs)

    def create_texture(self) -> np.array:
        if self.fg_intensity > 255 or self.bg_intensity < 0:
            raise ValueError("Ellipse intensity must lie in [0, 255]")
        
        x = np.linspace(
            0, self.texture_size[0], self.texture_size[0]
        )
        y = np.linspace(
            0, self.texture_size[1], self.texture_size[1]
        )
        X, Y = np.meshgrid(x, y)

        rect_texture = self.bg_intensity * np.ones(
            (self.texture_size[0], self.texture_size[1]), dtype=np.uint8
        )

        # setting up grid for extra dots
        # if self.width > self.length:
        #     grid_spacing = self.length * 2 + 100 
        # else: 
        #     grid_spacing = self.width * 2 + 100

        grid_x = np.arange(0, self.texture_size[0], 100 + self.width)
        grid_y = np.arange(0, self.texture_size[1], 100 + self.length)
        grid_X, grid_Y = np.meshgrid(grid_x, grid_y)
        grid_points = np.column_stack((grid_X.ravel(), grid_Y.ravel()))

        # valid_points = (grid_points[:,0] >= self.width / 2) & (grid_points[:,0] < self.texture_size[0] - self.width / 2) & \
        #                (grid_points[:,1] >= self.length / 2) & (grid_points[:,1] < self.texture_size[1] - self.length / 2)
        # valid_grid_points = grid_points[valid_points]
        # valid_distances = np.sqrt(
        #     (valid_grid_points[:,0] - self.center[0]) ** 2 + (valid_grid_points[:,1] - self.center[1]) **2 
        # )
        # # distance_from_center = np.sqrt((grid_points[:,0] - self.center[0]) ** 2 + (grid_points[:, 1] - self.center[1]) **2)
        # probabilities = np.exp(-valid_distances**2 / (2 * 60**2))
        # probabilities /= probabilities.sum()

        num_samples = min(self.frequency, len(grid_points))
        # selected_indices = np.random.choice(len(grid_points), size=num_samples, replace=False)
        selected_centers = grid_points[:num_samples]

        for center in selected_centers:
            center_x, center_y = center

            # if (
            #     self.width  <= center_x < self.texture_size[0] - self.width and
            #     self.length <= center_y < self.texture_size[1] - self.length 
            # ):
            rect_mask = (X >= center_x - self.width / 2) & (X <= center_x  + self.width / 2) & (
                        Y >= center_y - self.length / 2) &  (Y <= center_y + self.length / 2)
            rect_texture[rect_mask] = self.fg_intensity
        # valid_points = []
        # for px, py in grid_points:
        #     if (
        #         self.width / 2 <= px < self.texture_size[0] - self.width / 2 and
        #         self.length /2 <= py < self.texture_size[1] - self.length / 2
        #     ):
        #         valid_points.append((px, py))
        
        # if self.frequency > 1:
        #     sampled_points = [self.center] + valid_points[:self.frequency - 1]
        # else:
        #     sampled_points = [self.center]
        
        if self.frequency == 1:
            rect_mask = (X >= self.center[0] - self.width / 2) & (X <= self.center[0]  + self.width / 2) & (
                         Y >= self.center[1] - self.length / 2) &  (Y <= self.center[1] + self.length / 2)
            rect_texture[rect_mask] = self.fg_intensity

        return np.uint8(rect_texture)

    def __str__(self) -> str:
        return (
            f"{type(self).__name__} size:{self.texture_size} center:{self.circle_center} radius:{self.circle_radius} num of circles:{self.num_circles}"
            f"bg:{self.bg_intensity} fg:{self.fg_intensity}"
        )

class SinGrayTex(TextureBase):
    """
    Grayscale sinusoidal grating texture.
    """

    def __init__(self, frequency=10, texture_name="sin_gray", *args, **kwargs):
        self.frequency = frequency
        super().__init__(texture_name=texture_name, *args, **kwargs)

    def create_texture(self) -> np.array:
        x = np.linspace(0, 2 * np.pi, self.texture_size[0] + 1)
        y = np.linspace(0, 2 * np.pi, self.texture_size[1] + 1)
        array, Y = np.meshgrid(x[: self.texture_size[0]], y[: self.texture_size[1]])
        return utils.sin_byte(array, freq=self.frequency)

    def __str__(self) -> str:
        return (
            f"{type(self).__name__} size:{self.texture_size} frequency:{self.frequency}"
        )


class SinRgbTex(TextureBase):
    """
    Sinusoid that goes from black to the given rgb value.
    """

    def __init__(
        self, color=(255, 0, 0), frequency=10, texture_name="sin_rgb", *args, **kwargs
    ):
        self.frequency = frequency
        self.color = color
        super().__init__(texture_name=texture_name, *args, **kwargs)

    def create_texture(self) -> np.array:
        if not (
            all([x >= 0 for x in self.color]) and all([x <= 255 for x in self.color])
        ):
            raise ValueError(
                "SinRgbTex.sin_texture_rgb(): rgb values must lie in [0,255]"
            )
        x = np.linspace(0, 2 * np.pi, self.texture_size[0] + 1)
        y = np.linspace(0, 2 * np.pi, self.texture_size[1] + 1)
        array, Y = np.meshgrid(x[: self.texture_size[0]], y[: self.texture_size[1]])
        R = np.uint8((self.color[0] / 255) * utils.sin_byte(array, freq=self.frequency))
        G = np.uint8((self.color[1] / 255) * utils.sin_byte(array, freq=self.frequency))
        B = np.uint8((self.color[2] / 255) * utils.sin_byte(array, freq=self.frequency))
        rgb_sin = np.zeros(
            (self.texture_size[1], self.texture_size[0], 3), dtype=np.uint8
        )
        rgb_sin[..., 0] = R
        rgb_sin[..., 1] = G
        rgb_sin[..., 2] = B
        return rgb_sin

    def __str__(self) -> str:
        return f"{type(self).__name__} size:{self.texture_size} frequency:{self.frequency} rgb:{self.color}"


class GratingGrayTex(TextureBase):
    """
    Grayscale 2d square wave (grating)
    """

    def __init__(
        self,
        frequency=10,
        light_value=255,
        dark_value=0,
        texture_name="grating_gray",
        *args,
        **kwargs,
    ):
        self.frequency = frequency
        self.dark_value = dark_value
        self.light_value = light_value
        super().__init__(texture_name=texture_name, *args, **kwargs)

    def create_texture(self) -> np.array:
        x = np.linspace(0, 2 * np.pi, self.texture_size[0] + 1)
        y = np.linspace(0, 2 * np.pi, self.texture_size[1] + 1)
        X, Y = np.meshgrid(x[: self.texture_size[0]], y[: self.texture_size[1]])
        tex = utils.grating_byte(X, freq=self.frequency)
        tex[tex == 0] = self.dark_value
        tex[tex == 255] = self.light_value
        return tex

    def __str__(self) -> str:
        return (
            f"{type(self).__name__} size:{self.texture_size} frequency:{self.frequency}"
        )


class GratingRgbTex(TextureBase):
    """
    Rgb 2d square wave (grating) stimulus class (goes from black to rgb val)
    """

    def __init__(
        self,
        color=(255, 0, 0),
        frequency=10,
        texture_name="grating_rgb",
        *args,
        **kwargs,
    ):
        self.frequency = frequency
        self.color = color
        super().__init__(texture_name=texture_name, *args, **kwargs)

    def create_texture(self) -> np.array:
        if not (
            all([x >= 0 for x in self.color]) and all([x <= 255 for x in self.color])
        ):
            raise ValueError(
                "SinRgbTex.sin_texture_rgb(): rgb values must lie in [0,255]"
            )
        x = np.linspace(0, 2 * np.pi, self.texture_size[0] + 1)
        y = np.linspace(0, 2 * np.pi, self.texture_size[1] + 1)
        array, Y = np.meshgrid(x[: self.texture_size[0]], y[: self.texture_size[1]])
        R = np.uint8(
            (self.color[0] / 255) * utils.grating_byte(array, freq=self.frequency)
        )
        G = np.uint8(
            (self.color[1] / 255) * utils.grating_byte(array, freq=self.frequency)
        )
        B = np.uint8(
            (self.color[2] / 255) * utils.grating_byte(array, freq=self.frequency)
        )
        rgb_grating = np.zeros(
            (self.texture_size[1], self.texture_size[0], 3), dtype=np.uint8
        )
        rgb_grating[..., 0] = R
        rgb_grating[..., 1] = G
        rgb_grating[..., 2] = B
        return rgb_grating

    def __str__(self) -> str:
        return f"{type(self).__name__} size:{self.texture_size} frequency:{self.frequency} rgb:{self.color}"


class CalibrationTriangles(TextureBase):
    """
    Filled circle: grayscale on grayscale with circle_radius, centered at circle_center
    with face color fg_intensity on background bg_intensity. Center position is in pixels
    from center of image.
    """

    def __init__(
        self,
        tri_size=50,
        circle_radius=7,
        x_offset=0,
        y_offset=0,
        texture_name="circs",
        *args,
        **kwargs,
    ):
        self.tri_size = tri_size
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.circle_radius = circle_radius
        super().__init__(texture_name=texture_name, *args, **kwargs)

    def create_texture(self) -> np.array:
        self.midx = self.texture_size[0] // 2
        self.midy = self.texture_size[1] // 2

        self.pt1 = (
            int((self.midx + self.x_offset - (self.tri_size * math.sqrt(3)) // 2)),
            int((self.midy + self.y_offset + self.tri_size // 2)),
        )

        self.pt2 = (
            int((self.midx + self.x_offset + (self.tri_size * math.sqrt(3)) // 2)),
            int((self.midy + self.y_offset - self.tri_size // 2)),
        )

        self.pt3 = (
            int((self.midx + self.x_offset - (self.tri_size * math.sqrt(3)) // 2)),
            int((self.midy + self.y_offset - self.tri_size // 2)),
        )

        circle_texture = np.zeros((self.texture_size[1], self.texture_size[0]))

        [
            cv2.circle(circle_texture, i, self.circle_radius, 255, -1)
            for i in [self.pt1, self.pt2, self.pt3]
        ]

        return np.uint8(circle_texture)

    def __str__(self) -> str:
        return f"{type(self).__name__} size:{self.texture_size} center:{self.midx, self.midy} radius:{self.circle_radius}"

    def projct_coords(self) -> np.array:
        return np.array([self.pt1, self.pt2, self.pt3])


class RadialSinCube(TextureBase):
    def __init__(
        self, phase=0, period=32, texture_name="radial_sin_centering", *args, **kwargs
    ):
        self.phase = phase
        self.period = period
        super().__init__(texture_name=texture_name, *args, **kwargs)

    def create_texture(self) -> np.array:
        x = np.linspace(-self.period * np.pi, self.period * np.pi, self.texture_size[0])
        y = np.linspace(-self.period * np.pi, self.period * np.pi, self.texture_size[1])
        return np.round(
            (2 * np.pi / self.period)
            * np.sin(np.sqrt(x[None, :] ** 2 + y[:, None] ** 2) + self.phase)
            * 127
            + 127
        ).astype(np.uint8)

    def __str__(self) -> str:
        return f"{type(self).__name__} size:{self.texture_size} period:{self.period} phase: {self.phase}"

class CallibrationDots(TextureBase): 
    def __init__(
        self,
        circle_center=(0, 0),
        circle_radius=100,
        bg_intensity = 0,
        texture_name="callibration_dots",
        *args,
        **kwargs,
    ):
        self.circle_center = circle_center
        self.circle_radius = circle_radius
        self.bg_intensity = bg_intensity
        super().__init__(texture_name=texture_name, *args, **kwargs)

    def create_texture(self) -> np.array:
        x = np.linspace(0, self.texture_size[0], self.texture_size[0])
        y = np.linspace(0, self.texture_size[1], self.texture_size[1])
        X, Y = np.meshgrid(x, y)

        circle_texture = self.bg_intensity * np.ones(
            (self.texture_size[0], self.texture_size[1], 3), dtype=np.uint8
        )

        grid_centers = []
        spacing = 110
        # grid_size = int(np.sqrt(11))  # Arrange circles in a roughly square grid
        # offset = (grid_size - 1) * spacing / 2  # Center the grid around the given center
        rows, cols = 7, 13
        total_circles = rows * cols
        center_row, center_col = rows // 2, cols // 2
    
        for i in range(rows):
            for j in range(cols):
                center_x = self.circle_center[0] - (j - center_col) * spacing
                center_y = self.circle_center[1] - (i - center_row) * spacing
                grid_centers.append((center_x, center_y))

        # # Define specific colors for the circles
        # colors = [
        #     (255, 0, 0),   # Red
        #     (0, 255, 0),   # Green
        #     (0, 0, 255),   # Blue
        #     (255, 255, 0), # Yellow
        #     (0, 255, 255), # Cyan
        #     (255, 0, 255), # Magenta
        #     (128, 128, 128), # Gray
        #     (255, 128, 0), # Orange
        #     (128, 0, 255), # Purple
        #     (0, 128, 255)  # Light Blue
        # ]
        colors = [
            (
                int((idx / total_circles) * 255), 
                int(((total_circles - idx) / total_circles) * 255),
                int((idx % total_circles) * (255 /total_circles))
            )
            for idx in range(total_circles)
        ]

        # Draw each circle
        for idx, (cx, cy) in enumerate(grid_centers):
            circle_mask = (X - cx) ** 2 + (Y - cy) ** 2 <= self.circle_radius ** 2
            for channel in range(3):  # Apply the specific color to each RGB channel
                circle_texture[circle_mask, channel] = colors[idx][channel]

            # text_position = (int(cx), int(cy))
            # text = f"({int(cx)}, {int(cy)})"
            # cv2.putText(
            #     circle_texture, 
            #     text, 
            #     text_position, 
            #     fontFace=cv2.FONT_HERSHEY_SIMPLEX, 
            #     fontScale=0.3,
            #     color=(255, 255, 255),
            #     thickness=1, 
            #     lineType=cv2.LINE_AA
            # )
        return np.uint8(circle_texture)

    def __str__(self) -> str:
        return (
            f"{type(self).__name__} size:{self.texture_size} center:{self.circle_center} radius:{self.circle_radius} num of circles:{self.num_circles}"
            f"bg:{self.bg_intensity} fg:{self.fg_intensity}"
        )