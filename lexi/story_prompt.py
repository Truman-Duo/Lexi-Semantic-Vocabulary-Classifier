"""Style constraint prompt builders — separated from story.py to reduce coupling.
Only this module needs to import StyleProfile from style_analyzer."""

from typing import Optional
from .style_analyzer import StyleProfile


def build_style_constraints_en(profile: StyleProfile, style_name: str) -> str:
    label = f' style "{style_name}"' if style_name else ""
    parts = [
        f"\n\nApply these specific writing constraints derived from"
        f" quantitative analysis of the reference{label}:\n",
    ]
    if profile.avg_sentence_length > 0:
        parts.append(
            f"Sentence structure:\n"
            f"- Target average sentence length: ~{profile.avg_sentence_length:.0f} words\n"
            f"- Vary sentence length naturally (reference σ = {profile.sentence_length_std:.1f})\n"
        )
    if profile.avg_word_length > 0:
        parts.append(
            f"Vocabulary:\n"
            f"- Average word length: ~{profile.avg_word_length:.1f} characters\n"
        )
    if profile.type_token_ratio > 0:
        parts.append(
            f"- Vocabulary diversity (TTR): ~{profile.type_token_ratio:.2f}\n"
        )
    if profile.cefr_distribution:
        parts.append(f"- Target CEFR range: {profile.dominant_cefr()}\n")
    if profile.passive_voice_ratio > 0:
        parts.append(
            f"Voice:\n"
            f"- Passive voice: ~{profile.passive_voice_ratio*100:.0f}% of verb constructions\n"
        )
    if profile.flesch_kincaid_grade > 0:
        parts.append(
            f"Readability:\n"
            f"- Flesch-Kincaid grade level: ~{profile.flesch_kincaid_grade:.1f}\n"
            f"- Flesch Reading Ease: ~{profile.flesch_reading_ease:.1f}\n"
        )
    if any([
        profile.nominalization_ratio, profile.modifier_density,
        profile.lexical_density, profile.subordination_ratio,
        profile.coordination_ratio, profile.transition_density,
        profile.pronoun_density,
    ]):
        parts.append("Grammar and syntax:")
        if profile.nominalization_ratio > 0:
            parts.append(
                f"- Nominalization: ~{profile.nominalization_ratio*100:.0f}% of words "
                f"(use of -tion/-ment/-ity/-ness etc.)"
            )
        if profile.modifier_density > 0:
            parts.append(
                f"- Modifier density: ~{profile.modifier_density:.2f} "
                f"(adjectives + adverbs per content word)"
            )
        if profile.lexical_density > 0:
            parts.append(
                f"- Lexical density: ~{profile.lexical_density:.2f} "
                f"(content words ratio, i.e. information density)"
            )
        if profile.subordination_ratio > 0:
            parts.append(
                f"- Subordination: ~{profile.subordination_ratio:.1f} per sentence "
                f"(use of although/because/while/if/when clauses)"
            )
        if profile.coordination_ratio > 0:
            parts.append(
                f"- Coordination: ~{profile.coordination_ratio:.1f} per sentence "
                f"(use of and/but/or connections)"
            )
        if profile.transition_density > 0:
            parts.append(
                f"- Transition words: ~{profile.transition_density:.1f} per 100 words "
                f"(however/therefore/moreover etc.)"
            )
        if profile.pronoun_density > 0:
            parts.append(
                f"- Pronoun density: ~{profile.pronoun_density*100:.0f}% pronouns "
                f"(personal vs. impersonal style)"
            )
    return "\n".join(parts)


def build_style_constraints_zh(profile: StyleProfile, style_name: str) -> str:
    label = f'风格 "{style_name}"' if style_name else ""
    parts = [
        f"\n\n请应用以下从参考{label}中量化分析得出的写作约束：\n",
    ]
    if profile.avg_sentence_length > 0:
        parts.append(
            f"句子结构：\n"
            f"- 目标平均句长：约 {profile.avg_sentence_length:.0f} 词\n"
            f"- 句长自然变化（参考 σ = {profile.sentence_length_std:.1f}）\n"
        )
    if profile.avg_word_length > 0:
        parts.append(
            f"词汇：\n"
            f"- 平均词长：约 {profile.avg_word_length:.1f} 字符\n"
        )
    if profile.type_token_ratio > 0:
        parts.append(
            f"- 词汇多样性（型例比）：约 {profile.type_token_ratio:.2f}\n"
        )
    if profile.cefr_distribution:
        parts.append(f"- 目标 CEFR 范围：{profile.dominant_cefr()}\n")
    if profile.passive_voice_ratio > 0:
        parts.append(
            f"语态：\n"
            f"- 被动语态：约 {profile.passive_voice_ratio*100:.0f}% 的动词结构\n"
        )
    if profile.flesch_kincaid_grade > 0:
        parts.append(
            f"可读性：\n"
            f"- Flesch-Kincaid 年级水平：约 {profile.flesch_kincaid_grade:.1f}\n"
        )
    if any([
        profile.nominalization_ratio, profile.modifier_density,
        profile.lexical_density, profile.subordination_ratio,
        profile.coordination_ratio, profile.transition_density,
        profile.pronoun_density,
    ]):
        parts.append("语法与句法：")
        if profile.nominalization_ratio > 0:
            parts.append(
                f"- 名物化比例：约 {profile.nominalization_ratio*100:.0f}% "
                f"（-tion/-ment/-ity/-ness 等结尾词的使用密度）"
            )
        if profile.modifier_density > 0:
            parts.append(
                f"- 修饰词密度：约 {profile.modifier_density:.2f} "
                f"（形容词+副词 与 实词的比值）"
            )
        if profile.lexical_density > 0:
            parts.append(
                f"- 实词密度：约 {profile.lexical_density:.2f} "
                f"（信息密度指标）"
            )
        if profile.subordination_ratio > 0:
            parts.append(
                f"- 从属连词比例：约 {profile.subordination_ratio:.1f} 个/句 "
                f"（although/because/while/if/when 等从句）"
            )
        if profile.coordination_ratio > 0:
            parts.append(
                f"- 并列连词比例：约 {profile.coordination_ratio:.1f} 个/句 "
                f"（and/but/or 等连接）"
            )
        if profile.transition_density > 0:
            parts.append(
                f"- 过渡词密度：约 {profile.transition_density:.1f} 个/100词 "
                f"（however/therefore/moreover 等）"
            )
        if profile.pronoun_density > 0:
            parts.append(
                f"- 代词密度：约 {profile.pronoun_density*100:.0f}% "
                f"（人称化 vs. 非人称化风格）"
            )
    return "\n".join(parts)
