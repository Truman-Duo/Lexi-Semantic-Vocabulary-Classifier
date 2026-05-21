"""CLI dispatch — thin entry point."""

import sys
from lexi.controller import LexiController
from .classify_cmd import run_classify
from .story_cmd import handle_story
from .config_cmd import handle_config
from .style_cmd import handle_style
from .exercise_cmd import handle_exercise
from .plan_cmd import handle_plan


def main():
    if len(sys.argv) >= 2 and sys.argv[1] in ("story", "config", "style", "exercise", "plan"):
        subcommand = sys.argv[1]
        ctrl = LexiController()
        if subcommand == "story":
            handle_story(ctrl, sys.argv[2:])
        elif subcommand == "config":
            handle_config(ctrl, sys.argv[2:])
        elif subcommand == "style":
            handle_style(ctrl, sys.argv[2:])
        elif subcommand == "exercise":
            handle_exercise(ctrl, sys.argv[2:])
        elif subcommand == "plan":
            handle_plan(ctrl, sys.argv[2:])
    else:
        run_classify(sys.argv)


if __name__ == "__main__":
    main()
