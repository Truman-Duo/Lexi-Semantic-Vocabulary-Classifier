import json
import os
import pytest


@pytest.fixture
def temp_dir(tmp_path):
    return str(tmp_path)


@pytest.fixture
def small_categories_json(temp_dir):
    data = {
        "客观类": {
            "具体事物": ["dog", "cat", "house", "book"],
            "属性特征": ["big", "small", "red", "blue"],
        },
        "主观类": {
            "主观动作": ["run", "walk", "talk", "eat"],
            "情绪感受": ["happy", "sad", "angry"],
        },
        "抽象类": {
            "基础概念": ["time", "way", "life", "world"],
        },
    }
    path = os.path.join(temp_dir, "categories.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return path


@pytest.fixture
def small_stopwords_txt(temp_dir):
    path = os.path.join(temp_dir, "stopwords.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("the\na\nan\nis\nare\nwas\nwere\n")
    return path


@pytest.fixture
def small_overrides_json(temp_dir):
    data = {
        "主观类": {
            "情绪感受": ["joy"],
        },
    }
    path = os.path.join(temp_dir, "overrides.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return path


@pytest.fixture
def mock_lemminflect(mocker):
    mock_mod = mocker.patch("lexi.lemmatizer._get_lemminflect")
    instance = mock_mod.return_value

    def fake_lemmas(word):
        mapping = {
            "running": {"VERB": ["run"]},
            "walking": {"VERB": ["walk"]},
            "happiness": {"NOUN": ["happiness"]},
            "dogs": {"NOUN": ["dog"]},
            "cats": {"NOUN": ["cat"]},
            "talking": {"VERB": ["talk"]},
            "bigger": {"ADJ": ["big"]},
            "redder": {"ADJ": ["red"]},
        }
        return mapping.get(word, {})

    instance.getAllLemmas.side_effect = fake_lemmas
    return mock_mod


@pytest.fixture
def mock_wordfreq(mocker):
    freq_map = {
        "time": 5.2, "way": 4.8, "life": 4.5, "world": 4.3,
        "dog": 3.8, "cat": 3.5, "house": 4.0, "book": 3.9,
        "run": 4.2, "walk": 3.6, "talk": 3.4, "eat": 3.7,
        "big": 4.1, "small": 3.8, "red": 3.5, "blue": 3.3,
        "happy": 3.9, "sad": 3.2, "angry": 2.8,
        "the": 6.0, "a": 5.8, "an": 5.0,
    }
    mocker.patch("lexi.sorter._get_wordfreq", return_value=lambda w, lang: freq_map.get(w.lower(), 3.0))
    return freq_map


@pytest.fixture
def mock_nltk(mocker):
    mocker.patch("nltk.data.find", return_value=True)
    mocker.patch("nltk.download", return_value=True)
    mocker.patch("nltk.pos_tag", return_value=[("word", "NN")])
    return mocker


@pytest.fixture
def mock_openai(mocker):
    mock_response = mocker.MagicMock()
    mock_response.choices = [mocker.MagicMock()]
    mock_response.choices[0].message.content = (
        "This is a test story about a **dog** and a **cat**. "
        "They **run** in the **house**."
    )
    mock_response.usage.prompt_tokens = 150
    mock_response.usage.completion_tokens = 80

    mock_client = mocker.MagicMock()
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai_mod = mocker.patch("openai.OpenAI", return_value=mock_client)
    return mock_openai_mod


@pytest.fixture
def sample_input_txt(temp_dir):
    path = os.path.join(temp_dir, "input.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("The dog runs quickly in the big house. Cats are happy.\n")
    return path


@pytest.fixture
def sample_classified_json(temp_dir):
    data = {
        "total_words": 5,
        "categories": {
            "客观类": {
                "具体事物": [
                    {"word": "dog", "zipf": 3.8, "cefr": "B1",
                     "confidence": 1.0, "source": "dictionary"},
                    {"word": "cat", "zipf": 3.5, "cefr": "B1",
                     "confidence": 1.0, "source": "dictionary"},
                ],
                "属性特征": [
                    {"word": "big", "zipf": 4.1, "cefr": "A2",
                     "confidence": 1.0, "source": "dictionary"},
                ],
            },
            "主观类": {
                "主观动作": [
                    {"word": "run", "zipf": 4.2, "cefr": "A2",
                     "confidence": 1.0, "source": "dictionary"},
                ],
            },
        },
    }
    path = os.path.join(temp_dir, "classified.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return path


@pytest.fixture
def mock_config(mocker):
    from lexi.config import LexiConfig
    cfg = LexiConfig(api_key="sk-test", model="gpt-4o-mini")
    mocker.patch("lexi.controller.load_config", return_value=cfg)
    return cfg


@pytest.fixture
def sample_profile():
    from lexi.style_analyzer import StyleProfile
    return StyleProfile(
        avg_word_length=5.2,
        type_token_ratio=0.68,
        avg_sentence_length=20.3,
        sentence_length_std=7.8,
        passive_voice_ratio=0.12,
        flesch_reading_ease=45.0,
        flesch_kincaid_grade=12.5,
        cefr_distribution={"B1": 0.25, "B2": 0.35, "C1": 0.20},
        nominalization_ratio=0.08,
        modifier_density=0.35,
        lexical_density=0.52,
        subordination_ratio=1.5,
        coordination_ratio=0.8,
        transition_density=3.2,
        pronoun_density=0.05,
    )
