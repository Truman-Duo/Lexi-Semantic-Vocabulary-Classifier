"""Tests for AI exercise generation."""

import json
from lexi.exercises import ExerciseGenerator, Exercise, ExerciseItem
from lexi.config import LexiConfig


def _make_gen():
    return ExerciseGenerator(LexiConfig(api_key="sk-test", model="gpt-4o-mini"))


def _mock_response(mocker, content):
    mock_client = mocker.MagicMock()
    mock_response = mocker.MagicMock()
    mock_response.choices = [mocker.MagicMock()]
    mock_response.choices[0].message.content = content
    mock_client.chat.completions.create.return_value = mock_response
    mocker.patch("openai.OpenAI", return_value=mock_client)


def test_cloze_parsing(mocker):
    _mock_response(mocker, json.dumps([
        {"sentence": "The ______ of the experiment was surprising.", "word": "outcome"},
        {"sentence": "We need to ______ the problem carefully.", "word": "analyze"},
    ]))
    gen = _make_gen()
    result = gen.generate_cloze(["outcome", "analyze"], count=2)
    assert result.type == "cloze"
    assert len(result.items) == 2
    assert result.items[0].blank_word == "outcome"


def test_cloze_empty_response(mocker):
    _mock_response(mocker, "no json here")
    gen = _make_gen()
    result = gen.generate_cloze(["test"])
    assert result.type == "cloze"


def test_choice_parsing(mocker):
    _mock_response(mocker, json.dumps([
        {"word": "outcome", "question": "What does outcome mean?",
         "options": ["result", "income", "outline", "outcry"], "correct": "result"},
    ]))
    gen = _make_gen()
    result = gen.generate_choice(["outcome"], count=1)
    assert result.type == "choice"
    assert len(result.items) == 1
    assert len(result.items[0].options) == 4


def test_definitions_parsing(mocker):
    _mock_response(mocker, json.dumps([
        {"word": "outcome", "definition": "The final result of an event"},
        {"word": "analyze", "definition": "To examine something in detail"},
    ]))
    gen = _make_gen()
    result = gen.generate_definitions(["outcome", "analyze"])
    assert result.type == "definition"
    assert len(result.items) == 2


def test_check_sentence(mocker):
    _mock_response(mocker, "1. 用法评分: 4/5\n2. 正确使用了 'outcome'\n3. 无语法问题\n4. 无需修改")
    gen = _make_gen()
    result = gen.check_sentence("The outcome was good.", "outcome")
    assert "评分" in result


def test_extract_json():
    text = '```json\n[{"a":1}]\n```'
    result = ExerciseGenerator._extract_json(text)
    assert result == '[{"a":1}]'


def test_extract_json_no_codeblock():
    result = ExerciseGenerator._extract_json('[{"a":1}]')
    assert result == '[{"a":1}]'
