import sys
from typing import Union, Tuple, Callable

from .ctk_canvas import CTkCanvas
from ..theme_manager import ThemeManager
from ..draw_engine import DrawEngine
from .widget_base_class import CTkBaseClass


class CTkScrollbar(CTkBaseClass):
    """
    Scrollbar with rounded corners, configurable spacing.
    Connect to scrollable widget by passing .set() method and set command attribute.
    For detailed information check out the documentation.
    """

    def __init__(self, *args,
                 width: Union[int, str] = "default_init",
                 height: Union[int, str] = "default_init",
                 corner_radius: Union[int, str] = "default_theme",
                 border_spacing: Union[int, str] = "default_theme",
                 minimum_pixel_length: int = 20,

                 bg_color: Union[str, Tuple[str, str], None] = None,
                 fg_color: Union[str, Tuple[str, str], None] = "default_theme",
                 scrollbar_color: Union[str, Tuple[str, str]] = "default_theme",
                 scrollbar_hover_color: Union[str, Tuple[str, str]] = "default_theme",

                 hover: bool = True,
                 command: Callable = None,
                 orientation: str = "vertical",
                 **kwargs):

        # set default dimensions according to orientation
        if width == "default_init":
            if orientation.lower() == "vertical":
                width = 16
            else:
                width = 200
        if height == "default_init":
            if orientation.lower() == "horizontal":
                height = 16
            else:
                height = 200

        # transfer basic functionality (_bg_color, size, _appearance_mode, scaling) to CTkBaseClass
        super().__init__(*args, bg_color=bg_color, width=width, height=height, **kwargs)

        # color
        self._fg_color = ThemeManager.theme["color"]["frame_high"] if fg_color == "default_theme" else fg_color
        self._scrollbar_color = ThemeManager.theme["color"]["scrollbar_button"] if scrollbar_color == "default_theme" else scrollbar_color
        self._scrollbar_hover_color = ThemeManager.theme["color"]["scrollbar_button_hover"] if scrollbar_hover_color == "default_theme" else scrollbar_hover_color

        # shape
        self._corner_radius = ThemeManager.theme["shape"]["scrollbar_corner_radius"] if corner_radius == "default_theme" else corner_radius
        self._border_spacing = ThemeManager.theme["shape"]["scrollbar_border_spacing"] if border_spacing == "default_theme" else border_spacing

        self._hover = hover
        self._hover_state: bool = False
        self._command = command
        self._orientation = orientation
        self._start_value: float = 0  # 0 to 1
        self._end_value: float = 1  # 0 to 1
        self._minimum_pixel_length = minimum_pixel_length

        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 width=self._apply_widget_scaling(self._current_width),
                                 height=self._apply_widget_scaling(self._current_height))
        self._canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self._draw_engine = DrawEngine(self._canvas)

        self._canvas.bind("<Enter>", self._on_enter)
        self._canvas.bind("<Leave>", self._on_leave)
        self._canvas.tag_bind("border_parts", "<Button-1>", self._clicked)
        self._canvas.bind("<B1-Motion>", self._clicked)
        self._canvas.bind("<MouseWheel>", self._mouse_scroll_event)
        super().bind('<Configure>', self._update_dimensions_event)

        self._draw()

    def _set_scaling(self, *args, **kwargs):
        super()._set_scaling(*args, **kwargs)

        self._canvas.configure(width=self._apply_widget_scaling(self._desired_width),
                               height=self._apply_widget_scaling(self._desired_height))
        self._draw(no_color_updates=True)

    def _set_dimensions(self, width=None, height=None):
        super()._set_dimensions(width, height)

        self._canvas.configure(width=self._apply_widget_scaling(self._desired_width),
                               height=self._apply_widget_scaling(self._desired_height))
        self._draw(no_color_updates=True)

    def _get_scrollbar_values_for_minimum_pixel_size(self):
        # correct scrollbar float values if scrollbar is too small
        if self._orientation == "vertical":
            scrollbar_pixel_length = (self._end_value - self._start_value) * self._current_height
            if scrollbar_pixel_length < self._minimum_pixel_length and -scrollbar_pixel_length + self._current_height != 0:
                # calculate how much to increase the float interval values so that the scrollbar width is self.minimum_pixel_length
                interval_extend_factor = (-scrollbar_pixel_length + self._minimum_pixel_length) / (-scrollbar_pixel_length + self._current_height)
                corrected_end_value = self._end_value + (1 - self._end_value) * interval_extend_factor
                corrected_start_value = self._start_value - self._start_value * interval_extend_factor
                return corrected_start_value, corrected_end_value
            else:
                return self._start_value, self._end_value

        else:
            scrollbar_pixel_length = (self._end_value - self._start_value) * self._current_width
            if scrollbar_pixel_length < self._minimum_pixel_length and -scrollbar_pixel_length + self._current_width != 0:
                # calculate how much to increase the float interval values so that the scrollbar width is self.minimum_pixel_length
                interval_extend_factor = (-scrollbar_pixel_length + self._minimum_pixel_length) / (-scrollbar_pixel_length + self._current_width)
                corrected_end_value = self._end_value + (1 - self._end_value) * interval_extend_factor
                corrected_start_value = self._start_value - self._start_value * interval_extend_factor
                return corrected_start_value, corrected_end_value
            else:
                return self._start_value, self._end_value

    def _draw(self, no_color_updates=False):
        corrected_start_value, corrected_end_value = self._get_scrollbar_values_for_minimum_pixel_size()
        requires_recoloring = self._draw_engine.draw_rounded_scrollbar(self._apply_widget_scaling(self._current_width),
                                                                       self._apply_widget_scaling(self._current_height),
                                                                       self._apply_widget_scaling(self._corner_radius),
                                                                       self._apply_widget_scaling(self._border_spacing),
                                                                       corrected_start_value,
                                                                       corrected_end_value,
                                                                       self._orientation)

        if no_color_updates is False or requires_recoloring:
            if self._hover_state is True:
                self._canvas.itemconfig("scrollbar_parts",
                                        fill=ThemeManager.single_color(self._scrollbar_hover_color, self._appearance_mode),
                                        outline=ThemeManager.single_color(self._scrollbar_hover_color, self._appearance_mode))
            else:
                self._canvas.itemconfig("scrollbar_parts",
                                        fill=ThemeManager.single_color(self._scrollbar_color, self._appearance_mode),
                                        outline=ThemeManager.single_color(self._scrollbar_color, self._appearance_mode))

            if self._fg_color is None:
                self._canvas.configure(bg=ThemeManager.single_color(self._bg_color, self._appearance_mode))
                self._canvas.itemconfig("border_parts",
                                        fill=ThemeManager.single_color(self._bg_color, self._appearance_mode),
                                        outline=ThemeManager.single_color(self._bg_color, self._appearance_mode))
            else:
                self._canvas.configure(bg=ThemeManager.single_color(self._fg_color, self._appearance_mode))
                self._canvas.itemconfig("border_parts",
                                        fill=ThemeManager.single_color(self._fg_color, self._appearance_mode),
                                        outline=ThemeManager.single_color(self._fg_color, self._appearance_mode))

        self._canvas.update_idletasks()

    def configure(self, require_redraw=False, **kwargs):
        if "fg_color" in kwargs:
            self._fg_color = kwargs.pop("fg_color")
            require_redraw = True

        if "scrollbar_color" in kwargs:
            self._scrollbar_color = kwargs.pop("scrollbar_color")
            require_redraw = True

        if "scrollbar_hover_color" in kwargs:
            self._scrollbar_hover_color = kwargs.pop("scrollbar_hover_color")
            require_redraw = True

        if "command" in kwargs:
            self._command = kwargs.pop("command")

        if "corner_radius" in kwargs:
            self._corner_radius = kwargs.pop("corner_radius")
            require_redraw = True

        if "border_spacing" in kwargs:
            self._border_spacing = kwargs.pop("border_spacing")
            require_redraw = True

        if "width" in kwargs:
            self._set_dimensions(width=kwargs.pop("width"))

        if "height" in kwargs:
            self._set_dimensions(height=kwargs.pop("height"))

        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str) -> any:
        if attribute_name == "corner_radius":
            return self._corner_radius
        elif attribute_name == "border_spacing":
            return self._border_spacing
        elif attribute_name == "minimum_pixel_length":
            return self._minimum_pixel_length

        elif attribute_name == "fg_color":
            return self._fg_color
        elif attribute_name == "scrollbar_color":
            return self._scrollbar_color
        elif attribute_name == "scrollbar_hover_color":
            return self._scrollbar_hover_color

        elif attribute_name == "hover":
            return self._hover
        elif attribute_name == "command":
            return self._command
        elif attribute_name == "orientation":
            return self._orientation

        else:
            return super().cget(attribute_name)

    def _on_enter(self, event=0):
        if self._hover is True:
            self._hover_state = True
            self._canvas.itemconfig("scrollbar_parts",
                                    outline=ThemeManager.single_color(self._scrollbar_hover_color, self._appearance_mode),
                                    fill=ThemeManager.single_color(self._scrollbar_hover_color, self._appearance_mode))

    def _on_leave(self, event=0):
        self._hover_state = False
        self._canvas.itemconfig("scrollbar_parts",
                                outline=ThemeManager.single_color(self._scrollbar_color, self._appearance_mode),
                                fill=ThemeManager.single_color(self._scrollbar_color, self._appearance_mode))

    def _clicked(self, event):
        if self._orientation == "vertical":
            value = ((event.y - self._border_spacing) / (self._current_height - 2 * self._border_spacing)) / self._widget_scaling
        else:
            value = ((event.x - self._border_spacing) / (self._current_width - 2 * self._border_spacing)) / self._widget_scaling

        current_scrollbar_length = self._end_value - self._start_value
        value = max(current_scrollbar_length / 2, min(value, 1 - (current_scrollbar_length / 2)))
        self._start_value = value - (current_scrollbar_length / 2)
        self._end_value = value + (current_scrollbar_length / 2)
        self._draw()

        if self._command is not None:
            self._command('moveto', self._start_value)

    def _mouse_scroll_event(self, event=None):
        if self._command is not None:
            if sys.platform.startswith("win"):
                self._command('scroll', -int(event.delta/40), 'units')
            else:
                self._command('scroll', -event.delta, 'units')

    def set(self, start_value: float, end_value: float):
        self._start_value = float(start_value)
        self._end_value = float(end_value)
        self._draw()

    def get(self):
        return self._start_value, self._end_value

    def bind(self, sequence=None, command=None, add=None):
        """ called on the tkinter.Canvas """
        return self._canvas.bind(sequence, command, add)

    def unbind(self, sequence, funcid=None):
        """ called on the tkinter.Canvas """
        return self._canvas.bind(sequence, funcid)
