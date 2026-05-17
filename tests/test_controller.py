import json
import os
from lexi.controller import LexiController, OutputOptions, ClassifyResult
from lexi.story import StoryResult


def test_classify_file_not_found(mock_config):
    ctrl = LexiController()
    import pytest
    with pytest.raises(FileNotFoundError):
        ctrl.classify("nonexistent_file.txt")


def test_classify_calls_pipeline(mocker, mock_config, sample_input_txt, temp_dir):
    mock_run = mocker.patch("lexi.controller.run_pipeline")
    def fake_pipeline(**kwargs):
        json_path = kwargs.get("output_json")
        if json_path:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump({"total_words": 42}, f)
    mock_run.side_effect = fake_pipeline
    ctrl = LexiController()
    result = ctrl.classify(
        sample_input_txt,
        outputs=OutputOptions(markdown=False, json=True, csv=False, html=False, anki=False),
        output_dir=temp_dir,
    )
    mock_run.assert_called_once()
    assert result.total_words == 42
    assert "json" in result.output_files


def test_classify_callback_invocation(mocker, mock_config, sample_input_txt, temp_dir):
    mocker.patch("lexi.controller.run_pipeline", return_value=None)
    json_path = os.path.join(temp_dir, "test_output.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"total_words": 0}, f)
    progress_values = []
    status_values = []
    ctrl = LexiController()
    ctrl.classify(
        sample_input_txt,
        outputs=OutputOptions(markdown=False, json=True, csv=False, html=False, anki=False),
        output_dir=temp_dir,
        progress_callback=lambda p: progress_values.append(p),
        status_callback=lambda s: status_values.append(s),
    )
    assert len(progress_values) >= 0


def test_generate_story_file_not_found(mock_config):
    ctrl = LexiController()
    import pytest
    with pytest.raises(FileNotFoundError):
        ctrl.generate_story("nonexistent.json")


def test_generate_story_no_classified_words(mock_config, temp_dir):
    path = os.path.join(temp_dir, "empty.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"total_words": 0, "categories": {}}, f)
    ctrl = LexiController()
    import pytest
    with pytest.raises(ValueError, match="No classified words"):
        ctrl.generate_story(path)


def test_generate_story_success(
    mocker, mock_config, mock_openai, sample_classified_json, temp_dir,
):
    ctrl = LexiController()
    result = ctrl.generate_story(
        sample_classified_json,
        output_dir=temp_dir,
        count=3,
        strategy="balanced",
    )
    assert isinstance(result, StoryResult)
    assert "dog" in result.passage
    assert os.path.exists(os.path.join(temp_dir, "classified_story.md"))


def test_generate_story_with_style(
    mocker, mock_config, mock_openai, sample_classified_json, temp_dir,
):
    ctrl = LexiController()
    ctrl.styles.add_style("TestStyle", "Reference text for style.", "desc")
    result = ctrl.generate_story(
        sample_classified_json,
        output_dir=temp_dir,
        count=3,
        style="TestStyle",
    )
    assert isinstance(result, StoryResult)


def test_generate_story_style_not_found(
    mocker, mock_config, sample_classified_json,
):
    ctrl = LexiController()
    import pytest
    with pytest.raises(ValueError, match="Style"):
        ctrl.generate_story(sample_classified_json, style="NoSuchStyle")


def test_controller_uses_own_config():
    from lexi.config import LexiConfig
    cfg = LexiConfig(api_key="sk-custom", model="custom-model")
    ctrl = LexiController(config=cfg)
    assert ctrl.config.api_key == "sk-custom"


def test_controller_styles_property(mock_config):
    ctrl = LexiController()
    from lexi.styles import StyleManager
    assert isinstance(ctrl.styles, StyleManager)


def test_controller_save_config(mock_config, temp_dir):
    ctrl = LexiController()
    ctrl.config.api_key = "sk-newkey"
    path = ctrl.save_config(os.path.join(temp_dir, "config.json"))
    assert os.path.exists(path)
    with open(path, "r") as f:
        data = json.load(f)
    assert data["api_key"] == "sk-newkey"
