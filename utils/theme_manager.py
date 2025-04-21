# utils/theme_manager.py

from utils.styles import DARK_STYLE, DELEUM_STYLE

def toggle_theme(widget, current_theme, theme_button=None, summary_widget=None):
    """
    Toggle between Deleum and Dark themes.

    :param widget: The main window or widget to apply the theme to.
    :param current_theme: The current theme name (str).
    :param theme_button: (Optional) QPushButton to update the label.
    :param summary_widget: (Optional) Widget that needs icon color refresh.
    :return: The new theme name (str).
    """
    if current_theme == "Deleum":
        new_theme = "Dark"
        widget.setStyleSheet(DARK_STYLE)
        if theme_button:
            theme_button.setText("Theme: Dark")
    else:
        new_theme = "Deleum"
        widget.setStyleSheet(DELEUM_STYLE)
        if theme_button:
            theme_button.setText("Theme: Deleum")

    return new_theme


def apply_theme(widget, theme_name):
    """
    Applies the given theme to the widget.

    :param widget: The widget or window to style.
    :param theme_name: Either 'Deleum' or 'Dark'
    """
    if theme_name == "Dark":
        widget.setStyleSheet(DARK_STYLE)
    else:
        widget.setStyleSheet(DELEUM_STYLE)
