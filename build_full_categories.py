import nltk
from nltk.corpus import wordnet as wn
import json
from collections import defaultdict

CATEGORY_HYPERNYMS = {
    ("主观类", "情绪感受"): [
        "emotion.n.01", "feeling.n.01", "anger.n.01", "joy.n.01", "sadness.n.01",
        "fear.n.01", "love.n.01", "hate.n.01", "anxiety.n.01", "surprise.n.01",
        "disgust.n.01", "pride.n.01", "shame.n.01", "guilt.n.01", "envy.n.01",
        "excitement.n.01", "affection.n.01", "hostility.n.01", "calmness.n.01"
    ],
    ("主观类", "观点判断"): [
        "judgment.n.01", "belief.n.01", "opinion.n.01", "value.n.02", "evaluation.n.01",
        "assessment.n.01", "attitude.n.01", "perspective.n.01", "conviction.n.01",
        "standard.n.01", "criticism.n.01", "approval.n.01"
    ],
    ("主观类", "心理活动"): [
        "cognition.n.01", "thinking.n.01", "knowledge.n.01", "memory.n.01",
        "decision.n.01", "reasoning.n.01", "imagination.n.01", "planning.n.01",
        "perception.n.01", "attention.n.01", "learning.n.01", "intuition.n.01"
    ],
    ("主观类", "主观动作"): [
        "action.n.01", "activity.n.01", "motion.n.01", "walk.v.01", "run.v.01",
        "eat.v.01", "work.v.01", "communicate.v.01", "play.v.01", "create.v.01",
        "perform.v.01", "move.v.01", "gesture.n.01"
    ],
    ("客观类", "具体事物"): [
        "artifact.n.01", "object.n.01", "physical_entity.n.01", "living_thing.n.01",
        "animal.n.01", "plant.n.01", "food.n.01", "furniture.n.01", "vehicle.n.01",
        "building.n.01", "clothing.n.01", "instrumentality.n.01", "substance.n.01",
        "matter.n.01", "organism.n.01", "person.n.01"
    ],
    ("客观类", "客观动作"): [
        "happen.v.01", "occur.v.01", "change.v.01", "process.n.01", "event.n.01",
        "natural_process.n.01", "physical_process.n.01", "phenomenon.n.01"
    ],
    ("客观类", "属性特征"): [
        "attribute.n.02", "property.n.02", "color.n.01", "size.n.01", "shape.n.01",
        "quality.n.01", "characteristic.n.01", "state.n.02", "feature.n.02"
    ],
    ("抽象类", "基础概念"): [
        "abstraction.n.06", "concept.n.01", "quantity.n.01", "time.n.01",
        "space.n.01", "number.n.01", "unit.n.02", "measure.n.02", "idea.n.01"
    ],
    ("抽象类", "社会概念"): [
        "social_group.n.01", "society.n.01", "government.n.01", "economy.n.01",
        "law.n.01", "family.n.01", "organization.n.01", "institution.n.01",
        "culture.n.01", "politics.n.01", "religion.n.01"
    ],
    ("抽象类", "关系连接"): [
        "relation.n.01", "link.n.03", "cause.n.01", "effect.n.01", "condition.n.01",
        "comparison.n.01", "connection.n.01", "association.n.01"
    ]
}

HYPERNYM_SYNSETS = {}
for (main, sub), names in CATEGORY_HYPERNYMS.items():
    for name in names:
        try:
            ss = wn.synset(name)
            HYPERNYM_SYNSETS.setdefault((main, sub), []).append(ss)
        except:
            pass

def get_categories_from_wordnet(word):
    categories = set()
    synsets = wn.synsets(word)
    for ss in synsets:
        for path in ss.hypernym_paths():
            for ancestor in path:
                for (main_cat, sub_cat), targets in HYPERNYM_SYNSETS.items():
                    if ancestor in targets:
                        categories.add((main_cat, sub_cat))
    return list(categories)

def fallback_category(word):
    if word.endswith(('tion', 'sion', 'ment', 'ance', 'ence', 'ity', 'ness', 'ism', 'logy')):
        return ("抽象类", "基础概念")
    if word.endswith(('ate', 'ize', 'ify', 'ish', 'ure')):
        return ("主观类", "主观动作")
    if word.endswith(('ous', 'ive', 'ful', 'less', 'able', 'ible', 'al', 'ic')):
        return ("客观类", "属性特征")
    if word.endswith(('er', 'or', 'ist', 'ian')):
        return ("客观类", "具体事物")
    return None

def build_full_category_dict():
    all_lemmas = set()
    for ss in wn.all_synsets():
        for lemma in ss.lemmas():
            name = lemma.name().lower()
            if '_' in name:
                if len(name) >= 2 and re.match(r'^[a-z_]+$', name):
                    all_lemmas.add(name)
            else:
                if name.isalpha() and len(name) > 1:
                    all_lemmas.add(name)
    print(f"Total lemmas: {len(all_lemmas)}")

    category_map = defaultdict(lambda: defaultdict(list))
    not_found = []

    for i, word in enumerate(all_lemmas):
        if i % 10000 == 0:
            print(f"Processed {i}/{len(all_lemmas)}")
        cats = get_categories_from_wordnet(word)
        if not cats:
            fb = fallback_category(word)
            if fb:
                cats = [fb]
        if cats:
            for main_cat, sub_cat in cats:
                category_map[main_cat][sub_cat].append(word)
        else:
            not_found.append(word)

    result = {main: dict(sub) for main, sub in category_map.items()}
    with open("data/categories_full.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Saved categories_full.json with {sum(len(lst) for sub in category_map.values() for lst in sub.values())} words")
    print(f"Remaining not classified: {len(not_found)} (example: {not_found[:20]})")

if __name__ == "__main__":
    import re
    build_full_category_dict()