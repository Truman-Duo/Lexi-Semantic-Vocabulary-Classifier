from lexi.style_analyzer import StyleAnalyzer, StyleProfile


SAMPLE_TOEFL = (
    "The phenomenon of plate tectonics represents one of the most "
    "significant discoveries in the history of geological sciences. "
    "By examining the distribution of fossils across continents, "
    "scientists were able to develop a comprehensive theory that explains "
    "the gradual movement of the Earth's crust. This theory has been "
    "widely accepted by the scientific community. Further research has "
    "been conducted to refine our understanding of these processes. "
    "The evidence supports the conclusion that continental drift occurs "
    "over millions of years."
)


def test_analyze_empty():
    analyzer = StyleAnalyzer()
    profile = analyzer.analyze("")
    assert profile.avg_sentence_length == 0.0
    assert profile.avg_word_length == 0.0


def test_analyze_short():
    analyzer = StyleAnalyzer()
    profile = analyzer.analyze("The cat sat.")
    assert profile.avg_sentence_length > 0
    assert profile.avg_word_length > 0


def test_analyze_toefl():
    analyzer = StyleAnalyzer()
    profile = analyzer.analyze(SAMPLE_TOEFL)
    assert profile.avg_sentence_length > 10
    assert profile.avg_sentence_length < 40
    assert profile.avg_word_length > 3.0
    assert profile.type_token_ratio > 0.4
    assert profile.type_token_ratio < 1.0
    assert profile.passive_voice_ratio >= 0.0
    assert profile.flesch_reading_ease > 0
    assert profile.flesch_kincaid_grade > 0


def test_analyze_type_token_ratio():
    analyzer = StyleAnalyzer()
    text = "the cat the dog the cat the dog the fish"
    profile = analyzer.analyze(text)
    assert profile.type_token_ratio < 1.0
    assert profile.type_token_ratio > 0.0


def test_analyze_sentence_length():
    analyzer = StyleAnalyzer()
    text = "Short. A slightly longer sentence here. Another one."
    profile = analyzer.analyze(text)
    assert profile.avg_sentence_length > 2.0
    assert profile.sentence_length_std >= 0.0


def test_syllable_counting():
    analyzer = StyleAnalyzer()
    assert analyzer._count_syllables("the") == 1
    assert analyzer._count_syllables("table") == 2
    assert analyzer._count_syllables("computer") == 3
    assert analyzer._count_syllables("university") >= 4
    assert analyzer._count_syllables("a") == 1


def test_profile_to_frontmatter():
    profile = StyleProfile(
        avg_word_length=5.2,
        type_token_ratio=0.68,
        avg_sentence_length=20.3,
        sentence_length_std=7.8,
        passive_voice_ratio=0.12,
        flesch_reading_ease=45.0,
        flesch_kincaid_grade=12.5,
        cefr_distribution={"B1": 0.3, "B2": 0.5, "C1": 0.2},
    )
    fm = profile.to_frontmatter()
    assert fm["avg_word_length"] == "5.2"
    assert fm["type_token_ratio"] == "0.68"
    assert fm["cefr_B1"] == "0.3"
    assert fm["cefr_B2"] == "0.5"


def test_profile_from_frontmatter():
    fm = {
        "avg_word_length": "5.2",
        "type_token_ratio": "0.68",
        "cefr_B1": "0.25",
        "cefr_C1": "0.15",
    }
    profile = StyleProfile.from_frontmatter(fm)
    assert profile.avg_word_length == 5.2
    assert profile.type_token_ratio == 0.68
    assert profile.cefr_distribution["B1"] == 0.25
    assert profile.cefr_distribution["C1"] == 0.15


def test_profile_dominant_cefr():
    profile = StyleProfile()
    profile.cefr_distribution = {"A1": 0.1, "B1": 0.4, "B2": 0.3, "C1": 0.2}
    assert profile.dominant_cefr() == "B1"

    profile2 = StyleProfile()
    assert profile2.dominant_cefr() == "mixed"


def test_analyze_passive_voice():
    analyzer = StyleAnalyzer()
    text = (
        "The experiment was conducted by researchers. "
        "The results were analyzed carefully. "
        "Scientists have published their findings."
    )
    profile = analyzer.analyze(text)
    assert profile.passive_voice_ratio >= 0.0
    assert profile.passive_voice_ratio <= 1.0


def test_nominalization_ratio():
    analyzer = StyleAnalyzer()
    text = (
        "The implementation of the regulation required significant "
        "documentation and verification of the certification process."
    )
    profile = analyzer.analyze(text)
    assert profile.nominalization_ratio > 0.0


def test_modifier_density():
    analyzer = StyleAnalyzer()
    text = "The very large red dog quickly ran through the extremely wet grass."
    profile = analyzer.analyze(text)
    assert profile.modifier_density > 0.0


def test_lexical_density():
    analyzer = StyleAnalyzer()
    text = "The cat sat on the mat in the house by the tree."
    profile = analyzer.analyze(text)
    assert profile.lexical_density > 0.0
    assert profile.lexical_density < 1.0


def test_subordination_ratio():
    analyzer = StyleAnalyzer()
    text = (
        "Although it was raining, we went out because we needed food. "
        "While we walked, we talked about the project that was due soon."
    )
    profile = analyzer.analyze(text)
    assert profile.subordination_ratio > 0.0


def test_coordination_ratio():
    analyzer = StyleAnalyzer()
    text = "We bought apples and oranges but forgot the bananas and grapes."
    profile = analyzer.analyze(text)
    assert profile.coordination_ratio > 0.0


def test_transition_density():
    analyzer = StyleAnalyzer()
    text = (
        "However, the results were inconclusive. Therefore, we conducted "
        "another experiment. Moreover, we consulted additional experts."
    )
    profile = analyzer.analyze(text)
    assert profile.transition_density > 0.0


def test_pronoun_density():
    analyzer = StyleAnalyzer()
    text = "I think he told her that we should go with them to their house."
    profile = analyzer.analyze(text)
    assert profile.pronoun_density > 0.0


def test_all_metrics_present():
    analyzer = StyleAnalyzer()
    profile = analyzer.analyze(SAMPLE_TOEFL)
    assert profile.nominalization_ratio >= 0.0
    assert profile.modifier_density >= 0.0
    assert profile.lexical_density >= 0.0
    assert profile.subordination_ratio >= 0.0
    assert profile.coordination_ratio >= 0.0
    assert profile.transition_density >= 0.0
    assert profile.pronoun_density >= 0.0
