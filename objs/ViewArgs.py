from typing import TypedDict, Optional, List, Literal

class ButtonArgs(TypedDict):
    """
    Represents a button in a Discord view.
    - Button Must Link or Prompt or Call Tool.
    - Prompt is instructions for what to do when an option is selected.
    - Link is the URL to open when button is clicked.
    - If Link is provided, style must be "link".
    - Emoji is show next to the button label.
    - If emoji is provided, don't provide emoji in label.

    Style color of the button follows:
    - "primary" for blue,
    - "secondary" for gray,
    - "success" for green,
    - "danger" for red,
    - "link" for a link button.
    """
    label: str
    style: Literal["primary", "secondary", "success", "danger", "link"]
    prompt: Optional[str]
    emoji: Optional[str]
    link: Optional[str]

class OptionArgs(TypedDict):
    label: str
    description: Optional[str]
    value: str

class SelectArgs(TypedDict):
    """
    Represents a select menu in a Discord view.
    - Options is a list of options to choose from.
    - Placeholder is the text to show when no option is selected.
    - Prompt is instructions for what to do when an option is selected.
    - Prompt Must have `${values}` to get the selected values.
    - Max values and min values are the number of options that can be selected.
    - Min and Max is optional, if not provided, defaults to 1.
    """
    options: List[OptionArgs]
    placeholder: Optional[str]
    custom_id: str
    prompt: Optional[str]
    min_values: Optional[int]
    max_values: Optional[int]

class ViewArgs(TypedDict):
    """
    Can not have Empty Selects or Buttons at the same time.
    - For Many choices, use Selects.
    - For Command like actions, use Buttons.
    - The Button order follows left to right, top to bottom.
    - Selects are always at the bottom below the buttons.
    - You shouldn't use buttons for case with many choices use Selects instead.
    """
    selects: List[SelectArgs]
    buttons: List[ButtonArgs]
